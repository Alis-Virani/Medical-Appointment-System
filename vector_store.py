import os
import sys
import time
import hashlib
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

# ── Relevance threshold ──────────────────────────────────────────────────────
# Quadrant DB uses similarity scores (0-1); higher = more similar.
# Results with score < SIMILARITY_THRESHOLD are considered irrelevant and dropped.
SIMILARITY_THRESHOLD = 0.6  # tune: 1.0 = identical, 0.0 = totally unrelated

# ── Chunking parameters ──────────────────────────────────────────────────────
CHUNK_SIZE = 600    # characters per chunk
CHUNK_OVERLAP = 100 # overlap between consecutive chunks

# ── Embedding model ──────────────────────────────────────────────────────────
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # dimension of all-MiniLM-L6-v2


def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks for better semantic coverage."""
    text = text.strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start += chunk_size - overlap
    return chunks


def _doc_hash(text: str) -> str:
    """Short content hash used for deduplication."""
    return hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest()[:12]


def _text_to_hash_id(text: str) -> int:
    """Convert text to deterministic integer ID for Quadrant DB (uint64)."""
    hash_int = int(hashlib.md5(text.encode("utf-8", errors="replace")).hexdigest(), 16)
    return hash_int % (2**63)  # Keep it positive uint64


class MedicalVectorStore:
    def __init__(self, collection_name: str = "medical_knowledge"):
        self.collection_name = collection_name
        self.embedding_model = None
        self.client = None
        
        try:
            # Initialize Quadrant DB client (in-memory)
            self.client = QdrantClient(":memory:")
            
            # Load embedding model
            self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
            
            # Create or get collection
            self._ensure_collection()
            
        except Exception as e:
            print(f"[WARN] Vector Store Error ({collection_name}): {e}")
            self.client = None

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        if not self.client:
            return
        try:
            self.client.get_collection(self.collection_name)
        except Exception:
            # Collection doesn't exist, create it
            try:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=EMBEDDING_DIM,
                        distance=Distance.COSINE
                    ),
                )
            except Exception as e:
                print(f"[WARN] Failed to create collection {self.collection_name}: {e}")

    def _embed_text(self, text: str) -> List[float]:
        """Generate embedding for text using sentence-transformers."""
        if not self.embedding_model:
            return [0.0] * EMBEDDING_DIM
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"[WARN] Embedding error: {e}")
            return [0.0] * EMBEDDING_DIM

    # ── Low-level add ────────────────────────────────────────────────────────
    def add_texts(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add raw texts with embeddings. Skips duplicates by id."""
        if not self.client or not texts:
            return
        
        try:
            # Generate embeddings and create points
            points = []
            for text, metadata, doc_id in zip(texts, metadatas, ids):
                embedding = self._embed_text(text)
                
                # Convert string ID to integer for Quadrant DB (deterministic)
                point_id = _text_to_hash_id(doc_id)
                
                # Prepare payload (metadata + text)
                payload = {
                    "text": text,
                    **metadata
                }
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
            
            # Upsert points (auto-handles duplicates)
            if points:
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
        except Exception as e:
            print(f"[WARN] Vector Store add error: {e}")

    # ── Smart report storage ─────────────────────────────────────────────────
    def add_report(
        self,
        text: str,
        filename: str,
        user_id: str,
        session_id: Optional[str] = None,
    ) -> int:
        """
        Chunk `text` and store each chunk with metadata.
        Deduplicates at chunk level using content hash + user_id.
        Returns the number of new chunks stored.
        """
        if not self.client or not text:
            return 0
        chunks = _chunk_text(text)
        stored = 0
        ts = int(time.time())
        for i, chunk in enumerate(chunks):
            chunk_hash = _doc_hash(chunk)
            doc_id = f"{user_id}_{filename}_{chunk_hash}"
            meta: Dict = {
                "filename": filename,
                "user_id": str(user_id),
                "session_id": str(session_id or user_id),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "stored_at": ts,
            }
            self.add_texts([chunk], [meta], [doc_id])
            stored += 1
        return stored

    # ── Semantic search ──────────────────────────────────────────────────────
    def search(self, query: str, n_results: int = 3) -> Dict:
        """Full-collection semantic search with similarity filtering."""
        if not self.client:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            if collection_info.points_count == 0:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            # Embed query
            query_embedding = self._embed_text(query)
            
            # Search in Quadrant DB using query_points
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=min(n_results, collection_info.points_count),
                with_payload=True
            )
            
            return self._format_results(results.points)
        except Exception as e:
            print(f"[WARN] Vector Store search error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def search_by_user(
        self,
        query: str,
        user_id: str,
        n_results: int = 4,
    ) -> Dict:
        """
        Semantic search scoped to a specific user_id.
        Falls back to full search if user has no documents yet.
        """
        if not self.client:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        try:
            collection_info = self.client.get_collection(self.collection_name)
            if collection_info.points_count == 0:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
            
            # Embed query
            query_embedding = self._embed_text(query)
            
            # Build filter for user_id using Quadrant DB Filter object
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="user_id",
                        match=MatchValue(value=str(user_id))
                    )
                ]
            )
            
            # Search with user_id filter using query_points
            results = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=min(n_results, collection_info.points_count),
                with_payload=True,
                query_filter=query_filter
            )
            
            return self._format_results(results.points)
        except Exception as e:
            print(f"[WARN] Vector Store user-search error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

    def delete_report(self, filename: str, user_id: str):
        """Remove all chunks belonging to a specific report for a user."""
        if not self.client:
            return
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector={
                    "filter": {
                        "must": [
                            {"key": "user_id", "match": {"value": str(user_id)}},
                            {"key": "filename", "match": {"value": filename}}
                        ]
                    }
                }
            )
        except Exception as e:
            print(f"[WARN] Vector Store delete error: {e}")

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _format_results(self, scored_points) -> Dict:
        """Convert Quadrant DB scored points to ChromaDB-like format."""
        docs = []
        metas = []
        scores = []
        
        for point in scored_points:
            # Filter by similarity threshold
            if point.score < SIMILARITY_THRESHOLD:
                continue
            
            payload = point.payload or {}
            doc_text = payload.pop("text", "")
            
            docs.append(doc_text)
            metas.append(payload)
            scores.append(point.score)
        
        if not docs:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        return {
            "documents": [docs],
            "metadatas": [metas],
            "distances": [scores],  # Now scores (0-1), not distances
        }
    
    # ── Index Medical Knowledge from SQLite ──────────────────────────────────
    def index_medical_knowledge(self):
        """Index medical conditions, herbs, and drug interactions from SQLite"""
        import sqlite3
        
        print("📚 Indexing medical knowledge in vector store...")
        indexed = 0
        
        try:
            conn = sqlite3.connect("hospital.db", timeout=10)
            cur = conn.cursor()
            
            # Index medical conditions
            print("   → Indexing medical conditions...")
            cur.execute("""
                SELECT condition_name, symptoms, causes, complications, prevention, severity
                FROM medical_conditions
            """)
            
            for row in cur.fetchall():
                condition_name = row[0]
                # Create rich text for better semantic search
                full_text = f"""
                CONDITION: {condition_name}
                Symptoms: {row[1]}
                Causes: {row[2]}
                Complications: {row[3]}
                Prevention: {row[4]}
                Severity: {row[5]}
                """
                
                doc_id = f"condition_{condition_name.replace(' ', '_')}"
                metadata = {
                    "type": "medical_condition",
                    "name": condition_name,
                    "severity": row[5] or "medium"
                }
                
                self.add_texts([full_text], [metadata], [doc_id])
                indexed += 1
            
            # Index herb remedies
            print("   → Indexing herb remedies...")
            cur.execute("""
                SELECT herb_name, benefits, conditions_treat, dosage, side_effects, scientific_name
                FROM herb_remedies
            """)
            
            for row in cur.fetchall():
                herb_name = row[0]
                # Create rich text for semantic search
                full_text = f"""
                HERB: {herb_name}
                Benefits: {row[1]}
                Treats: {row[2]}
                Dosage: {row[3]}
                Side Effects: {row[4]}
                Scientific Name: {row[5]}
                """
                
                doc_id = f"herb_{herb_name.replace(' ', '_')}"
                metadata = {
                    "type": "herb_remedy",
                    "name": herb_name,
                    "treats": row[2] or ""
                }
                
                self.add_texts([full_text], [metadata], [doc_id])
                indexed += 1
            
            # Index drug interactions
            print("   → Indexing drug interactions...")
            cur.execute("""
                SELECT drug1, drug2, severity, effect, recommendation
                FROM drug_interactions
            """)
            
            for row in cur.fetchall():
                # Create text for drug interactions
                full_text = f"""
                DRUG INTERACTION WARNING
                Drugs: {row[0]} + {row[1]}
                Severity: {row[2]}
                Effect: {row[3]}
                Recommendation: {row[4]}
                """
                
                doc_id = f"interaction_{row[0]}_{row[1]}".replace(" ", "_")
                metadata = {
                    "type": "drug_interaction",
                    "drug1": row[0],
                    "drug2": row[1],
                    "severity": row[2]
                }
                
                self.add_texts([full_text], [metadata], [doc_id])
                indexed += 1
            
            conn.close()
            print(f"   ✅ Indexed {indexed} medical items in vector store\n")
            
        except Exception as e:
            print(f"   ⚠️  Error indexing medical knowledge: {e}\n")


# ── Singleton registry ───────────────────────────────────────────────────────
_stores: dict = {}

def get_vector_store(collection_name: str = "medical_knowledge") -> MedicalVectorStore:
    """Return (or create) the singleton MedicalVectorStore for the given collection."""
    global _stores
    if collection_name not in _stores:
        store = MedicalVectorStore(collection_name=collection_name)
        _stores[collection_name] = store
        
        # Index medical knowledge on first load
        if collection_name == "medical_knowledge":
            store.index_medical_knowledge()
    
    return _stores[collection_name]

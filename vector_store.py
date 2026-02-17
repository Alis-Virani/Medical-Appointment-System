import os
import sys

# Windows-specific SQLite3 fix for ChromaDB
if sys.platform.startswith("win"):
    try:
        import pysqlite3
        sys.modules["sqlite3"] = pysqlite3
    except ImportError:
        pass

import chromadb
from chromadb.utils import embedding_functions
from typing import List, Dict

class MedicalVectorStore:
    def __init__(self, collection_name="medical_knowledge"):
        try:
            self.client = chromadb.PersistentClient(path="./chroma_db")
            self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_fn
            )
        except Exception as e:
            print(f"⚠️ Vector Store Error: {e}")
            self.client = None
            self.collection = None

    def add_texts(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add texts to valid collection"""
        if self.collection:
            self.collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )

    def search(self, query: str, n_results: int = 3):
        """Semantic search"""
        if self.collection:
            return self.collection.query(
                query_texts=[query],
                n_results=n_results
            )
        return {"documents": [], "metadatas": []}

# Singleton
_vector_store = None
def get_vector_store():
    global _vector_store
    if _vector_store is None:
        _vector_store = MedicalVectorStore()
    return _vector_store

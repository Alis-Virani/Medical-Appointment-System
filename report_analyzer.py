import pdfplumber
from PIL import Image
import io
import base64
import requests

# Lazy-load EasyOCR — only initialized when first needed
_reader = None
_easyocr_failed = False  # Track if EasyOCR failed to load

def _get_reader():
    """Get or initialize the EasyOCR reader (lazy loading)."""
    global _reader, _easyocr_failed
    if _easyocr_failed:
        return None
    if _reader is None:
        try:
            import easyocr
            _reader = easyocr.Reader(['en'], gpu=False)
        except Exception:
            _easyocr_failed = True
            return None
    return _reader

def _resize_image(image_bytes, max_size=1200):
    """Resize image to max_size on longest side to reduce memory usage."""
    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()

def _ollama_vision(image_bytes, filename):
    """Use Ollama llama3.2-vision as fallback OCR."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2-vision",
                "prompt": "Extract all visible text from this medical report image. List every value, label, and finding you can see.",
                "images": [image_b64],
                "stream": False
            },
            timeout=60
        )
        if response.status_code == 200:
            result = response.json().get("response", "")
            return f"🖼️ **Vision Analysis ({filename}):**\n\n{result}"
        else:
            return f"⚠️ Ollama error: {response.text}"
    except requests.exceptions.ConnectionError:
        return "⚠️ Could not process image. EasyOCR ran out of memory and Ollama is not running. Please run 'ollama serve' in a terminal."
    except Exception as e:
        return f"❌ Vision fallback error: {str(e)}"

def analyze_medical_report(uploaded_file):
    """
    Analyze medical report (PDF or Image).
    Uses EasyOCR for images, falls back to Ollama Vision if EasyOCR fails.
    Uses pdfplumber for PDFs.
    """
    try:
        # Handle PDF
        if uploaded_file.type == "application/pdf":
            text = ""
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            if not text.strip():
                return "⚠️ PDF seems to be an image scan. Please upload as PNG/JPG for OCR."
            return f"📄 **PDF Report ({uploaded_file.name}):**\n\n{text[:4000]}"

        # Handle Images
        elif uploaded_file.type in ["image/png", "image/jpeg", "image/jpg"]:
            raw_bytes = uploaded_file.read()

            # Try EasyOCR first
            reader = _get_reader()
            if reader is not None:
                try:
                    image_bytes = _resize_image(raw_bytes, max_size=1200)
                    results = reader.readtext(image_bytes)
                    extracted_text = "\n".join(
                        [text for (_, text, conf) in results if conf > 0.3]
                    )
                    if extracted_text.strip():
                        return f"🖼️ **OCR Report ({uploaded_file.name}):**\n\n{extracted_text}"
                except Exception:
                    pass  # Fall through to Ollama

            # Fallback: Ollama Vision
            return _ollama_vision(raw_bytes, uploaded_file.name)

        else:
            return "⚠️ Unsupported file format."

    except Exception as e:
        return f"❌ Error analyzing report: {str(e)}"

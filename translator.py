try:
    from deep_translator import GoogleTranslator
    from langdetect import detect, detect_langs, LangDetectException
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    print("⚠️ Translation modules not found. Running in English-only mode.")

# Minimum character length before trusting language detection.
# Short inputs like "continue", "ok", "yes" are easily misidentified.
_MIN_DETECT_LENGTH = 20
# Minimum confidence probability required to override English.
_MIN_CONFIDENCE = 0.90

def detect_language(text: str, fallback_lang: str = "en") -> str:
    """
    Detect the language of the input text.
    Returns ISO 639-1 language code (e.g., 'en', 'hi', 'gu').

    Short or ambiguous inputs (< _MIN_DETECT_LENGTH chars, or confidence
    below _MIN_CONFIDENCE) fall back to `fallback_lang` (default 'en') to
    avoid misidentifying common English words as other languages.
    """
    if not TRANSLATION_AVAILABLE:
        return "en"
        
    try:
        if not text or not text.strip():
            return fallback_lang
        # For very short text, don't trust detection – too error-prone.
        if len(text.strip()) < _MIN_DETECT_LENGTH:
            return fallback_lang
        # Use detect_langs for a confidence score.
        langs = detect_langs(text)
        top = langs[0]  # highest-probability language
        if top.lang == 'en':
            return 'en'
        # Only accept a non-English detection if confidence is high enough.
        if top.prob >= _MIN_CONFIDENCE:
            return top.lang
        return fallback_lang
    except Exception:
        return fallback_lang

def translate_to_english(text: str) -> dict:
    """
    Translate text to English using deep-translator.
    Returns dict with 'original_text', 'translated_text', 'source_lang'.
    """
    default_response = {"original": text, "translated": text, "lang": "en"}
    
    if not TRANSLATION_AVAILABLE:
        return default_response

    try:
        if not text:
            return default_response
            
        lang = detect_language(text)
        if lang == 'en':
            return default_response
            
        translated = GoogleTranslator(source='auto', target='en').translate(text)
        return {
            "original": text, 
            "translated": translated, 
            "lang": lang
        }
    except Exception as e:
        print(f"Translation error: {e}")
        return default_response

def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text to target language using deep-translator.
    """
    if not TRANSLATION_AVAILABLE or target_lang == 'en' or not text:
        return text

    try:
        return GoogleTranslator(source='en', target=target_lang).translate(text)
    except Exception as e:
        print(f"Translation error (to {target_lang}): {e}")
        return text

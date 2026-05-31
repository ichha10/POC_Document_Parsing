import os
import re
import hashlib
from typing import List
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Try to import Google GenAI
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def get_embedding(text: str) -> List[float]:
    """
    Generates a dense vector embedding.
    # Live Mode: If GEMINI_API_KEY is found, calls Gemini's models/gemini-embedding-2 (3072 dimensions) using the modern google-genai client.
    # Mock Mode: If no key, builds a deterministic 128-dim normalized bag-of-words vector.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key and HAS_GENAI:
        try:
            client = genai.Client(api_key=api_key)
            result = client.models.embed_content(
                model="models/gemini-embedding-2",
                contents=text
            )
            if result.embeddings and len(result.embeddings) > 0:
                return result.embeddings[0].values
        except Exception as e:
            # Avoid emoji print to prevent UnicodeEncodeError on standard Windows CP1252 consoles
            print(f"[API WARNING] Live Gemini embedding failed (falling back to offline mock): {e}")

    # Offline/Mock Mode: Deterministic Bag-of-Words Vector Space Model
    vector = [0.0] * 128
    words = text.lower().split()
    
    # Simple English stop words to filter out
    stop_words = {"the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "of", "to", "in", "on", "at", "by", "for", "with", "about", "that", "this", "these", "those"}
    
    for word in words:
        # Clean word from punctuation
        word_clean = re.sub(r"[^\w]", "", word)
        if len(word_clean) > 2 and word_clean not in stop_words:
            # MD5 hash mapping to 128 indices
            h = int(hashlib.md5(word_clean.encode('utf-8')).hexdigest(), 16)
            vector[h % 128] += 1.0
            
    # Normalize to unit length (L2 norm) so cosine similarity is just the dot product
    norm = sum(x**2 for x in vector)**0.5
    if norm > 0:
        vector = [x / norm for x in vector]
        
    return vector

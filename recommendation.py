import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from url_utils import extract_text_from_url

# Load assessment data
with open("data/assessments.json", "r", encoding="utf-8") as f:
    assessments = json.load(f)

# Initialize embedding model and Faiss index
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
corpus = [f"{a['name']}: {a.get('description','')}" for a in assessments]
embeddings = model.encode(corpus, show_progress_bar=True)
# Normalize for cosine similarity
embeddings = np.vstack([v / np.linalg.norm(v) for v in embeddings]).astype('float32')
index = faiss.IndexFlatIP(embeddings.shape[1])
index.add(embeddings)

# Recommendation function
def recommend_assessments(query: str, top_k: int = 10):
    # If query is a URL, extract text first
    if query.startswith("http"):
        query = extract_text_from_url(query)
    # Encode and normalize
    q_vec = model.encode([query])
    q_vec = q_vec / np.linalg.norm(q_vec)
    q_vec = q_vec.astype('float32')
    # Search
    D, I = index.search(q_vec, top_k)
    results = []
    for idx, score in zip(I[0], D[0]):
        a = assessments[idx]
        results.append({
            "name": a["name"],
            "url": a["url"],
            "remote": a["remote"],
            "adaptive": a["adaptive"],
            "duration_minutes": a.get("duration_minutes"),
            "test_type": a.get("test_type")
        })
    return results
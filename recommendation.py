import json
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from url_utils import extract_text_from_url

# --- 1. Load SHL assessment data ---------------------------------------------
with open("data/assessments.json", encoding="utf-8") as f:
    assessments = json.load(f)

# --- 2. Build embedding model & FAISS index ---------------------------------
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Combine name + description for richer context
corpus_texts = [
    f"{a['name']}. {a.get('description','')}" for a in assessments
]
# Encode and normalize to unit‑length
embs = model.encode(corpus_texts, normalize_embeddings=True)
emb_matrix = np.vstack(embs).astype("float32")

# FAISS index for inner‑product (cosine) search
index = faiss.IndexFlatIP(emb_matrix.shape[1])
index.add(emb_matrix)

# --- 3. Keyword set for boosting (customizable) ------------------------------
BOOST_KEYWORDS = {
    "engineering", "devops", "ci/cd", "cloud", "docker", "kubernetes",
    "performance", "monitoring", "security", "testing", "agile",
    "data", "analysis", "leadership", "collaboration"
}

def extract_kw(text: str):
    toks = [t.lower().strip(".,()") for t in text.split()]
    return {kw for kw in BOOST_KEYWORDS if kw in toks}

# --- 4. Recommendation function ---------------------------------------------
def recommend_assessments(query: str, top_k: int = 10):
    """
    Args:
      query: natural‑language text or URL
      top_k: return up to this many assessments (min 1)
    Returns: list of dicts with keys name, url, remote, adaptive, duration_minutes, test_type
    """
    # 4.1 Handle URLs
    if query.startswith("http"):
        query = extract_text_from_url(query)

    # 4.2 Embed & normalize
    q_emb = model.encode([query], normalize_embeddings=True)[0]
    q_vec = np.array(q_emb, dtype="float32")

    # 4.3 Retrieve top candidates (search more to allow rerank)
    n_search = min(len(assessments), top_k * 3)
    scores, idxs = index.search(np.expand_dims(q_vec, 0), n_search)
    candidates = []

    # Pre‑extract keywords from query
    q_kw = extract_kw(query)

    # 4.4 Hybrid rerank: score + 0.1×(keyword overlap)
    for sim_score, idx in zip(scores[0], idxs[0]):
        a = assessments[idx]
        text = f"{a['name']}. {a.get('description','')}"
        overlap = len(q_kw & extract_kw(text))
        hybrid = float(sim_score) + 0.1 * overlap
        candidates.append((hybrid, a))

    # 4.5 Pick top_k after rerank
    candidates.sort(key=lambda x: x[0], reverse=True)
    top = candidates[:max(1, min(top_k, len(candidates)))]

    # 4.6 Format results per PDF spec
    results = []
    for _, a in top:
        results.append({
            "name": a["name"],
            "url": a["url"],
            "remote": a["remote"],
            "adaptive": a["adaptive"],
            "duration_minutes": a.get("duration_minutes"),
            "test_type": a.get("test_type")
        })
    return results

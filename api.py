from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from recommendation import recommend_assessments
from url_utils import extract_text_from_url

app = FastAPI()

class RecommendQuery(BaseModel):
    text: str

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/recommend")
async def recommend_endpoint(query: RecommendQuery):
    text = query.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Query text is empty.")
    # Handle URLs
    if text.startswith("http"):
        text = extract_text_from_url(text)
    results = recommend_assessments(text, top_k=10)
    if not results:
        raise HTTPException(status_code=404, detail="No recommendations found.")
    return {"query": text, "recommendations": results}
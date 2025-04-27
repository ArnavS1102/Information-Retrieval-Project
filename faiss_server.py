from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import numpy as np

app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')  
index = faiss.read_index("faiss/faiss.index")    
with open("faiss/metadata.pkl", "rb") as f:
    id_to_metadata = pickle.load(f)              

# Request format
class QueryRequest(BaseModel):
    query: str
    top_k: int = 5

@app.post("/search")
def search_query(req: QueryRequest):
    query_embedding = model.encode([req.query], convert_to_numpy=True)
    faiss.normalize_L2(query_embedding)

    distances, indices = index.search(query_embedding, req.top_k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        meta = id_to_metadata.get(idx, {})
        results.append({
            "url": meta.get("url", ""),
            "title": meta.get("title", ""),
            "meta_description": meta.get("meta_description", ""),
            "score": float(dist)
        })

    return {"results": results}

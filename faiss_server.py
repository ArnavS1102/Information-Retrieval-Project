# from fastapi import FastAPI
# from pydantic import BaseModel
# from vector_model import BertFaissVectorModel
# from link_model import SearchEngine
# from sentence_transformers import SentenceTransformer
# import os
# import asyncio


# combined_data_path = "combined_data_new.csv"  # ⚡ Update this path
# cache_dir = "faiss"
# model = SentenceTransformer('all-MiniLM-L6-v2')
# vector_model = BertFaissVectorModel(data_path=combined_data_path, cache_dir=cache_dir)

# app = FastAPI()
# # def load_model():
# #     print("Loading model (blocking)...")
# #     return SentenceTransformer('all-MiniLM-L6-v2')

# # @app.on_event("startup")
# # async def startup_event():
# #     global model
# #     loop = asyncio.get_event_loop()
# #     model = await loop.run_in_executor(None, load_model)
# #     print("✅ Model loaded.")

# # Initialize vector model

# # Initialize search engine (loads LinkAnalysisModel inside)
# # search_engine = SearchEngine(vector_model, combined_data_path)

# # --- Request format ---
# class QueryRequest(BaseModel):
#     query: str
#     top_k: int = 10

# # --- API Endpoints ---

# @app.post("/search/vector")
# def search_vector(req: QueryRequest):
#     results = vector_model.search(req.query, model, top_k=req.top_k)
#     return {"results": results}

# # @app.post("/search/pagerank")
# # def search_pagerank(req: QueryRequest):
# #     results = search_engine.pagerank_model(req.query, top_k=req.top_k)
# #     return {"results": results}

# # @app.post("/search/hits")
# # def search_hits(req: QueryRequest):
# #     results = search_engine.hits_model(req.query, top_k=req.top_k)
# #     return {"results": results}

# # @app.post("/search/hybrid")
# # def search_hybrid(req: QueryRequest):
# #     results = search_engine.hybrid_model(req.query, top_k=req.top_k)
# #     return {"results": results}


from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from link_model import SearchEngine
import faiss
import pickle
import numpy as np

app = FastAPI()

model = SentenceTransformer('all-MiniLM-L6-v2')  
index = faiss.read_index("faiss/faiss.index")    
with open("faiss/metadata.pkl", "rb") as f:
    id_to_metadata = pickle.load(f)    
    
search_engine = SearchEngine(model, "combined_data_new.csv") 
    
# Request format
class QueryRequest(BaseModel):
    query: str
    top_k: int = 10

@app.post("/search/vector")
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

@app.post("/search/pagerank")
def search_pagerank(req: QueryRequest):
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
    results = search_engine.pagerank_model(req.query, results,top_k=req.top_k)
    return {"results": results}

@app.post("/search/hits")
def search_hits(req: QueryRequest):
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
    results = search_engine.hits_model(req.query, results, top_k=req.top_k)
    return {"results": results}

@app.post("/search/hybrid")
def search_hybrid(req: QueryRequest):
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
    results = search_engine.hybrid_model(req.query, results, top_k=req.top_k)
    # results = search_engine.hybrid_model(req.query, top_k=req.top_k)
    return {"results": results}
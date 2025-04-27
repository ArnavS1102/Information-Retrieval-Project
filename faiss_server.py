from fastapi import FastAPI
from pydantic import BaseModel
from vector_model import BertFaissVectorModel
from link_model import SearchEngine
import os

# --- Setup FastAPI ---
app = FastAPI()

# --- Load Everything Once ---

# Set paths
combined_data_path = "combined_data.csv"  # ⚡ Update this path
cache_dir = "faiss"  # Folder where faiss.index and metadata.pkl are saved

# Initialize vector model
vector_model = BertFaissVectorModel(data_path=combined_data_path, cache_dir=cache_dir)

# Initialize search engine (loads LinkAnalysisModel inside)
search_engine = SearchEngine(vector_model)

# --- Request format ---
class QueryRequest(BaseModel):
    query: str
    top_k: int = 10

# --- API Endpoints ---

@app.post("/search/vector")
def search_vector(req: QueryRequest):
    results = vector_model.search(req.query, top_k=req.top_k)
    return {"results": results}

@app.post("/search/pagerank")
def search_pagerank(req: QueryRequest):
    results = search_engine.pagerank_model(req.query, top_k=req.top_k)
    return {"results": results}

@app.post("/search/hits")
def search_hits(req: QueryRequest):
    results = search_engine.hits_model(req.query, top_k=req.top_k)
    return {"results": results}

@app.post("/search/hybrid")
def search_hybrid(req: QueryRequest):
    results = search_engine.hybrid_model(req.query, top_k=req.top_k)
    return {"results": results}

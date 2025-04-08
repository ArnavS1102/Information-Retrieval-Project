import os
import pandas as pd
import numpy as np
import hashlib
import pickle
import faiss
from sentence_transformers import SentenceTransformer

class BertFaissVectorSpaceModel:
    def __init__(self, data_path, cache_dir, model_name='all-MiniLM-L6-v2'):
        self.data_path = data_path
        self.cache_dir = cache_dir
        self.df = pd.read_csv(data_path)
        self.index = None
        self.indexed_df = pd.DataFrame()
        self.doc_hashes = {}
        self.model = SentenceTransformer(model_name)
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()

    def _text_hash(self, url, full_text):
        key = f"{url}::{full_text}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def _load_cache(self):
        if os.path.exists(f"{self.cache_dir}/faiss_index.bin"):
            self.index = faiss.read_index(f"{self.cache_dir}/faiss_index.bin")
        if os.path.exists(f"{self.cache_dir}/indexed_df.csv"):
            self.indexed_df = pd.read_csv(f"{self.cache_dir}/indexed_df.csv")
        if os.path.exists(f"{self.cache_dir}/doc_hashes.pkl"):
            with open(f"{self.cache_dir}/doc_hashes.pkl", "rb") as f:
                self.doc_hashes = pickle.load(f)

    def _save_cache(self):
        if self.index is not None:
            faiss.write_index(self.index, f"{self.cache_dir}/faiss_index.bin")
        self.indexed_df.to_csv(f"{self.cache_dir}/indexed_df.csv", index=False)
        with open(f"{self.cache_dir}/doc_hashes.pkl", "wb") as f:
            pickle.dump(self.doc_hashes, f)

    def preprocess_and_vectorize(self):
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)
        new_rows = []
        new_texts = []
        hashes = {}

        for _, row in self.df.iterrows():
            url = row['url']
            full_text = row['full_text']
            doc_hash = self._text_hash(url, full_text)
            if url not in self.doc_hashes or self.doc_hashes[url] != doc_hash:
                new_rows.append(row)
                new_texts.append(full_text)
                hashes[url] = doc_hash

        if new_texts:
            print(f"Indexing {len(new_texts)} new or updated documents...")
            embeddings = self.model.encode(new_texts, show_progress_bar=True, convert_to_numpy=True)

            self.index = faiss.IndexFlatL2(embeddings.shape[1])
            self.index.add(embeddings)

            self.indexed_df = pd.DataFrame(new_rows)
            self.doc_hashes.update(hashes)
            self._save_cache()
        else:
            print("No new or updated documents to index.")

    def search(self, query, top_k=10):
        if self.index is None or self.indexed_df.empty:
            print("FAISS index not initialized. Run preprocess_and_vectorize() first.")
            return pd.DataFrame(), []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        results = self.indexed_df.iloc[indices[0]]
        return results[['url']], distances[0]

if __name__ == "__main__":
    model = BertFaissVectorSpaceModel("../combined_data.csv", cache_dir="./cache")
    model.preprocess_and_vectorize()
    query = input("Enter your search query: ")
    results, scores = model.search(query)
    print("\nTop Results:\n")
    for i, (url, score) in enumerate(zip(results['url'], scores)):
        print(f"{i+1}. {url} (distance: {score:.4f})")

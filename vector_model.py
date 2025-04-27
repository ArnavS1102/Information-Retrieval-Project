# import os
# import pandas as pd
# import numpy as np
# import hashlib
# import pickle
# from sentence_transformers import SentenceTransformer
# from sklearn.neighbors import NearestNeighbors

# class BertKNNVectorModel:
#     def __init__(self, data_path, cache_dir, model_name='all-MiniLM-L6-v2'):
#         self.data_path = data_path
#         self.cache_dir = cache_dir
#         self.df = pd.read_csv(data_path)
#         self.indexed_df = pd.DataFrame()
#         self.doc_hashes = {}
#         self.model = SentenceTransformer(model_name)
#         self.knn_index = None
#         self.embeddings = None
#         os.makedirs(cache_dir, exist_ok=True)
#         self._load_cache()

#     def _text_hash(self, url, full_text):
#         return hashlib.md5(f"{url}::{full_text}".encode('utf-8')).hexdigest()

#     def _load_cache(self):
#         if os.path.exists(f"{self.cache_dir}/indexed_df.csv"):
#             self.indexed_df = pd.read_csv(f"{self.cache_dir}/indexed_df.csv")
#         if os.path.exists(f"{self.cache_dir}/doc_hashes.pkl"):
#             with open(f"{self.cache_dir}/doc_hashes.pkl", "rb") as f:
#                 self.doc_hashes = pickle.load(f)
#         if os.path.exists(f"{self.cache_dir}/embeddings.npy"):
#             self.embeddings = np.load(f"{self.cache_dir}/embeddings.npy")

#     def _save_cache(self):
#         self.indexed_df.to_csv(f"{self.cache_dir}/indexed_df.csv", index=False)
#         with open(f"{self.cache_dir}/doc_hashes.pkl", "wb") as f:
#             pickle.dump(self.doc_hashes, f)
#         if self.embeddings is not None:
#             np.save(f"{self.cache_dir}/embeddings.npy", self.embeddings)

#     def preprocess_and_index(self):
#         self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)
#         new_rows, new_texts, hashes = [], [], {}

#         for _, row in self.df.iterrows():
#             url = row['url']
#             full_text = row['full_text']
#             doc_hash = self._text_hash(url, full_text)
#             if url not in self.doc_hashes or self.doc_hashes[url] != doc_hash:
#                 new_rows.append(row)
#                 new_texts.append(full_text)
#                 hashes[url] = doc_hash

#         if new_texts:
#             # print(f"Indexing {len(new_texts)} new or updated documents...")
#             new_embeddings = self.model.encode(new_texts, show_progress_bar=True, convert_to_numpy=True)

#             self.embeddings = new_embeddings
#             self.indexed_df = pd.DataFrame(new_rows)
#             self.doc_hashes.update(hashes)

#             self.knn_index = NearestNeighbors(n_neighbors=10, metric='cosine')
#             self.knn_index.fit(self.embeddings)

#             self._save_cache()
#         # else:
#             # print("No new documents to index.")

#     def search(self, query, top_k=10):
#         if self.embeddings is None or self.indexed_df.empty:
#             # print("No index available. Run preprocess_and_index() first.")
#             return []

#         query_embedding = self.model.encode([query], convert_to_numpy=True)
#         self.knn_index = NearestNeighbors(n_neighbors=top_k, metric='cosine')
#         self.knn_index.fit(self.embeddings)
#         distances, indices = self.knn_index.kneighbors(query_embedding)

#         results = self.indexed_df.iloc[indices[0]].copy()
#         results['score'] = 1 - distances[0]  # Cosine similarity

#         def resolve_description(row):
#             if pd.isna(row['meta_description']) or not row['meta_description'] or row['meta_description']=='No Description':
#                 tokens = row['body_text'].split()
#                 return ' '.join(tokens[:30])
#             return row['meta_description']

#         results['meta_description'] = results.apply(resolve_description, axis=1)

#         # Convert to JSON-serializable output
#         json_results = results[['url', 'title', 'meta_description', 'score']].to_dict(orient='records')
#         # json_results = results[['url', 'title', 'meta_description']].to_dict(orient='records')
#         return json_results



import os
import pandas as pd
import numpy as np
import faiss
import pickle
from urllib.parse import urlparse
from sentence_transformers import SentenceTransformer
import hashlib

class BertFaissVectorModel:
    def __init__(self, data_path, cache_dir, model_name='all-MiniLM-L6-v2'):
        self.data_path = data_path
        self.cache_dir = cache_dir
        self.df = pd.read_csv(data_path)
        os.makedirs(cache_dir, exist_ok=True)

        self.model = SentenceTransformer(model_name)
        self.index = None
        self.id_to_metadata = {}

        self.index_path = os.path.join(cache_dir, "faiss.index")
        self.meta_path = os.path.join(cache_dir, "metadata.pkl")

        self._load_index()

    def _load_index(self):
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            print("Loading FAISS index and metadata...")
            self.index = faiss.read_index(self.index_path)
            with open(self.meta_path, "rb") as f:
                self.id_to_metadata = pickle.load(f)

    def _save_index(self):
        faiss.write_index(self.index, self.index_path)
        with open(self.meta_path, "wb") as f:
            pickle.dump(self.id_to_metadata, f)

    def _text_hash(self, url, full_text):
        return hashlib.md5(f"{url}::{full_text}".encode('utf-8')).hexdigest()

    def preprocess_and_index(self):
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)

        texts = self.df['full_text'].tolist()
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

        d = embeddings.shape[1]  
        self.index = faiss.IndexFlatIP(d)  

        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

        for idx, row in self.df.iterrows():
            self.id_to_metadata[idx] = {
                "url": row['url'],
                "title": row['title'],
                "meta_description": row['meta_description'],
                "body_text": row['body_text'],
                "depth": row['depth'],
                "last_crawled": row['last_crawled']
            }

        self._save_index()
        print(f"✅ Indexed {len(texts)} documents.")

    def search(self, query, top_k=10):
        if self.index is None:
            raise ValueError("Index not loaded. Run preprocess_and_index() first.")

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(query_embedding)

        distances, indices = self.index.search(query_embedding, top_k)
        hits = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            meta = self.id_to_metadata.get(idx, {})
            hits.append({
                "url": meta.get("url", ""),
                "title": meta.get("title", ""),
                "meta_description": meta.get("meta_description", ""),
                "score": dist
            })

        return hits

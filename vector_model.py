import os
import pandas as pd
import numpy as np
import hashlib
import pickle
from sentence_transformers import SentenceTransformer
from sklearn.neighbors import NearestNeighbors

class BertKNNVectorModel:
    def __init__(self, data_path, cache_dir, model_name='all-MiniLM-L6-v2'):
        self.data_path = data_path
        self.cache_dir = cache_dir
        self.df = pd.read_csv(data_path)
        self.indexed_df = pd.DataFrame()
        self.doc_hashes = {}
        self.model = SentenceTransformer(model_name)
        self.knn_index = None
        self.embeddings = None
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()

    def _text_hash(self, url, full_text):
        return hashlib.md5(f"{url}::{full_text}".encode('utf-8')).hexdigest()

    def _load_cache(self):
        if os.path.exists(f"{self.cache_dir}/indexed_df.csv"):
            self.indexed_df = pd.read_csv(f"{self.cache_dir}/indexed_df.csv")
        if os.path.exists(f"{self.cache_dir}/doc_hashes.pkl"):
            with open(f"{self.cache_dir}/doc_hashes.pkl", "rb") as f:
                self.doc_hashes = pickle.load(f)
        if os.path.exists(f"{self.cache_dir}/embeddings.npy"):
            self.embeddings = np.load(f"{self.cache_dir}/embeddings.npy")

    def _save_cache(self):
        self.indexed_df.to_csv(f"{self.cache_dir}/indexed_df.csv", index=False)
        with open(f"{self.cache_dir}/doc_hashes.pkl", "wb") as f:
            pickle.dump(self.doc_hashes, f)
        if self.embeddings is not None:
            np.save(f"{self.cache_dir}/embeddings.npy", self.embeddings)

    def preprocess_and_index(self):
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)
        new_rows, new_texts, hashes = [], [], {}

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
            new_embeddings = self.model.encode(new_texts, show_progress_bar=True, convert_to_numpy=True)

            self.embeddings = new_embeddings
            self.indexed_df = pd.DataFrame(new_rows)
            self.doc_hashes.update(hashes)

            self.knn_index = NearestNeighbors(n_neighbors=10, metric='cosine')
            self.knn_index.fit(self.embeddings)

            self._save_cache()
        else:
            print("No new documents to index.")

    def search(self, query, top_k=10):
        if self.embeddings is None or self.indexed_df.empty:
            print("No index available. Run preprocess_and_index() first.")
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        self.knn_index = NearestNeighbors(n_neighbors=top_k, metric='cosine')
        self.knn_index.fit(self.embeddings)
        distances, indices = self.knn_index.kneighbors(query_embedding)

        results = self.indexed_df.iloc[indices[0]].copy()
        results['score'] = 1 - distances[0]  # Cosine similarity

        def resolve_description(row):
            if pd.isna(row['meta_description']) or not row['meta_description'] or row['meta_description']=='No Description':
                tokens = row['body_text'].split()
                return ' '.join(tokens[:30])
            return row['meta_description']

        results['meta_description'] = results.apply(resolve_description, axis=1)

        # Convert to JSON-serializable output
        json_results = results[['url', 'title', 'meta_description', 'score']].to_dict(orient='records')
        # json_results = results[['url', 'title', 'meta_description']].to_dict(orient='records')
        return json_results


# if __name__ == "__main__":
#     model = BertKNNVectorModel("combined_data.csv", cache_dir="cache")
#     # model.preprocess_and_index()
#     query = input("Enter your search query: ")
#     results = model.search(query)
#     print(results)

    # print("\nTop Results:\n")
    # for i, (url, score) in enumerate(zip(results['url'], scores)):
    #     print(f"{i+1}. {url} (distance: {score:.4f})")

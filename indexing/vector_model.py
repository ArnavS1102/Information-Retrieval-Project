import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib
import pickle
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class VectorSpaceModel:
    def __init__(self, data_path, cache_dir):
        self.data_path = data_path
        self.cache_dir = cache_dir
        self.vectorizer = TfidfVectorizer(stop_words='english', max_df=0.9)
        self.df = pd.read_csv(data_path)
        self.tfidf_matrix = None
        self.doc_hashes = {}
        self.indexed_df = pd.DataFrame()
        os.makedirs(cache_dir, exist_ok=True)
        print("88888")
        self._load_cache()

    def _text_hash(self, url, full_text):
        key = f"{url}::{full_text}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    def _load_cache(self):
        if os.path.exists(f"{self.cache_dir}/vectorizer.pkl"):
            with open(f"{self.cache_dir}/vectorizer.pkl", "rb") as f:
                self.vectorizer = pickle.load(f)
        if os.path.exists(f"{self.cache_dir}/tfidf_matrix.npz"):
            self.tfidf_matrix = np.load(f"{self.cache_dir}/tfidf_matrix.npz", allow_pickle=True)['arr_0'].item()
        if os.path.exists(f"{self.cache_dir}/indexed_df.csv"):
            self.indexed_df = pd.read_csv(f"{self.cache_dir}/indexed_df.csv")
        if os.path.exists(f"{self.cache_dir}/doc_hashes.pkl"):
            with open(f"{self.cache_dir}/doc_hashes.pkl", "rb") as f:
                self.doc_hashes = pickle.load(f)

    def _save_cache(self):
        with open(f"{self.cache_dir}/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        if isinstance(self.tfidf_matrix, np.ndarray):
            np.savez_compressed(f"{self.cache_dir}/tfidf_matrix.npz", arr_0=self.tfidf_matrix)
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
            updated_matrix = self.vectorizer.fit_transform(new_texts)
            self.tfidf_matrix = updated_matrix
            self.indexed_df = pd.DataFrame(new_rows)
            self.doc_hashes.update(hashes)
            self._save_cache()
        else:
            print("No new or updated documents to index.")

    def search(self, query, top_k=10):
        if self.tfidf_matrix is None or self.indexed_df.empty:
            print("TF-IDF matrix not initialized. Run preprocess_and_vectorize() first.")
            return pd.DataFrame(), []
        query_vec = self.vectorizer.transform([query])
        cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = cosine_similarities.argsort()[-top_k:][::-1]
        return self.indexed_df.iloc[top_indices]['url']

# if __name__ == "__main__":
#     model = VectorSpaceModel("../combined_data.csv")
#     model.preprocess_and_vectorize()
#     query = input("Enter your search query: ")
#     results, scores = model.search(query)
#     print("\nTop Results:\n")
#     for i, (index, row) in enumerate(results.iterrows()):
#         print(f"{i+1}- {row['url']}")

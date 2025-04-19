import os
import pandas as pd
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class TfidfSearchEngine:
    def __init__(self, data_path, cache_dir="cache"):
        self.data_path = data_path
        self.cache_dir = cache_dir
        self.df = pd.read_csv(data_path)
        self.vectorizer = None
        self.tfidf_matrix = None
        self.indexed_df = pd.DataFrame()
        os.makedirs(cache_dir, exist_ok=True)
        self._load_cache()

    def _load_cache(self):
        try:
            self.vectorizer = pickle.load(open(f"{self.cache_dir}/tfidf_vectorizer.pkl", "rb"))
            self.tfidf_matrix = np.load(f"{self.cache_dir}/tfidf_matrix.npy")
            self.indexed_df = pd.read_csv(f"{self.cache_dir}/indexed_df.csv")
        except:
            pass

    def _save_cache(self):
        pickle.dump(self.vectorizer, open(f"{self.cache_dir}/tfidf_vectorizer.pkl", "wb"))
        np.save(f"{self.cache_dir}/tfidf_matrix.npy", self.tfidf_matrix)
        self.indexed_df.to_csv(f"{self.cache_dir}/indexed_df.csv", index=False)

    def preprocess_and_index(self):
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=10000)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['full_text'])
        self.indexed_df = self.df.copy()
        self._save_cache()

    def search(self, query, top_k=10):
        if self.tfidf_matrix is None or self.indexed_df.empty or self.vectorizer is None:
            print("No index available. Run preprocess_and_index() first.")
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = similarities.argsort()[::-1][:top_k]
        results = self.indexed_df.iloc[top_indices].copy()
        results['score'] = similarities[top_indices]

        def resolve_description(row):
            if pd.isna(row['meta_description']) or not row['meta_description'] or row['meta_description'] == 'No Description':
                return ' '.join(row['body_text'].split()[:30])
            return row['meta_description']

        results['meta_description'] = results.apply(resolve_description, axis=1)

        return results[['url', 'title', 'meta_description', 'score']].to_dict(orient='records')

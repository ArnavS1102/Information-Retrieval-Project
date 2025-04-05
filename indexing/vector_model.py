# vector_space_model.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class VectorSpaceModel:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        # self.df.drop_duplicates(subset="url", keep="last", inplace=True)
        self.vectorizer = TfidfVectorizer(stop_words='english', max_df=0.9)
        self.tfidf_matrix = None

    def preprocess_and_vectorize(self):
        # Combine title, meta_description, and body_text
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['full_text'])

    def search(self, query, top_k=10):
        query_vec = self.vectorizer.transform([query])
        cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        top_indices = cosine_similarities.argsort()[-top_k:][::-1]
        return self.df.iloc[top_indices][['url', 'title', 'meta_description']], cosine_similarities[top_indices]

if __name__ == "__main__":
    model = VectorSpaceModel("../combined_data.csv")
    model.preprocess_and_vectorize()

    query = input("Enter your search query: ")
    results, scores = model.search(query)

    print("\nTop Results:\n")
    for i, (index, row) in enumerate(results.iterrows()):
        print(f"{i+1}. {row['title']} - {row['url']}")
        print(f"   {row['meta_description']}\n")

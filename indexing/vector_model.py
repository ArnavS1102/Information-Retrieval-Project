# Import necessary libraries
import os
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import hashlib
import pickle

class VectorSpaceModel:
    def __init__(self, data_path, cache_dir="tfidf_cache"):
        # Path to the input CSV file
        self.data_path = data_path
        # Directory where cache files (TF-IDF matrix, vectorizer, etc.) will be stored
        self.cache_dir = cache_dir
        # Initialize TF-IDF vectorizer with stopword removal and max_df filtering
        self.vectorizer = TfidfVectorizer(stop_words='english', max_df=0.9)

        # Load the dataset
        self.df = pd.read_csv(data_path)
        # Placeholder for the TF-IDF matrix (document vectors)
        self.tfidf_matrix = None
        # Dictionary to store content hash for each document (used for change detection)
        self.doc_hashes = {}  # Format: {url: hash(url + full_text)}
        # DataFrame to store indexed documents (metadata only)
        self.indexed_df = pd.DataFrame()

        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        # Load cache if available (vectorizer, matrix, doc hashes, indexed docs)
        self._load_cache()

    # Generate a unique hash for a document using URL + full_text
    def _text_hash(self, url, full_text):
        key = f"{url}::{full_text}"
        return hashlib.md5(key.encode('utf-8')).hexdigest()

    # Load cached vectorizer, matrix, document metadata, and hashes (if they exist)
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

    # Save the current state of the vectorizer, matrix, indexed documents, and hashes to disk
    def _save_cache(self):
        with open(f"{self.cache_dir}/vectorizer.pkl", "wb") as f:
            pickle.dump(self.vectorizer, f)
        if isinstance(self.tfidf_matrix, np.ndarray):
            np.savez_compressed(f"{self.cache_dir}/tfidf_matrix.npz", arr_0=self.tfidf_matrix)
        self.indexed_df.to_csv(f"{self.cache_dir}/indexed_df.csv", index=False)
        with open(f"{self.cache_dir}/doc_hashes.pkl", "wb") as f:
            pickle.dump(self.doc_hashes, f)

    # Process and vectorize only new or changed documents
    def preprocess_and_vectorize(self):
        # Combine title, meta_description, and body_text into one text field
        self.df['full_text'] = self.df[['title', 'meta_description', 'body_text']].fillna('').agg(' '.join, axis=1)

        # Temporary lists to hold new documents
        new_rows = []
        new_texts = []
        hashes = {}

        # Loop through all documents in the DataFrame
        for _, row in self.df.iterrows():
            url = row['url']
            full_text = row['full_text']
            doc_hash = self._text_hash(url, full_text)

            # Check if document is new or changed
            if url not in self.doc_hashes or self.doc_hashes[url] != doc_hash:
                new_rows.append(row)              # Store metadata
                new_texts.append(full_text)       # Store full text for vectorization
                hashes[url] = doc_hash            # Store new hash

        # If there are documents to index...
        if new_texts:
            print(f"Indexing {len(new_texts)} new or updated documents...")

            # Vectorize the new/updated documents
            updated_matrix = self.vectorizer.fit_transform(new_texts)
            self.tfidf_matrix = updated_matrix  # Overwrites previous matrix

            # Update the indexed document metadata
            self.indexed_df = pd.DataFrame(new_rows)

            # Update the stored hashes
            self.doc_hashes.update(hashes)

            # Save everything to cache
            self._save_cache()
        else:
            print("No new or updated documents to index.")

    # Perform semantic search using cosine similarity on the TF-IDF matrix
    def search(self, query, top_k=10):
        # Check if the model is ready
        if self.tfidf_matrix is None or self.indexed_df.empty:
            print("TF-IDF matrix not initialized. Run preprocess_and_vectorize() first.")
            return pd.DataFrame(), []

        # Transform the search query into a TF-IDF vector
        query_vec = self.vectorizer.transform([query])

        # Compute cosine similarity between query and document vectors
        cosine_similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get indices of top-k most similar documents
        top_indices = cosine_similarities.argsort()[-top_k:][::-1]

        # Return matching metadata and their scores
        return self.indexed_df.iloc[top_indices][['url', 'title', 'meta_description']], cosine_similarities[top_indices]

# Entry point when script is executed directly
if __name__ == "__main__":
    # Instantiate the model with a dataset
    model = VectorSpaceModel("../combined_data.csv")

    # Run preprocessing and indexing
    model.preprocess_and_vectorize()

    # Prompt user for a search query
    query = input("Enter your search query: ")

    # Perform the search
    results, scores = model.search(query)

    # Display the top search results
    print("\nTop Results:\n")
    for i, (index, row) in enumerate(results.iterrows()):
        print(f"{i+1}. {row['title']} - {row['url']}")
        print(f"   {row['meta_description']}\n")

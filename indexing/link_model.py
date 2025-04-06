import pandas as pd
import networkx as nx
from vector_model import VectorSpaceModel
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class LinkBasedModel:
    def __init__(self, graph_path, content_path):
        self.graph_df = pd.read_csv(graph_path)
        self.content_path = content_path
        self.G = nx.from_pandas_edgelist(self.graph_df, source='source', target='destination', create_using=nx.DiGraph())
        self.pagerank = None
        self.authorities = None

    def compute_link_scores(self):
        self.pagerank = nx.pagerank(self.G)
        _, self.authorities = nx.hits(self.G, max_iter=1000)

    def hybrid_search(self, query, alpha=0.5, top_k=10):
        # Run vector model
        vsm = VectorSpaceModel(self.content_path)
        vsm.preprocess_and_vectorize()
        results, tfidf_scores = vsm.search(query, top_k=top_k)

        # Normalize scores
        urls = results['url'].tolist()
        pr_scores = [self.pagerank.get(url, 0) for url in urls]
        auth_scores = [self.authorities.get(url, 0) for url in urls]

        scaler = MinMaxScaler()
        norm_tfidf = scaler.fit_transform(tfidf_scores.reshape(-1, 1)).flatten()
        norm_pr = scaler.fit_transform(np.array(pr_scores).reshape(-1, 1)).flatten()
        norm_auth = scaler.fit_transform(np.array(auth_scores).reshape(-1, 1)).flatten()

        # Combine scores (PageRank version)
        final_scores_pr = alpha * norm_tfidf + (1 - alpha) * norm_pr

        # Combine scores (HITS version)
        final_scores_hits = alpha * norm_tfidf + (1 - alpha) * norm_auth

        # Attach to DataFrame
        results = results.copy()
        results['tfidf'] = tfidf_scores
        results['pagerank_score'] = pr_scores
        results['authority_score'] = auth_scores
        results['hybrid_pagerank'] = final_scores_pr
        results['hybrid_hits'] = final_scores_hits

        return results.sort_values(by='hybrid_pagerank', ascending=False)

if __name__ == "__main__":
    model = LinkBasedModel("../web_graph.csv", "../combined_data.csv")
    model.compute_link_scores()

    query = input("Enter your search query: ")
    ranked_results = model.hybrid_search(query)

    print("\nTop Hybrid Results (TF-IDF + PageRank):\n")
    for i, row in ranked_results.head(10).iterrows():
        print(f"{i+1}. {row['title']} - {row['url']}")
        print(f"   {row['meta_description']}")
        print(f"   Score: {row['hybrid_pagerank']:.4f}\n")

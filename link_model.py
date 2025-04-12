import pandas as pd
import networkx as nx
import re

from vector_model import BertKNNVectorModel

class LinkAnalysisModel:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        self.graph = nx.DiGraph()
        self.pagerank_scores = {}
        self.hub_scores = {}
        self.authority_scores = {}
        self._build_graph()
        self._compute_scores()

    def _build_graph(self):
        def extract_links(text):
            if not isinstance(text, str):
                return []
            return re.findall(r'https?://[^\s\'",\[\]()]+', text)

        self.df['out_links'] = self.df['out_links'].apply(extract_links)

        for _, row in self.df.iterrows():
            src = row['url']
            for dst in row['out_links']:
                if isinstance(dst, str) and dst.strip():
                    self.graph.add_edge(src, dst)

    def _compute_scores(self):
        print("Computing PageRank and HITS...")
        self.pagerank_scores = nx.pagerank(self.graph, alpha=0.85)
        hubs, authorities = nx.hits(self.graph, max_iter=500, normalized=True)
        self.hub_scores = hubs
        self.authority_scores = authorities

    def _get_top_documents(self, score_dict, top_k=10, score_label='score'):
        sorted_items = sorted(score_dict.items(), key=lambda x: x[1], reverse=True)
        results = []

        visited = set()
        for url, score in sorted_items:
            if url in visited:
                continue
            matched = self.df[self.df['url'] == url]
            if matched.empty:
                continue
            row = matched.iloc[0]
            meta_desc = row['meta_description']
            if pd.isna(meta_desc) or not meta_desc or meta_desc == "No Description":
                meta_desc = ' '.join(str(row['body_text']).split()[:30])
            results.append({
                'url': url,
                'title': row['title'],
                'meta_description': meta_desc,
                score_label: round(score, 4)
            })
            visited.add(url)
            if len(results) >= top_k:
                break
        return results

    def get_top_by_pagerank(self, top_k=10):
        return self._get_top_documents(self.pagerank_scores, top_k, score_label='pagerank')

    def get_top_by_hits_authority(self, top_k=10):
        return self._get_top_documents(self.authority_scores, top_k, score_label='authority')

    def get_top_by_hits_hub(self, top_k=10):
        return self._get_top_documents(self.hub_scores, top_k, score_label='hub')


class SearchEngine:
    def __init__(self, data_path, cache_dir="cache"):
        self.vector_model = BertKNNVectorModel(data_path, cache_dir)
        self.link_model = LinkAnalysisModel(data_path)

        self.norm_pagerank = self._normalize(self.link_model.pagerank_scores)
        self.norm_authority = self._normalize(self.link_model.authority_scores)

    def _normalize(self, score_dict):
        values = list(score_dict.values())
        min_val, max_val = min(values), max(values)
        return {
            k: (v - min_val) / (max_val - min_val) if max_val > min_val else 0.0
            for k, v in score_dict.items()
        }

    def pagerank_model(self, top_k=10):
        return self.link_model.get_top_by_pagerank(top_k)

    def hits_model(self, top_k=10):
        return self.link_model.get_top_by_hits_authority(top_k)

    def hybrid_model(self, query, top_k=10, alpha=0.6, beta=0.2, gamma=0.2):
        vector_results = self.vector_model.search(query, top_k=top_k)
        hybrid_results = []

        for res in vector_results:
            url = res['url']
            vec_score = res['score']
            pr_score = self.norm_pagerank.get(url, 0.0)
            auth_score = self.norm_authority.get(url, 0.0)

            combined_score = (
                alpha * vec_score +
                beta * auth_score +
                gamma * pr_score
            )

            res.update({
                'pagerank': round(pr_score, 4),
                'authority': round(auth_score, 4),
                'combined_score': round(combined_score, 4)
            })
            hybrid_results.append(res)

        hybrid_results.sort(key=lambda x: x['combined_score'], reverse=True)
        return hybrid_results


if __name__ == "__main__":
    engine = SearchEngine(data_path="combined_data.csv")

    query = input("Enter your search query: ")
    print("\n--- Hybrid Ranked Results (Vector + PageRank + Authority) ---\n")
    hybrid = engine.hybrid_model(query)
    for i, doc in enumerate(hybrid, 1):
        print(f"{i}. {doc['title']} (Score: {doc['combined_score']:.4f})")
        print(f"   URL: {doc['url']}")
        print(f"   Description: {doc['meta_description']}\n")

    print("\n--- Top 10 Pages by PageRank ---\n")
    pagerank = engine.pagerank_model()
    for i, doc in enumerate(pagerank, 1):
        print(f"{i}. {doc['title']} (PageRank: {doc['pagerank']:.4f})")
        print(f"   URL: {doc['url']}")
        print(f"   Description: {doc['meta_description']}\n")

    print("\n--- Top 10 Pages by HITS Authority ---\n")
    hits = engine.hits_model()
    for i, doc in enumerate(hits, 1):
        print(f"{i}. {doc['title']} (Authority: {doc['authority']:.4f})")
        print(f"   URL: {doc['url']}")
        print(f"   Description: {doc['meta_description']}\n")

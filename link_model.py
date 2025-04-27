import pandas as pd
import networkx as nx
import re
import ast
import os

# from vector_model import BertKNNVectorModel

class LinkAnalysisModel:
    def __init__(self, data_path):
        self.df = pd.read_csv(data_path)
        count_ones = self.df["out_links"].apply(lambda x: x == 1 or x == '1').sum()
        self.graph = nx.DiGraph()
        self.pagerank_scores = {}
        self.hub_scores = {}
        self.authority_scores = {}
        self._build_graph()
        self._compute_scores()

    def _build_graph(self):
        def safe_parse_links(x):
            if isinstance(x, str):
                if x.strip() == '1':  # <-- Skip parsing if the original is '1'
                    return None  # Mark it as None
                try:
                    return ast.literal_eval(x)
                except (ValueError, SyntaxError):
                    return []
            return []

        self.df['out_links'] = self.df['out_links'].apply(safe_parse_links)

        for _, row in self.df.iterrows():
            src = row['url']
            out_links = row['out_links']
            if isinstance(out_links, list):
                for dst in out_links:
                    if isinstance(dst, str) and dst.strip():
                        self.graph.add_edge(src, dst)

    def _compute_scores(self):
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

    def query_aware_pagerank(self, query, vector_model, top_k=10):
        vector_results = vector_model.search(query, top_k=top_k * 3)
        relevant_urls = set(res['url'] for res in vector_results)
        subgraph = self.graph.subgraph(relevant_urls).copy()
        pagerank_scores = nx.pagerank(subgraph, alpha=0.85)
        docs = self._get_top_documents(pagerank_scores, top_k=top_k, score_label='pagerank')
        return pd.DataFrame(docs)[['url', 'title', 'meta_description']].to_dict(orient='records')

    def query_aware_hits(self, query, vector_model, top_k=10):
        vector_results = vector_model.search(query, top_k=top_k * 3)
        relevant_urls = set(res['url'] for res in vector_results)
        subgraph = self.graph.subgraph(relevant_urls).copy()
        _, authorities = nx.hits(subgraph, max_iter=500, normalized=True)
        docs = self._get_top_documents(authorities, top_k=top_k, score_label='authority')
        return pd.DataFrame(docs)[['url', 'title', 'meta_description']].to_dict(orient='records')



class SearchEngine:
    
    def __init__(self, vector_model, cache_dir="cache"):
        combined_data_path = os.getenv("COMBINED_DATA_PATH")
        current_dir = os.path.dirname(os.path.abspath(__file__))
        combined_data_path = os.path.join(current_dir, combined_data_path)
        # self.vector_model = BertKNNVectorModel(data_path, cache_dir)
        self.vector_model = vector_model
        self.link_model = LinkAnalysisModel(combined_data_path)

    def pagerank_model(self, query, top_k=10):
        return self.link_model.query_aware_pagerank(query, self.vector_model, top_k)

    def hits_model(self, query, top_k=10):
        return self.link_model.query_aware_hits(query, self.vector_model, top_k)

    def hybrid_model(self, query, top_k=10, alpha=0.6, beta=0.2, gamma=0.2):
        vector_results = self.vector_model.search(query, top_k=top_k)
        hybrid_results = []

        norm_pagerank = self._normalize(self.link_model.pagerank_scores)
        norm_authority = self._normalize(self.link_model.authority_scores)

        for res in vector_results:
            url = res['url']
            vec_score = res['score']
            pr_score = norm_pagerank.get(url, 0.0)
            auth_score = norm_authority.get(url, 0.0)

            combined_score = (
                alpha * vec_score +
                beta * auth_score +
                gamma * pr_score
            )

            meta_desc = res.get('meta_description')
            if not meta_desc or pd.isna(meta_desc) or meta_desc == "No Description":
                meta_desc = ' '.join(str(res.get('body_text', '')).split()[:30])

            hybrid_results.append({
                'url': url,
                'title': res['title'],
                'meta_description': meta_desc,
                'combined_score': round(combined_score, 4)
            })

        hybrid_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return pd.DataFrame(hybrid_results)[['url', 'title', 'meta_description']].to_dict(orient='records')

    def _normalize(self, score_dict):
        values = list(score_dict.values())
        min_val, max_val = min(values), max(values)
        return {
            k: (v - min_val) / (max_val - min_val) if max_val > min_val else 0.0
            for k, v in score_dict.items()
        }


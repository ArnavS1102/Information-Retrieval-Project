import os
import pandas as pd
from urllib.parse import urlparse
from dotenv import load_dotenv
from vector_model import BertKNNVectorModel

load_dotenv()

def get_directory_and_slug(url):
    path = urlparse(url).path.rstrip('/')
    if not path:
        return '', ''
    parts = path.split('/')
    return ('/'.join(parts[:-1]), parts[-1]) if len(parts) > 1 else ('', parts[0])

def get_url_key(url):
    parsed = urlparse(url)
    directory, slug = get_directory_and_slug(url)
    return (parsed.netloc.lower(), directory, slug)

if __name__ == "__main__":
    combined_data_path = os.getenv("COMBINED_DATA_PATH")
    cache_path = os.getenv("CACHE_PATH")

    df = pd.read_csv(combined_data_path, escapechar='\\')

    df.columns = [
        'url', 
        'title', 
        'meta_description', 
        'body_text', 
        'depth', 
        'last_crawled', 
        'out_links', 
        'anchor_texts'
    ]

    df = df.sort_values("last_crawled").drop_duplicates(subset="url", keep="first")
    df.dropna(subset=['url', 'body_text'], inplace=True)

    df['url_key'] = df['url'].apply(get_url_key)
    df = df.drop_duplicates(subset='url_key').drop(columns='url_key')

    urls = set(list(df['url']))
    print(len(urls))

    df.to_csv(combined_data_path, index=False, escapechar='\\')

    model = BertKNNVectorModel(combined_data_path, cache_path)
    model.preprocess_and_index()

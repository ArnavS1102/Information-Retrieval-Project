import os
import pandas as pd
from urllib.parse import urlparse
from dotenv import load_dotenv
from vector_model import BertKNNVectorModel
from link_model import SearchEngine
from tf_idf import TfidfSearchEngine

import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from datetime import datetime, timedelta


# Download NLTK resources
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')

load_dotenv()

# Text cleaning setup
stop_words = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text)  
    words = text.split()
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    return ' '.join(words)

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

    csv_files = [
    "datasets/data1.csv",
    "datasets/data2.csv",
    "datasets/data3.csv",
    "datasets/data4.csv"
    ]

    required_cols = [
        'url', 
        'title', 
        'meta_description', 
        'body_text', 
        'depth', 
        'last_crawled', 
        'out_links', 
        'anchor_texts'
    ]

    # dfs = []
    # for file in csv_files:
    #     temp_df = pd.read_csv(file)
    #     print(temp_df.columns)
    #     temp_df.columns = required_cols
    
    #     dfs.append(temp_df)


    dfs = []
    for file in csv_files:
        temp_df = pd.read_csv(file, escapechar='\\', low_memory=False)

        if len(temp_df.columns) == 6:
            temp_df['depth'] = 1
            start_time = datetime.now()
            temp_df['last_crawled'] = [start_time + timedelta(seconds=i) for i in range(len(temp_df))]
            temp_df['last_crawled'] = temp_df['last_crawled'].astype(str)

        else:
            temp_df.columns = required_cols

        dfs.append(temp_df)

    df = pd.concat(dfs, ignore_index=True)
    # df = pd.read_csv(combined_data_path, escapechar='\\')

    df.columns = required_cols

    df = df.sort_values("last_crawled").drop_duplicates(subset="url", keep="first")
    df.dropna(subset=['url', 'body_text'], inplace=True)

    # Clean the body_text
    df['body_text'] = df['body_text'].apply(clean_text)

    df['url_key'] = df['url'].apply(get_url_key)
    df = df.drop_duplicates(subset='url_key').drop(columns='url_key')

    urls = set(list(df['url']))
    print(len(urls))

    df.to_csv(combined_data_path, index=False, escapechar='\\')

    # vector_model = BertKNNVectorModel(combined_data_path, cache_path)
    # vector_model.preprocess_and_index()



    # query = 'Africa Politics'

    # engine = TfidfSearchEngine("combined_data.csv")
    # engine.preprocess_and_index()
    # print(engine.search("privacy preserving image recognition"))


    #For asking a Question:
    # results = vector_model.search(query)

    # link_engine = SearchEngine(combined_data_path)
    #For PageRank
    # results = link_engine.pagerank_model(query)

    #For HITS
    # results = link_engine.hits_model(query)

    #For Hybrid
    # results = link_engine.hybrid_model(query)

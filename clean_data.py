import sys
import json
import os
import pandas as pd
from urllib.parse import urlparse
from dotenv import load_dotenv
from vector_model import BertKNNVectorModel
from link_model import SearchEngine
import nltk
import re
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


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

def resolve_description(row):
    desc = row['meta_description']
    if (
        pd.isna(desc) or 
        not desc or 
        desc.strip().lower() == 'no description' or 
        re.match(r'^https?://', str(desc).strip())
    ):
        tokens = row['body_text'].split()
        return ' '.join(tokens[:30])
    return desc


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
    current_dir = os.path.dirname(os.path.abspath(__file__))
    combined_data_path = os.path.join(current_dir, combined_data_path)

    cache_path = os.getenv("CACHE_PATH")

    vector_model = BertKNNVectorModel(combined_data_path, cache_path)
    # vector_model.preprocess_and_index()

    query = sys.argv[1]
    model = sys.argv[2]
    
    link_engine = SearchEngine(vector_model)
    
    if(model == 'page_rank'):
        #For PageRank
        results = link_engine.pagerank_model(query)
        print(json.dumps(results))

    elif(model == 'hits'):
        #For HITS
        results = link_engine.hits_model(query)
        print(json.dumps(results))

    elif(model == 'hybrid'):
        #For Hybrid
        results = link_engine.hybrid_model(query)
        print(json.dumps(results))
    
    else:
        #For asking a Question:
        results = vector_model.search(query)
        print(json.dumps(results))
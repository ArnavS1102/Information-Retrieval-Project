import pandas as pd
from urllib.parse import urlparse

# === STEP 1: Load and clean initial combined_data.csv ===

# Load CSV
df = pd.read_csv("../combined_data.csv", escapechar='\\')

# Ensure expected columns
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

print("Original shape:", df.shape)

# Drop exact URL duplicates (keep earliest crawled version)
df = df.sort_values("last_crawled").drop_duplicates(subset="url", keep="first")

# Drop rows with missing critical content
df.dropna(subset=['url', 'body_text'], inplace=True)


print("After URL + content deduplication:", df.shape)

# === STEP 2: Heuristic deduplication using (domain, directory, slug) key ===

def get_directory_and_slug(url):
    parsed = urlparse(url)
    path = parsed.path.rstrip('/')
    if not path:
        return '', ''
    parts = path.split('/')
    if len(parts) == 1:
        return '', parts[0]
    directory = '/'.join(parts[:-1])
    slug = parts[-1]
    return directory, slug

def get_url_key(url):
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    directory, slug = get_directory_and_slug(url)
    return (netloc, directory, slug)

# Generate deduplication key
df['url_key'] = df['url'].apply(get_url_key)

# Drop duplicates based on the custom URL key
df = df.drop_duplicates(subset='url_key')
df = df.drop(columns=['url_key'])

print("After heuristic URL deduplication:", df.shape)

# === STEP 3: Save final deduplicated output ===
df.to_csv("../combined_data.csv", index=False, escapechar='\\')

li= [i for i in df['url']]

url_df = pd.DataFrame(li, columns=['url'])

url_df.to_csv('../visited.csv', index=False)

print(f"✅ Final deduplicated dataset saved with {len(df)} rows to 'combined_data_deduped.csv'.")

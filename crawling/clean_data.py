import pandas as pd

df1 = pd.read_csv("../combined_data.csv")

df1.columns = [
    'url', 
    'title', 
    'meta_description', 
    'body_text', 
    'depth', 
    'last_crawled', 
    'out_links', 
    'anchor_texts'
]

# df2.columns = [
#     'source', 
#     'destination',
#     'anchor']

print(df1.shape)
df1 = df1.sort_values("last_crawled").drop_duplicates(subset="url", keep="first")
print(df1.shape)

df1.dropna(subset=['url', 'body_text'], inplace=True)
df1.to_csv("../combined_data.csv")







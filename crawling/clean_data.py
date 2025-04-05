import pandas as pd

df1 = pd.read_csv("../combined_data.csv")
df2 = pd.read_csv("../web_graph.csv")


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

df2.columns = [
    'source', 
    'destination', 
    'anchor']

df1.dropna(subset=['url', 'body_text'], inplace=True)
df1.to_csv("../combined_data.csv")

df2.dropna(subset=['source'], inplace=True)
df2.to_csv("../web_graph.csv")


print(df1.loc[0])
print(df2.loc[0])



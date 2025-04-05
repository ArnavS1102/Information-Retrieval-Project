import pandas as pd
import ast
import os

input_file = '../combined_data.csv'
output_file = '../web_graph.csv'

if not os.path.exists(input_file):
    raise FileNotFoundError(f"File '{input_file}' not found. Please ensure it exists in the current directory.")

# Load the DataFrame
df = pd.read_csv(input_file, escapechar='\\')

# === Safely parse stringified lists ===
def safe_parse_list(value):
    try:
        return ast.literal_eval(value) if pd.notnull(value) else []
    except Exception:
        return []

df['out_links'] = df['out_links'].apply(safe_parse_list)
df['anchor_texts'] = df['anchor_texts'].apply(safe_parse_list)

# === Construct the web graph ===
web_graph = []

for _, row in df.iterrows():
    source = row['url']
    out_links = row['out_links']
    anchor_texts = row['anchor_texts']
    
    for dest, anchor in zip(out_links, anchor_texts):
        web_graph.append({
            'source': source,
            'destination': dest,
            'anchor': anchor
        })

# === Save web graph to CSV ===
web_graph_df = pd.DataFrame(web_graph)
web_graph_df.to_csv(output_file, index=False, escapechar='\\')

print(f"✅ Web graph successfully created with {len(web_graph_df)} edges and saved to '{output_file}'.")

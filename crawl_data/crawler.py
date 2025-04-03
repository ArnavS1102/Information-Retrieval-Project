# Step 1: Install Required Libraries (uncomment if not installed)
# !pip install advertools pandas beautifulsoup4 plotly

# Step 2: Import Necessary Libraries and Modules
import os
import time
import requests
import advertools as adv
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import signal

# Step 3: Define Global Parameters and Variables
MAX_PAGES = 50000   # Maximum total pages to crawl per batch
PER_SITE_LIMIT = 5000 # Maximum pages to process per seed website
SEED_TIMEOUT = 300  # Timeout for each seed (in seconds)

combined_data = []  # List to store combined page data (content + metadata)
web_graph = []      # List to store the web graph (link relationships)

# Load previously visited URLs (if running in batches)
visited_file = 'visited_urls.csv'
if os.path.exists(visited_file):
    visited_df = pd.read_csv(visited_file)
    visited_urls = set(visited_df['url'].tolist())
    print(f"Loaded {len(visited_urls)} visited URLs from {visited_file}.")
else:
    visited_urls = set()

# Step 4: Define Seed URLs (Expand for Diversity)
seed_urls = [
    "https://saharareporters.com/news",  # Sahara Reporters (Nigerian-African perspective)
    "https://africadailynews.net/",  # Africa Daily News
    "https://www.afrik-news.com/",  # Afrik-News
    "https://africatodaynewsnewyork.com/",  # Africa Today News
    "https://www.thecontinent.org/",  # The Continent (African-focused publication)

    # Business and Economy
    "https://africabusiness.com/",  # Africa Business News
    "https://www.miningweekly.com/page/africa",  # Mining Weekly (Africa section)
    "https://www.afro-impact.com/en/",  # Afro Impact (Business and social news)

    # Environment and Climate Change
    "http://greenpeaceafrica.org/",  # Greenpeace Africa
    "https://www.africa.com/",
    "https://allafrica.com/",
    "https://www.africanews.com/",
    "https://www.africanunion-un.org/post/african-culture-versatile-approach-to-realize-the-africa-we-want",
    "https://www.africantrails.co.uk/tour-info/africa-culture-and-history/",
    "https://au.int/en/flagships/encyclopaedia-africana",	
    # General News and Media
    "https://www.modernghana.com/",
    "https://www.africa-confidential.com/news",
    "https://africanewsconnect.com/",
    "https://www.bbc.com/news/world/africa",
    "https://www.cnn.com/africa",
    "https://www.aljazeera.com/topics/regions/africa.html",
    # Business and Economy
    "https://www.cnbcafrica.com/",
    "https://www.bizcommunity.com/",
    
    
    "https://greenafricadirectory.org/",
    
    # Science, Technology, and Innovation
    "https://techpoint.africa/",
    "http://africasciencenews.org/",
    "http://climdev-africa.org/", 

    # Travel and Tourism
    "https://blog.rhinoafrica.com/",
    "http://discoverafrica.com/",
    
   
]

# Step 5: Utility Function to Generate a Safe Output Filename from a URL
def generate_filename(site):
    domain = site.split("//")[-1].split("/")[0]
    domain = domain.replace("www.", "").replace(".", "_")
    return f"{domain}_crawl.jl"

# Step 6: Function to Process a Crawled Page and Extract Its Content Using BeautifulSoup
def process_page(row):
    url = row['url']

    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.title.string.strip() if soup.title and soup.title.string else 'No Title'

        meta_tag = soup.find('meta', attrs={'name': 'description'})
        meta_description = meta_tag['content'].strip() if meta_tag and meta_tag.get('content') else 'No Description'

        body_text = soup.get_text(separator=' ', strip=True)[:10000]

        # Extract outgoing links and their anchor texts, prioritize external links
        out_links = []
        anchor_texts = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(url, href)  # Convert relative URLs to absolute URLs
            if urlparse(full_url).scheme in ['http', 'https'] and not any(x in full_url for x in ['cookie', 'policy', 'login']):  # Exclude utility links
                out_links.append(full_url)
                anchor_texts.append(a_tag.get_text(strip=True))  # Extract anchor text

        return {
            'url': url,
            'title': title,
            'meta_description': meta_description,
            'body_text': body_text,
            'depth': row.get('depth', -1),
            'last_crawled': time.strftime('%Y-%m-%d %H:%M:%S'),
            'out_links': out_links,
            'anchor_texts': anchor_texts
        }

    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# Step 7: Timeout Handler for Seed-Level Timeout
def timeout_handler(signum, frame):
    raise TimeoutError("Crawling this seed took too long and was skipped.")

# Step 8: Main Crawling Loop – Process Each Seed Website with Timeout Handling
total_pages_crawled = len(visited_urls)  # Start from previously visited pages

for site in seed_urls:
    if total_pages_crawled >= MAX_PAGES:
        break

    print(f"\nStarting crawl for: {site}")

    try:
        # Set the timeout signal for this seed
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(SEED_TIMEOUT)  # Start the timer for this seed

        output_filename = generate_filename(site)

        # Calculate remaining pages allowed globally
        remaining_pages = MAX_PAGES - total_pages_crawled
        per_site_page_limit = min(PER_SITE_LIMIT, remaining_pages)

        adv.crawl(
            site,
            output_file=output_filename,
            follow_links=True,
            custom_settings={
                'USER_AGENT': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'CLOSESPIDER_PAGECOUNT': per_site_page_limit
            }
        )

        try:
            # Read the crawl results into a DataFrame
            data = pd.read_json(output_filename, lines=True)
        except Exception as e:
            print(f"Error reading crawl output for {site}: {e}")
            continue  # Skip this site if reading the file fails

        site_processed = 0

        for _, row in data.iterrows():
            if total_pages_crawled >= MAX_PAGES or site_processed >= PER_SITE_LIMIT:
                break

            this_url = row['url']
            if this_url in visited_urls:
                continue

            try:
                page_data = process_page(row)
                if page_data:
                    combined_data.append(page_data)
                    visited_urls.add(this_url)
                    total_pages_crawled += 1
                    site_processed += 1

                    # Record outgoing links with anchor texts (web graph)
                    for dest_url, anchor_text in zip(page_data.get('out_links', []), page_data.get('anchor_texts', [])):
                        web_graph.append({'source': this_url, 'destination': dest_url, 'anchor': anchor_text})
            except Exception as e:
                print(f"Error processing page {this_url}: {e}")
                continue  # Skip problematic pages and move on

        print(f"Finished crawl for: {site} | Pages processed for this site: {site_processed}")

    except TimeoutError as e:
        print(f"Timeout occurred for {site}: {e}")
    except Exception as e:
        print(f"Error crawling {site}: {e}")
    finally:
        signal.alarm(0)  # Disable the alarm after completing or skipping this seed

print(f"\nTotal unique pages processed: {total_pages_crawled}")

# Step 9: Save the Output Data to CSV Files (Append Mode)
combined_df = pd.DataFrame(combined_data)
web_graph_df = pd.DataFrame(web_graph)

# Append new data to existing files if they exist; otherwise create new files.
if os.path.exists('combined_data.csv'):
    combined_df.to_csv('combined_data.csv', mode='a', header=False, index=False,escapechar='\\')
else:
    combined_df.to_csv('combined_data.csv', index=False,escapechar='\\')

if os.path.exists('web_graph.csv'):
    web_graph_df.to_csv('web_graph.csv', mode='a', header=False, index=False,escapechar='\\')
else:
    web_graph_df.to_csv('web_graph.csv', index=False,escapechar='\\')

# Update visited URLs list
visited_df = pd.DataFrame({"url": list(visited_urls)})
visited_df.to_csv(visited_file, index=False,escapechar='\\')

print(f"Updated visited URLs saved to '{visited_file}' (total {len(visited_urls)} URLs).")

# Optionally download files to your local machine (uncomment if needed)
# files.download('combined_data.csv')
# files.download('web_graph.csv')
# files.download('visited_urls.csv')

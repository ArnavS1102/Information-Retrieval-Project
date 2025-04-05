I crawled 105,640 pages, and filtered the irrelevant links(youtube,reddit,twitter etc).
These are the 2 important documents and their description

1. combined_data.csv:
Contains detailed information about each unique crawled page.

Important columns in order:

url: The URL of the crawled page.

title: Page title (useful for indexing and search result snippets).

meta_description: Brief description of page content (useful for search snippets).

body_text: Main textual content of the page (used for indexing and keyword searches).

depth: How far from the seed URL this page was found.

last_crawled: Timestamp when the page was crawled.

out_links and anchor_texts: Outgoing links from the page and their anchor texts (useful for context).

Use for indexing:

This file alone is sufficient to build a basic keyword-based search index.

Can index the content (body_text) along with metadata (title, meta_description) to enable keyword searches.

2. web_graph.csv:
Represents relationships between pages based on hyperlinks.

Columns:

source: URL of the linking page.

destination: URL of the linked-to page.

anchor: Anchor text describing the link.

Use for indexing & ranking:

Essential for advanced search engine features like PageRank or other link-based ranking algorithms.

Helps determine authority and relevance of pages based on inbound links.

Useful for identifying related content clusters or communities.
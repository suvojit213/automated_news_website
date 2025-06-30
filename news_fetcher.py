import os
import requests
import json
from datetime import datetime
import argparse

# --- Configuration ---
OUTPUT_FILE = "news.json"
MAX_ARTICLES_IN_ARCHIVE = 300  # Increased archive size for more news

# --- API Endpoints and Topics ---
GNEWS_API_URL = "https://gnews.io/api/v4/search" # Using search endpoint for better results
NEWSDATA_API_URL = "https://newsdata.io/api/1/news"

# Topics for GNews (more general)
GNEWS_TOPICS = [
    "Artificial Intelligence",
    "Machine Learning",
    "Cybersecurity",
    "Data Science",
]

# Topics for NewsData.io (can be more specific)
# Using 'OR' to combine keywords in a single query to save credits
NEWSDATA_QUERY = "generative AI OR robotics OR quantum computing"


def load_existing_articles():
    """Loads articles from the existing news.json file."""
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('articles', [])
    except (FileNotFoundError, json.JSONDecodeError):
        print("news.json not found or is invalid. Starting fresh.")
        return []

def fetch_from_gnews(api_key):
    """Fetches news from GNews for a list of topics."""
    print("\n--- Fetching from GNews.io ---")
    all_gnews_articles = []
    for topic in GNEWS_TOPICS:
        print(f"-> Querying GNews for: '{topic}'")
        params = {
            "q": f'"{topic}"', # Use quotes for exact phrase matching
            "lang": "en",
            "country": "in,us", # Fetch from multiple countries
            "max": 15,
            "sortby": "publishedAt",
            "apikey": api_key
        }
        try:
            response = requests.get(GNEWS_API_URL, params=params)
            response.raise_for_status()
            articles = response.json().get('articles', [])
            print(f"   Found {len(articles)} articles.")
            all_gnews_articles.extend(articles)
        except requests.exceptions.RequestException as e:
            print(f"   Error fetching from GNews for '{topic}': {e}")
    return all_gnews_articles

def fetch_from_newsdata(api_key):
    """Fetches news from NewsData.io."""
    print("\n--- Fetching from NewsData.io ---")
    params = {
        'apikey': api_key,
        'q': NEWSDATA_QUERY,
        'language': 'en',
        'country': 'in,us',
        'category': 'technology,science'
    }
    try:
        response = requests.get(NEWSDATA_API_URL, params=params)
        response.raise_for_status()
        articles = response.json().get('results', [])
        print(f"   Found {len(articles)} articles from NewsData.io.")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"   Error fetching from NewsData.io: {e}")
        return []

def process_and_merge_articles(existing_articles, gnews_articles, newsdata_articles):
    """Merges new articles from all sources, removes duplicates, and sorts."""
    print("\n--- Merging all articles and removing duplicates ---")
    
    existing_urls = {article['url'] for article in existing_articles}
    
    # Process and add unique articles from GNews
    for article in gnews_articles:
        url = article.get('url')
        if url and url not in existing_urls and article.get('image'):
            processed = {
                'source': article.get('source', {'name': 'GNews'}),
                'title': article.get('title'),
                'url': url,
                'urlToImage': article.get('image'),
                'publishedAt': article.get('publishedAt')
            }
            existing_articles.append(processed)
            existing_urls.add(url)
            
    # Process and add unique articles from NewsData.io
    for article in newsdata_articles:
        url = article.get('link')
        if url and url not in existing_urls and article.get('image_url'):
            processed = {
                'source': {'name': article.get('source_id', 'NewsData.io')},
                'title': article.get('title'),
                'url': url,
                'urlToImage': article.get('image_url'),
                'publishedAt': article.get('pubDate')
            }
            existing_articles.append(processed)
            existing_urls.add(url)
    
    # Sort all articles by publishing date, newest first
    existing_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # Trim the list to the maximum size
    if len(existing_articles) > MAX_ARTICLES_IN_ARCHIVE:
        print(f"Archive size ({len(existing_articles)}) exceeds max ({MAX_ARTICLES_IN_ARCHIVE}). Trimming...")
        existing_articles = existing_articles[:MAX_ARTICLES_IN_ARCHIVE]

    return existing_articles

def save_to_json(articles):
    """Saves the final list of articles to the JSON file."""
    print(f"\nSaving {len(articles)} total articles to {OUTPUT_FILE}...")
    final_data = {
        'lastUpdatedAt': datetime.utcnow().isoformat() + "Z",
        'articles': articles
    }
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=4)
    print("✅ Successfully saved updated news archive!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch tech news from GNews and NewsData.io.")
    parser.add_argument('--gnews-key', type=str, required=True, help='Your GNews.io API key.')
    parser.add_argument('--newsdata-key', type=str, required=True, help='Your NewsData.io API key.')
    args = parser.parse_args()

    # 1. Load existing archive
    existing_articles = load_existing_articles()
    print(f"Loaded {len(existing_articles)} existing articles.")

    # 2. Fetch from both APIs
    gnews_articles = fetch_from_gnews(args.gnews_key)
    newsdata_articles = fetch_from_newsdata(args.newsdata_key)
    
    # 3. Merge, sort, and trim
    final_articles = process_and_merge_articles(existing_articles, gnews_articles, newsdata_articles)
    
    # 4. Save back to file
    save_to_json(final_articles)

import os
import requests
import json
from datetime import datetime
import argparse

# --- Configuration for GNews API ---
# API Key will be passed as a command-line argument.
GNEWS_API_URL = "https://gnews.io/api/v4/top-headlines"
PARAMS = {
    "topic": "technology", # Fetch technology news
    "lang": "en",          # In English language
    "country": "in",       # From India
    "max": 40,             # Max articles to fetch
}
OUTPUT_FILE = "news.json"

def fetch_news(api_key):
    """
    Fetches news from the GNews API and returns a list of articles.
    """
    if not api_key:
        raise ValueError("API key is missing. Please provide it via --api-key argument or set NEWS_API_KEY environment variable.")

    print("Fetching latest technology news from GNews...")
    
    # Add API key (token) to params
    PARAMS['apikey'] = api_key
    
    try:
        response = requests.get(GNEWS_API_URL, params=PARAMS)
        response.raise_for_status()
        news_data = response.json()
        print(f"Successfully fetched {len(news_data.get('articles', []))} articles.")
        return news_data.get('articles', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching news: {e}")
        return None

def process_articles(articles):
    """
    Filters and processes articles from GNews format to our website's format.
    """
    if not articles:
        return []

    print("Processing and filtering articles...")
    processed = []
    for article in articles:
        # GNews provides 'image' instead of 'urlToImage'
        if (article.get('title') and article.get('url') and article.get('image')):
            processed.append({
                'source': article.get('source', {'name': 'Unknown'}),
                'title': article.get('title', ''),
                'description': article.get('description', 'No description available.'),
                'url': article.get('url'),
                'urlToImage': article.get('image'), # Mapping 'image' to 'urlToImage'
                'publishedAt': article.get('publishedAt')
            })
    
    print(f"Filtered down to {len(processed)} high-quality articles.")
    return processed

def save_to_json(articles):
    """
    Saves the final list of articles to a JSON file.
    """
    print(f"Saving articles to {OUTPUT_FILE}...")
    
    final_data = {
        'lastUpdatedAt': datetime.utcnow().isoformat() + "Z",
        'articles': articles
    }
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved news to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch tech news from GNews.io.")
    parser.add_argument('--api-key', type=str, required=True, help='Your GNews.io API key.')
    
    args = parser.parse_args()
    
    articles = fetch_news(args.api_key)
    if articles:
        processed_articles = process_articles(articles)
        save_to_json(processed_articles)
    else:
        print("Could not fetch any articles. Exiting.")



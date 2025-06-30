import os
import requests
import json
from datetime import datetime
import argparse

# --- Configuration ---
GNEWS_API_URL = "https://gnews.io/api/v4/top-headlines"
OUTPUT_FILE = "news.json"
MAX_ARTICLES_IN_ARCHIVE = 250  # Limit to keep the JSON file and website fast

# List of AI related topics to search for.
# This will give a wide variety of relevant news.
TOPICS_TO_FETCH = [
    "Artificial Intelligence",
    "Machine Learning",
    "Cybersecurity",
    "Data Science",
    "Generative AI",
    "Robotics"
]

def load_existing_articles():
    """
    Loads articles from the existing news.json file if it exists.
    Returns a list of articles.
    """
    try:
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Return existing articles, ensuring they are a list
            return data.get('articles', [])
    except (FileNotFoundError, json.JSONDecodeError):
        # If file doesn't exist or is empty/corrupt, start fresh
        print("news.json not found or is invalid. Starting with a new list.")
        return []

def fetch_news_for_topic(topic, api_key):
    """
    Fetches news from GNews for a specific topic.
    """
    print(f"-> Fetching news for topic: '{topic}'...")
    params = {
        "q": topic,            # Use 'q' for keyword search to be more specific
        "lang": "en",
        "country": "in",
        "max": 20,             # Fetch a decent number of articles per topic
        "sortby": "publishedAt",
        "apikey": api_key
    }
    try:
        response = requests.get(GNEWS_API_URL, params=params)
        response.raise_for_status()
        news_data = response.json()
        articles = news_data.get('articles', [])
        print(f"   Found {len(articles)} articles for '{topic}'.")
        return articles
    except requests.exceptions.RequestException as e:
        print(f"   Error fetching news for '{topic}': {e}")
        return []

def process_and_merge_articles(existing_articles, new_articles):
    """
    Merges new articles with existing ones, removing duplicates and sorting.
    """
    print("\nMerging new articles and removing duplicates...")
    
    # Use a set of URLs for quick lookup of existing articles
    existing_urls = {article['url'] for article in existing_articles}
    
    unique_new_articles = []
    for article in new_articles:
        # Check if article from a valid source and has an image
        if article.get('url') not in existing_urls and article.get('image'):
            # Re-format the article to match our website's needs
            processed_article = {
                'source': article.get('source', {'name': 'Unknown'}),
                'title': article.get('title', ''),
                'description': article.get('description', 'No description available.'),
                'url': article.get('url'),
                'urlToImage': article.get('image'), # Map 'image' to 'urlToImage'
                'publishedAt': article.get('publishedAt')
            }
            unique_new_articles.append(processed_article)
            existing_urls.add(article['url']) # Add to set to avoid duplicates within the new batch

    print(f"Found {len(unique_new_articles)} new, unique articles.")
    
    # Combine old and new articles
    all_articles = existing_articles + unique_new_articles
    
    # Sort all articles by publishing date, newest first
    all_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
    
    # Trim the list to the maximum size
    if len(all_articles) > MAX_ARTICLES_IN_ARCHIVE:
        print(f"Archive size ({len(all_articles)}) exceeds max size ({MAX_ARTICLES_IN_ARCHIVE}). Trimming...")
        all_articles = all_articles[:MAX_ARTICLES_IN_ARCHIVE]

    return all_articles


def save_to_json(articles):
    """
    Saves the final list of articles to the JSON file.
    """
    print(f"\nSaving {len(articles)} articles to {OUTPUT_FILE}...")
    
    final_data = {
        'lastUpdatedAt': datetime.utcnow().isoformat() + "Z",
        'articles': articles
    }
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print("Successfully saved updated news archive!")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch and archive tech news from GNews.io.")
    parser.add_argument('--api-key', type=str, required=True, help='Your GNews.io API key.')
    args = parser.parse_args()

    # 1. Load what we already have
    existing_articles = load_existing_articles()
    print(f"Loaded {len(existing_articles)} existing articles from archive.")

    # 2. Fetch new articles for all topics
    all_new_articles = []
    for topic in TOPICS_TO_FETCH:
        all_new_articles.extend(fetch_news_for_topic(topic, args.api_key))
    
    # 3. Merge, sort, and trim
    final_articles = process_and_merge_articles(existing_articles, all_new_articles)
    
    # 4. Save back to the file
    save_to_json(final_articles)


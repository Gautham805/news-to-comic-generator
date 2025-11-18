import requests
import os
try:
    from newspaper import Article
except ImportError:
    from newspaper4k import Article
import feedparser
from datetime import datetime

class NewsFetcher:
    def __init__(self):
        self.api_key = os.getenv('NEWS_API_KEY')
        self.base_url = 'https://newsapi.org/v2/top-headlines'
    
    def fetch_top_news(self, country='us', category='general', page_size=5, language='en'):
        """Fetch top news headlines"""
        params = {
            'country': country,
            'category': category,
            'pageSize': page_size,
            'apiKey': self.api_key
        }
        
        # If language is specified and not English, use 'everything' endpoint
        if language != 'en':
            return self.search_news_by_language(category, language, page_size)
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return data['articles']
            return []
        except Exception as e:
            print(f"Error fetching news: {e}")
            return []
    
    def fetch_article_content(self, url):
        """Extract full article content from URL"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            return {
                'title': article.title,
                'text': article.text,
                'url': url,
                'authors': article.authors,
                'publish_date': str(article.publish_date) if article.publish_date else None
            }
        except Exception as e:
            print(f"Error extracting article: {e}")
            return None
    
    def search_news(self, query, page_size=5):
        """Search for specific news topics"""
        search_url = 'https://newsapi.org/v2/everything'
        params = {
            'q': query,
            'pageSize': page_size,
            'apiKey': self.api_key,
            'language': 'en',
            'sortBy': 'publishedAt'
        }
        
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return data['articles']
            return []
        except Exception as e:
            print(f"Error searching news: {e}")
            return []
    
    def search_news_by_language(self, query, language='ml', page_size=10):
        """Search news in specific language (e.g., Malayalam)"""
        search_url = 'https://newsapi.org/v2/everything'
        
        # Better search terms for Malayalam news
        search_queries = {
            'general': 'kerala OR india OR malayalam',
            'sports': 'cricket OR football OR kerala sports',
            'entertainment': 'malayalam cinema OR mollywood OR kerala entertainment',
            'technology': 'technology OR tech OR india technology',
            'science': 'science OR research',
            'health': 'health OR medical',
            'business': 'business OR economy OR kerala business'
        }
        
        search_term = search_queries.get(query, 'kerala')
        
        params = {
            'q': search_term,
            'pageSize': page_size,
            'apiKey': self.api_key,
            'sortBy': 'publishedAt',
            'language': 'en'  # Use English to get more results
        }
        
        # Try first with language filter
        try:
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok' and data.get('articles'):
                return data['articles']
            
            # If no results, try broader search
            params['q'] = 'india OR kerala'
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'ok':
                return data['articles']
            return []
        except Exception as e:
            print(f"Error searching {language} news: {e}")
            return []
    
    def fetch_malayalam_news_rss(self, category='general', page_size=10):
        """Fetch news from Malayalam RSS feeds as backup"""
        
        # Popular Malayalam/Kerala news RSS feeds
        rss_feeds = {
            'general': [
                'https://www.thehindu.com/news/national/kerala/feeder/default.rss',
                'https://indianexpress.com/section/cities/thiruvananthapuram/feed/',
            ],
            'sports': [
                'https://www.thehindu.com/sport/cricket/feeder/default.rss',
            ],
            'entertainment': [
                'https://www.thehindu.com/entertainment/feeder/default.rss',
            ]
        }
        
        feeds = rss_feeds.get(category, rss_feeds['general'])
        articles = []
        
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:page_size]:
                    articles.append({
                        'title': entry.get('title', 'No title'),
                        'description': entry.get('summary', 'No description')[:200],
                        'url': entry.get('link', ''),
                        'urlToImage': '',
                        'publishedAt': entry.get('published', str(datetime.now())),
                        'source': {'name': feed.feed.get('title', 'RSS Feed')}
                    })
                    if len(articles) >= page_size:
                        break
                if len(articles) >= page_size:
                    break
            except Exception as e:
                print(f"Error fetching RSS feed {feed_url}: {e}")
                continue
        
        return articles
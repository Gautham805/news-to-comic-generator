from flask import Flask, render_template, request, jsonify, send_from_directory
import os
from dotenv import load_dotenv
import uuid
from pathlib import Path

from news_fetcher import NewsFetcher
from summarizer import ComicSummarizer
from image_generator import ComicImageGenerator
from comic_assembler import ComicAssembler

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize components
news_fetcher = NewsFetcher()
summarizer = ComicSummarizer()
image_generator = ComicImageGenerator()
assembler = ComicAssembler()

# Ensure directories exist
Path('static/comics').mkdir(parents=True, exist_ok=True)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/fetch-news', methods=['GET'])
def fetch_news():
    """Fetch top news headlines"""
    try:
        category = request.args.get('category', 'general')
        language = request.args.get('language', 'en')
        
        print(f"Fetching news: category={category}, language={language}")
        
        if language == 'en':
            articles = news_fetcher.fetch_top_news(category=category, page_size=10)
        elif language == 'ml':
            # For Malayalam, use both NewsAPI and RSS
            print("Fetching Malayalam/Kerala news...")
            articles = news_fetcher.search_news_by_language(category, language='ml', page_size=10)
            
            # Always add RSS feeds for Malayalam
            print("Adding RSS feed articles...")
            rss_articles = news_fetcher.fetch_malayalam_news_rss(category, page_size=10)
            articles.extend(rss_articles)
            
            # Remove duplicates based on title
            seen = set()
            unique_articles = []
            for article in articles:
                title = article.get('title', '')
                if title and title not in seen:
                    seen.add(title)
                    unique_articles.append(article)
            articles = unique_articles[:10]
            print(f"Found {len(articles)} Malayalam articles")
        else:
            # For other Indian languages
            articles = news_fetcher.search_news_by_language(category, language=language, page_size=10)
        
        # Format articles for frontend
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('description', 'No description'),
                'url': article.get('url', ''),
                'urlToImage': article.get('urlToImage', ''),
                'publishedAt': article.get('publishedAt', '')
            })
        
        return jsonify({
            'success': True,
            'articles': formatted_articles
        })
    
    except Exception as e:
        print(f"Error in fetch_news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/search-news', methods=['POST'])
def search_news():
    """Search for news by keyword"""
    try:
        data = request.json
        query = data.get('query', '')
        language = data.get('language', 'en')
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        print(f"Searching news: query={query}, language={language}")
        
        if language == 'en':
            articles = news_fetcher.search_news(query, page_size=10)
        elif language == 'ml':
            # For Malayalam, search with Kerala context
            search_query = f"{query} kerala OR {query} india"
            articles = news_fetcher.search_news_by_language(search_query, language='ml', page_size=10)
            
            # Add RSS if needed
            if len(articles) < 5:
                rss_articles = news_fetcher.fetch_malayalam_news_rss('general', page_size=5)
                articles.extend(rss_articles)
        else:
            articles = news_fetcher.search_news_by_language(query, language=language, page_size=10)
        
        formatted_articles = []
        for article in articles:
            formatted_articles.append({
                'title': article.get('title', 'No title'),
                'description': article.get('description', 'No description'),
                'url': article.get('url', ''),
                'urlToImage': article.get('urlToImage', ''),
                'publishedAt': article.get('publishedAt', '')
            })
        
        return jsonify({
            'success': True,
            'articles': formatted_articles
        })
    
    except Exception as e:
        print(f"Error in search_news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/generate-comic', methods=['POST'])
def generate_comic():
    """Generate comic from news article"""
    try:
        data = request.json
        article_url = data.get('url', '')
        num_panels = data.get('num_panels', 4)
        
        if not article_url:
            return jsonify({'success': False, 'error': 'Article URL is required'}), 400
        
        # Step 1: Fetch full article content
        print("Fetching article content...")
        article = news_fetcher.fetch_article_content(article_url)
        
        # Fallback: use article title and description if full content fails
        if not article or not article.get('text'):
            print("Could not fetch full article, using title/description...")
            article_title = data.get('title', '')
            article_desc = data.get('description', '')
            
            if not article_title and not article_desc:
                return jsonify({'success': False, 'error': 'Could not fetch article content'}), 400
            
            article = {
                'text': f"{article_title}. {article_desc}",
                'title': article_title,
                'url': article_url
            }
        
        # Step 2: Create comic script
        print("Creating comic script...")
        script = summarizer.create_comic_script(article['text'], num_panels=num_panels)
        
        if not script:
            return jsonify({'success': False, 'error': 'Could not create comic script'}), 500
        
        # Step 3: Generate character descriptions
        print("Generating character descriptions...")
        character_descriptions = summarizer.generate_character_descriptions(script)
        
        # Step 4: Generate panel images
        print("Generating panel images...")
        comic_id = str(uuid.uuid4())
        panel_images = image_generator.generate_all_panels(
            script, 
            character_descriptions, 
            comic_id
        )
        
        if not panel_images:
            return jsonify({'success': False, 'error': 'Could not generate panel images'}), 500
        
        # Step 5: Assemble final comic
        print("Assembling comic...")
        final_comic_path = f'static/comics/{comic_id}/final_comic.png'
        result_path = assembler.assemble_comic(
            panel_images,
            final_comic_path,
            title=script.get('title', 'News Comic')
        )
        
        if not result_path:
            return jsonify({'success': False, 'error': 'Could not assemble comic'}), 500
        
        # Return success with comic URL
        comic_url = f'/comics/{comic_id}/final_comic.png'
        
        return jsonify({
            'success': True,
            'comic_url': comic_url,
            'title': script.get('title', 'News Comic'),
            'script': script
        })
    
    except Exception as e:
        print(f"Error generating comic: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/comics/<path:filename>')
def serve_comic(filename):
    """Serve generated comic images"""
    return send_from_directory('static/comics', filename)

if __name__ == '__main__':
    # Check if API keys are set
    if not os.getenv('GEMINI_API_KEY'):
        print("WARNING: GEMINI_API_KEY not set in .env file")
        print("Get your free API key at: https://aistudio.google.com/app/apikey")
    if not os.getenv('NEWS_API_KEY'):
        print("WARNING: NEWS_API_KEY not set in .env file")
    
    print("Starting News-to-Comic Generator...")
    print("Using FREE APIs: Google Gemini + Pollinations.ai")
    print("Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
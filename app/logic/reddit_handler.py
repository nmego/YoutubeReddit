import os
import json
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv
import praw

load_dotenv()

class RedditWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.data_folder = "reddit_data"
        self.cache_file = os.path.join(self.data_folder, "cache.json")
        
        # Create data folder if it doesn't exist
        os.makedirs(self.data_folder, exist_ok=True)
        
        # Initialize Reddit API client
        self.reddit = None
        self.setup_reddit_client()
    
    def setup_reddit_client(self):
        """Setup Reddit client with credentials from .env or use read-only mode"""
        try:
            # Try to get credentials from environment
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'ContentAggregator/1.0 by YourUsername')
            
            if client_id and client_secret:
                # Use authenticated client
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
                self.progress.emit("Using authenticated Reddit API...")
            else:
                # Use read-only mode (requires only user agent)
                self.reddit = praw.Reddit(
                    client_id=None,
                    client_secret=None,
                    user_agent=user_agent
                )
                self.progress.emit("Using read-only Reddit API...")
                
        except Exception as e:
            print(f"Error setting up Reddit client: {e}")
            self.reddit = None
    
    def load_cache(self):
        """Load cached data from JSON file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}
    
    def save_cache(self, cache):
        """Save data to cache JSON file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def format_timestamp(self, timestamp):
        """Format Unix timestamp to readable date"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%b %d, %Y at %H:%M')
        except:
            return "Unknown date"
    
    def format_number(self, num):
        """Format large numbers with K, M suffixes"""
        try:
            num = int(num)
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            else:
                return str(num)
        except:
            return "0"
    
    def get_posts_with_praw(self):
        """Get Reddit posts using PRAW library"""
        try:
            if not self.reddit:
                raise Exception("Reddit client not initialized")
            
            posts = []
            
            # Get hot posts from r/all or r/popular
            subreddit = self.reddit.subreddit('popular')  # or 'all'
            
            self.progress.emit("Fetching posts from r/popular...")
            
            # Get top 10 hot posts
            for i, submission in enumerate(subreddit.hot(limit=10), 1):
                self.progress.emit(f"Processing post {i}/10: {submission.title[:50]}...")
                
                # Get post data
                post_data = {
                    'id': submission.id,
                    'title': submission.title,
                    'author': str(submission.author) if submission.author else '[deleted]',
                    'subreddit': submission.subreddit.display_name,
                    'score': submission.score,
                    'upvote_ratio': getattr(submission, 'upvote_ratio', 0),
                    'num_comments': submission.num_comments,
                    'created_utc': submission.created_utc,
                    'created_formatted': self.format_timestamp(submission.created_utc),
                    'url': submission.url,
                    'permalink': submission.permalink,
                    'selftext': submission.selftext[:500] if submission.selftext else '',  # Limit text length
                    'is_self': submission.is_self,
                    'domain': submission.domain,
                    'post_type': 'text' if submission.is_self else 'link',
                    'gilded': getattr(submission, 'gilded', 0),
                    'locked': submission.locked,
                    'stickied': submission.stickied,
                    'nsfw': submission.over_18
                }
                
                # Add thumbnail info if available
                if hasattr(submission, 'thumbnail') and submission.thumbnail not in ['self', 'default', 'nsfw']:
                    post_data['thumbnail'] = submission.thumbnail
                
                # Format score and comments for display
                post_data['score_formatted'] = self.format_number(post_data['score'])
                post_data['comments_formatted'] = self.format_number(post_data['num_comments'])
                
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            raise Exception(f"Error fetching posts with PRAW: {str(e)}")
    
    def get_posts_fallback(self):
        """Fallback method using Reddit's JSON API if PRAW fails"""
        try:
            import requests
            
            self.progress.emit("Using fallback method (JSON API)...")
            
            url = "https://www.reddit.com/r/popular/hot.json?limit=10"
            headers = {
                'User-Agent': 'ContentAggregator/1.0 (by YourUsername)'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.reason}")
            
            data = response.json()
            posts = []
            
            for i, post_data in enumerate(data['data']['children'], 1):
                self.progress.emit(f"Processing post {i}/10...")
                
                post = post_data['data']
                
                processed_post = {
                    'id': post['id'],
                    'title': post['title'],
                    'author': post.get('author', '[deleted]'),
                    'subreddit': post['subreddit'],
                    'score': post['score'],
                    'upvote_ratio': post.get('upvote_ratio', 0),
                    'num_comments': post['num_comments'],
                    'created_utc': post['created_utc'],
                    'created_formatted': self.format_timestamp(post['created_utc']),
                    'url': post['url'],
                    'permalink': post['permalink'],
                    'selftext': post.get('selftext', '')[:500],  # Limit text length
                    'is_self': post['is_self'],
                    'domain': post.get('domain', ''),
                    'post_type': 'text' if post['is_self'] else 'link',
                    'gilded': post.get('gilded', 0),
                    'locked': post.get('locked', False),
                    'stickied': post.get('stickied', False),
                    'nsfw': post.get('over_18', False)
                }
                
                # Add thumbnail if available
                thumbnail = post.get('thumbnail')
                if thumbnail and thumbnail not in ['self', 'default', 'nsfw', '']:
                    processed_post['thumbnail'] = thumbnail
                
                # Format numbers
                processed_post['score_formatted'] = self.format_number(processed_post['score'])
                processed_post['comments_formatted'] = self.format_number(processed_post['num_comments'])
                
                posts.append(processed_post)
            
            return posts
            
        except Exception as e:
            raise Exception(f"Fallback method failed: {str(e)}")
    
    def run(self):
        try:
            self.progress.emit("Initializing Reddit data fetch...")
            
            cache = self.load_cache()
            
            # Check if we have recent cached data (less than 10 minutes old)
            current_time = time.time()
            if 'last_fetch' in cache and 'timestamp' in cache:
                cache_age = current_time - cache['timestamp']
                if cache_age < 600:  # 10 minutes = 600 seconds
                    self.progress.emit("Loading from cache...")
                    self.finished.emit(cache['last_fetch'])
                    return
            
            # Try to fetch new data
            posts = []
            
            # First try with PRAW
            try:
                posts = self.get_posts_with_praw()
            except Exception as praw_error:
                print(f"PRAW failed: {praw_error}")
                self.progress.emit("PRAW failed, trying fallback method...")
                
                # Fallback to JSON API
                try:
                    posts = self.get_posts_fallback()
                except Exception as fallback_error:
                    raise Exception(f"Both methods failed. PRAW: {praw_error}, Fallback: {fallback_error}")
            
            # Save to cache
            cache['last_fetch'] = posts
            cache['timestamp'] = current_time
            cache['method'] = 'praw' if self.reddit else 'json_api'
            self.save_cache(cache)
            
            self.progress.emit(f"Successfully loaded {len(posts)} posts!")
            self.finished.emit(posts)
            
        except Exception as e:
            self.error.emit(f"Error fetching Reddit posts: {str(e)}")
            
            # Try to return cached data even if it's old
            cache = self.load_cache()
            if 'last_fetch' in cache:
                self.progress.emit("Returning cached data due to error...")
                self.finished.emit(cache['last_fetch'])
            else:
                self.finished.emit([])
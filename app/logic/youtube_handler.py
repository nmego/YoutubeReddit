import os
import json
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from PyQt6.QtCore import QThread, pyqtSignal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class YouTubeWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    
    def __init__(self, channel_url):
        super().__init__()
        self.channel_url = channel_url
        self.data_folder = "youtube_data"
        self.cache_file = os.path.join(self.data_folder, "cache.json")
        self.api_key = os.getenv('YOUTUBE_KEY')
        
        # Create data folder if it doesn't exist
        os.makedirs(self.data_folder, exist_ok=True)
        
        if not self.api_key:
            self.error.emit("YouTube API key not found. Please add YOUTUBE_KEY to your .env file.")
            return
    
    def load_cache(self):
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading cache: {e}")
        return {}
    
    def save_cache(self, cache):
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving cache: {e}")
    
    def extract_channel_info(self, url):
        """Extract channel information from various YouTube URL formats"""
        try:
            if '/channel/' in url:
                channel_id = url.split('/channel/')[-1].split('/')[0].split('?')[0]
                return {'type': 'channel_id', 'id': channel_id}
            elif '/@' in url:
                handle = url.split('/@')[-1].split('/')[0].split('?')[0]
                return {'type': 'handle', 'id': handle}
            elif '/c/' in url:
                custom_name = url.split('/c/')[-1].split('/')[0].split('?')[0]
                return {'type': 'custom', 'id': custom_name}
            elif '/user/' in url:
                username = url.split('/user/')[-1].split('/')[0].split('?')[0]
                return {'type': 'username', 'id': username}
            else:
                # Try to extract from general youtube.com URL
                if 'youtube.com' in url:
                    return {'type': 'hash', 'id': hashlib.md5(url.encode()).hexdigest()}
        except Exception as e:
            print(f"Error extracting channel info: {e}")
        
        return {'type': 'hash', 'id': hashlib.md5(url.encode()).hexdigest()}
    
    def get_channel_id_from_handle_or_custom(self, channel_info):
        """Convert handle or custom URL to channel ID using YouTube API"""
        try:
            if channel_info['type'] == 'handle':
                # Search for channel by handle
                search_url = "https://www.googleapis.com/youtube/v3/search"
                params = {
                    'part': 'snippet',
                    'q': f"@{channel_info['id']}",
                    'type': 'channel',
                    'key': self.api_key,
                    'maxResults': 1
                }
                response = requests.get(search_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        return data['items'][0]['snippet']['channelId']
            
            elif channel_info['type'] in ['custom', 'username']:
                # Try to get channel by username/custom name
                channels_url = "https://www.googleapis.com/youtube/v3/channels"
                params = {
                    'part': 'id',
                    'forUsername' if channel_info['type'] == 'username' else 'forHandle': channel_info['id'],
                    'key': self.api_key
                }
                response = requests.get(channels_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if data.get('items'):
                        return data['items'][0]['id']
        
        except Exception as e:
            print(f"Error getting channel ID: {e}")
        
        return None
    
    def get_channel_videos(self, channel_id):
        """Get videos from a YouTube channel"""
        try:
            # First, get the uploads playlist ID
            channels_url = "https://www.googleapis.com/youtube/v3/channels"
            params = {
                'part': 'contentDetails,snippet',
                'id': channel_id,
                'key': self.api_key
            }
            
            response = requests.get(channels_url, params=params, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Failed to get channel info: {response.status_code}")
            
            channel_data = response.json()
            if not channel_data.get('items'):
                raise Exception("Channel not found")
            
            uploads_playlist_id = channel_data['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            channel_title = channel_data['items'][0]['snippet']['title']
            
            self.progress.emit(f"Found channel: {channel_title}")
            
            # Get videos from uploads playlist
            playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
            params = {
                'part': 'snippet,contentDetails',
                'playlistId': uploads_playlist_id,
                'maxResults': 20,  # Get up to 20 videos
                'key': self.api_key
            }
            
            response = requests.get(playlist_url, params=params, timeout=10)
            if response.status_code != 200:
                raise Exception(f"Failed to get playlist items: {response.status_code}")
            
            playlist_data = response.json()
            videos = []
            
            for item in playlist_data.get('items', []):
                video_id = item['contentDetails']['videoId']
                snippet = item['snippet']
                
                video_data = {
                    'id': video_id,
                    'title': snippet.get('title', 'No Title'),
                    'description': snippet.get('description', 'No description')[:200] + "...",
                    'published_at': self.format_date(snippet.get('publishedAt', '')),
                    'thumbnail_url': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                    'channel_title': snippet.get('channelTitle', channel_title)
                }
                
                videos.append(video_data)
            
            # Get additional video details (view count, etc.)
            if videos:
                video_ids = ','.join([v['id'] for v in videos])
                videos_url = "https://www.googleapis.com/youtube/v3/videos"
                params = {
                    'part': 'statistics',
                    'id': video_ids,
                    'key': self.api_key
                }
                
                response = requests.get(videos_url, params=params, timeout=10)
                if response.status_code == 200:
                    video_stats = response.json()
                    stats_dict = {item['id']: item['statistics'] for item in video_stats.get('items', [])}
                    
                    for video in videos:
                        stats = stats_dict.get(video['id'], {})
                        video['view_count'] = int(stats.get('viewCount', 0))
            
            return videos
            
        except Exception as e:
            raise Exception(f"Error fetching videos: {str(e)}")
    
    def format_date(self, date_string):
        """Format ISO date string to readable format"""
        try:
            dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return dt.strftime('%b %d, %Y')
        except:
            return date_string
    
    def download_thumbnail(self, video_id, thumbnail_url):
        """Download video thumbnail"""
        if not thumbnail_url:
            return None
            
        try:
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                thumbnail_path = os.path.join(self.data_folder, f"{video_id}.jpg")
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                return thumbnail_path
        except Exception as e:
            print(f"Error downloading thumbnail for {video_id}: {e}")
        return None
    
    def run(self):
        try:
            if not self.api_key:
                self.error.emit("YouTube API key not found. Please add YOUTUBE_KEY to your .env file.")
                return
                
            self.progress.emit("Analyzing channel URL...")
            
            channel_info = self.extract_channel_info(self.channel_url)
            cache = self.load_cache()
            
            # Create cache key
            cache_key = f"{channel_info['type']}_{channel_info['id']}"
            
            # Check if data is cached (and not older than 1 hour)
            if cache_key in cache:
                cached_data = cache[cache_key]
                cache_time = cached_data.get('timestamp', 0)
                current_time = datetime.now().timestamp()
                
                # Use cache if it's less than 1 hour old
                if current_time - cache_time < 3600:  # 1 hour = 3600 seconds
                    self.progress.emit("Loading from cache...")
                    videos = cached_data.get('videos', [])
                    
                    # Verify thumbnails still exist
                    for video in videos:
                        thumbnail_path = os.path.join(self.data_folder, f"{video['id']}.jpg")
                        if os.path.exists(thumbnail_path):
                            video['thumbnail_path'] = thumbnail_path
                    
                    self.finished.emit(videos)
                    return
            
            self.progress.emit("Getting channel information...")
            
            # Get actual channel ID
            if channel_info['type'] == 'channel_id':
                channel_id = channel_info['id']
            else:
                channel_id = self.get_channel_id_from_handle_or_custom(channel_info)
                if not channel_id:
                    raise Exception("Could not find channel. Please check the URL.")
            
            self.progress.emit("Fetching videos...")
            videos = self.get_channel_videos(channel_id)
            
            # Download thumbnails
            for i, video in enumerate(videos):
                self.progress.emit(f"Downloading thumbnail {i+1}/{len(videos)}: {video['title'][:50]}...")
                
                thumbnail_path = os.path.join(self.data_folder, f"{video['id']}.jpg")
                if not os.path.exists(thumbnail_path):
                    downloaded_path = self.download_thumbnail(video['id'], video.get('thumbnail_url', ''))
                    if downloaded_path:
                        video['thumbnail_path'] = downloaded_path
                else:
                    video['thumbnail_path'] = thumbnail_path
            
            # Save to cache
            cache[cache_key] = {
                'videos': videos,
                'timestamp': datetime.now().timestamp(),
                'channel_url': self.channel_url
            }
            self.save_cache(cache)
            
            self.progress.emit(f"Successfully loaded {len(videos)} videos!")
            self.finished.emit(videos)
            
        except Exception as e:
            self.error.emit(str(e))
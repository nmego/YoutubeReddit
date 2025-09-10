import os
import praw
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QLabel, QFrame, QMessageBox, QProgressBar, QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap
from dotenv import load_dotenv
from custom_scroll import CustomScrollArea

load_dotenv()

class CommentWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(dict, list)
    error = pyqtSignal(str)
    
    def __init__(self, post_data):
        super().__init__()
        self.post_data = post_data
        self.reddit = None
        self.setup_reddit_client()
    
    def setup_reddit_client(self):
        """Setup Reddit client"""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            user_agent = os.getenv('REDDIT_USER_AGENT', 'ContentAggregator/1.0 by YourUsername')
            
            if client_id and client_secret:
                self.reddit = praw.Reddit(
                    client_id=client_id,
                    client_secret=client_secret,
                    user_agent=user_agent
                )
            else:
                self.reddit = praw.Reddit(
                    client_id=None,
                    client_secret=None,
                    user_agent=user_agent
                )
        except Exception as e:
            print(f"Error setting up Reddit client: {e}")
            self.reddit = None
    
    def format_timestamp(self, timestamp):
        """Format Unix timestamp to readable date"""
        try:
            dt = datetime.fromtimestamp(timestamp)
            return dt.strftime('%b %d, %Y at %H:%M')
        except:
            return "Unknown date"
    
    def run(self):
        try:
            if not self.reddit:
                self.error.emit("Reddit client not available")
                return
            
            self.progress.emit("Loading post details...")
            
            # Get the submission
            submission = self.reddit.submission(id=self.post_data['id'])
            
            # Get full post data
            post_details = {
                'id': submission.id,
                'title': submission.title,
                'author': str(submission.author) if submission.author else '[deleted]',
                'subreddit': submission.subreddit.display_name,
                'score': submission.score,
                'upvote_ratio': getattr(submission, 'upvote_ratio', 0),
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'created_formatted': self.format_timestamp(submission.created_utc),
                'selftext': submission.selftext,
                'url': submission.url,
                'is_self': submission.is_self,
                'domain': submission.domain,
                'gilded': getattr(submission, 'gilded', 0),
                'locked': submission.locked,
                'stickied': submission.stickied,
                'nsfw': submission.over_18
            }
            
            self.progress.emit("Loading comments...")
            
            # Get top 5 comments
            submission.comments.replace_more(limit=0)  # Remove "load more comments"
            top_comments = []
            
            for comment in submission.comments[:5]:
                if hasattr(comment, 'body'):
                    comment_data = {
                        'id': comment.id,
                        'author': str(comment.author) if comment.author else '[deleted]',
                        'body': comment.body,
                        'score': comment.score,
                        'created_utc': comment.created_utc,
                        'created_formatted': self.format_timestamp(comment.created_utc),
                        'is_submitter': comment.is_submitter,
                        'gilded': getattr(comment, 'gilded', 0),
                        'replies': []
                    }
                    
                    # Get top 2 replies for each comment
                    if hasattr(comment, 'replies') and len(comment.replies) > 0:
                        for reply in comment.replies[:2]:
                            if hasattr(reply, 'body'):
                                reply_data = {
                                    'id': reply.id,
                                    'author': str(reply.author) if reply.author else '[deleted]',
                                    'body': reply.body,
                                    'score': reply.score,
                                    'created_utc': reply.created_utc,
                                    'created_formatted': self.format_timestamp(reply.created_utc),
                                    'is_submitter': reply.is_submitter,
                                    'gilded': getattr(reply, 'gilded', 0)
                                }
                                comment_data['replies'].append(reply_data)
                    
                    top_comments.append(comment_data)
            
            self.finished.emit(post_details, top_comments)
            
        except Exception as e:
            self.error.emit(f"Error loading post: {str(e)}")

class CommentFrame(QFrame):
    def __init__(self, comment_data, is_reply=False):
        super().__init__()
        self.comment_data = comment_data
        self.is_reply = is_reply
        
        # Different styling for replies
        if is_reply:
            self.setStyleSheet("""
                QFrame {
                    border-left: 3px solid #0078d4;
                    margin: 5px 5px 5px 30px;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #383838;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid #555555;
                    margin: 8px;
                    padding: 10px;
                    border-radius: 6px;
                    background-color: #404040;
                }
            """)
        
        layout = QVBoxLayout()
        layout.setSpacing(5)
        
        # Author and metadata
        author_text = f"u/{comment_data['author']}"
        if comment_data.get('is_submitter'):
            author_text += " [OP]"
        
        metadata = f"{author_text} • {comment_data['score']} points • {comment_data['created_formatted']}"
        if comment_data.get('gilded', 0) > 0:
            metadata += f" • 🥇 {comment_data['gilded']}"
        
        author_label = QLabel(metadata)
        author_label.setStyleSheet("color: #0078d4; font-size: 10px; font-weight: bold;")
        
        # Comment body
        body_text = comment_data['body']
        if len(body_text) > 500:
            body_text = body_text[:500] + "..."
        
        body_label = QLabel(body_text)
        body_label.setWordWrap(True)
        body_label.setStyleSheet("color: #ffffff; font-size: 11px; margin: 5px 0px;")
        
        layout.addWidget(author_label)
        layout.addWidget(body_label)
        
        self.setLayout(layout)

class RedditPostViewer(QWidget):
    back_clicked = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.current_post = None
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Header with back button
        header_layout = QHBoxLayout()
        
        self.back_button = QPushButton("← Back to Posts")
        self.back_button.setMinimumHeight(35)
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        self.back_button.clicked.connect(self.back_clicked.emit)
        
        header_layout.addWidget(self.back_button)
        header_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        # Status label
        self.status_label = QLabel()
        self.status_label.setStyleSheet("color: #cccccc; font-size: 12px;")
        
        # Scroll area for content
        self.scroll_area = CustomScrollArea()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(10)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def load_post(self, post_data):
        """Load a Reddit post and its comments"""
        self.current_post = post_data
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Clear previous content
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i)
            if child.widget():
                child.widget().setParent(None)
        
        # Start loading comments
        self.worker = CommentWorker(post_data)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_post_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_post_loaded(self, post_details, comments):
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Loaded post with {len(comments)} comments")
        
        # Post header
        post_frame = QFrame()
        post_frame.setStyleSheet("""
            QFrame {
                border: 2px solid #0078d4;
                margin: 10px;
                padding: 15px;
                border-radius: 8px;
                background-color: #404040;
            }
        """)
        
        post_layout = QVBoxLayout(post_frame)
        
        # Title
        title_label = QLabel(post_details['title'])
        title_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        
        # Post metadata
        metadata_parts = []
        metadata_parts.append(f"r/{post_details['subreddit']}")
        metadata_parts.append(f"u/{post_details['author']}")
        metadata_parts.append(f"{post_details['score']} points")
        metadata_parts.append(f"{post_details['num_comments']} comments")
        metadata_parts.append(post_details['created_formatted'])
        
        metadata_text = " • ".join(metadata_parts)
        metadata_label = QLabel(metadata_text)
        metadata_label.setStyleSheet("color: #999999; font-size: 11px; margin-bottom: 10px;")
        
        # Post content
        if post_details['selftext']:
            content_label = QLabel(post_details['selftext'])
            content_label.setWordWrap(True)
            content_label.setStyleSheet("color: #ffffff; font-size: 12px; margin-bottom: 10px;")
            post_layout.addWidget(content_label)
        elif not post_details['is_self']:
            link_label = QLabel(f"🔗 External Link: {post_details['url']}")
            link_label.setStyleSheet("color: #0078d4; font-size: 11px; margin-bottom: 10px;")
            post_layout.addWidget(link_label)
        
        post_layout.addWidget(title_label)
        post_layout.addWidget(metadata_label)
        
        self.scroll_layout.addWidget(post_frame)
        
        # Comments header
        if comments:
            comments_header = QLabel(f"💬 Top {len(comments)} Comments")
            comments_header.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            comments_header.setStyleSheet("color: #ffffff; margin: 20px 10px 10px 10px;")
            self.scroll_layout.addWidget(comments_header)
            
            # Add comments
            for comment in comments:
                comment_frame = CommentFrame(comment)
                self.scroll_layout.addWidget(comment_frame)
                
                # Add replies
                for reply in comment.get('replies', []):
                    reply_frame = CommentFrame(reply, is_reply=True)
                    self.scroll_layout.addWidget(reply_frame)
        else:
            no_comments_label = QLabel("No comments available")
            no_comments_label.setStyleSheet("color: #999999; margin: 20px; text-align: center;")
            no_comments_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_comments_label)
        
        self.scroll_layout.addStretch()
    
    def on_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ Error occurred")
        QMessageBox.critical(self, "Error", error_message)
        
        # Show error in scroll area
        error_label = QLabel(f"Error loading post: {error_message}")
        error_label.setStyleSheet("color: #ff6666; margin: 20px; text-align: center;")
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setWordWrap(True)
        self.scroll_layout.addWidget(error_label)
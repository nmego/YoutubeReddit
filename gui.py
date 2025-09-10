from PyQt6.QtWidgets import (QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QMessageBox, 
                            QProgressBar, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from widgets import YouTubeTab, RedditPostFrame
from reddit_handler import RedditWorker
from reddit_post_viewer import RedditPostViewer
from custom_scroll import CustomScrollArea

class RedditTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Use stacked widget to switch between post list and post viewer
        self.stacked_widget = QStackedWidget()
        
        # Create post list page
        self.post_list_page = self.create_post_list_page()
        
        # Create post viewer page
        self.post_viewer_page = RedditPostViewer()
        self.post_viewer_page.back_clicked.connect(self.show_post_list)
        
        # Add pages to stack
        self.stacked_widget.addWidget(self.post_list_page)
        self.stacked_widget.addWidget(self.post_viewer_page)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.stacked_widget)
        
        self.setLayout(layout)
        
        # Start with post list
        self.stacked_widget.setCurrentWidget(self.post_list_page)
    
    def create_post_list_page(self):
        """Create the main post list page"""
        page = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with load button
        header_layout = QHBoxLayout()
        
        self.load_button = QPushButton("🔄 Load Top 10 Posts from Reddit")
        self.load_button.setMinimumHeight(45)
        self.load_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 12px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        self.load_button.clicked.connect(self.load_posts)
        
        header_layout.addWidget(self.load_button)
        header_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555555;
                border-radius: 8px;
                text-align: center;
                background-color: #404040;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 6px;
            }
        """)
        
        # Status label
        self.status_label = QLabel("Click 'Load Top 10 Posts' to get started")
        self.status_label.setStyleSheet("color: #cccccc; padding: 10px; font-size: 12px;")
        
        # Scroll area for posts
        self.scroll_area = CustomScrollArea()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addLayout(header_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.scroll_area)
        
        page.setLayout(layout)
        return page
    
    def load_posts(self):
        self.load_button.setEnabled(False)
        self.load_button.setText("⏳ Loading...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Clear previous posts
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i)
            if child.widget():
                child.widget().setParent(None)
        
        # Start worker thread
        self.worker = RedditWorker()
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_posts_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_posts_loaded(self, posts):
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.load_button.setText("🔄 Load Top 10 Posts from Reddit")
        
        if not posts:
            self.status_label.setText("No posts found.")
            no_posts_label = QLabel("No posts found.")
            no_posts_label.setStyleSheet("color: #999999; padding: 40px; text-align: center; font-size: 14px;")
            no_posts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_posts_label)
        else:
            self.status_label.setText(f"✅ Loaded {len(posts)} posts (click any post to view details)")
            
            for post in posts:
                post_frame = RedditPostFrame(post)
                post_frame.post_clicked.connect(self.show_post_details)
                self.scroll_layout.addWidget(post_frame)
        
        self.scroll_layout.addStretch()
    
    def on_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.load_button.setText("🔄 Load Top 10 Posts from Reddit")
        self.status_label.setText("❌ Error occurred")
        QMessageBox.critical(self, "Error", error_message)
    
    def show_post_details(self, post_data):
        """Switch to post viewer and load the selected post"""
        self.post_viewer_page.load_post(post_data)
        self.stacked_widget.setCurrentWidget(self.post_viewer_page)
    
    def show_post_list(self):
        """Switch back to post list"""
        self.stacked_widget.setCurrentWidget(self.post_list_page)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Content Aggregator - Enhanced Dark Theme")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and tab widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # App title
        title_label = QLabel("📱 Content Aggregator")
        title_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #555555;
                border-radius: 8px;
                background-color: #3c3c3c;
                padding: 5px;
            }
            QTabBar::tab {
                background-color: #555555;
                color: #ffffff;
                padding: 12px 20px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background-color: #3c3c3c;
                border-bottom: 3px solid #0078d4;
            }
            QTabBar::tab:hover:!selected {
                background-color: #666666;
            }
        """)
        
        # Create tabs
        self.youtube_tab = YouTubeTab()
        self.reddit_tab = RedditTab()
        
        # Add tabs to tab widget
        self.tab_widget.addTab(self.youtube_tab, "📺 YouTube")
        self.tab_widget.addTab(self.reddit_tab, "🔗 Reddit")
        
        layout.addWidget(title_label)
        layout.addWidget(self.tab_widget)
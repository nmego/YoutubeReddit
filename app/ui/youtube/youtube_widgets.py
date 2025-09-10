import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QLabel, QFrame, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont
from ...logic.youtube_handler import YouTubeWorker

class VideoFrame(QFrame):
    def __init__(self, video_data):
        super().__init__()
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #666666;
                margin: 8px;
                padding: 12px;
                border-radius: 8px;
                background-color: #404040;
            }
            QFrame:hover {
                border: 2px solid #0078d4;
                background-color: #454545;
            }
        """)
        
        layout = QHBoxLayout()
        layout.setSpacing(15)
        
        # Thumbnail container
        thumbnail_container = QFrame()
        thumbnail_container.setFixedSize(160, 120)
        thumbnail_container.setStyleSheet("""
            QFrame {
                border: 1px solid #555555;
                border-radius: 6px;
                background-color: #333333;
                margin: 0px;
                padding: 0px;
            }
        """)
        
        thumbnail_layout = QVBoxLayout(thumbnail_container)
        thumbnail_layout.setContentsMargins(0, 0, 0, 0)
        
        # Thumbnail
        thumbnail_label = QLabel()
        thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        if os.path.exists(video_data.get('thumbnail_path', '')):
            pixmap = QPixmap(video_data['thumbnail_path'])
            # Scale to fill the container while maintaining aspect ratio
            scaled_pixmap = pixmap.scaled(
                158, 118, 
                Qt.AspectRatioMode.KeepAspectRatioByExpanding, 
                Qt.TransformationMode.SmoothTransformation
            )
            thumbnail_label.setPixmap(scaled_pixmap)
            thumbnail_label.setStyleSheet("border: none; background: transparent;")
        else:
            thumbnail_label.setText("No Thumbnail")
            thumbnail_label.setStyleSheet("""
                border: none;
                background-color: #555555;
                color: #999999;
                font-size: 11px;
            """)
        
        thumbnail_layout.addWidget(thumbnail_label)
        
        # Video info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)
        
        # Title
        title_label = QLabel(video_data.get('title', 'No Title'))
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #ffffff; margin: 0px;")
        title_label.setMaximumHeight(60)  # Limit title height
        
        # Stats
        stats_text = ""
        if 'view_count' in video_data:
            stats_text += f"{video_data['view_count']:,} views"
        if 'published_at' in video_data:
            if stats_text:
                stats_text += " • "
            stats_text += video_data['published_at']
        
        if stats_text:
            stats_label = QLabel(stats_text)
            stats_label.setStyleSheet("color: #999999; font-size: 10px; margin: 0px;")
        
        # Description
        desc_text = video_data.get('description', 'No description')
        if len(desc_text) > 150:
            desc_text = desc_text[:150] + "..."
        
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #cccccc; font-size: 10px; margin: 0px;")
        
        # Add to layout
        info_layout.addWidget(title_label)
        if stats_text:
            info_layout.addWidget(stats_label)
        info_layout.addWidget(desc_label)
        info_layout.addStretch()
        
        layout.addWidget(thumbnail_container)
        layout.addLayout(info_layout, 1)
        
        self.setLayout(layout)

class YouTubeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Input section
        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Enter YouTube channel URL (e.g., https://www.youtube.com/@channelname)")
        self.url_input.setMinimumHeight(40)
        self.url_input.setStyleSheet("""
            QLineEdit {
                background-color: #404040;
                border: 2px solid #666666;
                padding: 10px;
                border-radius: 6px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 2px solid #0078d4;
            }
        """)
        
        self.load_button = QPushButton("🔍 Load Videos")
        self.load_button.setMinimumHeight(40)
        self.load_button.setMinimumWidth(120)
        self.load_button.clicked.connect(self.load_videos)
        
        input_layout.addWidget(self.url_input, 4)
        input_layout.addWidget(self.load_button, 1)
        
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
        self.status_label = QLabel("Enter a YouTube channel URL to get started")
        self.status_label.setStyleSheet("color: #cccccc; padding: 10px; font-size: 12px;")
        
        # Scroll area for videos - using custom scrollbar styling
        from ..shared.custom_scroll import CustomScrollArea
        self.scroll_area = CustomScrollArea()
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(5)
        
        self.scroll_area.setWidget(self.scroll_content)
        self.scroll_area.setWidgetResizable(True)
        
        layout.addLayout(input_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
    
    def load_videos(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Warning", "Please enter a YouTube channel URL")
            return
        
        self.load_button.setEnabled(False)
        self.load_button.setText("⏳ Loading...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # Clear previous videos
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i)
            if child.widget():
                child.widget().setParent(None)
        
        # Start worker thread
        self.worker = YouTubeWorker(url)
        self.worker.progress.connect(self.update_status)
        self.worker.finished.connect(self.on_videos_loaded)
        self.worker.error.connect(self.on_error)
        self.worker.start()
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_videos_loaded(self, videos):
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.load_button.setText("🔍 Load Videos")
        
        if not videos:
            self.status_label.setText("No videos found for this channel.")
            no_videos_label = QLabel("No videos found for this channel.")
            no_videos_label.setStyleSheet("color: #999999; padding: 40px; text-align: center; font-size: 14px;")
            no_videos_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(no_videos_label)
        else:
            self.status_label.setText(f"✅ Loaded {len(videos)} videos (click to view details)")
            
            for video in videos:
                video_frame = VideoFrame(video)
                self.scroll_layout.addWidget(video_frame)
        
        self.scroll_layout.addStretch()
    
    def on_error(self, error_message):
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.load_button.setText("🔍 Load Videos")
        self.status_label.setText("❌ Error occurred")
        QMessageBox.critical(self, "Error", error_message)
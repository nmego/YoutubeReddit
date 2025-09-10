import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, 
                            QPushButton, QLabel, QFrame, QMessageBox, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class RedditPostFrame(QFrame):
    post_clicked = pyqtSignal(dict)
    
    def __init__(self, post_data):
        super().__init__()
        self.post_data = post_data
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
                cursor: pointer;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(8)
        
        # Title
        title_label = QLabel(post_data.get('title', 'No Title'))
        title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #ffffff; margin: 0px;")
        
        # Info bar
        info_parts = []
        info_parts.append(f"r/{post_data.get('subreddit', 'unknown')}")
        info_parts.append(f"u/{post_data.get('author', 'unknown')}")
        info_parts.append(f"{post_data.get('score_formatted', post_data.get('score', 0))} points")
        info_parts.append(f"{post_data.get('comments_formatted', post_data.get('num_comments', 0))} comments")
        
        if 'created_formatted' in post_data:
            info_parts.append(post_data['created_formatted'])
        
        info_text = " • ".join(info_parts)
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: #999999; font-size: 10px; margin: 0px;")
        
        # Preview text if available
        if post_data.get('selftext') and post_data['selftext'].strip():
            preview_text = post_data['selftext']
            if len(preview_text) > 200:
                preview_text = preview_text[:200] + "..."
            
            preview_label = QLabel(preview_text)
            preview_label.setWordWrap(True)
            preview_label.setStyleSheet("color: #cccccc; font-size: 10px; margin-top: 5px;")
            layout.addWidget(preview_label)
        
        # Post type indicator
        post_type = "💬 Text Post" if post_data.get('is_self') else f"🔗 Link ({post_data.get('domain', '')})"
        type_label = QLabel(post_type)
        type_label.setStyleSheet("color: #0078d4; font-size: 9px; margin: 0px;")
        
        layout.addWidget(title_label)
        layout.addWidget(info_label)
        layout.addWidget(type_label)
        
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.post_clicked.emit(self.post_data)

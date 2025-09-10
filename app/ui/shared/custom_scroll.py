from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt

class CustomScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_scrollbars()
    
    def setup_scrollbars(self):
        """Setup custom scrollbar styling that doesn't interfere with content"""
        self.setStyleSheet("""
            QScrollArea {
                border: 1px solid #555555;
                border-radius: 8px;
                background-color: #3c3c3c;
                padding: 0px;
            }
            
            /* Vertical Scrollbar */
            QScrollBar:vertical {
                background-color: transparent;
                width: 14px;
                margin: 0px;
                border: none;
                border-radius: 7px;
            }
            
            QScrollBar::handle:vertical {
                background-color: #666666;
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:vertical:hover {
                background-color: #777777;
            }
            
            QScrollBar::handle:vertical:pressed {
                background-color: #0078d4;
            }
            
            /* Remove scrollbar buttons (arrows) */
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {
                height: 0px;
                background: none;
                border: none;
            }
            
            QScrollBar::up-arrow:vertical,
            QScrollBar::down-arrow:vertical {
                background: none;
                border: none;
            }
            
            QScrollBar::add-page:vertical,
            QScrollBar::sub-page:vertical {
                background: transparent;
            }
            
            /* Horizontal Scrollbar */
            QScrollBar:horizontal {
                background-color: transparent;
                height: 14px;
                margin: 0px;
                border: none;
                border-radius: 7px;
            }
            
            QScrollBar::handle:horizontal {
                background-color: #666666;
                border-radius: 7px;
                min-width: 30px;
                margin: 2px;
            }
            
            QScrollBar::handle:horizontal:hover {
                background-color: #777777;
            }
            
            QScrollBar::handle:horizontal:pressed {
                background-color: #0078d4;
            }
            
            /* Remove scrollbar buttons (arrows) */
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {
                width: 0px;
                background: none;
                border: none;
            }
            
            QScrollBar::left-arrow:horizontal,
            QScrollBar::right-arrow:horizontal {
                background: none;
                border: none;
            }
            
            QScrollBar::add-page:horizontal,
            QScrollBar::sub-page:horizontal {
                background: transparent;
            }
        """)
        
        # Set scroll properties for smooth scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setWidgetResizable(True)
        
        # Enable smooth scrolling
        self.verticalScrollBar().setSingleStep(20)
        self.horizontalScrollBar().setSingleStep(20)
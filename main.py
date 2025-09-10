import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Set enhanced dark theme
    app.setStyleSheet("""
        QMainWindow {
            background-color: #1e1e1e;
            color: #ffffff;
        }
        QWidget {
            background-color: #1e1e1e;
            color: #ffffff;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        QLabel {
            color: #ffffff;
        }
        QMessageBox {
            background-color: #2b2b2b;
            color: #ffffff;
            border: 1px solid #555555;
            border-radius: 8px;
        }
        QMessageBox QPushButton {
            min-width: 80px;
            background-color: #0078d4;
            color: #ffffff;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: bold;
        }
        QMessageBox QPushButton:hover {
            background-color: #106ebe;
        }
        /* Text selection styling */
        QLabel:selection {
            background-color: #0078d4;
            color: #ffffff;
        }
        QTextEdit:selection {
            background-color: #0078d4;
            color: #ffffff;
        }
    """)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
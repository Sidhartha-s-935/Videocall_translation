from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPalette, QColor
import socketio
import sys

class CaptionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-time Captions")
        
        # Set window flags to make it stay on top and frameless
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool  # This prevents the window from showing in taskbar
        )
        
        # Create central widget and layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create caption label
        self.caption_label = QLabel("")
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignCenter)
        self.caption_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
            }
        """)
        
        # Set the window background to be transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.caption_label)
        self.central_widget.setLayout(layout)
        
        # Set initial size and position
        self.resize(800, 100)
        self.move_to_bottom()
        
        # Initialize Socket.IO client
        self.sio = socketio.Client()
        self.setup_socketio()
        
        # Connect to the Flask server
        try:
            self.sio.connect('http://localhost:5000')
        except Exception as e:
            print(f"Failed to connect to server: {e}")
    
    def move_to_bottom(self):
        """Position the window at the bottom of the screen"""
        screen = QApplication.primaryScreen().geometry()
        self.move(
            (screen.width() - self.width()) // 2,
            screen.height() - self.height() - 50
        )
    
    def setup_socketio(self):
        @self.sio.on('transcription_update')
        def on_transcription_update(data):
            translation = data.get('translation', '')
            self.update_caption(translation)
    
    def update_caption(self, text):
        """Update the caption text"""
        self.caption_label.setText(text)
    
    def mousePressEvent(self, event):
        """Enable window dragging"""
        self.old_pos = event.globalPos()
    
    def mouseMoveEvent(self, event):
        """Handle window dragging"""
        delta = event.globalPos() - self.old_pos
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

def run_caption_window():
    """Function to start the caption window"""
    app = QApplication(sys.argv)
    window = CaptionWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_caption_window()

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from flask_socketio import SocketIO
import sys

class SignalHandler(QObject):
    update_caption = pyqtSignal(str)

class CaptionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Real-time Captions')
        self.setStyleSheet("background-color: black;")
        
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | 
            Qt.FramelessWindowHint |
            Qt.Tool 
        )
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        self.caption_label = QLabel()
        self.caption_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 24px;
                font-family: Arial;
                padding: 10px;
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 5px;
            }
        """)
        self.caption_label.setWordWrap(True)
        self.caption_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.caption_label)
        
        screen = QApplication.primaryScreen().geometry()
        window_width = screen.width() // 2
        window_height = 100
        self.setGeometry(
            (screen.width() - window_width) // 2,
            screen.height() - window_height - 50, 
            window_width,
            window_height
        )
        
        self.signal_handler = SignalHandler()
        self.signal_handler.update_caption.connect(self.update_caption)
        
        self.socketio = SocketIO('http://localhost:5000')
        self.setup_socketio()
        
        self.connection_timer = QTimer()
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(5000)
    
    def setup_socketio(self):
        @self.socketio.on('transcription_update')
        def handle_transcription(data):
            translation = data.get('translation')
            if translation:
                self.signal_handler.update_caption.emit(translation)
    
    def update_caption(self, text):
        self.caption_label.setText(text)
    
    def check_connection(self):
        try:
            self.socketio.emit('ping')
        except Exception as e:
            print(f"Connection error: {e}")
            self.socketio = SocketIO('http://localhost:5000')
            self.setup_socketio()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragPosition = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.dragPosition)
            event.accept()

def run_caption_window():
    app = QApplication(sys.argv)
    window = CaptionWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_caption_window()

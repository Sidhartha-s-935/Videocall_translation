import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from socketio import Client

class CaptionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.connectSocket()
        
    def initUI(self):
        self.setWindowTitle('Real-time Captions')
        self.setGeometry(300, 300, 600, 200)
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create labels for transcription and translation
        self.transcription_label = QLabel('Waiting for speech...')
        self.transcription_label.setWordWrap(True)
        self.transcription_label.setAlignment(Qt.AlignCenter)
        
        self.translation_label = QLabel('')
        self.translation_label.setWordWrap(True)
        self.translation_label.setAlignment(Qt.AlignCenter)
        
        # Add labels to layout
        layout.addWidget(self.transcription_label)
        layout.addWidget(self.translation_label)
        
        # Set window flags to keep it always on top
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        
    def connectSocket(self):
        # Use socketio.Client() instead of Flask-SocketIO
        self.socketio = Client()
        
        @self.socketio.on('connect')
        def on_connect():
            print("Connected to server")
            
        @self.socketio.on('disconnect')
        def on_disconnect():
            print("Disconnected from server")
            
        @self.socketio.on('transcription_update')
        def on_transcription(data):
            transcription = data.get('transcription', '')
            translation = data.get('translation', '')
            
            self.transcription_label.setText(f"English: {transcription}")
            if translation:
                self.translation_label.setText(f"Translation: {translation}")
            else:
                self.translation_label.setText('')
                
        # Connect to the server
        try:
            self.socketio.connect('http://localhost:5000')
        except Exception as e:
            print(f"Failed to connect to server: {e}")

def run_caption_window():
    app = QApplication(sys.argv)
    window = CaptionWindow()
    window.show()
    sys.exit(app.exec_())

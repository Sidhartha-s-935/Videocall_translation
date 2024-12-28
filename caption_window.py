import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QPalette, QColor
from socketio import Client
import threading
import logging


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SocketThread(QObject):
    transcription_received = pyqtSignal(str, str)
    connection_status = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.socketio = Client(
            logger=True,
            engineio_logger=True,
            reconnection=True,
            reconnection_attempts=5,
            reconnection_delay=1
        )
        self.setup_socket_events()

    def setup_socket_events(self):
        @self.socketio.on('connect')
        def on_connect():
            logger.info(f"Connected to server with SID: {self.socketio.sid}")
            self.connection_status.emit(True)

        @self.socketio.on('disconnect')
        def on_disconnect():
            logger.info("Disconnected from server")
            self.connection_status.emit(False)

        @self.socketio.on('*')
        def catch_all(event, data):
            logger.debug(f"Received event {event}: {data}")

        @self.socketio.on('transcription_update')
        def on_transcription(data):
            logger.info(f"Received transcription update: {data}")
            try:
                if isinstance(data, dict):
                    transcription = data.get('transcription', '')
                    translation = data.get('translation', '')
                    
                    logger.debug(f"Processing transcription: {transcription}")
                    logger.debug(f"Processing translation: {translation}")
                    
                    # Emit the signal in the main thread
                    self.transcription_received.emit(
                        transcription or 'Waiting for speech...',
                        translation or 'Translation will appear here...'
                    )
            except Exception as e:
                logger.error(f"Error processing transcription update: {e}", exc_info=True)

    def connect_to_server(self):
        try:
            self.socketio.connect(
                'http://localhost:5000',
                transports=['websocket', 'polling'],
                wait_timeout=10,
                wait=True
            )
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}", exc_info=True)
            return False

    def disconnect(self):
        try:
            if self.socketio.connected:
                self.socketio.disconnect()
        except Exception as e:
            logger.error(f"Error during disconnect: {e}", exc_info=True)

class CaptionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.socket_handler = None
        self.initUI()
        self.setupSocket()

    def initUI(self):
        self.setWindowTitle('Real-time Captions')
        self.setGeometry(300, 300, 800, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)

        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#f0f0f0'))
        self.setPalette(palette)

        self.transcription_label = QLabel('Waiting for speech...')
        self.translation_label = QLabel('Translation will appear here...')

        for label in (self.transcription_label, self.translation_label):
            label.setWordWrap(True)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("""
                QLabel {
                    background-color: white;
                    border: 1px solid #ccc;
                    border-radius: 8px;
                    padding: 15px;
                    font-size: 16px;
                }
            """)
            label.setMinimumHeight(80)

            font = QFont()
            font.setPointSize(12)
            label.setFont(font)

        transcription_header = QLabel('English Transcription')
        translation_header = QLabel('Translation')
        for header in (transcription_header, translation_header):
            header.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            header.setFont(font)

        layout.addWidget(transcription_header)
        layout.addWidget(self.transcription_label)
        layout.addWidget(translation_header)
        layout.addWidget(self.translation_label)

        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

    
    def update_connection_status(self, connected):
        if connected:
            self.setWindowTitle('Real-time Captions (Connected)')
        else:
            self.setWindowTitle('Real-time Captions (Disconnected)')

    def setupSocket(self):
        self.socket_handler = SocketThread()
        self.socket_handler.transcription_received.connect(self.update_labels)
        self.socket_handler.connection_status.connect(self.update_connection_status)
        
        # Start connection in a separate thread
        self.socket_thread = threading.Thread(target=self._connect_socket)
        self.socket_thread.daemon = True
        self.socket_thread.start()

    def _connect_socket(self):
        success = self.socket_handler.connect_to_server()
        logger.info(f"Socket connection {'successful' if success else 'failed'}")

    def update_labels(self, transcription, translation):
        try:
            logger.debug(f"Updating labels - Transcription: {transcription}")
            logger.debug(f"Updating labels - Translation: {translation}")
            
            self.transcription_label.setText(transcription)
            self.translation_label.setText(translation)
        except Exception as e:
            logger.error(f"Error updating labels: {e}", exc_info=True)   

    def closeEvent(self, event):
        if self.socket_handler:
            self.socket_handler.disconnect()
        super().closeEvent(event)

def run_caption_window():
    app = QApplication(sys.argv)
    window = CaptionWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_caption_window()

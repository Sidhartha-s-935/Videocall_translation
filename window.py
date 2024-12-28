import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QComboBox, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import logging
from model import ContinuousTranscriber

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TranscriptionThread(QObject):
    transcription_received = pyqtSignal(str, str)
    
    def __init__(self):
        super().__init__()
        self.transcriber = None
        
    def handle_transcription(self, transcription, translation):
        self.transcription_received.emit(
            transcription or 'Waiting for speech...',
            translation or 'Translation will appear here...'
        )
    
    def start_transcription(self, target_language):
        try:
            if self.transcriber:
                self.transcriber.stop_transcription()
            
            self.transcriber = ContinuousTranscriber(target_language=target_language)
            self.transcriber.set_callback(self.handle_transcription)
            self.transcriber.start_transcription()
            logger.info(f"Started transcription with target language: {target_language}")
        except Exception as e:
            logger.error(f"Error starting transcription: {e}", exc_info=True)
    
    def stop_transcription(self):
        try:
            if self.transcriber:
                self.transcriber.stop_transcription()
                logger.info("Stopped transcription")
        except Exception as e:
            logger.error(f"Error stopping transcription: {e}", exc_info=True)

class TranslationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.transcription_thread = None
        self.initUI()
        self.setupTranscription()

    def initUI(self):
        self.setWindowTitle('Real-time Translation')
        self.setGeometry(300, 300, 800, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)

        # Set window background color
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#f0f0f0'))
        self.setPalette(palette)

        # Create control panel
        control_panel = QWidget()
        control_layout = QHBoxLayout(control_panel)
        
        # Language selector
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            'English', 'Spanish', 'French', 'Italian', 
            'Portuguese', 'Romanian', 'Catalan'
        ])
        self.language_combo.setMinimumWidth(150)
        
        # Start/Stop button
        self.toggle_button = QPushButton('Start Translation')
        self.toggle_button.setCheckable(True)
        
        control_layout.addWidget(QLabel('Select Language:'))
        control_layout.addWidget(self.language_combo)
        control_layout.addWidget(self.toggle_button)
        control_layout.addStretch()

        # Create labels for transcription and translation
        self.transcription_label = QLabel('Waiting for speech...')
        self.translation_label = QLabel('Translation will appear here...')

        # Style the labels
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

        # Create and style headers
        transcription_header = QLabel('English Transcription')
        translation_header = QLabel('Translation')
        for header in (transcription_header, translation_header):
            header.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(10)
            font.setBold(True)
            header.setFont(font)

        # Add all widgets to main layout
        layout.addWidget(control_panel)
        layout.addWidget(transcription_header)
        layout.addWidget(self.transcription_label)
        layout.addWidget(translation_header)
        layout.addWidget(self.translation_label)

        # Window properties
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        # Connect signals
        self.toggle_button.clicked.connect(self.toggle_translation)
        self.language_combo.currentTextChanged.connect(self.language_changed)

    def setupTranscription(self):
        self.transcription_thread = TranscriptionThread()
        self.transcription_thread.transcription_received.connect(self.update_labels)

    def toggle_translation(self, checked):
        if checked:
            self.toggle_button.setText('Stop Translation')
            language = self.language_combo.currentText().lower()
            self.transcription_thread.start_transcription(language)
        else:
            self.toggle_button.setText('Start Translation')
            self.transcription_thread.stop_transcription()

    def language_changed(self, language):
        if self.toggle_button.isChecked():
            self.transcription_thread.stop_transcription()
            self.transcription_thread.start_transcription(language.lower())

    def update_labels(self, transcription, translation):
        try:
            self.transcription_label.setText(transcription)
            self.translation_label.setText(translation)
        except Exception as e:
            logger.error(f"Error updating labels: {e}", exc_info=True)

    def closeEvent(self, event):
        if self.transcription_thread:
            self.transcription_thread.stop_transcription()
        super().closeEvent(event)

def run_translation_window():
    app = QApplication(sys.argv)
    window = TranslationWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_translation_window()

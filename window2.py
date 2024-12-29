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

class TranslationThread(QObject):
    translation_received = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.transcriber = None

    def handle_translation(self, translation):
        self.translation_received.emit(
            translation or 'Translation will appear here...'
        )

    def start_translation(self, target_language):
        try:
            if self.transcriber:
                self.transcriber.stop_transcription()

            self.transcriber = ContinuousTranscriber(target_language=target_language)
            self.transcriber.set_callback(lambda _, translation: self.handle_translation(translation))
            self.transcriber.start_transcription()
            logger.info(f"Started translation with target language: {target_language}")
        except Exception as e:
            logger.error(f"Error starting translation: {e}", exc_info=True)

    def stop_translation(self):
        try:
            if self.transcriber:
                self.transcriber.stop_transcription()
                logger.info("Stopped translation")
        except Exception as e:
            logger.error(f"Error stopping translation: {e}", exc_info=True)

class TranslationWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.translation_thread = None
        self.initUI()
        self.setupTranslation()

    def initUI(self):
        self.setWindowTitle('Real-time Translation')
        self.setGeometry(300, 300, 800, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)

        #dark moode
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#2b2b2b'))
        palette.setColor(QPalette.WindowText, QColor('#ffffff'))
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
        self.language_combo.setStyleSheet("""
        background-color: #2b2b2b;
        color: #ffffff;
        """)
        self.language_combo.setMinimumWidth(150)

        # Start/Stop button
        self.toggle_button = QPushButton('Start Translation')
        self.toggle_button.setStyleSheet("""
        background-color: #2b2b2b;
        color: #ffffff;
        """)

        self.toggle_button.setCheckable(True)

        control_layout.addWidget(QLabel('Select Language:'))
        control_layout.addWidget(self.language_combo)
        control_layout.addWidget(self.toggle_button)
        control_layout.addStretch()

        # Translation label
        self.translation_label = QLabel('Translation will appear here...')
        self.translation_label.setWordWrap(True)
        self.translation_label.setAlignment(Qt.AlignCenter)
        self.translation_label.setStyleSheet("""
            QLabel {
                background-color: #3c3f41;
                border: 1px solid #5c5c5c;
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
                color: #dcdcdc;
            }
        """)
        self.translation_label.setMinimumHeight(80)

        # Add widgets to the main layout
        layout.addWidget(control_panel)
        layout.addWidget(self.translation_label)

        # Window properties
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.Tool)

        # Connect signals
        self.toggle_button.clicked.connect(self.toggle_translation)
        self.language_combo.currentTextChanged.connect(self.language_changed)

    def setupTranslation(self):
        self.translation_thread = TranslationThread()
        self.translation_thread.translation_received.connect(self.update_label)

    def toggle_translation(self, checked):
        if checked:
            self.toggle_button.setText('Stop Translation')
            language = self.language_combo.currentText().lower()
            self.translation_thread.start_translation(language)
        else:
            self.toggle_button.setText('Start Translation')
            self.translation_thread.stop_translation()

    def language_changed(self, language):
        if self.toggle_button.isChecked():
            self.translation_thread.stop_translation()
            self.translation_thread.start_translation(language.lower())

    def update_label(self, translation):
        try:
            self.translation_label.setText(translation)
        except Exception as e:
            logger.error(f"Error updating label: {e}", exc_info=True)

    def closeEvent(self, event):
        if self.translation_thread:
            self.translation_thread.stop_translation()
        super().closeEvent(event)

def run_translation_window():
    app = QApplication(sys.argv)
    window = TranslationWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run_translation_window()



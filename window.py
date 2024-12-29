import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QPushButton, QComboBox, QHBoxLayout
)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QColor, QPalette
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
            translation or 'Waiting for speech...'
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
        self.setWindowTitle('Speech Translation')
        self.setGeometry(300, 300, 600, 200)

        # Set up dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #000000;
            }
            QPushButton {
                background-color: #7B68EE;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 100px;
                min-height: 40px;
            }
            QPushButton:checked {
                background-color: #483D8B;
            }
            QComboBox {
                background-color: #1A1A1A;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 20px;
                min-width: 150px;
                min-height: 40px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #1A1A1A;
                color: white;
                selection-background-color: #7B68EE;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Translation display
        self.translation_label = QLabel('Waiting for speech...')
        self.translation_label.setWordWrap(True)
        self.translation_label.setAlignment(Qt.AlignCenter)
        self.translation_label.setStyleSheet("""
            QLabel {
                background-color: #1A1A1A;
                color: white;
                border-radius: 10px;
                padding: 20px;
                font-size: 16px;
            }
        """)
        self.translation_label.setMinimumHeight(100)

        # Controls container
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setSpacing(10)

        # Language dropdown
        self.language_combo = QComboBox()
        self.language_combo.addItems([
            'English', 'Spanish', 'French', 'Italian', 
            'Portuguese', 'Romanian', 'Catalan'
        ])

        # Start/Stop button
        self.toggle_button = QPushButton('Start')
        self.toggle_button.setCheckable(True)

        # Add controls to layout
        controls_layout.addWidget(self.language_combo)
        controls_layout.addWidget(self.toggle_button)
        controls_layout.addStretch()

        # Add widgets to main layout
        layout.addWidget(self.translation_label)
        layout.addWidget(controls_widget)

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
            self.toggle_button.setText('Stop')
            language = self.language_combo.currentText().lower()
            self.translation_thread.start_translation(language)
        else:
            self.toggle_button.setText('Start')
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

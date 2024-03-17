from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPlainTextEdit
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QFont
import sys

class TranslationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.translated_text_edit = QPlainTextEdit()
        self.translated_text_edit.setReadOnly(True)
        
        font = QFont("Arial", 14) 
        self.translated_text_edit.setFont(font)
        self.translated_text_edit.setStyleSheet("background-color: black; color: white; border: none; padding: 10px;")

        layout.addWidget(self.translated_text_edit)

        self.setLayout(layout)

        self.setStyleSheet("background-color: black;")
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.update_displayed_content()

        self.resize(800, 100)

        self.translated_text_edit.textChanged.connect(self.adjust_window_size)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_displayed_content)
        self.timer.start(1000)

    def update_displayed_content(self):
        try:
            with open("translated.txt", "r", encoding="utf-8") as file:
                content = file.read().strip()

            self.translated_text_edit.setPlainText(content)

        except Exception as e:
            print(f"Error updating displayed content: {e}")

    def adjust_window_size(self):
        text_height = self.translated_text_edit.document().size().height()
        self.resize(self.width(), int(text_height) + 20)  
    def mousePressEvent(self, event):
        self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.old_pos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        pass

    def closeEvent(self, event):
        with open("translated.txt", "w", encoding="utf-8") as file:
            file.write("")

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = TranslationApp()
    main_app.show()
    sys.exit(app.exec_())

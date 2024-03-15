from PyQt5.QtWidgets import QApplication, QVBoxLayout, QWidget, QPlainTextEdit, QLabel, QPushButton, QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QPoint
from PyQt5.QtGui import QFont
import sys

class TranslationApp(QWidget):
    def __init__(self):
        super().__init__()

        self.drag_position = QPoint()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.title_label = QLabel("Real-time Translation History")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("background-color: black; color: white;")
        self.title_label.setFont(QFont('Arial', 16))

        close_button = QPushButton("X")
        close_button.setStyleSheet("background-color: red; color: white;height:10;width:10;")
        close_button.clicked.connect(self.close_app)

        title_layout = QHBoxLayout()
        title_layout.addWidget(self.title_label)
        title_layout.addWidget(close_button)
        
        layout.addLayout(title_layout)

        self.translated_text_edit = QPlainTextEdit()
        self.translated_text_edit.setReadOnly(True)
        self.translated_text_edit.setStyleSheet("background-color: black; color: white;")
        self.translated_text_edit.setFont(QFont('Arial', 16))

        layout.addWidget(self.translated_text_edit)

        self.setLayout(layout)

        self.setStyleSheet("background-color: black;")
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.setGeometry(300, 300, 800, 100)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_displayed_content)
        self.timer.start(1000)

    def update_displayed_content(self):
        try:
            with open("translated.txt", "r", encoding="utf-8") as file:
                content = file.read().replace('\n', ' ').strip()

            self.translated_text_edit.setPlainText(content)

        except Exception as e:
            print(f"Error updating displayed content: {e}")

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.title_label.rect().contains(event.pos()):
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)

    def mouseReleaseEvent(self, event):
        self.drag_position = QPoint()

    def close_app(self):
        with open("translated.txt", "w", encoding="utf-8") as file:
            file.write("")

        self.close()

    def closeEvent(self, event):
        with open("translated.txt", "w", encoding="utf-8") as file:
            file.write("")

        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_app = TranslationApp()
    main_app.show()
    sys.exit(app.exec_())

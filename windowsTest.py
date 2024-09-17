from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import QTimer, Qt, QEvent, QCoreApplication
from PyQt6.QtGui import QCursor, QKeySequence, QShortcut
import sys
import keyboard
class PopupMessage(QWidget):
    def __init__(self, message):
        print("init!")
        super().__init__()
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.label = QLabel(message, self)
        self.label.setStyleSheet("background-color: rgba(255, 255, 255, 0.8); border-radius: 5px; padding: 10px;")

        self.adjustSize()
        self.move(QCursor.pos())
        self.show()
        print("show!")
        self.cursor_pos = QCursor.pos()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_cursor)
        self.timer.start(100)  # 每100毫秒检查一次鼠标位置

    def check_cursor(self):
        if QCursor.pos() != self.cursor_pos:
            print("close!")
            self.close()

def show_popup_message():
    print("show1")
    QCoreApplication.postEvent(app, ShowPopupEvent("Hello, world!"))

class ShowPopupEvent(QEvent):
    def __init__(self, message):
        super().__init__(QEvent.Type(QEvent.registerEventType()))
        self.message = message

if __name__ == '__main__':
    app = QApplication(sys.argv)
    def eventFilter(obj, event):
        if isinstance(event, ShowPopupEvent):
            PopupMessage(event.message)
            return True
        return False
    app.installEventFilter(eventFilter)
    keyboard.add_hotkey('ctrl+q', show_popup_message)
    sys.exit(app.exec())
    
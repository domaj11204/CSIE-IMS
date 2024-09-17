"""顯示搜尋結果的黑色彈出視窗"""
import sys
import pyautogui
from PyQt6.QtWidgets import QApplication, QLabel, QWidget
from PyQt6.QtCore import Qt, QPoint, QTimer
import time

class MouseTooltipWidget(QWidget):
    def __init__(self, text):
        super().__init__()
        self.label = QLabel(text, self)
        self.label.setStyleSheet("background-color: black; color: white; border: 1px solid white; padding: 5px;")
        self.label.adjustSize()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.adjustSize()
        height = self.height()
        x, y = pyautogui.position()
        self.move(QPoint(x, y-height))  # 初始位置設定為螢幕上的某個位置

def main():
    app = QApplication(sys.argv)
    
    # 讀取命令行參數
    if len(sys.argv) < 2:
        print("Usage: python script.py <text_to_display>")
        sys.exit(1)

    text_to_display = ' '.join(sys.argv[1:])
    
    tooltip_widget = MouseTooltipWidget(text_to_display)
    tooltip_widget.show()
    start_x, start_y = pyautogui.position()

    # 使用 QTimer 來定期檢查滑鼠位置
    def check_mouse_position():
        x, y = pyautogui.position()
        if x != start_x or y != start_y:
            tooltip_widget.close()
            app.quit()

    timer = QTimer()
    timer.timeout.connect(check_mouse_position)
    timer.start(500)  # 每 500 毫秒檢查一次滑鼠位置

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
"""
用於實作所有需要的pyqt彈出視窗
執行時使用subprocess+參數呼叫此檔案
TODO: 但這種作法導致彈出視窗的反應較慢
"""

from PyQt6 import QtWidgets, QtGui, uic
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QWidget
import sys
import keyboard
import time
import threading
from RNSApi import send_triple
from modules.utils import get_server_url, call_api
import requests
# log文件設定
import logging
logFileName = "./log/PyQt_"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
logging.basicConfig(filename=logFileName, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# 註冊一個事件，用於監聽是否要開啟視窗
show_window = threading.Event()

test = 1
app_path = "unknown_exe_path"
app_name = "unknown_exe_name"

# PyQt windows class
class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My PyQt Window"+str(test))
        #Load the UI Page by PyQt6
        # 選擇使用的ui模板
        uic.loadUi('./01.ui', self)
        
class AddTermWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AddTermWindow"+str(test))
        #Load the UI Page by PyQt6
        # 選擇使用的ui模板
        uic.loadUi('./add term.ui', self)

class excerpt_from_code(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ttttt")
        # 選擇使用的ui模板
        uic.loadUi('./excerpt code2.ui', self)


def save_excerpt(my_window:MyWindow):
    """按鈕的click事件

    Args:
        my_window (MyWindow): 用於讀資料
    """
    # TODO: 處理軟體名稱的部分應該在這裡做
    print(my_window.excerptText.toPlainText())
    if "來自論文: " in window.windowTitle.text()[0:6]:
        window_title = window.windowTitle.text().split("論文: ",1)[1]
    else:
        window_title = window.windowTitle.text().split("標題: ",1)[1]
    
    url = get_server_url() + "/excerpt"
    result = requests.post(url, json={"text": my_window.excerptText.toPlainText(),
                                      "description": my_window.DescriptionText.toPlainText(),
                                      "tag_string": my_window.TagString.text(),
                                      "app_path": app_path,
                                      "app_name": app_name,
                                      "window_title": window_title})
    print(result)
    my_window.close()

# 原本用於特殊的程式碼摘錄事件，且使用專用的ui，目前暫不使用
def save_code(my_window:MyWindow):
    """匯出程式碼時按鈕的click事件

    Args:
        my_window (MyWindow): 用於讀資料
    """
    file_name = my_window.Path.text()
    error_message = my_window.ErrorMessage.toPlainText()
    code_text = my_window.CodeText.toPlainText()
    description = my_window.DescriptionText.toPlainText()
    # 從設定取得url
    url = get_server_url() + "/code_excerpt"
    # 將摘錄資訊Post到FastAPI
    import requests
    requests.post(
        url,
        json={"file_name": file_name,
              "code_text": code_text, 
              "description": description, 
              "error_message": error_message}
    )
    my_window.close()
    
from modules.debug_utils import timer
@timer
def save_term(term_window:AddTermWindow):
    """新增術語按鈕的click事件

    Args:
        term_window (AddTermWindow): 用於讀資料
    """
    data = {}
    data["term"] = term_window.Term.text()
    data["description"] = term_window.DescriptionText.toPlainText()
    data["path"] = term_window.Path.text()
    data["abstract"] = term_window.AbstractText.toPlainText()
    term_window.close()
    print(data)
    import requests
    response = requests.post(
        "http://localhost:27711/term",
        json=data
    )
    if response.status_code == 200:
        print("新增術語完成!")
        print(data)
    

    
if __name__ == "__main__":
    mode = sys.argv[1]
    print("pyQT:", mode)     
    if mode == "export_from_app":
        pyqt_title = sys.argv[2]
        pyqt_text = sys.argv[3]
        app_path = sys.argv[4]
        print("pyQT:", pyqt_title)
        # 嘗試切出exe_name，若不是windows應該沒辦法用
        try:
            app_name = app_path.split("/")[-1]
        except:
            print("WARN: app_name切失敗，可能是因為不是Windows路徑")
        # 使用通用的摘錄，用於研討會實際案例    
        # if "Visual Studio Code" in pyqt_title:
        #     """程式碼摘錄
        #     """
        #     # 目前用減號切，如果檔名中有減號會出問題
        #     app = QApplication(sys.argv)
        #     filename = pyqt_title.split(" - ")[0].replace("● ","") # 過濾掉檔名前的符號
        #     window  = excerpt_from_code()
        #     window.setWindowTitle("程式碼匯出")
        #     window.fileName.setText("檔案: " + filename)
        #     window.excerptText.setText(pyqt_text)
        #     # 綁定儲存按鈕的事件
        #     window.saveExcerpt.clicked.connect(lambda: save_code(window))
        if "zotero.exe" == app_path.split("/")[-1]:
            """論文摘錄
            """
            print("論文摘錄")
            # 目前用減號切，如果檔名中有減號會出問題
            app = QApplication(sys.argv)
            filename = pyqt_title.split(" - Zetoro")[0]
            paper_name = filename.split(" - ")[0]
            window  = MyWindow()
            window.setWindowTitle("論文: " + paper_name)
            window.windowTitle.setText("來自論文: " + paper_name)
            window.excerptText.setText(pyqt_text)
            window.saveExcerpt.clicked.connect(lambda: save_excerpt(window))
        else:
            
            app = QApplication(sys.argv)
            window = MyWindow()
            window.setWindowTitle(str(pyqt_title))
            window.windowTitle.setText("標題: " + pyqt_title)
            window.excerptText.setText(pyqt_text)
            window.saveExcerpt.clicked.connect(lambda: save_excerpt(window))
        
    if "add_term" in mode:
        # 新增術語，可以直接開啟或選擇術語後開啟
        pyqt_title = sys.argv[2] # 標題
        term = sys.argv[3] # 術語，可能為空
        app_path = sys.argv[4] # 路徑，可能為空
        
        app = QApplication(sys.argv)
        window = AddTermWindow()
        window.setWindowTitle(str(pyqt_title))
        window.Term.setText(term)
        window.Path.setText(app_path)
        window.SaveButton.clicked.connect(lambda: save_term(window))
    
    # 視窗置中
    screen_size = QtWidgets.QApplication.screens()[0].size()
    screen_w = screen_size.width()            # 電腦螢幕寬度
    screen_h = screen_size.height()           # 電腦螢幕高度
    new_x = int((screen_w - window.width())/2)   # 計算後的 x 座標
    new_y = int((screen_h - window.height())/2)   # 計算後的 y 座標
    window.move(new_x, new_y)              # 移動視窗
    window.show()
    window.activateWindow()
    sys.exit(app.exec())



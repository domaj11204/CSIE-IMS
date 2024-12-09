"""本檔案處理摘錄相關功能，並提供API給FastAPI使用"""
import pyperclip
import keyboard
import time
import subprocess
import sys
import signal
from modules.windows import get_foreground_window_title 
excerpt_window_pid = None

from pydantic import BaseModel
class excerpt_data(BaseModel):
    window_title:str
    text:str
    description:str
    app_path:str
    app_name:str
    tag_string:str=""
    
    model_config = {
        "json_schema_extra":{
            "examples": [
                {
                    "window_title": "testTitle",
                    "text": "testText",
                    "description": "testDescription",
                    "app_path": "testAppPath",
                    "app_name": "testAppName",
                    "tag_string": "testTagString"
                }
            ]
        },
        "extra": "allow"
    }

def signal_handler(sig, frame):
    if excerpt_window_pid:
        print("關閉excerpt_window...")
        excerpt_window_pid.terminate()  # 或者 proc.kill() 如果 terminate()不夠
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    """處理關於在任意頁面中匯出任何可複製的文字
    """
    # 先備份剪貼簿
    clipbord_backup = pyperclip.paste()
    # 發出新的快捷鍵之前要先把前一個快捷鍵釋放
    # keyboard.release(shortcut)
    keyboard.press_and_release('ctrl+c')

    time.sleep(0.05)
    try:
        text = pyperclip.paste()
        pyperclip.copy(clipbord_backup) # 復原剪貼簿
        windowTitle, app_path = get_foreground_window_title()
        
        
        print("標題:", windowTitle,"\n獲取的文字:", text)
        
        # 彈出記錄用介面
        excerpt_window_pid = subprocess.run(["python", "./PyQt.py", "export_from_app", windowTitle, text, app_path])
        print("subprocess end")
        # 讀取neo4j中關於這個網頁的描述
        # description = DB.getDescription(title=trueTitle)
        
    except Exception as e:
        print("無法讀取剪貼簿:", e)
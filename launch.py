"""管理整個系統，管理快捷鍵、Thread、初始化及關閉。
"""
import asyncio
import time
import json
import logging
import signal
import keyboard
from modules.neo4j import neo4jDB, pageStruct
import pyperclip
from modules.windows import get_foreground_window_title 
from modules.debug_utils import print_func_name
from modules.utils import call_api
import subprocess

excerpt_pid = None
uvicorn_pid = None
DB:neo4jDB = None


def signal_handler(signum, frame):
    """用於捕捉ctrl+c的handler，進行關閉連線及廣播後才關閉程式

    Args:
        signum (_type_): _description_
        frame (_type_): _description_
    """
    if signum == signal.SIGINT.value:
        print("正在關閉連線......")
        DB.close()
        try:
            excerpt_pid.terminate()()
            excerpt_pid.wait()
        except:
            print("關閉視窗失敗，可能是因為視窗不存在")
        print("關閉fastapi server中......")
        try:
            uvicorn_pid.terminate()
            uvicorn_pid.wait()
        except:
            print("關閉fastapi server失敗。")
        print("關閉完成!")
        exit()
    else:
        exit()

import asyncio

def sync_wrapper(async_func, *args, **kwargs):
    """用於將async function包裝成一般function"""
    asyncio.run(async_func(*args, **kwargs))
    
@print_func_name
def export_hotkey(shortcut:str):
    """處理關於在任意頁面中匯出任何可複製的文字
    """
    excerpt_pid = subprocess.run(["python", "./excerpt.py"])

@print_func_name
async def search_key_word(shortcut:str):
    """將選擇的關鍵字的相關訊息顯示出來
    """
    # 發出新的快捷鍵之前要先把前一個快捷鍵釋放
    keyboard.release(shortcut)
    # 先備份剪貼簿
    clipbord_backup = pyperclip.paste()
    keyboard.press_and_release('ctrl+c')

    time.sleep(0.05)
    try:
        text = pyperclip.paste()
        pyperclip.copy(clipbord_backup) # 復原剪貼簿
        # result = (await call_api("/v1/knowledge_base/search", "get", params={"keyword": text, "source_str":"obsidian", "top_k":1}))["result"]
        result += (await call_api("/v1/knowledge_base/search", "get", params={"keyword": text, "source_str":"history", "top_k":1}))["result"]
        # 彈出視窗
        subprocess.run(["python", "./term_window.py", result])
        print("測試結束")
    except Exception as e:
        import traceback
        print("查詢知識庫失敗:", e)
        print(traceback.format_exc())
        
@print_func_name
def add_term(shortcut:str):
    # 發出新的快捷鍵之前要先把前一個快捷鍵釋放
    keyboard.release(shortcut)
    # 先備份剪貼簿
    clipbord_backup = pyperclip.paste()
    keyboard.press_and_release('ctrl+c')
    time.sleep(0.05)
    try:
        text = pyperclip.paste()
        pyperclip.copy(clipbord_backup) # 復原剪貼簿
        # 原本由kb管理新增術語的邏輯，但這樣就不是由launch管理pid
        # result = kb.add_term(text)
        windowTitle, app_path = get_foreground_window_title()
        excerpt_window_pid = subprocess.run(["python", "./PyQt.py", "add_term_from_app", "新增術語", text, app_path])
        
    except Exception as e:
        import traceback
        print("新增術語失敗:", e)
        print(traceback.format_exc())

async def download_tag_list():
    """用於下載資料庫中的所有標籤並存成txt，減少標籤推薦時的IO時間
    """
    # TODO: 下載標籤列表
    # record_list = DB.search(label="標籤")
    while True:
        try:
            record_list = (await call_api("/v1/knowledge_base/tag", "GET"))["tags"]
            if len(record_list) > 0:
                break
            else:
                print("錯誤：", record_list)
                continue
        except Exception as e:
            print(f"下載標籤列表失敗: {e}")
            time.sleep(5)
    with open("./TagList.txt",'w') as f:
        for record in record_list:
            print(record, file=f)
    print("更新完成，待命中")

@print_func_name
def test_hotkey():
    string = """
    Run su
    """
    record = DB.get_graph_information()
    print(DB.records_to_df(records=record, key=None))
    # subprocess.run(["python", "./PyQt.py", "AA", string])

@print_func_name
def excerpt_code():
    """專門用於程式碼匯出
    """
    from modules.code import error_message_excerpt
    error_message_excerpt()


if __name__ == "__main__":
    # log文件設定
    logFileName = "./log/"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    logging.basicConfig(filename=logFileName, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

    # 讀取config.yaml
    from modules.utils import read_config
    config = read_config()

    # 初始化知識庫
    from modules.knowledge_base import knowledge_base
    kb = knowledge_base(config=config)

    # 監聽快捷鍵，內建額外thread的功能，在window下不需要root權限
    shortcuts = config["shortcuts"]
    keyboard.add_hotkey(shortcuts["export"], export_hotkey, args=[shortcuts["export"]]) # 匯出資料
    keyboard.add_hotkey(shortcuts["search"], sync_wrapper, args=(search_key_word, shortcuts["search"])) # 顯示關鍵字資訊
    keyboard.add_hotkey(shortcuts["add"], add_term, args=[shortcuts["add"]])
    keyboard.add_hotkey(shortcuts["excerpt"], excerpt_code) # 專門匯出程式碼
    # 註: 理論上add_hotkey可以加上參數trigger_on_release，但目前因為不明原因，反而在按下快捷鍵後不須放開，而是同時按下其他按鍵後才能觸發 https://github.com/boppreh/keyboard/issues/291
    # 測試用
    keyboard.add_hotkey('ctrl+t', test_hotkey)

    # 連線資料庫
    DB = neo4jDB(config["neo4j"]["url"], config["neo4j"]["user"], config["neo4j"]["password"])

    # 使用subporcess運行fastapi server
    uvicorn_pid = subprocess.Popen(["python", "launch_uvicorn.py", config["FastAPI"]["host"], config["FastAPI"]["port"]], stdout=None, stderr=None)
    uvicorn_pid2 = subprocess.Popen(["python", "launch_uvicorn.py", config["FastAPI"]["host"], "27712"], stdout=None)
    # 目前的情況看起來可以正常的關閉子thread，不知道為啥
    signal.signal(signal.SIGINT, signal_handler)

    # 更新TagList
    print("更新tag中...")
    import asyncio
    asyncio.run(download_tag_list())
    
    while True:
        time.sleep(30)
        if uvicorn_pid.poll() is not None:
            print("FastAPI1錯誤關閉。", uvicorn_pid.poll())
            exit()
        if uvicorn_pid2.poll() is not None:
            print("FastAPI2錯誤關閉。", uvicorn_pid2.poll())
            exit()
    asyncio.get_event_loop().run_forever()
    """暫時棄用websocket
    asyncio.get_event_loop().run_until_complete(
        websockets.serve(echo, 'localhost', 27709))
    asyncio.get_event_loop().run_forever()
    """
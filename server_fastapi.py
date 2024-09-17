"""此檔案管理系統中關於fastapi的內容
預期的呼叫方式為
`$uvicorn server_fastapi:app --host 0.0.0.0 --port 27711 --reload`
"""
from typing import Annotated

from fastapi import FastAPI, Query, HTTPException, Response, status
from fastapi.responses import JSONResponse
from typing import Dict
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, HttpUrl
from router import obsidian, llm, embedded, chrome, reference, neo4j, rag, knowledge_base, rdf, history
import time
import threading
import os
import psutil
from modules.MessageHandle import messageHandle, set_DB
from excerpt import excerpt_data
from modules.utils import read_config, call_api
config = read_config()
# log文件設定
import logging
logFileName = "./log/fastapi_"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
logging.basicConfig(filename=logFileName, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# 建立FastAPI，並設定swagger_ui中預設折疊所有的項目
app = FastAPI(swagger_ui_parameters = {"docExpansion":"none"})
app.include_router(obsidian.router)
app.include_router(llm.router)
#app.include_router(embedded.router)
app.include_router(chrome.router)
app.include_router(reference.router)
app.include_router(neo4j.router)
app.include_router(rag.router)
app.include_router(knowledge_base.router) # 因為已經import modules.knowledge_base，所以要改名
app.include_router(rdf.router)
app.include_router(history.router)

from fastapi.middleware.cors import CORSMiddleware
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
import gradio as gr

# TODO: 目前為自動啟動gradio，可考慮改為確認FastAPI啟動後再啟動
from webui import demo
gr.mount_gradio_app(app, demo, path="/gradio", allowed_paths=["."])

# 用於儲存摘錄等需要分兩個HTTP API的資料
process_status = {
    "is_running": False,
    "result": None
}

executor = ThreadPoolExecutor(max_workers=1)

class NoteItem(BaseModel):
    name: str
    tags: set[str] = set()
    url: HttpUrl | None = None
    note: str | None = None

class test_A(BaseModel):
    name: str
    des: str
class test_B(BaseModel):
    name: str
    des2: str

class triple(BaseModel):
    APIVersion:str=None
    predicate:str=None
    subject:dict
    object:dict



class goal_json(BaseModel):
    goal:str

class shortcut_data(BaseModel):
    shortcut:str
    name:str


    
@app.get("/")
def root():
    return {"Hello": "FastAPI"}

@app.post("/add_tag/{name}", response_model=NoteItem)
async def add_tag(name: str, tag_list: Annotated[frozenset[str], Query(
    description="要新增的標籤列表"
)]) -> NoteItem:
    """
    為已建立的筆記物件新增標籤
    - name: 物件名稱
    - tag_list: 要新增的標籤列表
    """
    note_item = get_note_item(name)
    if note_item == None:
        raise HTTPException(status_code=404, detail="查無此物件")
    note_item.tags.add(tag_list)
    return note_item

@app.get("/tag_recommend", 
        summary="根據關鍵字推薦標籤", 
        response_model=list)
async def tag_recommend(keyword:str) -> list[str]:
    if keyword == "":
        return []
    recommend_result = ""
    with open('./TagList.txt','r') as f:
        tag_list = f.readlines()
    for tag in tag_list:
        if keyword in tag:
            recommend_result += tag
    return recommend_result.split("\n")[:-1] # 去掉最後一個換行造成的空白

# 可用URL關閉伺服器
# 參考: https://github.com/tiangolo/fastapi/issues/1509#issuecomment-787196514
def self_terminate():
    time.sleep(1)
    parent = psutil.Process(psutil.Process(os.getpid()).ppid())
    parent.kill()

@app.get("/kill")
async def kill():
    threading.Thread(target=self_terminate, daemon=True).start()
    return {"success":True}

@app.post("/upload_triple")
def test_triple(triple: triple):
    print("APIVersion: ", triple.APIVersion)
    print("predicate: ", triple.predicate)
    print("subject: ", triple.subject)
    print("object: ", object)
    # 先串回原本處理websocket用的messagehandler
    
    # https://docs.pydantic.dev/1.10/usage/exporting_models/
    print("ready for message handler:", triple.model_dump_json())
    messageHandle(triple.model_dump_json())
    return {"triple": "ok"}

@app.post(
    path="/goal",
    summary="設定目標",
    description="設定當前的目標",
)
def set_goal(goal:goal_json):
    print("設定目標:", goal.goal)
    # TODO: 未實作
    return {"result": "ok"}

@app.get(path="/highlight",
        summary="取得游標選取的文字",
        description="藉由剪貼簿取得游標選取的文字。\n\n有些剪貼簿內容可能無法完整還原。",
        response_model=str,
        responses={
            200: {
                "description": "游標選取的文字",
            }}
        )
async def get_highlight():
    import pyperclip
    import keyboard
    # 先備份剪貼簿
    clipbord_backup = pyperclip.paste()
    # 發出新的快捷鍵之前要先把前一個快捷鍵釋放
    keyboard.press_and_release('ctrl+c')

    time.sleep(0.05)
    text = pyperclip.paste()
    pyperclip.copy(clipbord_backup) # 復原剪貼簿
    return text

@app.get(path="/shortcut",
         summary="取得快捷鍵列表",
         description="取得快捷鍵列表",
         response_model=dict)
async def get_shortcut():
    from modules.utils import read_config
    config = read_config()["shortcuts"]
    return {"result":list(config.values())}

@app.get(path="/shortcut",
         summary="新增快捷鍵",
         description="新增快捷鍵與對應的名稱",
         response_model=dict)
async def add_shortcut(shortcut_dict:shortcut_data):
    from modules.utils import read_config
    config = read_config()["shortcuts"]
    if shortcut_dict.name in config or shortcut_dict.shortcut in config.values():
        return {"result":"快捷鍵已存在"}
    else:
        pass
    return {"result":list(config.values())}

@app.get(path="/excerpt",
        summary="呼叫摘錄視窗",
        description="紀錄反白文字及視窗，呼叫摘錄視窗",
        response_model=str,
        responses={
            200: {
                "description": "摘錄結果，包含視窗名稱及檔案",
                "content": {
                    "application/json": {
                        "example": {
                            "window_title": "視窗標題", 
                            "text": "摘錄內容",
                            "description": "摘錄說明",
                            "app_path": "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe"}}
                    }   
                }
            }
        )

async def excerpt():
    """處理關於在任意頁面中匯出任何可複製的文字"""
    if process_status["is_running"]:
        raise HTTPException(status_code=400, detail="Process is already running")

    # 設置子進程狀態
    process_status["is_running"] = True
    process_status["result"] = None

    # # 重置事件
    # process_event.clear()

    # # 啟動背景任務
    # print("啟動背景任務")
    # loop = asyncio.get_running_loop()
    # loop.run_in_executor(executor, run_subprocess)

    # print("等待...")
    # 非同步等待子進程完成
    process = await asyncio.create_subprocess_shell(
        "python ./excerpt.py",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()
    if process.returncode == 0:
        while process_status["result"] is None:
            await asyncio.sleep(0.1)
        return JSONResponse(content=process_status["result"])
    else:
        return {"GGG":"GGG"}

def run_subprocess():
    try:
        import keyboard
        import pyperclip
        from modules.windows import get_foreground_window_title

        # 先備份剪貼簿
        clipbord_backup = pyperclip.paste()
        keyboard.press_and_release('ctrl+c')

        time.sleep(0.05)
        global excerpt_window_pid
        text = pyperclip.paste()
        pyperclip.copy(clipbord_backup)  # 復原剪貼簿
        windowTitle, app_path = get_foreground_window_title()

        print("標題:", windowTitle, "\n獲取的文字:", text)

        # 彈出記錄用介面
        subprocess.run(["python", "./PyQt.py", "export_from_app", windowTitle, text, app_path])
        process_status["is_running"] = False
        process_event.set()
    except Exception as e:
        result = f"無法讀取剪貼簿: {e}"
    
        
@app.post(path="/excerpt",
        summary="新增摘錄",
        description="新增剪貼簿中的摘錄",
        response_model=dict)
async def accept_excerpt(excerpt_data:excerpt_data):
    """接收摘錄資料
    """
    # 若是由HTTP API呼叫出的摘錄，則將資料存入process_status，不作其他處理。
    if process_status["is_running"]:
        process_status["result"] = excerpt_data.dict()
        process_status["is_running"] = False
        return {"result": "continue"}
    
    # 預設的快捷鍵呼叫
    else:
        print(excerpt_data.dict())
        result = (await call_api("/v1/knowledge_base/excerpt", "post", data=excerpt_data.dict()))["result"]
    # process_event.set()
    return {"result": result}

@app.post(
    path="/gradio/",
    summary="啟動gradio",
    description="將gradio掛載到fastapi下",
    response_model=dict
)
async def mount_gradio():
    from webui import demo
    gr.mount_gradio_app(app, demo, path="/gradio", allowed_paths=["."])
    return 
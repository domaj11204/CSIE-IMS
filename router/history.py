from pydantic import BaseModel
from fastapi import APIRouter
import aiohttp
router = APIRouter(
    prefix="/v1/history",
    tags=["history"]
)

from modules.history import HistorySource
from modules.knowledge_base import source
history_obj = HistorySource()

@router.post(path="/",
            summary="初始化，即複製瀏覽紀錄檔案並解析",
            description="將瀏覽紀錄讀出來",
            response_description="瀏覽紀錄schema",
            response_model=dict
            )
async def copy_history():
    global history_obj
    # 初始化obj
    if history_obj == None:
        history_obj = HistorySource()
    history_obj.copy_history()
    result = history_obj.parse_sqlite()
    return {"result": result}

@router.get(
    path="/data",
    summary="說明取得資料需要的參數",
    description="用於取得特定資料對應的唯一index參數",
    response_model=dict
)
def data_info():
    return {"result": "id"}

@router.get(
    path="/data/id/{id}",
    summary="用Key取得文獻資料",
)
def get_data(id:str):
    global history_obj
    return {"data":history_obj.get_data(id=id)}

@router.get(
    path="/search",
    summary="搜尋瀏覽紀錄",
    description="搜尋標題與URL，回傳結果",
    response_description="專門為瀏覽紀錄所設計的搜尋，和source的搜尋完全不同",
    response_model=dict
)
async def search(keyword:str, search_type:str=None, top_k:int=None, type_list:str=None):
    global history_obj
    result = history_obj.search(keyword)
    return {"result":result}

@router.post(
    path="/reload",
    summary="重新載入reference模組",
    description="重新載入modules/reference.py。\n\n以python內建的importlib.reload實現。",
    response_description="重新載入結果",
    response_model=dict
)
async def reload_modules():
    global history_obj
    print(hex(id(history_obj)))
    import importlib
    # # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    # importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.history"))
    from modules.history import HistorySource # 必須重新匯入，否則雖然neo4j的address不同但neo4j_source的address是相同的
    history_obj = HistorySource()
    print(hex(id(history_obj)))
    return {"result": str(type(history_obj))}

@router.get(
    path="/load/entity",
    summary="回傳用於載入的實體",
    description="將所有資料整理成實體，提供給知識庫載入",
    response_model=dict
)
async def load_entity():
    global history_obj
    if history_obj == None: history_obj = HistorySource()
    return {"entities": history_obj.load_entities()}

@router.get(
    path="/md5",
    summary="取得原始瀏覽紀錄檔案的md5",
    response_model=dict
)
async def get_origin_md5():
    return {"md5": history_obj.get_origin_md5()}
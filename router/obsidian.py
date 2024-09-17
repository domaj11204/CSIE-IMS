from fastapi import APIRouter, status, Response, Request
from modules.knowledge_base import source
from modules.debug_utils import error
import configparser
import aiohttp
from pydantic import BaseModel
router = APIRouter(
    prefix="/v1/obsidian",
    tags=["obsidian"]
)

class obsidian_note(BaseModel):
    title:str
    tags:set = set()
    content:str | None = None
    abstract:str | None = None
    description:str | None = None

class standard_response(BaseModel):
    result:str | bool

from modules.obsidian import obsidian_source
obsidian_obj = obsidian_source()


@router.get(
    path="/uuids",
    summary="取得所有UUID",
    response_description="UUID陣列",
    response_model=dict
)
async def get_uuids():
    error("準備棄用")
    global obsidian_obj
    uuids = await obsidian_obj.get_uuids()
    return {"uuids": "準備棄用"}

@router.get(
    path="/search",
    summary="搜尋筆記",
    description="搜尋標題與內容，回傳UUID",
    response_description="UUID陣列",
    response_model=dict
)
async def search(keyword:str, search_type:str="keyword", top_k:int=None, type_list:str=None):
    global obsidian_obj
    uuids = await obsidian_obj.search(keyword, search_type, top_k)
    return {"uuids":uuids}

@router.get(
    path="/file_list",
    summary="取得所有筆記的標題",
    description="取得所有筆記的標題!!",
    response_description="包含所有標題與路徑的陣列",
    response_model=list
)
async def get_all_note_path():
    global obsidian_obj
    file_list = await obsidian_obj.get_file_list()
    return {"file_list":file_list}

@router.get(
    path="/data",
    summary="說明該source需要哪些資訊才能讀到原始資料",
    response_description="該source需要的資訊，例如path或URI或UUID等",
    response_model=dict
)
async def get_need_info():
    return {"result":"path"}

@router.get(
    path="/data/path/{path:path}", # 這樣path裡面可以包含斜線
    summary="根據URI取得筆記內容",
    description="根據URI取得筆記內容，該URI為相對URI",
    response_description="筆記內容",
    response_model=dict
)
def get_data_by_path(path:str):
    result = obsidian_obj.get_data_by_path(path)
    return {"result":result}

@router.get(
    path="/data/{uuid}",
    summary="根據UUID取得筆記內容",
    description="根據UUID取得URI後取得筆記內容",
    response_description="筆記內容",
    response_model=dict
)
async def get_data(uuid:str, request:Request):
    params = dict(request.query_params)
    result = await obsidian_obj.get_data(uuid, params=params)
    return {"data":result}

@router.get(
    path="/url/{uuid}",
    summary="收到UUID回傳筆記的URL",
    description="接受除了uuid之外的path資訊",
    response_description="筆記的URL",
    response_model=dict
)
async def get_url(uuid:str=None, request:Request={}):
    params = dict(request.query_params)
    url = await obsidian_obj.get_url(uuid, params=params)
    return {"url":url}

@router.post(
    path="/note",
    status_code=201,
    summary="新增筆記",
    description="新增筆記，預設為呼叫obsidian的local-rest-api",
    response_model=standard_response
)
async def create_note(note:obsidian_note|None, response:Response):
    """新增筆記
    """
    # 讀取url相關設定
    from modules.utils import read_config
    config = read_config()
    obsidian_api_url = config["obsidian"]["url"]

    # 檢查目標檔案是否已存在
    async with aiohttp.request(method="get", url=obsidian_api_url + "/vault/" + note.title, 
        headers={
            "accept": "application/vnd.olrapi.note+json",
            "Authorization": config["obsidian"]["authorization"]
        }) as resp:
        if resp.status == 404:
            # 若檔案不存在則新增筆記
            from modules.obsidian import obsidian_source
            obsidian = obsidian_source()
            if note.content != None:
                result = obsidian.new_note(
                    note_type="note",
                    title=note.title,
                    content={"text":note.content}
                )
            else:
                result = obsidian.new_note(
                    note_type="term",
                    title=note.title,
                    content={
                    "tag": note.tags,
                    "abstract": note.abstract,
                    "description": note.description
                })
            if result:
                return {"result":result}
            else:
                response.status_code = status.HTTP_400_BAD_REQUEST
                return {"result":"錯誤，新增失敗"}
        else:
            response.status_code = status.HTTP_409_CONFLICT
            return {"result":"錯誤，檔案可能已存在"}
    response.status_code = status.HTTP_400_BAD_REQUEST
    return {"result":"錯誤，未知錯誤"}        


@router.post(
    path="/split",
    summary="將筆記內容切成chunk",
    description="將筆記內容切成chunk，用於儲存到知識庫與向量資料庫",
    response_description="entity、document、metadata",
    response_model=dict
)
def split(split_data:source.split_data):
    global obsidian_obj
    return {"split_result":obsidian_obj.split(split_data)}

@router.get(
    path="/path2link",
    summary="將筆記路徑轉為markdown格式的obsidian uri",
    response_model=dict
)
def path2link(path:str):
    global obsidian_obj
    return {"result":obsidian_obj.path2uri(path)}

@router.get(
    path="/chunk/to-uri",
    summary="將chunk的uuid轉為obsidian使用的URI",
    response_model=dict,
    response_description="markdown及uri跳脫處理後的uri"
)
async def chunk2uri(uuid:str):
    global obsidian_obj
    return {"uri": (await obsidian_obj.chunk2uri(uuid))}

@router.post(
    path="/reference_string/",
    summary="該Chunk的reference string",
    description="回傳該chunk顯示在回答中的內容",
    response_model=dict
)
async def reference_string(reference_data:dict):
    global obsidian_obj
    return {"reference_string": (await obsidian_obj.reference_string(reference_data))}

@router.post(
    path="/reload",
    summary="重新載入obsidian模組",
    description="重新載入modules/obsidian.py。\n\n以python內建的importlib.reload實現。",
    response_description="重新載入結果",
    response_model=dict
)
async def reload_modules():
    global obsidian_obj
    print(hex(id(obsidian_obj)))
    import importlib
    # # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    # importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.obsidian"))
    from modules.obsidian import obsidian_source # 必須重新匯入，否則雖然neo4j的address不同但neo4j_source的address是相同的
    obsidian_obj = obsidian_source()
    print(hex(id(obsidian_obj)))
    return {"result": str(type(obsidian_obj))}

@router.post(
    path="/setting",
    summary="修改設定",
    description="修改設定，先檢查是否存在，修改後回傳修改結果",
    response_model=dict
)
def setting(setting:dict):
    global obsidian_obj
    return obsidian_obj.change_setting(setting)
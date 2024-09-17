from fastapi import APIRouter, status, Response, Request
from modules.knowledge_base import source
import aiohttp
from pydantic import BaseModel
router = APIRouter(
    prefix="/v1/rdf",
    tags=["rdf"]
)

from modules.rdf import rdf_source
rdf_obj = rdf_source()

@router.get(
    path="/uuids",
    summary="取得所有UUID",
    response_description="UUID陣列",
    response_model=dict
)
async def get_uuids():
    error("準備棄用")
    uuids = await rdf_obj.get_uuids()
    return {"uuids":uuids}

@router.get(
    path="/file_list",
    summary="根據設定檔將知識本體相關資訊新增到知識圖譜中",
    description="根據設定檔取得匯入到知識圖譜時的必要資訊",
    response_description="清單",
    response_model=dict
)
async def get_file_list():
    return {"file_list": (await rdf_obj.get_file_list())}

@router.get(
    path="/data",
    summary="說明該source需要哪些資訊才能讀到原始資料",
    response_description="該source需要的資訊，例如path或URI或UUID等",
    response_model=dict
)
async def get_need_info():
    return {"result":"path"}

@router.get(
    path="/data/{uuid}",
    summary="根據UUID取得知識本體",
    description="根據UUID取得path後取得知識本體",
    response_description="完整知識本體",
    response_model=dict
)
async def get_data(uuid:str, request:Request):
    params = dict(request.query_params)
    result = await rdf_obj.get_data(uuid, **params)
    return {"data":result}

@router.get(
    path="/data/path/{path:path}",
    summary="根據path取得整個rdf",
    response_description="整個rdf",
    response_model=dict
)
async def get_data_by_path(path:str):
    return {"rdf":(await rdf_obj.get_data(path=path))}

@router.get(
    path="/data/uri/{uri}",
    summary="根據URI取得有關的triple",
    description="根據URI取得所有相關的triple",
    response_description="triple",
    response_model=dict
)
async def get_data_by_uri(uri:str, depth:int=1):
    result = await rdf_obj.get_data(uri=uri, depth=depth)
    return {"triple":result}

@router.get(
    path="/url/{uuid}",
    summary="收到UUID回傳知識本體的URL",
    description="接受除了uuid之外的path資訊",
    response_description="知識本體的URL",
    response_model=dict
)
async def get_url(uuid:str=None, request:Request={}):
    params = dict(request.query_params)
    url = await rdf_obj.get_url(uuid, params=params)
    return {"url":url}

@router.get(
    path="/search",
    summary="搜尋",
    description="根據關鍵字搜尋，直接回傳相關的文字結果",
    response_description="RDF/XML中的相關文字結果",
    response_model=dict
)
async def search(keyword:str, search_type:str=None, top_k:int=None, type_list:str=None):
    type_list = type_list.split(",") if type_list is not None else None
    return {"result":(await rdf_obj.search(keyword, search_type, top_k=top_k, type_list=type_list))}

@router.post(
    path="/split",
    summary="將知識本體切成符合的chunk",
    response_description="切完的完整chunk資訊",
    response_model=dict
)
async def split(split_data:source.split_data):
    return {"split_result":(rdf_obj.split(split_data))}
@router.post(
    path="/reference_string/",
    summary="該Chunk的reference string",
    description="回傳該chunk顯示在回答中的內容",
    response_model=dict
)
async def reference_string(reference_data:dict):
    return {"reference_string": (await rdf_obj.reference_string(reference_data))}

@router.post(
    path="/reload",
    summary="重新載入rdf模組",
    description="重新載入modules/rdf.py。\n\n以python內建的importlib.reload實現。",
    response_description="重新載入結果",
    response_model=dict
)
async def reload_modules():
    global rdf_obj
    print(hex(id(rdf_obj)))
    import importlib
    # # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    # importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.rdf"))
    from modules.rdf import rdf_source # 必須重新匯入，否則雖然neo4j的address不同但neo4j_source的address是相同的
    rdf_obj = rdf_source()
    print(hex(id(rdf_obj)))
    return {"result": str(type(rdf_obj))}

@router.post(
    path="/setting",
    summary="修改設定",
    description="修改設定，先檢查是否存在，修改後回傳修改結果",
    response_model=dict
)
def setting(setting:dict):
    return rdf_obj.change_setting(setting)
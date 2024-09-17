from fastapi import APIRouter, Response, status, Body
from fastapi.responses import RedirectResponse
import configparser
import aiohttp
from pydantic import BaseModel
from excerpt import excerpt_data
from typing import Annotated
router = APIRouter(
    prefix="/v1/knowledge_base",
    tags=["knowledge_base"]
)
from modules.knowledge_base import knowledge_base, source
knowledge_base_obj = knowledge_base()

class source_or_type(BaseModel):
    source:str = None
    type:str = None
    uuids:list = None
class add_term_elem(BaseModel):
    term:str
    description:str | None
    path:str | None
    abstract:str | None
    
class relation_model(BaseModel):
    uuid1:str
    uuid2:str
    relation:str
    property:dict = {}

@router.get(
    path="/",
    summary="確認KB資料庫的狀態",
    response_description="KB資料庫是否可用",
    response_model=dict,
    responses={
        200: {
            "description": "可用",
            "content":{
                "application/json":{
                    "example":{
                        "status":"可用"
                    }
                }
            }
        }
    }
)
async def get_kbdb_status():
    global knowledge_base_obj
    status = await knowledge_base_obj.db_status()
    print("get_kbdb_status:", status)
    return status




@router.post(
    path="/reload",
    summary="重新載入知識庫模組",
    description="重新載入知識庫模組檔案。\n\n以python內建的importlib.reload實現。",
    response_description="新模組的記憶體位置",
    response_model=dict
)
def reload_modules():
    global knowledge_base_obj
    print(hex(id(knowledge_base_obj)))
    import importlib
    # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.knowledge_base"))
    from modules.knowledge_base import knowledge_base
    knowledge_base_obj = knowledge_base()
    print(hex(id(knowledge_base_obj)))
    return {"result": str(type(knowledge_base_obj))}

@router.get(
    path="/uuids",
    summary="根據類型或來源取得UUID清單",
    description="根據類型或來源取得知識庫中的UUID清單",
    response_model=dict
)
async def get_uuids(type:str=None, source:str=None, keyword:str=None, search_type:str=None, source_str:str=None, type_str:str=None, top_k:int=None):
    global knowledge_base_obj
    source_list = source_str.split(",") if source_str is not None else None
    type_list = type_str.split(",") if type_str is not None else None
    uuids = await knowledge_base_obj.get_uuids(
        type=type, 
        source=source, 
        keyword=keyword,
        search_type=search_type,
        source_list=source_list,
        type_list=type_list,
        top_k=top_k)
    return {"uuids":uuids}

@router.get(
    path="/search",
    summary="搜尋",
    description="根據搜尋條件做搜尋，回傳UUID清單及簡單的結果",
    response_model=dict
)
async def search(keyword:str, search_type:str="keyword", top_k:int=1, source_str:str="obsidian", type_str:str=""):
    global knowledge_base_obj
    result = await knowledge_base_obj.search(
        keyword=keyword,
        search_type=search_type,
        source_list=source_str.split(","),
        type_list=type_str.split(","),
        top_k=top_k)
    return {"result":result}

@router.get(
    path="/entity",
    summary="回傳最新的實體",
    description="回傳最新的實體，可輸入數量，用於測試",
    response_model=dict
)
async def get_latest_entity(top_k:int=1):
    global knowledge_base_obj
    latest_entity_list = await knowledge_base_obj.get_latest_entity(top_k=top_k)
    return {"latest_entity":latest_entity_list}

@router.post(
    path="/entity",
    summary="新增實體",
    description="新增實體，預設由知識庫管理UUID",
    response_description="新增的實體資訊",
    response_model=dict,
    responses={
        400: {
            "description": "新增失敗",
        },
        409: {
            "description": "有相同UUID或相同內容的實體存在",
        },
        200: {
            "description": "新增成功",
            "content":{
                "application/json":{
                    "example":{
                        "result": "新增成功",
                        "uuid": "實體UUID"
                    }
                }
            }
        }
    }
)
async def add_entity(entity:Annotated[dict, 
                                      Body(examples={
                "name": "實體名稱",
                "type": "實體類型",
                "description": "實體描述",
            })
                                      ], response:Response):
    global knowledge_base_obj
    result = await knowledge_base_obj.add_entity(entity)
    print("knowledge_base.py:result:", result) 
    if result == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"result": "新增失敗"}
    elif result["result"] == "已存在":
        response.status_code = status.HTTP_409_CONFLICT
        return {"result": "已存在"}
    else:
        return result

@router.get(
    path="/entity_count",
    summary="取得知識庫中的該type或source實體數量",
    response_description="實體數量",
    response_model=dict
)
async def get_entity_count_by_type(type:str=None, source:str=None):
    global knowledge_base_obj
    result = await knowledge_base_obj.get_entity_count(type=type, source=source)
    return result

@router.get(
    path="/entity/{uuid}",
    summary="根據UUID取得完整的知識庫實體",
    description="取得原始資料data後和其他metadata合併成實體",
    response_description="完整實體",
    response_model=dict
)
async def get_entity_by_uuid(uuid:str):
    global knowledge_base_obj
    entity = await knowledge_base_obj.get_entity(uuid=uuid)
    return {"entity":entity}

@router.get(
    path="/data/{uuid}",
    summary="根據UUID取得原始資料",
    description="根據UUID取得和該來源取得原始資料",
    response_description="原始資料",
    response_model=dict
)
async def get_data_by_uuid(uuid:str):
    global knowledge_base_obj
    result = await knowledge_base_obj.get_data(uuid=uuid)
    return result

@router.get(
    path="/relations/{uuid}",
    summary="根據UUID取得相鄰節點資訊",
    response_description="相鄰節點資訊",
    response_model=dict
)
async def get_realation(uuid:str):
    global knowledge_base_obj
    relations = await knowledge_base_obj.get_relation(uuid=uuid)
    return {"relations":relations}

@router.post(
    path="/relation",
    summary="新增關係",
    description="新增關係到知識庫",
    response_description="新增關係的結果",
    response_model=dict,
    responses={
        200: {
            "description": "新增成功",
            "content":{
                "application/json":{
                    "example":{
                        "result": "新增成功"
                    }
                }
            }
        }
    }
)
async def add_relation(relation_model:relation_model):
    global knowledge_base_obj
    result = await knowledge_base_obj.add_relation(**(relation_model.dict()))
    return {"result":result}



@router.post(
    path="/load_data",
    summary="載入該來源或類型的所有資料",
    description="載入該來源或類型的所有資料，根據hash檢查是否已存在。\n\n以json list回傳uuid及name",
    response_description="載入的資料，包含uuid及name",
    response_model=dict
)
async def load_data(source_or_type:source_or_type):
    global knowledge_base_obj
    result = await knowledge_base_obj.load_data(source=source_or_type.source, type_str=source_or_type.type)
    return {"result":result}
    
@router.post(
    path="/indexing",
    summary="將該類型或來源已載入的資料切檔、嵌入並建立索引",
    response_description="嵌入的資料數量",
    response_model=dict
)
async def indexing(source:str=None, type:str=None):
    global knowledge_base_obj
    result = await knowledge_base_obj.indexing(source=source, type=type)
    return result

@router.delete(
    path="/indexing",
    summary="將該來源或類型的index刪除",
    response_description="刪除的index數量",
    response_model=dict
)
async def delete_indexing(source_or_type:source_or_type):
    global knowledge_base_obj
    result = await knowledge_base_obj.delete_indexing(source=source_or_type.source, type=source_or_type.type)
    return result


@router.post(
    path="/term",
    status_code=201,
    summary="新增術語",
    description="新增術語到知識庫，預設為呼叫obsidian的新增筆記api",)
def term(term:add_term_elem, response:Response):
    # TODO: 路徑相關處理未實作
    global knowledge_base_obj
    result = knowledge_base_obj.add_term(term.term, term.path, term.abstract, term.description)
    if result == False:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return {"result": "新增失敗"}
    
@router.get(
    path="/url/{uuid}",
    summary="根據UUID取得該資料的URL",
    response_description="重導向到該URL",
)
async def redirect_url_by_uuid(uuid:str):
    global knowledge_base_obj
    url = await knowledge_base_obj.get_url(uuid=uuid)
    from modules.debug_utils import print_var
    print_var(url) # url = file://D:\research\extensions\chrome-extension/data/symptoms.owl
    if "file://" not in url:
        return RedirectResponse(url=url)
    else:
        from starlette.responses import FileResponse
        return FileResponse(path=url.replace("file://", ""))


@router.get(
    path="/tag",
    tags=["tag"],
    summary="取得所有標籤",
    response_model=dict
)
async def get_tag_list():
    global knowledge_base_obj
    tags = await knowledge_base_obj.get_tag_list()
    return {"tags":tags}

@router.post(
    path="/excerpt",
    summary="新增摘錄",
    description="新增摘錄到知識庫",
    response_description="新摘錄的實體資訊",
    response_model=dict
)
async def add_excerpt(data:excerpt_data):
    global knowledge_base_obj
    result = await knowledge_base_obj.add_excerpt(data)
    return {"result":result}

@router.get(
    path="/{uuid}",
    summary="根據UUID取得資訊",
    description="根據UUID取得知識庫中的資訊",
    response_description="知識庫中的資訊",
    response_model=dict
)
async def get_info_by_uuid(uuid:str):
    global knowledge_base_obj
    if knowledge_base_obj is None:
        knowledge_base_obj = knowledge_base()
    result = await knowledge_base_obj.get_info(uuid=uuid)
    return {"info":result}

@router.delete(
    path="/{uuid}",
    summary="根據UUID刪除知識庫中的資料",
    response_description="刪除的資料",
    response_model=dict
)
async def delete_uuid(uuid:str):
    global knowledge_base_obj
    result = await knowledge_base_obj.delete_uuid(uuid=uuid)
    return result
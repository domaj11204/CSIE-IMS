from pydantic import BaseModel
from fastapi import APIRouter, Body
from typing import Annotated
import aiohttp
from modules.knowledge_base import source
from modules.debug_utils import print_var
router = APIRouter(
    prefix="/v1/neo4j",
    tags=["neo4j", "source"]

)

class neo4j_server_setting(BaseModel):
    url: str | None = None
    user: str | None = None
    password: str | None = None

class Entity(BaseModel):
    name: str
    type: str|None = None
    uuid: str
    description: str|None = None
    relation: list = []
    data_hash: str | None = None
    check_key: list | None = None
    model_config={
        "json_schema_extra": {
            "example": {
                "name": "test",
                "url": "test_url",
                "type": "測試用網頁",
                "uuid": "959f0349-fd3c-480a-a29d-7fc9f06f1288",
                "description": "test",
                "founder": "預設"
            }
        },
        # 加上extra能讓模型接受額外的參數，除了allow以外還有ignore, forbid 
        # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
        "extra": "allow"
    }

class relation_model(BaseModel):
    uuid1: str
    uuid2: str
    relation: str
    property: dict={}


# ===== 以module模擬外部應用 ======
from modules.neo4j import neo4j_source
neo4j_obj = neo4j_source()
# ===============================
@router.get(path="/",
            summary="取得neo4j的狀態",
            response_description="neo4j最新的一筆資料\n\nstatus包含正常、未初始化及未知的知識庫資料庫",
            response_model=dict,
            responses={
                200:{
                    "description": "成功",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "正常",
                                "last_node": "[<Record n=<Node element_id='4:516c4a38-5fd9-4e12-be22-93950217512e:24208' labels=frozenset({'測試用網頁'}) properties={'tabId': 2055685637, '建立時間': neo4j.time.DateTime(2024, 12, 3, 8, 10, 41, 920902700), 'founder': '預設', 'tabURL': 'https://blog.camel2243.com/posts/html-understand-why-sometimes-pressing-enter-will-automatically-submit-form-and-sometimes-not/', 'UUID': '7cf48ebd-9ee0-40d7-affe-ece8f29fc780', '描述': \"[html] 從 html spec 了解有時候按下 enter 會自動 submit form，有時卻不會？ | Camel 's blog\", '名稱': \"[html] 從 html spec 了解有時候按下 enter 會自動 submit form，有時卻不會？ | Camel 's blog\"}>>]"
            }}}}})
async def get_neo4j_status():
    global neo4j_obj
    if neo4j_obj == None:
        return {"status": "未初始化"}
    else:
        return {"status": "正常",
                "last_node": str(neo4j_obj.DB.get_latest_node(num_node=1))}

@router.post(path="/",
            summary="初始化neo4j",
            description="根據config中的預設設定連線到neo4j，並取得最新的一筆資料",
            response_description="neo4j最新的一筆資料",
            response_model=dict,
            responses={
                200: {
                    "description": "成功",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "正常",
                                "last_node": "[<Record n=<Node element_id='4:516c4a38-5fd9-4e12-be22-93950217512e:24208' labels=frozenset({'測試用網頁'}) properties={'tabId': 2055685637, '建立時間': neo4j.time.DateTime(2024, 12, 3, 8, 10, 41, 920902700), 'founder': '預設', 'tabURL': 'https://blog.camel2243.com/posts/html-understand-why-sometimes-pressing-enter-will-automatically-submit-form-and-sometimes-not/', 'UUID': '7cf48ebd-9ee0-40d7-affe-ece8f29fc780', '描述': \"[html] 從 html spec 了解有時候按下 enter 會自動 submit form，有時卻不會？ | Camel 's blog\", '名稱': \"[html] 從 html spec 了解有時候按下 enter 會自動 submit form，有時卻不會？ | Camel 's blog\"}>>]"
            }}}}})
async def set_neo4j():
    # TODO: 此API應該提供除了使用config的設定之外，還能使用post body提供參數進行設定
    global neo4j_obj
    neo4j_obj = neo4j_source()
    return {"last_node": str(neo4j_obj.DB.get_latest_node(num_node=1))}


@router.get(path="/search",
            summary="搜尋",
            description="根據預設的搜尋欄位搜尋",
            response_description="搜尋結果",
            response_model=dict,
            responses={
                200: {
                    "description": "成功",
                    "content": {
                        "application/json": {
                            "example": {
                                "result": [
                                    "8f53981f-666f-4560-b930-0f3692410f12"
                                ]
            }}}}})
async def search(keyword:str, search_type:str="keyword", top_k:int=1, type_list:str=None):
    global neo4j_obj
    if neo4j_obj == None:
        return {"result": "未初始化"}
    if type_list != None:
        type_list = type_list.split(",| ")
    result = await neo4j_obj.search(keyword=keyword, search_type=search_type, top_k=top_k, type_list=type_list)
    return {"result": result}

@router.post(
    path="/reload",
    summary="重新載入neo4j模組",
    description="重新載入modules/neo4j.py。\n\n以python內建的importlib.reload實現。",
    response_description="重新載入結果",
    response_model=dict
)
async def reload_modules():
    global neo4j_obj
    print(hex(id(neo4j_obj)))
    import importlib
    # # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    # importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.neo4j"))
    from modules.neo4j import neo4j_source # 必須重新匯入，否則雖然neo4j的address不同但neo4j_source的address是相同的
    neo4j_obj = neo4j_source()
    print(hex(id(neo4j_obj)))
    return {"result": str(type(neo4j_obj))}



@router.get(
    path="/entity_count",
    summary="取得資料庫中某個type或source的實體數量",
    response_description="數量",
    response_model=dict
)
async def get_entity_count_by_type(type:str=None, source:str=None):
    global neo4j_obj
    result = await neo4j_obj.get_entity_count(type=type, source=source)
    return {"entity_count": result}

@router.post(
    path="/split",
    summary="將entity切成chunk",
    description="將entity切成chunk，用於儲存到知識庫與向量資料庫",
    response_description="entity、document、metadata",
    response_model=dict
)
async def split(split_data:source.split_data):
    global neo4j_obj
    result = neo4j_obj.split(split_data)
    return {"split_result": result}

@router.get(
    path="/entity",
    summary="取得最新的知識庫實體",
    response_description="最新前k的知識庫實體(任何節點)",
    response_model=dict
)
async def get_latest_entity(top_k:int=1):
    global neo4j_obj
    latest_entity_list = await neo4j_obj.get_latest_entity(top_k)
    return {"latest_entity": latest_entity_list}

@router.post(
    path="/entity",
    summary="新增entity",
    description="新增entity到neo4j",
    response_description="新增entity結果，包含新增成功與新增失敗，若成功也會回傳uuid",
    response_model=dict
)
async def add_entity(entity:Annotated[
    Entity,
    Body(
        openapi_examples={
            "包含關係的網頁摘錄":{
                "summary": "包含關係的網頁摘錄",
                "description": "新增網頁摘錄到知識庫",
                "value":{
                    "name": "測試用名稱",
                    "type": "測試用摘錄",
                    "uuid": "c2086a17-451f-4d1e-8c1a-f61f43c2f715",
                    "description": "測試用描述",
                    "relation":[
                        {
                            "uuid1": "c2086a17-451f-4d1e-8c1a-f61f43c2f715",
                            "uuid2": "9d509060-ab32-4a8f-8f0a-f8e21276eb1f",
                            "relation": "摘錄自",
                            "property": {
                                "關係屬性": "測試屬性"
                            }
                        }
                    ],
                    "check_key": ["name", "uuid"]
                }
            }
        }
    )
]):
    """新增知識實體到neo4j"""
    global neo4j_obj
    print("router.neo4j:post entity", entity)
    result = await neo4j_obj.add_entity(entity.dict())
    return result

@router.get(
    path="/uuids",
    summary="根據type或source取得UUID清單",
    response_description="知識庫中的UUID清單",
    response_model=dict
)
async def get_uuids_by_type(type:str=None, source:str=None):
    global neo4j_obj
    uuids = await neo4j_obj.get_uuids(type=type, source=source)
    return {"uuids": uuids}

@router.get(
    path="/relations/{uuid}",
    summary="顯示與UUID有關的關係",
    response_description="與UUID有關的關係，以result:[]表示",
    response_model=dict
)
async def get_relations(uuid:str):
    global neo4j_obj
    relations = await neo4j_obj.get_relations(uuid)
    return {"relations": relations}

@router.post(
    path="/relation",
    summary="新增關係",
    response_description="新增關係結果",
    response_model=dict,
)
async def create_relation(relation:relation_model):
    global neo4j_obj
    relation_dict = {
        "uuid1": relation.uuid1,
        "uuid2": relation.uuid2,
        "relation": relation.relation,
    }
    relation_dict.update(relation.property)
    result = await neo4j_obj.create_relation(**relation_dict)
    if result:
        return {"result": "新增成功"}
    else:
        return {"result": "新增失敗"}

@router.get(
    path="/chunk/to-uri",
    summary="根據UUID取得此chunk對應的uri",
    response_description="此chunk對應的uri",
    response_model=dict
)
async def get_uri_by_uuid(uuid:str):
    global neo4j_obj
    result = await neo4j_obj.chunk2uri(uuid)
    return {"uri": result}

@router.post(
    path="/reference_string",
    summary="渲染出該chunk的引用訊息",
    response_model=dict,
    responses={
        200: {
            "description": "成功",
            "content": {
                "application/json": {
                    "example": {
  "reference_string": "參考摘錄: <a href=\"https://navidre.medium.com/which-vector-database-should-i-use-a-comparison-cheatsheet-cb330e55fca\" target=\"_blank\">Which Vector Database Should I Use? A Comparison Cheatsheet | by Navid Rezaei | Medium</a>"
}
                }
            }
        }
    }
)
async def reference_string(reference_data:dict=Body(..., example={"parent_uuid":"8fa78383-0dab-4c56-9dc2-0c7a30a0d935"})):
    global neo4j_obj
    result = await neo4j_obj.reference_string(reference_data)
    return {"reference_string": result}

@router.delete(
    path="/chunk/{uuid}",
    summary="刪除知識庫中的chunk",
    response_model=dict
)
async def delete_chunk(uuid:str):
    global neo4j_obj
    result = await neo4j_obj.delete_chunk(uuid)
    return {"result": result}

@router.get(
    path="/tag",
    tags=["tag"],
    summary="取得所有的tag",
    response_model=dict
)
async def get_tag():
    global neo4j_obj
    tags = await neo4j_obj.get_tag()
    return {"tags":tags}

@router.get(
    path="/{uuid}",
    summary="根據UUID取得資訊",
    response_description="知識庫中的資訊",
    response_model=dict
)
async def get_data_by_uuid(uuid:str):
    global neo4j_obj
    try:
        result = await neo4j_obj.get_data(uuid=uuid)
    except:
        result = "查詢錯誤，可能無此uuid"
    return {"data": result}

@router.delete(
    path="/{uuid}",
    summary="刪除知識庫中的資料",
    response_description="刪除的節點資訊",
    response_model=dict
)
async def delete_uuid(uuid:str):
    global neo4j_obj
    result = await neo4j_obj.delete_node(uuid)
    return {"result":result}
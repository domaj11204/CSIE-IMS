from pydantic import BaseModel
from fastapi import APIRouter
import aiohttp
router = APIRouter(
    prefix="/v1/reference",
    tags=["refernece"]

)

class file_path(BaseModel):
    path: str | None = None

class search_param(BaseModel):
    keyword: str
    field_list: list[str] = ["Title"]
    



from modules.reference import ReferenceSource
from modules.knowledge_base import source
reference_obj = None


@router.post(path="/",
            summary="讀取文獻檔案",
            description="根據給予的路徑或config中的預設路徑讀取文獻清單",
            response_description="文獻清單長度",
            response_model=int
            )
async def read_reference_file(reference_file_path:file_path):
    global reference_obj
    # 設定清單路徑 file_path
    if reference_file_path.path != None:
        file_path = reference_file_path.path
    else:
        from modules.utils import read_config
        file_path = read_config()["reference"]["path"]
    
    # 初始化obj
    if reference_obj == None:
        reference_obj = ReferenceSource(file_path=file_path)
    
    # 讀檔
    reference_obj.parse_file(file_path)
    return len(reference_obj.library)

@router.get(
    path="/data",
    summary="說明取得資料需要的參數",
    description="此reference取得資料需要的參數是Key",
    response_model=dict
)
def data_info():
    return {"result": "Key"}

@router.get(
    path="/data/Key/{key}",
    summary="用Key取得文獻資料",
)
def get_data(key:str):
    global reference_obj
    # TODO: 資料應該為pdf檔或URL，以後再處理
    return {"data":reference_obj.get_data(key=key)}

@router.post(path="/search",
            summary="搜尋文件",
            description="根據給予的參數搜尋文獻清單",
            response_description="搜尋結果",
            response_model=dict,
            responses={
                404: {"description": "未讀取文獻檔案"},
                200: {
                    "description": "搜尋結果，包含標題與代號",
                    "content": {
                        "application/json": {
                            "example": {"result": [{"Title": "論文標題", "Key": "論文代號"}]}
                        }   
                    }
                }
            })
# response寫法參考https://fastapi.tiangolo.com/advanced/additional-responses/
async def search(search_parameter:search_param):
    global reference_obj
    # 檢查obj初始化
    if reference_obj == None:
        return {"error": "未讀取文獻檔案"}
    
    # 搜尋
    result = reference_obj.search(search_parameter.keyword, search_parameter.field_list)
    simplify_result = []
    for record in result:
        simplify_result += [{
            "Title": record["Title"],
            "Key": record["Key"]
        }]
    return {"result": simplify_result}

@router.get(path="/zotero/uri/{item_id}",
            summary="取得論文的URI",
            description="根據Zotero定義的論文ID取得文件的URI",
            response_description="Zotero的URI",
            response_model=str,
            responses={
                200: {
                    "description": "文件的URI",
                    "content": {
                        "application/json": {
                            "URI": "https://www.google.com"
                        }
                    }
                }
            })
async def get_zotero_uri(item_id:str):
    # zotero://select/library/items/YE9N9JZE
    # zotero://open-pdf/library/items/IY2AMDGI
    return {"URI": "zotero://select/library/items/{item_id}"}

@router.post(
    path="/split",
    summary="將資料內容切成chunk",
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
    summary="重新載入reference模組",
    description="重新載入modules/reference.py。\n\n以python內建的importlib.reload實現。",
    response_description="重新載入結果",
    response_model=dict
)
async def reload_modules():
    global reference_obj
    print(hex(id(reference_obj)))
    import importlib
    # # modules會被編譯到cache中，因此加上這行才能確保完全重新載入https://docs.python.org/3/library/importlib.html#importlib.invalidate_caches
    # importlib.invalidate_caches() 
    importlib.reload(importlib.import_module("modules.reference"))
    from modules.reference import ReferenceSource # 必須重新匯入，否則雖然neo4j的address不同但neo4j_source的address是相同的
    reference_obj = ReferenceSource()
    print(hex(id(reference_obj)))
    return {"result": str(type(reference_obj))}

@router.post(
    path="/setting",
    summary="修改設定",
    description="修改設定，先檢查是否存在，修改後回傳修改結果",
    response_model=dict
)
def setting(setting:dict):
    global obsidian_obj
    return obsidian_obj.change_setting(setting)

@router.get(
    path="/load/entity",
    summary="回傳用於載入的實體",
    description="將所有資料整理成實體，提供給知識庫載入",
    response_model=dict
)
async def load_entity():
    global reference_obj
    if reference_obj == None: reference_obj = ReferenceSource()
    return {"entities": reference_obj.load_entities()}

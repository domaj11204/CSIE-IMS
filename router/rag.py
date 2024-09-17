from pydantic import BaseModel, Extra
from fastapi import APIRouter
import aiohttp
router = APIRouter(
    prefix="/v1/rag",
    tags=["rag"]

)
from modules.rag import rag
rag_obj = rag()
class llm_filter_input(BaseModel):
    query: str
    context: str
    
class retrieval_result(BaseModel):
    document_list: list
    
class text_input(BaseModel):
    text:str

class query_input(BaseModel):
    query:str
    source_list: list = []
    type_list: list = []
    
    model_config={
        "json_schema_extra": {
            "example": {
                "query": "FastAPI使用哪個port?",
                "source_list": ["筆記", "摘錄"]
            }
        },
        # 加上extra能讓模型接受額外的參數，除了allow以外還有ignore, forbid 
        # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict.extra
        "extra": "allow"
    }
class source_or_type(BaseModel):
    source:str|None = None
    type:str|None = None
    uuids:list|None = None
class chunk_data(BaseModel):
    source:str|None = None
    type:str|None = None
    uuids:list|None = None
    
class chunk(BaseModel):
    embedding_data: str
    metadata: dict
    
@router.post(
    path="/reload",
    summary="重新載入RAG模組",
    description="重新載入RAG模組檔案。\n\n以python內建的importlib.reload實現。",
    response_description="新模組的記憶體位置",
    response_model=dict
)
def reload_modules():
    global rag_obj
    print(hex(id(rag_obj)))
    import importlib
    importlib.reload(importlib.import_module("modules.rag"))
    from modules.rag import rag
    rag_obj = rag()
    print(hex(id(rag_obj)))
    return {"result": str(type(rag_obj))}

@router.post(
    path="/query",
    summary="使用config設定進行RAG",
    description="可勾選來源進行檢索",
    response_description="RAG結果"
)
async def query(query_input:query_input)->dict:
    global rag_obj
    if rag_obj == None:
        rag_obj = rag()
    result_data = await rag_obj.query(**query_input.dict())
    return result_data

@router.post(
    path="/reference_synthesis",
    summary="將參考資料附加在回答後",
    description="將參考資料附加在回答後",
    response_description="合成後的html回答",
    response_model=dict
)
async def reference_synthesis(data:dict):
    global rag_obj
    if rag_obj == None:
        rag_obj = rag()
    result = await rag_obj.reference_synthesis(data)
    return {"result": result}
    
@router.post(
    path="/indexing",
    summary="將資料索引",
    description="將資料索引，包含切成chunk並嵌入，將metadata存入向量資料庫",
    response_description="新增的索引",
    response_model=dict
)
async def indexing(source_or_type:source_or_type):
    global rag_obj
    if rag_obj == None:
        rag_obj = rag()
    if source_or_type.source is None and source_or_type.uuids is None:
        return {"result": "必須設定source或先取得uuids"}
    result = await rag_obj.indexing(source=source_or_type.source, uuids=source_or_type.uuids)
    return {"result": result}

@router.delete(
    path="/indexing",
    summary="刪除索引",
    response_model=dict
)
async def indexing(chunk_data:chunk_data):
    global rag_obj
    if rag_obj == None:
        rag_obj = rag()
    result = await rag_obj.delete_index(source=chunk_data.source, type=chunk_data.type, uuid_list=chunk_data.uuids)
    return {"result": result}


@router.get(
    path="/vectordb/{uuid}",
    summary="查詢向量資料庫中該uuid的相關資訊",
    response_model=dict
)
async def get_data_from_vecterdb(uuid:str):
    global rag_obj
    data = await rag_obj.get_data_in_vector_by_uuid(uuid)
    return {"data": data}

@router.post(
    path="/langchain/llm_filter/",
    summary="LLM Filter",
    description="使用LLM評估上下文是否與問題有關。\n\n以langchain和自訂prompt實現。",
    response_description="是/否",
    response_model=dict
)
async def llm_filter(query:str, context:str):
    # TODO
    result = "否"
    # 設定prompt
    pass
    # 使用非同步請求呼叫LLM API
    pass
    # async with aiohttp.request(method="get", url="http://
    
    # 回傳結果
    return {"result": result}

@router.get(
    path="/langchain/generate_cypher",
    summary="根據query生成cypher",
    description="根據query生成cypher，預設使用ChatGPT-4o。\n\n使用LangChain中的Neo4j代理",
    response_description="cypher",
)
async def generate_cypher(query:str):
    # TODO
    # 可參考: https://towardsdatascience.com/integrating-neo4j-into-the-langchain-ecosystem-df0e988344d2
    pass

@router.post(
    path="/langchain/split_text",
    summary="將文本分割成句子",
    description="將文本分割成句子，不考慮markdown等特殊格式的特殊處理",
)
async def langchain_split_text(input:text_input):
    global rag_obj
    result = rag_obj.split_text(input.text)
    return {"result": result}
    
@router.get(
    path="/llamaindex/retrieval",
    summary="使用llamaindex進行檢索",
    description="使用llamaindex進行檢索，考量多種檢索方法",
    response_description="檢索結果",
    response_model=dict
)
async def llamaindex_retrieval(query:str):
    # TODO
    # 可參考: https://www.llamaindex.ai/blog/llamaindex-enhancing-retrieval-performance-with-alpha-tuning-in-hybrid-search-in-rag-135d0c9b8a00
    pass

@router.post(
    path="/langchain/self_query",
    summary="self_query",
    description="使用LangChain執行self-query",
    response_description="檢索結果",
    response_model=dict
)
async def langchain_self_query(query:str):
    # TODO
    return {"result": "self-query檢索結果"}

@router.get(
    path="/datasource",
    summary="查看資料來源",
    description="查看所有資料來源資訊",
    response_description="資料來源資訊",
    response_model=dict
)
async def get_datasource():
    # 檢查rag初始化
    if rag_obj == None:
        rag_obj = rag()
    # 取得資料來源
    return rag_obj.get_sources()

@router.post(
    path="/datasource",
    summary="設定資料來源",
    description="設定資料來源",
    response_description="資料來源資訊",
    response_model=dict
)
async def set_datasource(source_list:list):
    # 檢查rag初始化
    if rag_obj == None:
        rag_obj = rag()
    # 設定資料來源
    rag_obj.set_sources(source_list)
    return rag_obj.get_sources()
@router.get(
    path="/embedding_model",
    summary="回傳使用的嵌入模型名稱",
    response_description="嵌入模型名稱",
    response_model=dict
)
async def get_embedding_model_name():
    if rag_obj == None:
        rag_obj = rag()
    model_name = rag_obj.config["embedded_model"]
    return {"embedding_model_name": model_name}

@router.post(
    path="/embedding_model",
    summary="初始化嵌入模組",
)
def init_embedding_model():
    global rag_obj
    rag_obj.init_embedded()
    
@router.post(
    path="/index/insert",
    summary="新增資料到索引中",
    description="新增資料到索引中",
    response_description="儲存在向量資料庫中的metadata",
    response_model=dict
)
async def insert_data(chunk:chunk):
    global rag_obj
    if rag_obj == None:
        rag_obj = rag()
    #result = rag_obj.insert_chunk(chunk)
    
    return result
@router.get(
    path="/setting",
    summary="取得RAG的設定",
    description="使用key參數指定某個設定，若無指定則回傳所有設定",
    response_model=dict)
def get_setting(key:str=None):
    global rag_obj
    if rag_obj == None: rag_obj = rag()
    result = str(rag_obj.get_setting(key))
    return {"result":result}

@router.post(
    path="/setting",
    summary="修改RAG的某個設定",
    response_description="修改後的所有設定",
    response_model=dict
)
def change_setting(setting:dict):
    global rag_obj
    if rag_obj == None: rag_obj = rag()
    print("rag:setting:", setting)
    result = rag_obj.change_setting(setting)
    return result
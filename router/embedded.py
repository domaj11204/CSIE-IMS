from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from fastapi import APIRouter, Query
import aiohttp
import requests
from modules.embedded import embedded
router = APIRouter(
    prefix="/v1/embedded",
    tags=["embedded"]
)

embedded_obj = None

class embedded_setting(BaseModel):
    model_name:str = "BAAI/bge-m3"
    model_type: Optional[Literal["SentenceTransformer", "openai", "Transformers"]] = None
    # 解決model_為pydantic保留字的問題
    class Config:
        protected_namespaces = ()

class embedded_status(BaseModel):
    max_length:int
    dim:int
    
class embedded_result(BaseModel):
    base64:str
    shape: list
    dtype: str
    sha256: str
    token_length: list

class sentence_to_embedded(BaseModel):
    sentences:List[str] = Field (Query(..., title="要嵌入的句子"))
    prefix:str = ""
    
@router.get(
    path="/",
    summary="取得嵌入模組的狀態",
    response_description="嵌入模組的狀態",
    response_model=dict,
    responses={
        404: {"description": "設定失敗"},
        200: {
            "description": "設定後的模型資訊",
            "content": {
                "application/json": {
                    "example": {"model_name": "text-embedding-ada-002",
                                "max_length": 512, 
                                "dim": 768}
                }   
            }
        }
    }
)
def get_embedded_status():
    global embedded_obj
    return {"model_name": embedded_obj.model_name,
            "max_length": embedded_obj.max_length, 
            "dim":embedded_obj.dim}
    
    
@router.post(
    path="/",
    summary="設定嵌入",
    response_description="嵌入模組的狀態",
    response_model=dict,
    responses={
        404: {"description": "設定失敗"},
        200: {
            "description": "設定後的模型資訊",
            "content": {
                "application/json": {
                    "example": {"model_name": "text-embedding-ada-002",
                                "max_length": 512, 
                                "dim": 768}
                }   
            }
        }
    }
)
def setting(embedded_setting:embedded_setting)->dict:
    global embedded_obj
    if embedded_obj == None:
        embedded_obj = embedded()
    result = embedded_obj.set_embedded_model(embedded_setting.model_name)
    return {"model_name": embedded_setting.model_name,
            "max_length": embedded_obj.max_length, 
            "dim":embedded_obj.dim}
    

@router.post(
    path="/encode",
    summary="嵌入",
    description="將多個句子嵌入，以base64編碼回傳嵌入結果。",
    response_description="嵌入結果",
    response_model=embedded_result
)
def encode(sentence_to_embedded:sentence_to_embedded)->embedded_result:
    global embedded_obj
    response = requests.post(
            embedded_obj.config["url"],
            json={"sentences":sentence_to_embedded.sentences, "prefix":sentence_to_embedded.prefix}
        )    
        
    response_json = response.json()
    # print("response_json:")
    # print(response_json)
    return response_json
    
# @router.get(
#     path="/vectordb",
#     summary="取得向量資料庫資訊",
#     response_description="向量資料庫資訊",
#     response_model=dict
# )
# def get_vectordb_info():
#     print(hex(id(embedded_obj)))
#     embedded_obj.init_vectorstore()
#     embedded_obj.embedded_once()
#     return {"result": embedded_obj.get_vectordb_info()}

@router.post(
    path="/reload",
    summary="重新載入嵌入模組",
    description="重新載入嵌入模組檔案。\n\n以python內建的importlib.reload實現。",
    response_description="新模組的記憶體位置",
    response_model=dict
)
def reload_modules():
    global embedded_obj
    print(hex(id(embedded_obj)))
    import importlib
    importlib.reload(importlib.import_module("modules.embedded"))
    from modules.embedded import embedded
    embedded_obj = embedded()
    print(hex(id(embedded_obj)))
    return {"result": str(type(embedded_obj))}
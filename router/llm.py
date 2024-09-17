from pydantic import BaseModel
from fastapi import APIRouter
import aiohttp
router = APIRouter(
    prefix="/v1/llm",
    tags=["llm"]

)

class llm_info(BaseModel):
    model_name:str | None = None
    url:str | None = None
    mode:str | None = None
    model_config = {
        "json_schema_extra": {
            "example": {
                "model_name": "MediaTek-Research/Breeze-7B-Instruct-v0_1",
                "mode": "openai"
            }
        }
    }

class llm_one_chat(BaseModel):
    input:str
    system_message:str | None = None
from modules.llm import llm
llm_obj = None

@router.post(
    path="/reload",
    summary="重新載入LLM模組",
    description="重新載入LLM模組檔案。\n\n以python內建的importlib.reload實現。",
    response_description="新模組的記憶體位置",
    response_model=dict
)
def reload_modules():
    global llm_obj
    print(hex(id(llm_obj)))
    import importlib
    importlib.reload(importlib.import_module("modules.llm"))
    from modules.llm import llm
    llm_obj = llm()
    print(hex(id(llm_obj)))
    return {"result": str(type(llm_obj))}

@router.get(
    path="/rag_default/",
    summary="使用預設的RAG搜尋",
    # description="取得所有筆記的標題!!",
    response_description="簡單處理好的RAG回答與引用",
    response_model=dict
)
async def rag_default(query:str):
    async with aiohttp.request(method="get", url="http://10.147.19.2:8000", 
        params={"query":query}
        ) as response:
        result = await response.json()
        return result
    
@router.get(path="/",
            summary="取得當前llm資訊",
            description="取得當前llm資訊\n包含模型名稱、url及mode",
            response_description="llm資訊",
            response_model=dict
            )
async def get_llm_info():
    return {"model_name":llm_obj.model_name,
            "url":llm_obj.url,
            "mode":llm_obj.mode}
    
@router.post(path="/",
             summary="初使化llm",
             description="根據要求初使化llm物件，缺少的資訊由config補充",
             response_description="llm資訊",
             response_model=dict,
             )
async def set_llm(llm_info:llm_info):
    global llm_obj
    if llm_obj == None:
        llm_obj = llm()
    setting_list = ["model_name", "url", "mode"]

    for setting in setting_list:
        if llm_info.dict()[setting] != None:
            llm_obj.__setattr__(setting, llm_info.dict()[setting])

    llm_obj.set_model()
    #llm_obj = llm()
    return await get_llm_info()


@router.get("/chat",
            summary="測試聊天功能是否正常",
            response_model=dict)
async def llm_chat_test():
    return dict(llm_obj.chat(input="你好，你能做什麼?"))

@router.post("/chat",
             summary="和llm單輪對話",
             description="和llm單輪對話，除了輸入外也可包含系統訊息。\n回傳值包含完整的訊息",
             response_model=dict)
async def llm_chat(llm_one_chat:llm_one_chat):
    return dict(llm_obj.chat(input=llm_one_chat.input, system_message=llm_one_chat.system_message))
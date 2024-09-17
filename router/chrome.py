from fastapi import APIRouter
import configparser
import aiohttp
from pydantic import BaseModel
router = APIRouter(
    prefix="/v1/chrome",
    tags=["chrome"]
)

class triple(BaseModel):
    predicate:str=None
    subject:dict
    object:dict

class action_data(BaseModel):
    action_info: dict
    tab_info: dict
    opener_tab_info: dict = None
    
from modules.chrome import ChromeSource
chrome_obj = ChromeSource()

@router.get(
    path="/",
    summary="查看伺服器狀態",
    description="供Extension在連線時查看伺服器狀態",
    response_model=dict
)
async def get_status():
    return {"status": "ok"}

@router.post(
    path="/excerpt",
    summary="匯出摘錄",
    response_description="知識庫中摘錄節點的資訊",
    response_model=str
)
async def excerpt(update_triple:triple) -> str:
    global chrome_obj
    result = await chrome_obj.excerpt(update_triple.dict())
    return {"result": result}

@router.post(
    path="/triple",
    summary="用於上傳網頁更新的三元體",
    description="接受網頁更新三元體，並將相關資訊儲存到知識圖譜中",
    response_description="儲存結果及相關的UUID",
    response_model=dict)
async def test_triple(triple: triple):
    global chrome_obj
    try:
        result = await chrome_obj.new_triple(triple.model_dump(mode="json"))
        return {"result": result}
    except Exception as e:
        print(e)
        return {"result": "錯誤：" + str(e)}
    # https://docs.pydantic.dev/1.10/usage/exporting_models/
    # print("ready for message handler:", triple.model_dump_json())
    # messageHandle(triple.model_dump_json())
    return {"triple": "ok"}

# 以下為未來版本可能會用到的API
# @router.post(
#     path="/UpdateTo",
#     summary="更新頁面",
#     response_description="舊分頁title、新分頁title",
#     response_model=list
# )
# async def tab_update(update_triple:triple):
#     return triple.subject["name"]

# @router.post(
#     path="/action",
#     summary="用於新增動作紀錄",
#     description="接受瀏覽器動作資訊，將資訊整理後儲存到知識庫中",
#     response_description="儲存結果及相關的UUID",
#     response_model=dict
# )
# async def post_action(action_data: action_data):
#     global chrome_obj
#     action_info = action_data.action_info
#     tab_info = action_data.tab_info
#     opener_tab_info = action_data.opener_tab_info
#     print_var(action_info)
#     print_var(tab_info)
#     print_var(opener_tab_info)
#     result = await chrome_obj.new_action(action_info)
#     return {"result": result}

# @router.get(
#     path="/activate",
#     summary="取得目前焦點的頁面",
#     response_description="焦點頁面的相關訊息",
#     response_model=dict
# )
# async def get_activate():
#     """跟extension取得目前焦點頁面的訊息
    
#     return (dict): 焦點頁面的相關訊息
#     """
#     # TODO: 跟extension取得目前焦點頁面的訊息
#     pass
#     return {"title": "title",
#             "url": "url",
#             "tab_id": "tab_id"}
from fastapi import APIRouter, Body
from typing import Annotated
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
    
class excerpt_data(BaseModel):
    text: str
    description: str
    tag_string: str
    url: str
    title: str

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
    description="接受Extension傳來的摘錄資訊，將其儲存至知識庫中。",
    response_description="摘錄結果與該摘錄的UUID",
    response_model=dict,
    responses={
        200: {
            "description": "成功儲存摘錄",
            "content": {
                "application/json": {
                    "example": {
                        "result": "儲存成功",
                        "uuid": "c2086a17-451f-4d1e-8c1a-f61f43c2f715"
                    }
                }
            }
        }
    }
)
async def excerpt(excerpt_data:Annotated[
        excerpt_data,
        Body(
            openapi_examples={
                "含摘錄的一般摘錄":{
                    "summary": "包含摘錄的一般摘錄",
                    "description": "不只是匯出網頁而已，而是包含摘錄",
                    "value": {
                        "title": "測試用視窗標題(網頁標題)",
                        "text": "摘錄文字",
                        "description": "使用者對此摘錄的說明",
                        "tag_string": "測試用tag, 測試用Tag, ",
                        "url": "https://www.test.com",
                    }}})
    ]):
    global chrome_obj
    # TODO: excerpt未完成
    result = await chrome_obj.excerpt(excerpt_data.dict())
    return {"result": result["result"], "uuid": result.get("uuid", "")}

@router.post(
    path="/web",
    summary="儲存網頁資訊",
    description="接受網頁資訊，將其儲存至知識庫中。",
    response_description="儲存結果及該網頁的UUID",
    response_model=dict,
    responses={
        200: {
            "description": "成功儲存網頁",
            "content": {
                "application/json": {
                    "example": {
                        "result": "儲存成功",
                        "uuid": "61e59388-03f9-4bc5-8f24-f9927708b1d9"
                    }
                }
            }
        }
    }
)
async def save_web(web_data: Annotated[
    dict,
    Body(
        openapi_examples={
            "網頁基礎資訊":{
                "summary": "基礎網頁",
                "description": "一般網頁的基礎資訊",
                "value": {
                    "title": "測試用網頁標題",
                    "url": "https://www.test1.com"
                }},
            "含標籤及描述的網頁":{
                "summary": "含標籤網頁",
                "description": "一般網頁的基礎資訊",
                "value": {
                    "title": "標籤網頁標題",
                    "url": "https://www.test2.com",
                    "description": "使用者對此網頁的說明",
                    "tag_string": "測試用tag, 測試用Tag, "
                }}
            })
    ]):
    # TODO: 若此網頁已經存在怎麼辦?
    global chrome_obj
    result = await chrome_obj.save_web(web_data)
    return {"result": result["result"], "uuid": result.get("uuid", "")}


@router.post(
    path="/triple",
    summary="用於上傳網頁更新的三元體",
    description="接受網頁更新三元體，並將相關資訊儲存到知識圖譜中",
    response_description="儲存結果及相關的UUID",
    response_model=dict,
    responses={
        200: {
            "description": "成功上傳三元體，uuid1為舊分頁的UUID，uuid2為新分頁的UUID。\n在知識庫中建立\"update_to\"關係",
            "content": {
                "application/json": {
                    "example": {
                        "result": "成功",
                        "uuid1": "c2086a17-451f-4d1e-8c1a-f61f43c2f715",
                        "uuid2": "3eb5aa0f-4b1a-4e37-994c-71c61f2e287d"
                    }
                }
            }
        }
    })
async def test_triple(triple:Annotated[
    triple,
    Body(
        openapi_examples={
            "網頁更新":{
                "summary": "網頁更新",
                "description": "網頁更新時Extension送來的三元體",
                "value": {
                    "predicate": "update_to",
                    "subject": {
                        "name": "舊分頁標題",
                        "tabURL": "http://old_page_url.com",
                        "tabId": 2055685215
                    },
                    "object": {
                        "name": "新分頁標題",
                        "tabURL": "http://new_page_url.com",
                        "tabId": 2055685215
                    }
                }
            }
        }
    )
]):
    global chrome_obj
    try:
        result = await chrome_obj.new_triple(triple.model_dump(mode="json"))
        return result
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
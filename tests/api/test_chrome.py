"""測試chrome模組，由於知識庫API未完善(relation會重複、刪除未測試等)，
因此本測試目前僅檢查API回覆內容是否正確，並未真的驗證是否有成功儲存。
2024-12-01測試完成
"""
import pytest
pytest_plugins = ('pytest_asyncio',)
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from modules.utils import call_api


@pytest.mark.asyncio
async def test_copy_history_success():
    """上傳測試用三元體->驗證->刪除
    由於知識庫API未完善，目前僅測試該API的回覆是否正確，並未真的驗證是否有成功儲存。
    2024-12-01測試完成
    """
    # 上傳triple
    result = (await call_api("v1/chrome/triple", "post", {
        "subject": {
            "name": "舊分頁標題",
            "tabURL": "http://old_page_url.com",
            "tabId": 2055685215
        },
        "object": {
            "name": "新分頁標題",
            "tabURL": "http://new_page_url.com",
            "tabId": 2055685215
        }, "predicate": "update_to"
        }))
    assert result["result"] == "成功"
    # uuid1 = result["uuid1"]
    # uuid2 = result["uuid2"]
    # # 用relation驗證
    # result = (await call_api(f"v1/knowledge_base/relations/{uuid1}", "get", debug_mode=True))["result"]
    # # 用搜尋驗證
    # search_result = (await call_api("v1/chrome/search", "get", params={"keyword": "test"}))["result"]
    # # 刪除測試節點
    # delete_result1 = (await call_api(f"v1/knowledge_base/{uuid1}", "delete", debug_mode=True))["result"]
    # delete_result2 = (await call_api(f"v1/knowledge_base/{uuid2}", "delete", debug_mode=True))["result"]
    # # 檢查刪除結果
    # result = (await call_api(f"v1/chrome/search", "get", params={"keyword": "test"}))["result"]
    
@pytest.mark.asyncio
async def test_excerpt():
    """模擬Extension傳遞摘錄資訊到chrome/excerpt端點，檢查儲存結果是否成功
    但並未檢查該摘錄是否真的有被儲存及其關係是否正確。
    2024-11-29測試成功
    """
    excerpt_data = {
        "title": "測試用視窗標題(網頁標題)",
        "text": "摘錄文字",
        "description": "使用者對此摘錄的說明",
        "tag_string": "測試用tag, 測試用Tag, ",
        "url": "https://www.test.com"
    }
    result = (await call_api("v1/chrome/excerpt", "post", excerpt_data, debug_mode=True))["result"]
    assert result == "儲存成功"
    
@pytest.mark.asyncio
async def test_save_web():
    web_data = {
        "title": "標籤網頁標題",
        "url": "https://www.test2.com",
        "description": "使用者對此網頁的說明",
        "tag_string": "測試用tag, 測試用Tag, "
    }
    result = (await call_api("v1/chrome/web", "post", web_data))
    assert len(result["uuid"]) == 36
    web_data2 = {
        "title": "測試用網頁標題",
        "url": "https://www.test1.com"
    }
    result = (await call_api("v1/chrome/web", "post", web_data2))
    assert len(result["uuid"]) == 36
    
    

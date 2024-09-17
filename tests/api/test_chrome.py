"""測試chrome模組"""
import pytest
pytest_plugins = ('pytest_asyncio',)

from modules.utils import call_api


@pytest.mark.asyncio
async def test_copy_history_success():
    """上傳測試用三元體->驗證->刪除"""
    # 上傳triple
    result = (await call_api("v1/chrome/triple", "post", {
        "subject": {"name": "test", "url": "test_url"},
        "predicate": "update_to",
        "object": {"name": "test", "url": "test_url"}
        }, debug_mode=True))["result"]
    uuid = result["uuid"]
    # 用relation驗證
    result = (await call_api(f"v1/knowledge_base/relations/{uuid}", "get", debug_mode=True))["result"]
    # 用搜尋驗證
    search_result = (await call_api("v1/chrome/search", "get", params={"keyword": "test"}))["result"]
    # 刪除測試節點
    delete_result1 = (await call_api(f"v1/knowledge_base/{uuid1}", "delete", debug_mode=True))["result"]
    delete_result2 = (await call_api(f"v1/knowledge_base/{uuid2}", "delete", debug_mode=True))["result"]
    # 檢查刪除結果
    result = (await call_api(f"v1/chrome/search", "get", params={"keyword": "test"}))["result"]
    
@pytest.mark.asyncio
async def test_excerpt():
    result = (await call_api("v1/chrme/excerpt", "post", {}, debug_mode=True))["result"]
    
    result = (await call_api(f"v1/knowledge_base/{uuid}", "delete", debug_mode=True))["result"]
    
    

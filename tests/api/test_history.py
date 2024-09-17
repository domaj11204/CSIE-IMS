"""測試History模組"""
import pytest
pytest_plugins = ('pytest_asyncio',)

from modules.utils import call_api


@pytest.mark.asyncio
async def test_copy_history_success():
    """測試history模組，複製瀏覽紀錄->查看取得資料的方法->搜尋瀏覽紀錄"""
    # 要先備份原本的瀏覽紀錄檔案
    # TODO: 路徑應根據設定檔
    # TODO: 測試時可以使用測試的設定檔
    import shutil
    shutil.copy("./data/History.db", "./data/History.db.bak")
    # 取得原始瀏覽紀錄檔案的md5
    origin_md5 = (await call_api("v1/history/md5", "get"))["md5"]
    response = await call_api("v1/history/", "post")
    assert response == {"result": True}
    # 驗證檔案並還原
    from hashlib import md5
    from modules.utils import read_config
    history_file_path = read_config()["history"]["history_path"]
    new_md5 = md5(open(history_file_path, "rb").read()).hexdigest()
    assert new_md5 == origin_md5
    # 驗證完成，還原
    shutil.copy("./data/History.db.bak", "./data/History.db")

@pytest.mark.asyncio
async def test_data():
    result = await call_api("v1/history/data", "get")
    assert result["result"] == "id"

@pytest.mark.asyncio
async def test_get_data():
    data = (await call_api("v1/history/data/id/721341", "get"))["data"]
    assert len(data["url"]) > 0

@pytest.mark.asyncio
async def test_search():
    result = await call_api("v1/history/search", "get", params={"keyword": "Google"})
    assert result["result"][:2]=="標題"
        
    

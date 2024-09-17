"""
本檔案嘗試案例驅動開發(也許真的有這種東西，但現在先懶得查)
自動測試所有API
"""
import requests
import asyncio
import pytest
from modules.utils import call_api
from modules.test_utils import remove_uuids
pytest_plugins = ('pytest_asyncio',)

# 基本讀取資料測試
@pytest.mark.asyncio
async def test_get_data():
    test_uuid = "01ed9ce2-6bab-43a1-bccd-432298719331"
    
    uuids = (await call_api("v1/knowledge_base/uuids", "get", params={"source": "rdf"}))["uuids"]
    assert test_uuid in uuids
    
    # info = (await call_api("v1/knowledge_base/{test_uuid}", "get"))["info"]
    
    split_result = (await call_api("v1/rdf/split", "post",))
    response = await call_api("v1/knowledge_base/{test_uuid}", "info")
    response = await call_api("v1/rdf/data/{test_uuid}", "get")
    response = await call_api("v1/rag/query", "post", {"source_list":["obsidian"], "type_list": [], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" in response["answer_text"]
    assert "參考筆記" in bot_message["result"]
    assert "參考摘錄" not in bot_message["result"]
    response = await call_api("v1/rag/query", "post", {"source_list":[], "type_list": ["測試用筆記"], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" in response["answer_text"]
    assert "參考筆記" in bot_message["result"]
    assert "參考摘錄" not in bot_message["result"]

#切chunk測試
@pytest.mark.asyncio
async def test_split_data():
    split_data = (await call_api("v1/rdf/split", "post"))["split_result"]
    excepted_split_result = {}
    assert excepted_split_result == split_data
    
# 關鍵字搜尋測試
@pytest.mark.asyncio
async def test_keyword_search():
    keyword = "血虛證類"
    search_type = "keyword"
    top_k = 3
    response = await call_api("v1/rdf/search", "get", params={"keyword":keyword, "search_type":search_type, "top_k":top_k})
    excepted_result = {
        "result": [
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#心肝血虛證型",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類"
            ],
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#心脾血虛證型",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類"
            ],
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#肝脾血虛證型",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類"
            ],
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#肝腎血虛證型",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類"
            ],
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類",
            "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
            "http://www.w3.org/2002/07/owl#Class"
            ],
            [
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#血虛證類",
            "http://www.w3.org/2000/01/rdf-schema#subClassOf",
            "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#虛證門"
            ]
        ]
    }
    assert response == excepted_result
    keyword = "血虛證"
    response = await call_api("v1/rdf/search", "get", params={"keyword":keyword, "search_type":search_type, "top_k":top_k})
    excepted_result = {"result": []}
    assert response == excepted_result
    
# 模糊搜尋測試
@pytest.mark.asyncio
async def test_fuzzy_search():
    keyword = "肝脾血證"
    search_type = "fuzzy"
    top_k = 3
    response = await call_api("v1/rdf/search", "get", params={"keyword":keyword, "search_type":search_type, "top_k":top_k})
    excepted_result = {"result": []}
    
# rag測試
@pytest.mark.asyncio
async def test_rag_api2():
    response = await call_api("v1/rag/query", "post", {"source_list":["neo4j"], "type_list": [], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" not in response["answer_text"]
    assert "參考筆記" not in bot_message["result"]
    response = await call_api("v1/rag/query", "post", {"source_list":[], "type_list": ["摘錄"], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" not in response["answer_text"]
    assert "參考筆記" not in bot_message["result"]
    
# 渲染測試
@pytest.mark.asyncio
async def test_reference_string():
    reference_string = (await call_api("/v1/rdf/reference_string", "post", data={"reference_data":{}}))["reference_string"]
    excepted_reference_string = ""
    assert excepted_reference_string == reference_string

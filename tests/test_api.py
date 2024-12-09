"""
本檔案嘗試案例驅動開發(也許真的有這種東西，但現在先懶得查)
自動測試所有API
最後全部通過日期: 2024-11-25
"""
import requests
import asyncio
import pytest
from modules.utils import call_api
from modules.test_utils import remove_uuids, remove_host
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
async def new_note():
    result = await call_api("v1/obsidian/note", "post", data={
        "title": "pytest用標題",
        "tags": ["pytest測試用"],
        "content": "pytest用內容",
        "abstract": "pytest用摘要",
        "description": "pytest用描述"
    })
    return result

@pytest.mark.asyncio
async def test_rag_api1():
    """以obsidian為source的rag測試
    """
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
    
@pytest.mark.asyncio
async def test_rag_api2():
    """以neo4j為source的rag測試
    """
    response = await call_api("v1/rag/query", "post", {"source_list":["neo4j"], "type_list": [], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" not in response["answer_text"]
    assert "參考筆記" not in bot_message["result"]
    response = await call_api("v1/rag/query", "post", {"source_list":[], "type_list": ["摘錄"], "query":"FastAPI使用哪個port?"})
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "27711" not in response["answer_text"]
    assert "參考筆記" not in bot_message["result"]

@pytest.mark.asyncio
async def test_rag_api3():
    """
    """
    response = await call_api("v1/rag/query", "post", {"source_list":["neo4j"], "type_list": [], "query":"RAG結合甚麼可以提升效果?"})
    reference_list = response["reference_list"]
    assert reference_list[0]["parent_source"] == "neo4j"
    assert reference_list[0]["parent_type"] == "摘錄"
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert "參考摘錄" in bot_message["result"]
    response = await call_api("v1/rag/query", "post", {"source_list":[], "type_list": ["摘錄"], "query":"RAG結合甚麼可以提升效果?"})
    reference_list = response["reference_list"]
    bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response))
    assert reference_list[0]["parent_source"] == "neo4j"
    assert reference_list[0]["parent_type"] == "摘錄"
    assert "參考摘錄" in bot_message["result"]
    
@pytest.mark.asyncio
async def test_rag_api4():
    response = await call_api("v1/rag/query", "post", {"source_list":["neo4j", "obsidian"], "type_list": [], "query":"RAG結合甚麼可以提升效果?"})
    reference_list = response["reference_list"]
    reference_result_list = []
    for reference in reference_list:
        reference_result_list.append(reference["parent_source"])
    assert "neo4j" in reference_result_list
    assert "obsidian" in reference_result_list
    
    response = await call_api("v1/rag/query", "post", {"source_list":["obsidian"], "type_list": ["摘錄"], "query":"RAG結合甚麼可以提升效果?"})
    reference_list = response["reference_list"]
    reference_result_list = []
    for reference in reference_list:
        reference_result_list.append(reference["parent_source"])
    assert "neo4j" in reference_result_list
    assert "obsidian" in reference_result_list
    
@pytest.mark.asyncio
async def test_rag_rdf():
    response = await call_api("v1/rag/query", "post", {"source_list":["rdf"], "type_list": [], "query":"血虛證類有哪些證型?", "top_k": 4})
    # 改成血虛類證型包含哪些證候?結果可能不同
    reference_list = response["reference_list"]
    answer_text = response["answer_text"]
    reference_result_list = []
    for reference in reference_list:
        reference_result_list.append(reference["parent_source"])
    assert "neo4j" not in reference_result_list
    assert "obsidian" not in reference_result_list
    assert "心脾血虛" in answer_text
    assert "肝脾血虛" in answer_text
    assert "肝腎血虛" in answer_text
    assert "心肝血虛" in answer_text
    # response = await call_api("v1/rag/query", "post", {"source_list":[], "type_list": ["知識本體"], "query":"RAG結合甚麼可以提升效果?"})
    # reference_list = response["reference_list"]
    # reference_result_list = []
    # for reference in reference_list:
    #     reference_result_list.append(reference["parent_source"])
    # assert "neo4j" in reference_result_list
    # assert "obsidian" in reference_result_list

    
@pytest.mark.asyncio
async def test_split_obsidian():
    import json
    result = (await call_api("v1/obsidian/split", "post", 
        data={
            "entity": {
                "path": "每日筆記/2023-07-24.md",
                "建立時間": "2024-07-22T06:22:49.992213800",
                "source": "obsidian",
                "UUID": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                "描述": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault\n5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)\n6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題\n7. 使用以下指令重製ssh-key密碼為空\n```\n   ssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用\n註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。",
                "名稱": "每日筆記/2023-07-24.md",
                "type": "測試用筆記",
                "data": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault\n5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)\n6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題\n7. 使用以下指令重製ssh-key密碼為空\n```\n   ssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用\n註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。"
            },
            "chunk_size": 100
        }
    ))["split_result"]
    excepted_entities = [
        {
            "entity": {
                "name": "新增宿舍的筆記同步_0",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-0",
                # "uuid": "ec5c82e6-dde0-474a-9f72-dd2f18c04823",
                "data_hash": "da9cb4ab6e933274ba7b161898458362",
                "relation": [
                    {
                        # "uuid1": "ec5c82e6-dde0-474a-9f72-dd2f18c04823",
                        # "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 100
                        }
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault",
            "metadata": {
                # "uuid": "ec5c82e6-dde0-474a-9f72-dd2f18c04823",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        },
        {
            "entity": {
                "name": "新增宿舍的筆記同步_1",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-1",
                # "uuid": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                "data_hash": "3abe9d126581477d8dd77f5e26e444a2",
                "relation": [
                    {
                        # "uuid1": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                        # "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 100
                        }
                    },
                    {
                        # "uuid1": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                        # "uuid2": "ec5c82e6-dde0-474a-9f72-dd2f18c04823",
                        "relation": "上一段"
                    },
                    {
                        # "uuid2": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                        # "uuid1": "ec5c82e6-dde0-474a-9f72-dd2f18c04823",
                        "relation": "下一段"
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)",
            "metadata": {
                # "uuid": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        },
        {
            "entity": {
                "name": "新增宿舍的筆記同步_2",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-2",
                # "uuid": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                "data_hash": "b2040938ecb7cccdf2587a68302ad189",
                "relation": [
                    {
                        # "uuid1": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                        # "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 100
                        }
                    },
                    {
                        # "uuid1": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                        # "uuid2": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                        "relation": "上一段"
                    },
                    {
                        # "uuid2": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                        # "uuid1": "ed0af604-9e81-4d7d-9da3-4b12f71354a7",
                        "relation": "下一段"
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題",
            "metadata": {
                # "uuid": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        },
        {
            "entity": {
                "name": "新增宿舍的筆記同步_3",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-3",
                # "uuid": "95a76800-7cc3-446a-98c7-d97275b1800b",
                "data_hash": "393697624abfc33fc0fcb9c91ccfe3f5",
                "relation": [
                    {
                        # "uuid1": "95a76800-7cc3-446a-98c7-d97275b1800b",
                        # "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 100
                        }
                    },
                    {
                        # "uuid1": "95a76800-7cc3-446a-98c7-d97275b1800b",
                        # "uuid2": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                        "relation": "上一段"
                    },
                    {
                        # "uuid2": "95a76800-7cc3-446a-98c7-d97275b1800b",
                        # "uuid1": "bfbf3a8b-8f72-47cc-9096-de2e2b6c9203",
                        "relation": "下一段"
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "7. 使用以下指令重製ssh-key密碼為空\n```\nssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用",
            "metadata": {
                # "uuid": "95a76800-7cc3-446a-98c7-d97275b1800b",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        },
        {
            "entity": {
                "name": "新增宿舍的筆記同步_4",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-4",
                # "uuid": "69da5133-339c-4c33-a1b8-0c04a68c7e1f",
                "data_hash": "5f3077d694d8ae91a8ea33c3e935ad4d",
                "relation": [
                    {
                        # "uuid1": "69da5133-339c-4c33-a1b8-0c04a68c7e1f",
                        # "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 100
                        }
                    },
                    {
                        # "uuid1": "69da5133-339c-4c33-a1b8-0c04a68c7e1f",
                        # "uuid2": "95a76800-7cc3-446a-98c7-d97275b1800b",
                        "relation": "上一段"
                    },
                    {
                        # "uuid2": "69da5133-339c-4c33-a1b8-0c04a68c7e1f",
                        # "uuid1": "95a76800-7cc3-446a-98c7-d97275b1800b",
                        "relation": "下一段"
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。",
            "metadata": {
                # "uuid": "69da5133-339c-4c33-a1b8-0c04a68c7e1f",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        }
    ]
    remove_uuids(result)
    remove_uuids(excepted_entities)
    assert excepted_entities == result
    result = (await call_api("v1/obsidian/split", "post", 
        data={
            "entity": {
                "path": "每日筆記/2023-07-24.md",
                "建立時間": "2024-07-22T06:22:49.992213800",
                "source": "obsidian",
                "UUID": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                "描述": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault\n5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)\n6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題\n7. 使用以下指令重製ssh-key密碼為空\n```\n   ssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用\n註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。",
                "名稱": "每日筆記/2023-07-24.md",
                "type": "測試用筆記",
                "data": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault\n5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)\n6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題\n7. 使用以下指令重製ssh-key密碼為空\n```\n   ssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用\n註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。"
            },
            "chunk_size": 1024
        }
    ))["split_result"]
    excepted_entities = [
        {
            "entity": {
                "name": "新增宿舍的筆記同步_0",
                "description": "每日筆記/2023-07-24.md-新增宿舍的筆記同步-0",
                "uuid": "626eb8d1-1212-4e50-b08d-70d2eddd306b",
                "data_hash": "3df08f6ebdbb22c6e3d5aebbc301b22f",
                "relation": [
                    {
                        "uuid1": "626eb8d1-1212-4e50-b08d-70d2eddd306b",
                        "uuid2": "63521fde-06ee-4bd6-b374-fef9c8a0ec80",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 1024
                        }
                    }
                ],
                "type": "chunk",
                "標題1": "新增宿舍的筆記同步"
            },
            "document": "# 新增宿舍的筆記同步\n1. 參考[[Git指令]]，新增ssh key\n2. 使用ssh -T測試OK\n3. 用[[git clone]]將整份筆記下載\n4. 在Obsidian中開啟vault\n5. [[obsidian-git]]已自動安裝完成，設定也同步完成(只有快捷鍵不知道為甚麼變成commit)\n6. 但[[obsidian-git]]無法push，報錯無法連線到Obsidian sync.git，但[[Source tree]]可以，推測是ssh-key的密碼問題\n7. 使用以下指令重製ssh-key密碼為空\n```\nssh-keygen -p -f github_key\n```\n8. 重製為空後即可正常使用\n註: 使用ssh-add等[[ssh agent]]功能應該也能解決，但由於ssh-add指令用錯參數導致實驗失敗，就直接將密碼重製了。",
            "metadata": {
                "uuid": "626eb8d1-1212-4e50-b08d-70d2eddd306b",
                "year": 2023,
                "month": 7,
                "day": 24,
                "parent_source": "obsidian",
                "parent_type": "測試用筆記",
                "標題1": "新增宿舍的筆記同步"
            }
        }
    ]
    remove_uuids(result)
    remove_uuids(excepted_entities)
    print("=------")
    print(result)
    print("-----")
    print(excepted_entities)
    print("-----")
    assert excepted_entities == result
    
@pytest.mark.asyncio
async def test_split_neo4j():
    import json
    result = (await call_api("v1/neo4j/split", "post",
        data={
            "entity": {
                "摘錄": "IMRaD is an acronym for Introduction – Method – Results – and – Discussion.",
                "建立時間": "2023-11-30T11:18:07.312695946",
                "建立者": "defaultUser",
                "source": "neo4j",
                "UUID": "a1ac7e25-144c-4d84-83f6-f128b8bb84f2",
                "名稱": "摘錄於2023-11-30",
                "type": "摘錄",
                "data": {
                    "摘錄": "IMRaD is an acronym for Introduction – Method – Results – and – Discussion.",
                    "建立時間": "2023-11-30T11:18:07.312695946",
                    "建立者": "defaultUser",
                    "source": "neo4j",
                    "UUID": "a1ac7e25-144c-4d84-83f6-f128b8bb84f2",
                    "名稱": "摘錄於2023-11-30",
                    "type": "摘錄"
                }
            },
            "chunk_size": 1024
        }))["split_result"]
    excepted_entities = [
        {
            "entity": {
                "name": "摘錄於2023-11-30",
                "description": "",
                "data_hash": "39c46e951177dec83eea3cc90c97d42b",
                "uuid": "199fcfec-fa7f-4c07-866b-b94230129650",
                "relation": [
                    {
                        "uuid1": "199fcfec-fa7f-4c07-866b-b94230129650",
                        "uuid2": "a1ac7e25-144c-4d84-83f6-f128b8bb84f2",
                        "relation": "屬於",
                        "properties": {
                            "chunk_size": 1024
                        }
                    }
                ],
                "type": "chunk"
            },
            "document": "摘錄:IMRaD is an acronym for Introduction – Method – Results – and – Discussion.\n說明:",
            "metadata": {
                "uuid": "199fcfec-fa7f-4c07-866b-b94230129650",
                "year": 2023,
                "month": 11,
                "day": 30,
                "parent_type": "摘錄",
                "parent_source": "neo4j"
            }
        }
    ]
    remove_uuids(result)
    remove_uuids(excepted_entities)
    assert excepted_entities == result
    result = (await call_api("v1/neo4j/split", "post",
    data={
        "entity": {
            "摘錄": "IMRaD is an acronym for Introduction – Method – Results – and – Discussion.",
            "建立時間": "2023-11-30T11:18:07.312695946",
            "建立者": "defaultUser",
            "source": "neo4j",
            "UUID": "a1ac7e25-144c-4d84-83f6-f128b8bb84f2",
            "名稱": "摘錄於2023-11-30",
            "type": "摘錄",
            "data": {
                "摘錄": "IMRaD is an acronym for Introduction – Method – Results – and – Discussion.",
                "建立時間": "2023-11-30T11:18:07.312695946",
                "建立者": "defaultUser",
                "source": "neo4j",
                "UUID": "a1ac7e25-144c-4d84-83f6-f128b8bb84f2",
                "名稱": "摘錄於2023-11-30",
                "type": "摘錄"
            }
        },
        "chunk_size": 100
    }))["split_result"]
    print(json.dumps(result, indent=4))
    
@pytest.mark.asyncio
async def test_keyword_search():
    response = await call_api("v1/knowledge_base/search", "get", params={
        "source_str": "obsidian",
        "type_str": "",
        "search_type": "keyword",
        "keyword": "05-14",
        "top_k": 3
    })
    excepted_result = {
    "result": "查詢結果:\n<a href=\"http://127.0.0.1:27711/v1/knowledge_base/url/53fe1711-d044-45b3-9449-78e8ba4b2eaf\" target=\"_blank\">每日筆記/2024-05-14.md</a>\n"
    }
    assert remove_host(response) == remove_host(excepted_result)

@pytest.mark.asyncio
async def test_fuzzy_search():
    response = await call_api("v1/knowledge_base/search", "get", params={
        "source_str": "obsidian",
        "type_str": "",
        "search_type": "fuzzy",
        "keyword": "05-14",
        "top_k": 3
        })
    # UWRatio的結果
    excepted_result = {
    "result": "查詢結果:\n<a href=\"http://127.0.0.1:27711/v1/knowledge_base/url/53fe1711-d044-45b3-9449-78e8ba4b2eaf\" target=\"_blank\">每日筆記/2024-05-14.md</a>\n<a href=\"http://10.147.19.205:27711/v1/knowledge_base/url/dfc2e518-d292-4f4f-88fa-e3b52eaa9055\" target=\"_blank\">每日筆記/2023-08-14.md</a>\n<a href=\"http://10.147.19.205:27711/v1/knowledge_base/url/5d56e48d-97b6-46ca-994b-15aa9b6c7b54\" target=\"_blank\">每日筆記/2023-09-05.md</a>\n"
    }
    assert remove_host(response) == remove_host(excepted_result)
    
@pytest.mark.asyncio
async def test_entity_count():
    source_list = ["obsidian", "neo4j"]
    type_list = ["筆記", "摘錄"]
    for source in source_list:
        entity_count = (await call_api("v1/knowledge_base/entity_count", "get", params={"source": source}))["entity_count"]
        assert entity_count > 0
    for type in type_list:
        entity_count = (await call_api("v1/knowledge_base/entity_count", "get", params={"type": type}))["entity_count"]
        assert entity_count > 0
    
        
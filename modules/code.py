import textwrap
import time
import requests
def error_message_excerpt():
    error_message = requests.get("http://localhost:27711/highlight").text
    time.sleep(3)
    # 讀取程式碼摘錄
    excerpt_result = requests.get("http://localhost:27711/excerpt").json()
    # 從檔案標題解析檔名
    file_path = get_file_path(excerpt_result["window_title"])
    # 儲存到知識庫中
    requests.post(
        "http://localhost:27711/knowledge_base/entity",
        json={
            "name": f"{file_path}錯誤紀錄",
            "description": textwrap.dedent(f"""
                檔案: {file_path}
                報錯: {error_message}
                說明: {excerpt_result['description']}
                code: 
                ```
                {excerpt_result['text']}
                ```
            """),
            "type": "錯誤紀錄"
        }
    )



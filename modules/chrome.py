from modules.knowledge_base import source
from modules.utils import call_api
from modules.debug_utils import print_var
class ChromeSource(source):
    """與Chrome Extension溝通用的模組"""
    
    def __init__(self):
        super().__init__(name="chrome")
        self.focus_tab = None
        
    async def new_triple(self, triple:dict)->dict:
        """處理分頁動作三元體
        return (dict): 儲存結果及UUID
        """
        # print_var(triple)
        subject_title = triple["subject"]["name"]
        object_title = triple["object"]["name"]
        predicate = triple["predicate"]
        # 取得當前時間
        from datetime import datetime
        currentTime = datetime.now().strftime("%H:%M:%S") 
        print(f"{currentTime} {subject_title} {predicate} {object_title}")
        
        # 不捕捉Activate
        # # Activate，紀錄焦點分頁並新增到知識庫
        # if triple["predicate"] == "Activate":
        #     self.focus_tab = triple["object"]
        #     result = (await call_api("/v1/knowledge_base/entity", "post", triple["object"]))["result"]
        #     return result
        print_var(triple["subject"])
        print_var(triple["predicate"])
        print_var(triple["object"])

        if predicate == "update_to": # 真正要處理的更新分頁
            old_page = triple["subject"]
            old_page["type"] = "測試用網頁"
            new_page = triple["object"]
            new_page["type"] = "測試用網頁"
            # 新增實體
            old_page_uuid = (await call_api("/v1/knowledge_base/entity", "post", old_page))["uuid"]
            new_page_uuid = (await call_api("/v1/knowledge_base/entity", "post", new_page))["uuid"]
            # 新增關係
            relation_result = (await call_api("/v1/knowledge_base/relation", "post", {
                "uuid1":old_page_uuid, 
                "uuid2":new_page_uuid, 
                "relation":"update_to"}, debug_mode=True))["result"]
            print_var(relation_result)
        else:
            return {"result": "未知的predicate"}
        
        
        
        # # Update，建立新分頁資訊，但不一定會馬上更新完
        # elif triple["predicate"] == "UpdateTo":
        #     entity_result = (await call_api("/v1/knowledge_base/entity", "get", self.focus_tab))["result"]
        
        # Close，關閉分頁，後面會接著touch所以不用處理
        # Open，開啟分頁，同上
        return {"result":"成功",
                "uuid1": old_page_uuid,
                "uuid2": new_page_uuid}
    
    async def new_action(self, action_info:dict):
        """傳入action資訊，轉成儲存到知識庫的實體"""
        # TODO: 之後把triple都改成action
        print_var(action_info)
        # 以action的類型作為entity的名稱？
        action_type = action_info["type"]
        # create時的info會包含openerTabId
        # 將action_info作為entity
        entity = action_info
        
        # 儲存到知識庫
        result = (await call_api("/v1/knowledge_base/entity", "post", entity))["result"]
        
        return {"儲存結果":{"ttt":"ccc"}}
    
    async def excerpt(self, excerpt_data:dict):
        """匯出摘錄，將摘錄訊息加上Chrome的相關資訊後傳到/excerpt端點"""
        # TODO: 也許用通用的摘錄，在需要特殊的資訊時再跟Extension要會比較簡單
        # 但前提是通用摘錄介面也有tag推薦
        
        # 建立摘錄來源視窗的節點
        web_info = {
            "title": excerpt_data["title"],
            "url": excerpt_data["url"],
        }
        web_result = await self.save_web(web_info)
        # 將Extension傳來的格式轉換成通用的摘錄格式，並加上Chrome的相關資訊
        excerpt_request = {
            "window_title": excerpt_data.pop("title"),
            "text": excerpt_data.pop("text"),
            "description": excerpt_data.pop("description"),
            "app_path": "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe", # TODO: 取得更準確的瀏覽器路徑
            "app_name": "Google Chrome",
            "tag_string": excerpt_data.pop("tag_string")
        }
        if "uuid" in web_result: # 如果前面的網頁有建立成功
            excerpt_request["from_uuid"] = web_result["uuid"]
        excerpt_request.update(excerpt_data) # 補上剩下的資訊，雖然應該沒有了
        print_var(excerpt_request)
        result = await (call_api("/excerpt", "post", excerpt_request, debug_mode=True))
        return result
    
    async def save_web(self, web_data:dict):
        """儲存網頁資訊
        return (dict): 儲存結果及UUID
        """
        web_info = {
            "name": web_data["title"],
            "title": web_data["title"],
            "url": web_data["url"],
            "type": "網頁"
        }
        if "description" in web_data.keys():
            web_info["description"] = web_data["description"]
        web_result = await (call_api("v1/knowledge_base/entity", "post", web_info))
        return web_result
from modules.knowledge_base import source
from modules.utils import call_api
from modules.debug_utils import print_var
class ChromeSource(source):
    """與Chrome Extension溝通用的模組"""
    
    def __init__(self):
        super().__init__(name="chrome")
        self.focus_tab = None
        
    async def new_triple(self, triple:dict):
        """處理分頁動作三元體"""
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
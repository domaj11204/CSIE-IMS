"""
本模組負責與知識庫相關的內容，目前主要是查詢
會用到所有知識來源，包含筆記與知識圖譜
"""

# 每個項目應該都有專屬的ID
from typing import Literal
import requests
from uuid import uuid4
from modules.utils import get_server_url, call_api
from modules.debug_utils import print_var, error
import aiohttp
class knowledge_entity(object):
    # 知識庫的基本單位，包含術語、概念、出版社等
    # 每個實體都有UUID，代表知識庫中的一個節點
    # 檢索系統使用兩種檢索分別搜尋嵌入資料庫與知識庫
    # 嵌入資料庫的metadata中包含description外，也包含URI等可存取到原始訊息的資訊
    # 知識庫本質是提供一個讀取界面
    # 儲存方面呢？
    # 將多種來源的資訊整理到知識圖譜中
        # 知識圖譜中包含非結構化資訊彼此間的關係？
        #用於檢查資料是否合法?
    def __init__(self, name, description:str=None, uuid:str=None, data:dict={}) -> None:
        from colorama import Back
        print(Back.Green + "警告，準備移除")
        self.name = name
        self.description = name if description is None else description
        self.type = "default"
        self.uuid = uuid4() if uuid is None else uuid
        self.data = data
    def get_file_list(self):
        """用於最初載入資料，資訊載入到知識庫中"""
        print("未定義如何取得檔案清單")
        return {}
    def get_data(self):
        """定義如何通過URI取得資料"""
        print("未定義如何取得此概念的資料")
        return {}
    
    def save_data(self):
        """將該實體儲存到知識圖譜中
        預設使用neo4j"""
        print("使用預設方法儲存到知識圖譜中")
        url = get_server_url()+"/neo4j/save_kb_entity"
        response = requests.post(url=url,
                                 data={
                                    "name": self.name,
                                    "type": self.type,
                                    "UUID": self.uuid,
                                    "description": self.description,
                                    "other": self.data
                                 })

            
class note(knowledge_entity):
    """用於處理筆記概念
    """
    def __init__(self, name:str=None, path:str=None) -> None:
        """初始化筆記來源(以檔案為單位)

        Args:
            name (str, optional): 代號，推薦使用檔名，預設為None
            path (str, optional): 檔案路徑，供讀取使用，預設為None
        """
        super().__init__()
        self.type = "note"
        self.name = name
        self.uri = path
        # 設定uuid
        # 儲存到知識庫中
    
    def get_data(self):
        pass

class web_page(knowledge_entity):
    def __init__(self, name:str=None, url:str=None) -> None:
        super().__init__()
        self.type = "web_page"
        self.url = url
        self.name = name
        
class paper(knowledge_entity):
    """做為知識庫基本單位的論文概念，

    Args:
        knowledge_entity (_type_): _description_
    """
    
    def __init__(self, title:str=None, information:dict=None) -> None:
        super().__init__()
        self.type = "paper"
        self.parse_information(information)
    
    def parse_information(self, information:dict):
        """從dict中解析meta data，如果為特定格式則儲存在特定key中

        Args:
            information (dict): _description_
        """
        if "format" in information.keys():
            if information["format"] == "bib":
                import bibtexparser
                
        pass

class term(knowledge_entity):
    """作為知識庫中術語的基本單位
    """
    def __init__(self, name:str, definition:str=None, context:list=[], synonyms:list=[]) -> None:
        """初始化術語
        
        Args:
            context (list): 術語的上下文、語境。例如embedded=嵌入，在NLP或機器學習的語境中。
            synonyms (list): 術語的同義詞。
        """
        super().__init__()
        self.type = "term"
        self.name = name
        self.definition = definition
    
    def get_data(self):
        return self.definition  
    
from .debug_utils import print_func_name
import requests
class source(object):
    from pydantic import BaseModel
    class split_data(BaseModel):
        entity: dict
        chunk_size: int

    def __init__(self, name, config:dict=None):
        """source模組的初始化，設定名稱與讀取設定"""
        from modules.utils import read_config
        self.name = name
        try:
            self.config = config if config != None else read_config()[self.name]
        except:
            print(f"source:{name} 沒有config")
        
    def get_data(self, **kwargs):
        """取得原始資料(不在知識庫中的資料)"""
        print("未設定如何取得資料")
        return "未設定如何取得資料"
        
    async def search(self, keyword:str, search_type:str, top_k:int, **kwargs)->list:
        """搜尋，根據不同搜尋方式呼叫不同函數
        這是所有source預設的搜尋函數
        可能回傳UUID、簡單dict等
        **kwargs: 用於傳遞其他搜尋參數，例如欄位filter
        """
        if search_type == "keyword": return (await self.keyword_search(keyword, top_k=top_k, **kwargs))
        elif search_type == "fuzzy": return (await self.fuzzy_search(keyword, top_k=top_k, **kwargs))
        else:
            print("未知的搜尋類型") 
            return []
    
    async def get_uuids(self)->list:
        error("準備棄用")
        uuids = (await call_api("/v1/knowledge_base/uuids", "get", params={"source":self.name}))["uuids"]
        return None
        return uuids
    
    async def keyword_search(self, keyword:str, top_k:int=3, type_list:list=[])->list:
        """預設的關鍵字搜尋函數，
        以知識庫中的名稱做搜尋，回傳uuids。
        TODO: 和模糊搜尋合併
        """
        from colorama import Fore
        print(Fore.GREEN+"使用預設關鍵字搜尋"+Fore.RESET)
        result_uuids = []
        # TODO: 條件中應該加上type，這會一路影響到neo4j的uuids
        # 取得該source的所有uuid
        uuids = (await call_api("/v1/knowledge_base/uuids", "get", params={"source":self.name}))["uuids"]
        name_dict = {}
        for uuid in uuids:
            name = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["名稱"]
            name_dict[uuid] = name
        # 從短到長排序
        name_dict = dict(sorted(name_dict.items(), key=lambda x: len(x[1])))
        for key, value in name_dict.items():
            # 若名稱中包含關鍵字則保留
            if keyword in value:
                result_uuids.append(key)
            if len(result_uuids) >= top_k: break
        return result_uuids
    
    async def fuzzy_search(self, keyword:str, top_k:int=3)->list:
        """預設的模糊搜尋，預設為使用QRatio搜尋知識庫的名稱欄位"""
        name_dict = {} # 用於紀錄名稱及對應的uuid
        result_uuids = [] # 用於儲存搜尋結果
        # 取得該source的所有uuid
        # TODO: 同關鍵字搜尋，應考量用type做過濾
        uuids = (await call_api("/v1/knowledge_base/uuids", "get", params={"source":self.name}))["uuids"]
        # 將uuid和對應的名稱存入搜尋用字典
        for uuid in uuids:
            name = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["名稱"]
            name_dict[uuid] = name
        
        from thefuzz.process import extract
        from thefuzz import fuzz
        # 使用QRatio模糊搜尋
        result_list = extract(keyword, name_dict, limit=top_k, scorer=fuzz.UWRatio)
        # 將uuid取出
        for result in result_list:
            result_uuids.append(result[2])
        return result_uuids
    
    def change_setting(self, setting:dict):
        """修改設定，先檢查是否存在，接著修改
        回傳該模組目前的所有設定。
        attribute優於config，若原本為int會轉成int"""
        attribute = vars(self) # https://www.geeksforgeeks.org/how-to-get-a-list-of-class-attributes-in-python/
        # 先檢查是否有不合法的key
        for key in setting.keys():
            if key not in attribute and key not in self.config:
                return {"result": "錯誤，不合法的key"}
        for key in setting.keys():
            if key in attribute:
                if type(getattr(self, key)) == int:
                    setting[key] = int(setting[key])
                setattr(self, key, setting[key])
            if key in self.config:
                if type(self.config[key]) == int:
                    setting[key] = int(setting[key])
                self.config[key] = setting[key]
        return {"result": vars(self)}
        
    def split_preprocess(self, split_data:split_data):
        """切割資料前處理，解析split_data
        """
        # 決策: 不知道有沒有更好的傳資料方法。理論上應該要用self的，但這些資訊並不是一個source物件應該儲存的，但把每個chunk都實例出一個物件又很怪
        # 一個spliter只用一次，好怪好怪
        entity = split_data.entity
        chunk_size = split_data.chunk_size
        text = entity["data"]
        parent_uuid = entity["UUID"]
        parent_name = entity["名稱"]
        parent_source = entity["source"]
        return entity, chunk_size, text, parent_uuid, parent_name, parent_source
    
    def split(self, split_data:split_data):
        """將資料切割成指定大小的chunk
        """
        # FIXME: 未完成
        print_var(split_data)
        entity, chunk_size, text, parent_uuid, parent_name, parent_source = self.split_preprocess(split_data)
        if len(text) == 0:
            return []
        split_result = [] 
        # 字分割器
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from uuid import uuid4
        from hashlib import md5
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=0
        )
        char_split_contents = text_splitter.split_text(text)
        for index in range(len(char_split_contents)):
            char_split_content = char_split_contents[index]
            # 儲存到知識庫中的資料
            uuid = str(uuid4())
            # TODO: relation有改過，這邊可能會出問題
            char_split_entity = {
                    "name": parent_name + "_" + str(index),
                    "description": parent_name + "_" + str(index),
                    "uuid": uuid,
                    "data_hash": md5(char_split_content.encode()).hexdigest(),
                    "relation": [{"uuid1":uuid, "uuid2":parent_uuid, "relation":"屬於", "properties":{"chunk_size":chunk_size}}],
                    "type": "chunk",
                }
            metadata = {}
            metadata["uuid"] = uuid
            metadata["parent_source"] = entity["source"]
            metadata["parent_type"] = entity["type"]               
            split_result.append({"entity": char_split_entity,"document":char_split_content, "metadata":metadata})
        return split_result
    
    async def reference_string(self, reference_data:dict):
        """預設的渲染參考資料方法，會找source取得該chunk所屬parent的url"""
        from modules.utils import get_server_url
        uuid = reference_data["parent_uuid"]
        url = get_server_url() + f"/v1/knowledge_base/url/{uuid}"
        name = (await call_api(f"v1/knowledge_base/{uuid}", "get"))["info"]["名稱"]
        return f"參考資料:<a href=\"{url}\" target=\"_blank\">{name}</a>\n"
    
    async def get_url(self, uuid:str=None, **kwargs):
        if "path" in kwargs:
            path = kwargs["path"]
        else:
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["path"]
        if "://" in path:
            return path
        else:
            from modules.utils import convert_to_absolute_uri
            return "file://" + convert_to_absolute_uri(path)
    
class knowledge_base(object):
    """知識庫，用於整合各種知識來源，用於呼叫搜尋、讀檔等基本功能
    藉由fastapi提供給RAG或使用者直接使用
    TODO: 讀檔
    TODO: 看能不能想辦法強制繼承的類別要實際某些方法
    """
    def __init__(self, config:dict=None):
        self.config = config
        if config == None:
            from .utils import read_config
            self.config = read_config()["knowledge_base"]
        self.source_list = []
        self.db = self.config["db"] if "db" in self.config.keys() else "neo4j"
        self.user_name = self.config["user_name"] if "user_name" in self.config.keys() else "預設"
    
    async def db_status(self):
        """取得知識庫狀態
        """
        from modules.utils import call_api
        if self.db == "neo4j":
            # 非同步請求，否則會造成伺服器卡死
            result = await call_api(f"/v1/{self.db}", "post")
            result = await call_api(f"/v1/{self.db}", "get")
            print("kb.py:result:", result)
            if result["status"] != "未初始化":
                return {"status": "正常"}
            else: return result
        else:
            return {"status": "未知的知識庫資料庫"}
        
    @print_func_name
    async def search(self, keyword:str, search_type:str, source_list:list=[], type_list:list=[], top_k:int=3)->list:
        """通過關鍵字搜尋知識庫，回傳UUID清單並簡單渲染結果
        TODO: 可以優化成查詢時直接取得名稱
        FIXME: 使用API或外部知識時不會取得UUID
        TODO: 可能會出現搜尋到的資料不存在知識庫中的情況?
        """
        print_var(source_list)
        uuids = []
        result_str = "查詢結果:\n"
        # TODO: 目前是將type轉source，應該有更乾脆的做法
        for type in type_list:
            if len(type) > 0:
                source_list.extend(self.get_source_by_type(type))
        print_var(source_list)
        source_list = list(set(source_list))
        for source in source_list:
            source_search_result = await call_api(f"v1/{source}/search", 
                                               "get", 
                                               params={"keyword":keyword, 
                                                       "search_type": search_type, 
                                                       "top_k":top_k, 
                                                       "type_list":",".join(type_list)},
                                               debug_mode=True)
            if "uuids" in source_search_result.keys():
                uuids.extend(source_search_result["uuids"])
            else:
                result_str += source_search_result["result"] + "\n"
        from modules.utils import get_server_url
        for uuid in uuids:
            url = get_server_url() + f"/v1/knowledge_base/url/{uuid}"
            name = (await call_api(f"v1/{self.db}/{uuid}", "get"))["data"]["名稱"]
            result_str += f"<a href=\"{url}\" target=\"_blank\">{name}</a>\n"
        return result_str
    
    async def get_data(self, uuid:str):
        """根據UUID取得原始資料。"""
        source = (await call_api(f"v1/{self.db}/{uuid}", "get"))["data"]["source"]
        result = await call_api(f"v1/{source}/data/{uuid}", "get")
        return result

    async def get_info(self, uuid:str):
        """根據UUID取得簡單的資訊
        """
        from modules.utils import call_api
        info = (await call_api(f"v1/{self.db}/{uuid}", "get"))["data"]
        return info
    
    async def delete_uuid(self, uuid:str):
        result = await call_api(f"v1/{self.db}/{uuid}", "delete")["data"]
        return result
            
    async def get_entity(self, uuid:str):
        """根據UUID取得完整實體"""
        # 先取得知識庫中的相關資訊
        simple_result = (await self.get_info(uuid))
        # 嘗試取得完整資訊
        try:
            if simple_result["type"] == "chunk":
                data = (await call_api(f"v1/rag/vectordb/{uuid}", "get"))["data"]
            else:
                source = simple_result["source"]
                data = (await call_api(f"v1/{source}/data/{uuid}", "get", params=simple_result))["data"]
        except:
            # TODO: 改成回傳錯誤訊息而不是直接中斷
            raise
        simple_result["data"] = data
        return simple_result
    
    async def get_entity_count(self, source:str=None, type:str=None):
        """取得知識庫中的實體數量
        """
        # FIXME: 準備刪除測試用筆記
        if type == "筆記":
            type = "測試用筆記"
        if source is not None:
            result = await call_api(f"v1/{self.db}/entity_count", "get", params={"source": source})
        if type is not None:
            result = await call_api(f"v1/{self.db}/entity_count", "get", params={"type": type})
        return result

    @staticmethod
    def add_term(term, path:str|None, abstract:str|None, description:str|None)->bool:
        """新增術語到知識庫
        TODO: 目前寫死到obsidian，之後再改成可以選擇
        """
        # 呼叫obsidian的筆記api
        try:
            import requests
            response = requests.post(
                "http://localhost:27711/obsidian/note",
                json={
                    "title": term,
                    "tags":["術語"],
                    "description": description,
                    "abstract": abstract
                }
            )
            if response.status_code == 201:
                return True
            else:
                print("kb:新增術語失敗", response.status_code, response.text)
                return False
        except:
            return False
        
    async def add_excerpt(self, excerpt_data:dict):
        """新增摘錄到知識庫
        return (dict): 儲存的結果，若成功則包含uuid
        """
        # 先直接存成實體
        try:
            entity = excerpt_data.copy()
            entity["type"] = "摘錄"
            entity["name"] = "摘錄自" + entity.pop("window_title")
            if "text" in entity.keys(): # 如果有text代表是有內容的摘錄，而不是純粹的網頁摘錄
                entity["摘錄"] = entity.pop("text")
            result = await self.add_entity(entity) # 新增到實體
            if result["result"] == "新增失敗":
                return "失敗"
            if "tag_string" in entity.keys():
                import re
                tag_list = re.split(r"[, ]",entity.pop("tag_string"))
                for tag in tag_list:
                    if len(tag) == 0: continue
                    tag_uuid = await(self.add_tag(tag))
                    await call_api(f"v1/{self.db}/relation", "post", {"uuid1":result["uuid"], "uuid2":tag_uuid, "relation":"有標籤"})
                
            if "from_uuid" in excerpt_data.keys():
                # 已經有摘錄來源的uuid，包含視窗、論文、網頁等
                parent_uuid = excerpt_data["from_uuid"]
            else: # 沒有附摘錄來源的uuid，以視窗標題為關鍵字搜尋
                # TODO: 但這樣做會搜尋到自己，必須想辦法避免
                # 也許可以直接新增一個視窗資訊?
                parent_name = entity["name"].replace("摘錄自", "") # 取得原始視窗標題
                # 根據視窗標題找到該uuid
                parent_uuid = (await call_api(f"v1/{self.db}/search", "get", params={"keyword":parent_name, "search_type":"keyword"}))["result"][0]
            # 儲存摘錄關係
            relation_result = await call_api(f"v1/{self.db}/relation", "post", {"uuid1":result["uuid"], "uuid2":parent_uuid, "relation":"摘錄自"})
            return {"result": "儲存成功",
                    "uuid": result["uuid"]}
            
        except Exception as e:
            print("knowledgebase新增摘錄失敗:", e)
            return "失敗"
    async def load_data(self, source:str, type_str:str):
        # FIXME: 需要調整type
        print(f"source:{source}, type_str:{type_str}")
        # TODO: 檔案清單太侷限，考慮改成實體清單
        
        # 先試試看來源有沒有支援entity的載入
        entity_result = await call_api(f"v1/{source}/load/entity", "get")
        if "錯誤" not in entity_result.keys():
            result = []
            for entity in entity_result["entities"]:
                entity["uuid"] = str(uuid4())
                await self.add_entity(entity)
                result.append({"name":entity["name"], "uuid":entity["uuid"]})    
            return result
        
        # 舊做法，應棄用
        else:
            file_list = (await call_api(f"v1/{source}/file_list", "get"))["file_list"]
            
            result = []
            for file in file_list:
                print("file:", file)
                entity = file
                # file_path = file["path"]
                # file_content = await call_api(f"v1/{source}/data/{file_path}", "get")
                # file_content = file_content["result"]
                entity["uuid"] = str(uuid4())
                entity["source"] = source
                # entity["type"] = type_str
                
                await self.add_entity(entity) # "description": file_content好像沒啥用
                result.append({"name":file["name"], "uuid":uuid})
            return result
    
    async def add_entity(self, entity:dict):
        """新增實體到知識庫
        包含摘錄等實體
        注意: entity中不能使用data作為key
        return: 新增結果，包含結果說明"result"及新增的"uuid"
        """
        print("收到的entity:", entity)
        # FIXME: 怪問題，暫時先這樣解決
        if "entity" in entity:
            print("錯誤!")
            entity = entity["entity"]
        # entity檢查及前處理
        # TODO: 這個data是其他資料的意思，但這樣命名會和一般的data稿混
        # if "data" in entity.keys(): return {"result": "失敗", "description":"entity中不能包含key: data"}
        if "name" not in entity.keys(): return {"result": "失敗", "description":"缺少name"}
        if "uuid" not in entity.keys(): entity["uuid"] = str(uuid4())
        if "type" not in entity.keys(): entity["type"] = "default"
        if "筆記" in entity["type"]: entity["type"] = "測試用筆記" # 測試用
        if "description" not in entity.keys(): entity["description"] = entity["name"]
        if "founder" not in entity.keys(): entity["founder"] = self.user_name
        # 用於檢查資料是否有更新，未實作完成
        # if "data_hash" not in entity.keys():
        #     from hashlib import md5
        #     data_info = (await call_api(f"v1/{entity['source']}/data/", "get"))["result"]
        #     if data_info not in entity.keys():
        #         print("無法取得data")
        #         entity["data_hash"] = md5(entity["description"].encode()).hexdigest()
        #     else:
        #         info = entity[data_info]
        #         source = entity["source"]
        #         data = (await call_api(f"v1/{source}/data/{data_info}/{info}", "get"))["data"]
        #         entity["data_hash"] = md5(str(data).encode()).hexdigest()
        
        # 改成不需要特別把data獨立出來      
        # entity["data"] = {}
        # key_list = list(entity.keys())
        # for key in key_list:
        #     if key not in ["name", "uuid", "type", "description", "relation", "data", "data_hash"]:
        #         entity["data"][key] = entity[key]
        #         del entity[key]
        print("knowledge_base.py:處理後的entity:", entity)
        # 檢查資料庫狀態
        result = await call_api(f"/v1/{self.db}", "get")
        if "status" not in result or result["status"] != "正常":
            # 若資料庫狀態錯誤則嘗試開啟
            print("嘗試開啟資料庫...")
            # TODO: 若網路不穩可能會斷線，要想辦法處理
            await call_api(f"/v1/{self.db}", "post")
        
        # 新增實體
        result = await call_api(f"v1/{self.db}/entity", "post", entity)
        print(result)
        # 嵌入實體
        # TODO: 若uuid未嵌入則需要嵌入? 但切割後parent也不再嵌入資料庫中
        return {"result": result["result"],
                "uuid": result["uuid"]}
    
    async def add_relation(self, uuid1:str, uuid2:str, relation:str, property:dict={}):
        """新增關係到知識庫
        TODO: 如何檢查、處理已存在的relation
        """
        result = (await call_api(f"v1/{self.db}/relation", "post", {
            "uuid1":uuid1, 
            "uuid2":uuid2, 
            "relation":relation, 
            "property":property}))["result"]
        return result
    
    async def get_latest_entity(self, top_k:int=1):
        """取得最新的實體，用於測試"""
        latest_entity_list = (await call_api(f"/v1/{self.db}/entity", "get", params={"top_k":top_k}))["latest_entity"]
        return latest_entity_list
    
    def get_source_by_type(self, type)->list:
        """根據類型判斷實際來源
        """
        source_list = []
        for key, value in self.config["type"].items():
            if key == type:
                source_list.append(value)
        return source_list
    
    def get_type_by_source(self, source)->list:
        type_list = []
        for key, value in self.config["type"].items():
            if value == source:
                type_list.append(key)
        return type_list
    
    async def indexing(self, source:str=None, type:str=None):
        """將該類型已載入的資料嵌入
        """
        from modules.debug_utils import print_var
        print_var(source)
        print_var(type)
        uuid_list = (await self.get_uuids(source=source, type=type))
        from modules.utils import call_api
        # 將uuid交給rag處理
        result = await call_api(f"v1/rag/indexing", "post", {"uuids":uuid_list})
        print(result)
        return {"result": len(result["result"])}
    
    async def delete_indexing(self, source:str=None, type:str=None):
        """將該類型或來源的index刪除
        """
        if source == None:
            source = self.get_source_by_type(type)
        from modules.utils import call_api
        result = await call_api(f"v1/rag/indexing", "delete", {"source": source, "type": type})
        return {"result": len(result["result"])}

    async def test(self):
        from modules.utils import call_api
        result = await call_api("/v1/knowledge_base/indexing", "post", params={"source":"obsidian"})
        print("knowledge_base:result:", result)
    
    async def get_uuids(self, 
                        source:str=None, 
                        type:str=None, 
                        keyword:str=None, 
                        search_type:str=None, 
                        source_list:list=None, 
                        type_list:list=None, 
                        top_k:int=None)->list:
        """根據來源取得所有UUID
        TODO: 應該讓來源、類型、關鍵字能同時作用
        TODO: 不存在的來源或類型可以有額外的結果訊息
        FIXME: 型態可以精簡，在某些情況下應該可以直接用source_list來取代source
        """
        # 有關鍵字就呼叫搜尋函數
        if keyword is not None:
            uuids = (await self.search(keyword=keyword, search_type=search_type, source_list=source_list, type_list=type_list, top_k=top_k))["uuids"]
        # 否則用來源或類型過濾
        if source is not None:
            uuids = (await call_api(f"/v1/{self.db}/uuids", "get", params={"source": source}))["uuids"]
        else:
            uuids = (await call_api(f"/v1/{self.db}/uuids", "get", params={"type": type}))["uuids"]
        return uuids
    
    async def get_url(self, uuid):
        """從source取得開啟該uuid的url"""
        # 取得基本資訊
        info = await self.get_info(uuid)
        # 從資訊中挑出來源
        source = info["source"]
        # 取得url轉換時必要的資訊
        need_info = (await call_api(f"/v1/{source}/data", "get"))["result"]
        # 從基本資訊終將必要資訊拿出來
        uuid_info = info[need_info]
        url = (await call_api(f"/v1/{source}/url/{uuid}", "get", params={need_info:uuid_info}))["url"]
        return url
    
    async def get_relation(self, uuid:str, depth:int=1):
        """取得對應深度為1的相關資料"""
        #TODO: 支援1以外的自訂深度，但是如何顯示?
        from modules.utils import call_api
        result = (await call_api(f"/v1/{self.db}/relations/{uuid}", "get"))["relations"]
        return result
    
    async def get_tag_list(self):
        """從知識庫取得所有tag"""
        tags = (await call_api(f"/v1/{self.db}/tag", "get"))["tags"]
        return tags
    
    async def add_tag(self, tag:str)->str:
        """新增tag到知識庫並回傳該UUID，若已存在則僅回傳UUID
        return (str): tag的UUID
        """
        tag_entity = {
            "name": tag,
            "type": "標籤",
            "uuid": str(uuid4())
        }
        uuid = (await call_api(f"/v1/{self.db}/entity", "post", tag_entity, debug_mode=True))["uuid"]
        return uuid
        
        
                                   
if __name__ == "__main__":
    import asyncio
    kb_obj = knowledge_base()
    asyncio.run(kb_obj.test())
    # print(kb_obj.get_source_by_type("term"))
    # from modules.utils import call_api
    # print(call_api("/v1/neo4j", "get"))
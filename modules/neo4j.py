"""
處理此系統和neo4j的溝通函數
預期功能:
    1. 確認DB連線
    2. 取得特定節點的資訊
    3. 自訂查詢
    4. 新增網頁節點
    5. 新增摘錄節點
    6. 新增文獻節點
    7. 匯入其他知識圖譜
"""
from neo4j import GraphDatabase, Result
from neo4j.time import DateTime
import time
import re
from dataclasses import dataclass
from neo4j.exceptions import DriverError, Neo4jError
import logging
from modules.debug_utils import print_func_name, print_var

@dataclass
class pageStruct:
    id: str
    url: str
    title: str
    
class neo4jDB(object):

    def __init__(self, uri, user, password, database=None, RNSUser="defaultUser"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        self.RNSUser = RNSUser
        self.name = "Neo4j"
    def close(self):
        self.driver.close()

    def test(self, message=""):
        if message=="":
            message = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        with self.driver.session() as session:
            greeting = session.execute_write(self._create_and_return_greeting, message)
            print(greeting)
    
    def cypher_test(self, cypher:str):
        result = self.driver.execute_query(query_=cypher, result_transformer_=lambda res: res.to_df(True, True))
        print(result)
        return result
    
    def cypher_to_df(self, cypher:str, parameter:dict=None):
        # 若有多筆結果可能會出現nan，可以用pandas.isna判斷
        result = self.driver.execute_query(query_=cypher, parameters_=parameter, result_transformer_=lambda res: res.to_df(True, True))
        return result
    
    def cypher(self, cypher:str, parameter:dict=None):
        result = self.driver.execute_query(query_=cypher, parameters_=parameter)
        return result

    def get_graph_information(self):
        query="""
        CALL apoc.schema.nodes()        
        """
        records, summary, keys = self.driver.execute_query(query, database_="neo4j")
        for record in records:
            print(record.get("name"), record.get("properties"))
            
        return records
    
    def _create_and_return_web(self, page:pageStruct):
        """根據給定的pageStruct建立網頁節點

        Args:
            page (pageStruct): 網頁結構

        Returns:
            _type_: 無
        """
            # To learn more about the Cypher syntax,
            # see https://neo4j.com/docs/cypher-manual/current/

            # The Cheat Sheet is also a good resource for keywords,
            # see https://neo4j.com/docs/cypher-cheat-sheet/

        query = (
            "CREATE (p1:WebPage { name: $pageName }) "
            "RETURN p1.name"
        )
        try:
            record = self.driver.execute_query(
                query, pageName = page.title,
                database_=self.database,
                result_transformer_=lambda r: r.single(strict=True)
            )
            return {"p1": record["p1.name"]}
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            raise
            
    def createWebFullInfo(self, page:pageStruct, description="", tag_list=[]):
        """
        根據網頁資訊建立網站及網頁節點。
        description及tag_list是可選的。
        """
        # prurl = page.url.replace("https:","").replace("http:","")
        # prurlChecker = re.compile(r"^//")
        # domainChecker = re.compile(r"//[^/]*/")
        print("tag_list:", tag_list)
        pathList = page.url.split("/") # 切開後的url
        if ( pathList[0] == "" or pathList[1] != "" or pathList[2] == "" ):
            logging.error("url解析錯誤，url:"+ page.url)
        protocol = pathList[0]
        domain = pathList[2]
        domainURL = pathList[0] + "//" + pathList[2]
        path = "/".join(pathList[3:])
        query = ""
        if description != "":
            query = """
                        MERGE (p0:`網站`{ url:$domainURL, domain:$domain })
                        MERGE (p1:`網頁`{url:$url, path:$path, 標題:$title})
                        ON CREATE SET p1.`建立時間`=localdatetime.realtime(\"+08:00\"), p1.`建立者`=$user, p1.`path`=$path, p1.`標題`=$title, p1.`描述`=$description
                        ON MATCH SET p1.`描述`= p1.`描述`+'\\nnew:'+$description, p1.`修改時間`=localdatetime.realtime(\"+08:00\")
                        MERGE (p0) - [:`有子網頁`] -> (p1)                  
                        RETURN p1
                    """
        else:
            query = """
                        MERGE (p0:`網站`{ url:$domainURL, domain:$domain })
                        MERGE (p1:`網頁`{url:$url})
                        ON CREATE SET p1.`建立時間`= localdatetime.realtime(\"+08:00\"), p1.`建立者`=$user, p1.`path`=$path, p1.`標題`=$title, p1.`描述`=''
                        MERGE (p0) - [:`有子網頁`] -> (p1)                   
                        RETURN p1
                    """
        logging.debug(f"query:{query}")
                
        '''
        # 考慮將所有path都建立成獨立節點
        nowURL = domainURL
        nodeOrder = 1 # 用於建立node的編號
        for index in range(len(pathList)):
            if len(nowWeb) == 0:
                break
            if (nowURL is None):
                query += f"MERGE (p{webOrder}:`網站`{{url:{nowWeb}, path:{nowWeb}}})"
                nowURL = nowWeb
                continue
            nowURL += "/" + nowWeb
            if (webOrder == len(webList) - 1):
                query += f"MERGE (p{webOrder}:`子網站`{{url:{nowURL}, path:{}}}) \
                            MERGE (p{webOrder-1}) - [:`有子網站`] -> (p{webOrder})"   
            else:
                query += f"MERGE (p{webOrder}:`子網站`{{url:{nowURL}}}) \
                            MERGE (p{webOrder-1}) - [:`有子網站`] -> (p{webOrder})"
            webOrder += 1
        '''

        try:
            record = self.driver.execute_query(
                query,
                database_=self.database,
                domain = domain, domainURL = domainURL, url = page.url, path=path, title=page.title, description=description,
                user = self.RNSUser,
                result_transformer_=lambda r: r.single(strict=True)
            )
            logging.debug(f"query record:{record}")
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

        # 新增標籤
        if len(tag_list) == 0:
            return
        query = """
            UNWIND $tag_list AS tag
            MERGE (WebPage:`網頁`{ url:$url })
            MERGE (Tag:`標籤`{ name:tag })
            ON CREATE SET Tag.`UUID`=randomUUID()
            MERGE (WebPage) - [:`有標籤`] -> (Tag)
        """
        try:
            record = self.driver.execute_query(
                query,
                tag_list = tag_list,
                url = page.url,
                database_=self.database
            )
            logging.debug(f"query record:{record}")
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

    def excerptFromTriple(self, returnJson:dict, tag_list=[], app_name="", app_path="", app_title=""):
        """
        根據triple產生摘錄節點。
        在這之前會先建立網站和網頁節點。
        不考慮摘錄重複的情況。

        Args:
            returnJson (dict): 摘錄的相關triple
        TODO: app_title相關資訊未完成
        """
        # 父節點相關query
        parent_query = ""
        if app_name != "":
            # 如果父節點是app，相關應用可能只有在虛擬環境會用到，但總之先存著
            parent_query = """
                MERGE (exe:`應用程式` { name: $app_name, path: $app_path })
                MERGE (parent:`軟體` { name: $app_name })
                MERGE (parent) - [:`有路徑`] -> (exe)
            """
        else:
            # 父節點是網頁
            parent_query = """
                MATCH (parent:`網頁` { url: $url })            
            """
        # 組合成完整的query
        query = parent_query + """  
            MERGE (p0:`摘錄` { text: $excerptText, `描述`: $description })
            MERGE (p0) - [:`來自`] -> (parent)
            MERGE (parent) - [:`有摘錄`]-> (p0)
            SET p0 += {`建立時間`:localdatetime.realtime(\"+08:00\"), `建立者`:$user}
            RETURN p0
        """
        logging.debug(f"query:{query}")
        
        try:
            record = self.driver.execute_query(
                query, 
                url=returnJson["object"].get("tabURL", ""), 
                excerptText = returnJson["subject"].get("text", ""), 
                description = returnJson["subject"]["description"], 
                app_name = app_name,
                app_path = app_path,
                user = self.RNSUser,
                database_=self.database,
                result_transformer_=lambda r: r.single(strict=True)
            )
            logging.debug(f"query record:{record}")
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

        # 處理標籤相關
        if len(tag_list) == 0:
            return
        query = """
            UNWIND $tag_list AS tag
            MERGE (p0:`摘錄` { text: $excerptText })
            MERGE (p2:`標籤` { name: tag})
            MERGE (p0) - [:`有標籤`]-> (p2)
        """
        logging.debug(f"query:{query}")
        try:
            record = self.driver.execute_query(
                query, excerptText = returnJson["subject"]["text"], 
                tag_list = tag_list,
                database_=self.database,
            )
            logging.debug(f"query record:{record}")
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

    def search(self, keyword:str="", field:str="名稱", label:str=None, returnProperties=["name"], top_k=10, type_list:list=["摘錄"]):
        """查詢節點，以list回傳
        Args:
            label (str): 標籤名(optional)
        """
        if type_list is None: # 例外處理，但這樣寫有點醜，實際應該寫在通用性更好的地方
            type_list = []
        # 這部分可以寫成，有需要的回傳屬性P都轉成n.P AS P，接在RETURN後面
        # 有需要的話再做
        query = ""
        if label != None:
            # Neo4j查詢中的label問題，見https://community.neo4j.com/t/having-a-label-as-a-parameter-in-a-cypher-query-efficiently/26555/4
            temp = label
            label = label.replace('`', '\'').replace(';', '_') # 防止注入
            print(f"label: {temp} -> {label}")
            query += f"""MATCH (n:`{label}`)"""
        elif len(type_list) > 0: # 若有要求type_list，則使用Cypher的label來過濾
            query += f"""MATCH (n:"""
            for type in type_list:
                query += f"""`{type}`|"""
            query = query[:-1] + ") "
        else:
            query += "MATCH (n) "
        if keyword != "":
            keyword = keyword.replace('`', '\'').replace(';', '_') # 防止注入
            query += f""" WHERE n.`{field}` CONTAINS '{keyword}'"""
    
        query += " RETURN n.UUID AS UUID, n.名稱 AS name"
        query += f""" ORDER BY size(n.`{field}`) ASC """
        query += f""" LIMIT {top_k}"""
        try:
            records, summary, keys= self.driver.execute_query(
                query, 
                database_=self.database# ,
                # result_transformer_=lambda r: r.value("properties")
            )
            logging.debug(f"query:{summary.query}")
            logging.debug(f"query record:{records}")
            
            # 這部分也是可以根據要求的回傳屬性P做處理，目前先包成list+dict
            recordList = []
            # print("record:", records)
            for record in records:
                recordList.append(record.value())
                # print("key:", record.keys())
                # print("1:", record.value())
            return recordList
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

    @staticmethod # 如果沒加上這個，就會自動傳入self
    def records_to_df(records:list, key="n"):
        """將neo4j driver回傳的record轉成dict
        僅用於轉換，因此使用staticmethod，綁訂於類別而不須實例化
        TODO: 目前僅考慮回傳一個field的情況(key=n並沒有作用)
        Args:
            record_list (list): _description_
        """
        result_list = []
        print("records: ", records)
        for record in records:
            print("record: ", record.keys())
            print(record[0])
            record_dict = {}
            for node_key in record[0].keys():
                if node_key != "建立時間" and node_key != "修改時間":
                    record_dict[node_key] = record[key][node_key]
                else:
                    record_dict[node_key] = str(record[key][node_key])
            result_list.append(record_dict)
        return result_list   

    def get_latest_node(self, label:str=None, num_node=10):
        """列出該label下最新新增的node

        Args:
            label (str): 標籤名(optional)
        """
        # 這部分可以寫成，有需要的回傳屬性P都轉成n.P AS P，接在RETURN後面
        # 有需要的話再做
        if label != None:
            query = ("""MATCH (n:`$label`)
                        WHERE n.`建立時間` IS NOT NULL
                        RETURN n
                        ORDER BY n.`建立時間` DESC
                        LIMIT $num""")
            
        else:
            query = ("""  MATCH (n)
                        WHERE n.`建立時間` IS NOT NULL
                        RETURN n
                        ORDER BY n.`建立時間` DESC
                        LIMIT $num""")
        logging.debug(f"query:{query}")
        ## 查詢最新的三筆摘錄
        try:
            records, summary, keys= self.driver.execute_query(
                query, 
                database_=self.database, #
                label=label,
                num=num_node
                # result_transformer_=lambda r: r.value("properties")
            )
            logging.debug(f"query record:{records}")
            return records
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise

    def create_entity(self, label:str, name:str, uuid:str, description:str, **kwargs):
        """新增節點

        Args:
            label (str): 標籤名
            name (str): 節點名
            uuid (str): entiry uuid
            description (str): 描述
            **kwargs: 其他資訊.
        """
        params = {"名稱": name, "UUID": uuid, "描述": description}
        params.update(kwargs)
        print_var(params)
        # 建構cypher
        cypher = f"CREATE (n:`{label}` {{"
        cypher += ", ".join([f"`{key}`: $`{key}`" for key in params.keys()])
        cypher += f", `建立時間`: localdatetime.realtime('+08:00')"
        cypher += "}) RETURN n"
        
        logging.debug(f"query:{cypher}")
        # 新的寫法，可以解決execute query出現的問題
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run(cypher, parameters=params)
                records = [record["n"] for record in result]
                logging.debug(f"Query records: {records}")
                return records
            except Neo4jError as e:
                logging.error(f"Query failed: {cypher}", exc_info=True)
                logging.error(f"Parameters used: {params}", exc_info=True)
                raise
    def create_relation(self, relation:dict):
        """新增關係
        relation (dict): {"uuid1":"頭uuid", "uuid2":"尾uuid", "relation":"關係名", "properties":dict}
        return (dict): depth1的關係
        """
        relation_name = relation["relation"]
        # TODO: 如果有關係屬性要做的處理，未測試
        property_str = ""
        if "property" in relation and len(relation["property"])>0:
            property_str = ", ".join([f"`{key}`: ${key}" for key in relation["property"].keys()])
            relation.update(relation["property"])
        if "建立時間" not in relation:
            property_str += "`建立時間`: localdatetime.realtime('+08:00')"
        # else: property_str = ""
        cypher = f"MATCH (n), (m) WHERE n.UUID = $uuid1 AND m.UUID = $uuid2 CREATE (n)-[:`{relation_name}`{{{property_str}}}]->(m) RETURN n, m"
        # params = {
        #     "uuid1":relation["uuid1"],
        #     "uuid2":relation["uuid2"],
        # }
        logging.debug(f"query:{cypher}")
        with self.driver.session(database=self.database) as session:
            try:
                result = session.run(cypher, parameters=relation)
                records = [record["n"] for record in result]
                logging.debug(f"Query records: {records}")
                return records
            except Neo4jError as e:
                logging.error(f"Query failed: {cypher}", exc_info=True)
                logging.error(f"Parameters used: {relation}", exc_info=True)
                raise
    
    def get_by_uuid(self, uuid:str):
        """根據uuid取得節點資訊
        Args:
            uuid (str): entity uuid
        """
        query = f"""MATCH (n) WHERE n.UUID = '{uuid}' RETURN n"""
        logging.debug(f"query:{query}")
        try:
            records, summary, keys= self.driver.execute_query(
                query, 
                database_=self.database, #
                uuid=uuid
                # result_transformer_=lambda r: r.value("properties")
            )
            logging.debug(f"query record:{records}")
            if len(records) == 0:
                return {}
            result_dict = dict(records[0]["n"])
            result_dict["type"] = list(records[0]["n"].labels)[0]
            return result_dict
        # Capture any errors along with the query and data for traceability
        except (DriverError, Neo4jError) as exception:
            print("%s raised an error: \n%s", query, exception)
            logging.error(f"{query} raised an error: \n{exception}")
            raise
    
    def pretty_print(self, relation_result):
        from modules.debug_utils import print_var
        pretty_str = ""
        for relation in relation_result:
            # print_var(relation)
            from_name = relation["from"]["name"] if "name" in relation["from"] else relation["from"]["名稱"]
            to_name = relation["to"]["name"] if "name" in relation["to"] else relation["to"]["名稱"]
            # print(f"{from_name} - [{relation['r']['type']}] -> {to_name}")
            pretty_str += f"{from_name} - [{relation['r']['type']}] -> {to_name}\n"
        return pretty_str
            
    def get_depth1(self, uuid:str):
        """取得該節點的depth1關係"""
        from pandas import isna
        query_out = f"MATCH (n)-[r]->(m) WHERE n.UUID = '{uuid}' RETURN n, r, m"
        result_out_dict = self.cypher_to_df(query_out).to_dict(orient="records")
        query_in = f"MATCH (n)<-[r]-(m) WHERE n.UUID = '{uuid}' RETURN n, r, m"
        result_in_dict = self.cypher_to_df(query_in).to_dict(orient="records")
        # from modules.debug_utils import print_var
        # print_var(result_out)
        result_list = []
        
        for record in result_out_dict:
            result = {"from":{}, "to":{}, "r":{}}
            result["from"].update({"type":list(record["n().labels"])[0]})
            result["to"].update({"type":list(record["m().labels"])[0]})
            for key in record.keys():
                if record[key] == None or isna(record[key]):
                    continue
                if type(record[key]) == DateTime:
                    record[key] = str(record[key])
                if "n().prop" in key:
                    prop_name = key.split(".")[-1]
                    value = record[key]
                    result["from"].update({prop_name:value})
                if "m().prop" in key:
                    prop_name = key.split(".")[-1]
                    value = record[key]
                    result["to"].update({prop_name:value})
                if key == "r->.type":
                    result["r"]["type"] = record[key]
            result_list.append(result)
            
        for record in result_in_dict:
            result = {"from":{}, "to":{}, "r":{}}
            result["from"].update({"type":list(record["n().labels"])[0]})
            result["to"].update({"type":list(record["m().labels"])[0]})
            for key in record.keys():
                if record[key] == None or isna(record[key]):
                    continue
                if "n().prop" in key:
                    prop_name = key.split(".")[-1]
                    value = record[key]
                    result["to"].update({prop_name:value})
                if "m().prop" in key:
                    prop_name = key.split(".")[-1]
                    value = record[key]
                    result["from"].update({prop_name:value})
                if key == "r->.type":
                    result["r"]["type"] = record[key]
            result_list.append(result)
        self.pretty_print(result_list)
        return result_list
        
from modules.knowledge_base import source
class neo4j_source(source):
    """管理Neo4j資料來源
    特殊內容：標籤等知識庫
    """
    def __init__(self, name: str = "neo4j", config: dict = None) -> None:
        super().__init__(name="neo4j", config=config)
        
        # TODO: Neo4j金鑰隱私問題
        # 連線到Neo4j Server
        self.server_url = self.config["url"]
        self.server_user = self.config["user"]
        self.server_password = self.config["password"]
        self.DB = neo4jDB(self.config["url"], self.config["user"], self.config["password"], "neo4j")

    async def get_data(self, uuid:str):
        """根據uuid取得資訊"""
        data = self.DB.get_by_uuid(uuid=uuid)
        
        # FastAPI不接受Neo4j的時間格式，通過轉成str暫時解決
        for key, value in data.items():
            if type(value) == DateTime:
                data[key] = str(value)
        return data
    
    async def get_latest_entity(self, top_k:int=1):
        """取得最新的entity"""
        result = self.DB.get_latest_node(num_node=top_k)
        return result
        
    async def get_entity_count(self, type:str=None, **kwargs)->int:
        """根據Type等條件過濾節點並計算數量
        """
        # 允許除了type以外的過濾條件，為了避免出錯過濾None的情況
        kwargs = {key:value for key, value in kwargs.items() if value != None}
        if type != None: cypher_match = f"MATCH (n:{type}) " 
        else:            cypher_match = f"MATCH (n) "
        if len(kwargs) != 0:
            cypher_where = "WHERE " + " AND ".join([f"n.{key} = ${key}" for key in kwargs])
        else:
            cypher_where = ""
        cypher = f"{cypher_match} {cypher_where} RETURN count(n)"
        result_df = self.DB.cypher_to_df(cypher, kwargs)
        return int(result_df.iloc[0, 0])
    
    def split(self, split_data:source.split_data):
        from uuid import uuid4
        from hashlib import md5
        entity, chunk_size, text, parent_uuid, parent_name, parent_source = super().split_preprocess(split_data)
        if len(text) == 0:
            return []
        if entity["type"] == "摘錄":
            excerpt = entity["摘錄"]
            description = entity.get("描述", "")
            text = f"摘錄:{excerpt}\n說明:{description}" # TODO: 需要考慮摘錄太長可能被截斷的問題
            split_result = [] 
            metadata = {}
            # # 字分割器
            # from langchain_text_splitters import RecursiveCharacterTextSplitter
            # text_splitter = RecursiveCharacterTextSplitter(
            #     chunk_size=self.config["chunk_size"], 
            #     chunk_overlap=0
            # )
            # char_split_contents = text_splitter.split_documents(text)
            uuid = str(uuid4())
            
            char_split_entity = {
                "name": entity["名稱"],
                "description": description,
                "data_hash": md5(text.encode()).hexdigest(),
                "uuid": uuid,
                "relation": [{"uuid1":uuid, "uuid2":parent_uuid, "relation":"屬於", "properties":{"chunk_size":chunk_size}}],
                "type": "chunk",
            }
            metadata["uuid"] = uuid
            import re
            com = re.compile(r"[0-9]*-[0-9][0-9]-[0-9][0-9]") # 用RE切日期出來，可能會有相容性問題
            date = re.findall(com, entity["名稱"])[0].split("-")
            metadata["year"] = int(date[0])
            metadata["month"] = int(date[1])
            metadata["day"] = int(date[2])
            metadata["parent_type"] = entity["type"]
            metadata["parent_source"] = entity.get("source", "neo4j") # TODO: 要改成可相容的寫法
            split_result.append({"entity":char_split_entity, "document":text, "metadata":metadata})
            return split_result
    
    def check_by_dict(self, condition:dict):
        # FIXME: 
        cypher = f"""MATCH(n:{condition.pop('type')}) WHERE """
        cypher += " AND ".join([f"n.{key} = ${key}" for key in condition])
        cypher += """ RETURN n"""
        result = self.DB.cypher_to_df(cypher, parameter=condition)
        print("neo4j.py:check_by_dict:", result)
        print_var(result)
        print(list(result.columns.values))
        if len(result) == 0:
            return False, None
        else:
            return True, result["n().prop.UUID"][0]
    
    async def add_entity(self, entity:dict, other_key=[]):
        """新增entity，之後使用uuid檢查是否新增成功
        """
        # print("debug:", type(self.DB.get_by_uuid(uuid=entity["uuid"])))
        if len(self.DB.get_by_uuid(uuid=entity["uuid"])) != 0:
            return {"result":"uuid已存在", "uuid":entity["uuid"]}
        # TODO: data_hash未實作完成，先註解掉
        # FIXME: 在chrome新增網頁資訊時只會以名稱和描述檢查重複與否，不會判斷URL，但也不用判斷tabid，因此需要想辦法傳遞需要判斷的項目
        if "check_key" in entity.keys() and entity["check_key"] is not None and len(entity["check_key"])>0: # 以check_key list說明檢查重複的條件
            check_dict = {key:entity[key] for key in entity["check_key"]}
            entity.pop("check_key")
        else:
            check_dict = {"名稱":entity["name"], "type":entity["type"], "描述":-["description"]}
        for key in other_key:
            check_dict[key] = entity[key]
        check_result, uuid = self.check_by_dict(check_dict)# , "data_hash":entity["data_hash"]}):
        if check_result:
            return {"result":"相同屬性已存在", "uuid":uuid}
        # 處理tag_string
        import re
        if "tag_string" in entity:
            tag_list = re.split(r"[, ]", entity["tag_string"])
            entity.pop("tag_string")
            for tag in tag_list:
                tag_uuid = self.add_entity({"name":tag, "type":"標籤"})
                entity["relation"].append({"uuid1":entity["uuid"], "uuid2":tag_uuid, "relation":"有標籤"})


        # 先把type和relation拿出來
        label = entity.pop("type")
        relation = entity.pop("relation", None)
        # 將entity剩餘的資料新增到知識圖譜中
        self.DB.create_entity(label=label,
                              **entity)
        # 檢查是否需要新增relation
        if relation is not None:
            for relationship in relation:
                print(self.DB.create_relation(relationship))
        if len(self.DB.get_by_uuid(uuid=entity["uuid"])) != 0:
            return {"result":"新增成功", "uuid": entity["uuid"]}
        else:
            return {"result":"新增失敗"}
        
    async def create_relation(self, **kwargs):
        relation_result = self.DB.create_relation(kwargs)
        return len(relation_result) > 0
    
    async def get_uuids(self, type:str=None, **kwargs)->list:
        """根據source或type取得uuid清單，應該可以和過濾或搜尋結合
        return (list): uuid清單
        """
        kwargs = {key:value for key, value in kwargs.items() if value != None}
        if type != None:
            if "筆記" in type: type="測試用筆記" # 測試用
            cypher_match = f"MATCH (n:{type}) " 
        else:
            cypher_match = f"MATCH (n) "
        if len(kwargs) != 0:
            cypher_where = "WHERE " + " AND ".join([f"n.{key} = ${key}" for key in kwargs])
        else:
            cypher_where = ""
        cypher = f"{cypher_match} {cypher_where} RETURN n.UUID"
        result = self.DB.cypher_to_df(cypher, kwargs)
        print_var(result)
        if len(result)>0: return list(result["n\.UUID"])
        else: return []
        
    
    async def delete_node(self, uuid:str):
        """刪除節點
        """
        #TODO: 未測試
        cypher = f"MATCH (n) WHERE n.UUID = '{uuid}' DETACH DELETE n"
        result = self.DB.cypher(cypher)
        print("neo4j:cypher_result:", type(result), "\n", result)
        return "ok"
    
    async def delete_chunk(self, uuid:str):
        #TODO 未完成
        cypher = """
        MATCH(n:`chunk`)
        MATCH(m:`摘錄`)
        WHERE (n)-[]->(m)
        DETACH DELETE n"""
        
    async def get_relations(self, uuid:str):
        return self.DB.get_depth1(uuid)
    
    async def chunk2uri(self, uuid:str):
        """neo4j的uri未定義"""
        return ""
    
    async def reference_string(self, reference_data:dict):
        """渲染參考字串
        TODO: 節點不是Chunk時的情況
        TODO: 用超連結開啟Neo4j中的節點或顯示其資訊的方法
        """
        parent_data = await self.get_data(uuid=reference_data["parent_uuid"])
        parent_name = parent_data.get("名稱","取得名稱錯誤")
        parent_type = parent_data.get("type", "取得類型錯誤")
        relation_result = self.DB.get_depth1(reference_data["parent_uuid"])
        reference_string = ""
        for relation in relation_result:
            if relation["r"]["type"] == "來自":
                name = relation["to"]["name"] if "name" in relation["to"] else relation["to"]["名稱"]
                url = relation["to"]["url"] if "url" in relation["to"] else ""
                # 等等，原來可以用html不一定要用markdown嘛!?
                reference_string = f'參考{parent_type}: <a href="{url}" target="_blank">{name}</a>'
        
        return reference_string
    
    async def get_tag(self):
        """取得標籤清單
        TODO: 清單長度為0
        TODO: 標籤以外可能是tag或tags等label
        TODO: 標籤間「可能」有從屬關係，如何顯示
        """
        query = """MATCH (n:`標籤`) RETURN n.name"""
        result = self.DB.cypher_to_df(query)
        print_var(result)
        if len(result) == 0:
            return []
        return list(result["n\.name"])
    
    async def keyword_search(self, keywords, top_k=3, type_list=[], **kwargs):
        """關鍵字搜尋，"""
        result = self.DB.search(keyword=keywords, top_k=top_k, type_list=type_list, **kwargs)
        return result
    # TODO: neo4j未覆寫模糊搜尋
    
async def test():
    from modules.utils import call_api
    neo4j_obj = neo4j_source()
    result = await neo4j_obj.get_tag()
    print_var(result)
    
if __name__ == "__main__":
    neo4j_obj = neo4j_source()
    import asyncio
    asyncio.run(test())
    
    # # 復原Neo4j：上傳標籤
    # ## 載入標籤
    # with open("TagList.txt", "r", encoding="utf-8") as f:
    #     tag_list = f.read().split("\n")
    #     print(tag_list)
    #     for tag in tag_list:
    #         neo4j_obj.DB.cypher("MERGE (n:`標籤`{name:$tag})", {"tag":tag})
        
        
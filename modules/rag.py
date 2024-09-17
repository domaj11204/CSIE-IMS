"""主要RAG框架，管理整個RAG流程，包含向量資料庫的讀寫
段落的部份則跟知識庫模組拿
"""
from .llm import llm
import os
os.environ["LANGCHAIN_TRACING_V2"]="true"
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"]="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"
os.environ["LANGCHAIN_PROJECT"]="RetrievalTest"
from modules.debug_utils import print_func_name, print_var, timer
from modules.utils import call_api
class rag(object):
    """管理RAG整體流程的流程
    TODO: 將檢索器拿出去
    """
    def __init__(self, config:dict=None):
        """rag物件初始化，由於FastAPI未啟動完成，因此不能使用需要其他本地的FastAPI

        Args:
            config (dict, optional): 可以指定載入的config. Defaults to None.
        """
        print("rag初始化中...")
        if config != None:
            self.config = config
        else:
            from .utils import read_config
            self.config = read_config()["rag"]
        # 取得embedded的基本名稱
        self.embedded_model_name = self.config["embedded_model"]
        self.llm_model = self.config["llm_model"]
        self.llm_mode = self.config["llm_mode"]
        if "collection_name" in self.config:
            self.collection_name = self.config["collection_name"]
        else:
            self.collection_name = self.embedded_model_name.replace("/", "-")+str(self.config["chunk_size"])+self.config["hnsw_space"]
        self.chroma_client = None 
        self.retriever = None
        self.chroma_collection = None
        print("rag初始化完成!")

    async def init_chroma(self):
        await self.init_embedded()
        import chromadb
        if self.chroma_collection is not None:
            return
        if "db_host" in self.config:
            self.chroma_client = chromadb.HttpClient(host=self.config["db_host"], port=self.config["db_port"])
        else:
            self.chroma_client = chromadb.PersistentClient(
                path= self.config["db_path"]
            )
        # self.chroma_client.delete_collection(self.collection_name) # 刪除
        self.chromadb_collection = self.chroma_client.get_or_create_collection(name=self.collection_name, embedding_function=MyEmbeddings())
        # result = self.chromadb_collection.count()
        # from modules.utils import call_api, b64embedding2np
        # query_embedding = await call_api("v1/embedded/encode", "post", {"sentences":["FastAPI使用端口?"]})
        # query_embedding = b64embedding2np(b64=query_embedding["base64"], dtype=query_embedding["dtype"], shape=query_embedding["shape"], sha256=query_embedding["sha256"])
        # result = self.chromadb_collection.query(query_embeddings=query_embedding)
        
    async def init_embedded(self):
        """初始化嵌入模組"""
        import requests
        from modules.utils import call_api
        # url = get_server_url() + "/embedded/"
        # print("url:", url)
        # response = requests.post(url, json={"model_name": self.config["embedded_model"], "model_type": "SentenceTransformer"})
        
        response = await call_api("/v1/embedded/", "POST", {"model_name": self.config["embedded_model"], "model_type": "SentenceTransformer"})
        print("response1:", response)
        
    async def init_llm(self):
        """初始化llm模組
        """
        from modules.utils import call_api
        response = await call_api("/v1/llm/", "POST", {"model_name":self.llm_model, "mode":self.llm_mode})
        print("init_llm:", response)
        
    @timer
    def init_retrieval(self, source_list:list=[], type_list:list=[])->None:
        """初始化(設定)檢索器"""
        retrieval_method = self.config["retrieval_method"]
        if "similarity" in retrieval_method or "mmr" in retrieval_method:
            if "similarity" in retrieval_method:
                self.retriever = self.chroma_search("similarity", source_list, type_list)
            if "mmr" in retrieval_method:
                self.retriever = self.chroma_search("mmr", source_list, type_list)
        if "bm25" in retrieval_method or "無" in retrieval_method:
            # 無檢索方法也使用bm25，這樣可以在本地執行
            return self.bm25(query)
        if "hyde" in retrieval_method:
            self.retriever = self.hyde(query)
        if "self_query" in retrieval_method:
            self.retriever = self.self_query(query)
        if "LLM_filter" in retrieval_method:
            self.retriever = self.contextual_compression_retriever()
    
    async def check_status(self, source_list:list=[], type_list:list=[]):
        """檢查RAG各模組是否初始化完成"""
        #TODO: 先直接初始化，之後要先檢查
        await self.init_embedded()
        await self.init_llm()
        await self.init_chroma()
        self.init_retrieval(source_list, type_list)
        
    async def query(self, query:str, source_list=[], type_list=[], **kwargs)->dict:
        """根據query執行rag查詢，回傳結果文字及相關內容
        
        Args:
            query (str): 查詢字串

        Returns:
            dict: 包含answer_text, context[], rag_parameter{}
        """
        # 處理輸入參數
        # TODO: 這種設定方法會和config設定衝突，要再想辦法解決
        if "top_k" in kwargs:
            self.config["search_k"]=kwargs["top_k"]
        if "retriever" in kwargs:
            self.config["retrieval_method"]=[kwargs["retriever"]]
        if "post_retriever" in kwargs and len(kwargs["post_retriever"])>0 :
            self.config["retrieval_method"].append(kwargs["post_retriever"])
        if "pre_retriever" in kwargs and len(kwargs["pre_retriever"])>0 :
            self.config["retrieval_method"].append(kwargs["post_retriever"])
        if "prompt" in kwargs:
            self.config["prompt_template"]=kwargs["prompt"]
        if "llm" in kwargs:
            self.config["llm_model"]=kwargs["llm"]
        if "embedded" in kwargs:
            self.config["embedded_model"]=kwargs["embedded"]
        await self.check_status(source_list, type_list)
        
        # 檢索
        if  "無" in self.config["retrieval_method"]:
            # 不使用任何retrieval時的特殊情況，用於實驗有無RAG的區別
            context = ""
            reference_str = "無參考"
            self.embedded_model_name = "無"
            self.embedded_db_path = "無"
        else:
            # 根據模型名稱使用嵌入資料庫，若資料庫不存在則嵌入並存到資料庫中
            # self.embedded()
            retrieval_result = self.retrieval(query, source_list)
            context = self.format_docs(retrieval_result)
            reference_str =""
            reference_list = []
            for document in retrieval_result:
                reference = {
                    "uuid": document.metadata["uuid"], 
                    "parent_source": document.metadata.get("parent_source", ""),
                    "parent_type": document.metadata.get("parent_type", "")}
                # 根據不同類別建立參考資料，之後用於渲染結果
                relation_result = (await call_api("/v1/knowledge_base/relations/"+document.metadata["uuid"], "GET"))["relations"]
                from modules.debug_utils import print_var
                print_var(relation_result)
                for relation in relation_result:
                    if relation["r"]["type"] == "屬於":
                        parent_type = relation["to"]["type"]
                        parent_uuid = relation["to"]["UUID"]
                        reference["parent_uuid"] = parent_uuid
                # FIXME: 應該只傳uuid給source，讓source取得必要的資訊?
                # 渲染和前端有關，這邊只負責將rag的完整結果存成dict 
                if "筆記" in parent_type:
                    from modules.debug_utils import print_var
                    response = await call_api("/v1/knowledge_base/"+parent_uuid, "GET")
                    print_var(response)
                    path = response["info"]["path"]
                    reference_str = reference_str + "參考: " + path.replace("\\", "/") + "#" + document.metadata.get("標題1", "") + "\n"
                    reference["path"] = path
                    reference["head"] = document.metadata.get("標題1", "")
                reference_list.append(reference)
        
        # 生成
        answer_text = await self.generate_answer(query, context, model_name=self.config["llm_model"])
        
        return {
            "answer_text": answer_text,
            "context": context,
            "reference": reference_str,
            "reference_list": reference_list,
            "rag_parameter": {
                "query": query,
                "embedded_model": self.embedded_model_name,
                "embedded_db_path": self.config["db_path"],
                "retrieval_method": self.config["retrieval_method"],
                "LLM_model": self.config["llm_model"],
                "prompt_template": self.config["prompt_template"],
            }
        }

    async def indexing(self, source=None, uuids=None)->list:
        """為知識庫中已存在的資料建立索引
        return (list): 嵌入完的UUID，包含子UUID"""
        from modules.utils import call_api, b64embedding2np
        from colorama import Back
        await self.init_embedded()
        await self.init_chroma()
        if uuids is None:
            # 取得所有UUID
            uuid_list = (await call_api(f"/v1/knowledge_base/uuids", "GET", params={"source":source}))["uuids"]
        else: uuid_list = uuids
        # for取得資料、切割、嵌入、存入向量資料庫
        # TODO: 讓其在前端顯示
        # TODO: 怎麼處理和論文有關的摘錄?
        new_uuid_list = []
        origin_count = self.chromadb_collection.count()
        from tqdm import tqdm
        for uuid in tqdm(uuid_list, desc="indexing進度"):
            # 檢查是否已嵌入
            if self.check_embedded(uuid=uuid):
                print(Back.GREEN+"已嵌入，跳過。")
                continue
            else:
                # 取得完整資料
                entity = (await call_api(f"/v1/knowledge_base/entity/{uuid}", "GET"))["entity"]
                print(entity)
                source = entity["source"]
                # 按照設定切割
                # 以下為針對不同來源或類型做特殊處理的部分，由於這樣的改良應該屬於RAG相關改良，因此放在這?
                # 決策:為了方便修改應該一併放在source裡面，新增時做對應的更改，參考渲染同理
                split_result = (
                    await call_api(f"v1/{source}/split", 
                        "post", 
                        data={"entity":entity, "chunk_size":self.config["chunk_size"]}
                        ))["split_result"]
                if len(split_result) == 0: # 檔案內容為空造成切出來是空則跳過
                    continue
                # 嵌入
                split_contents = []
                ids = []
                metadatas = []
                entities = []
                for split_content in split_result:
                    ids.append(split_content["entity"]["uuid"])
                    new_uuid_list.append(split_content["entity"]["uuid"])
                    metadatas.append(split_content["metadata"])
                    split_contents.append(split_content["document"])
                    entities.append(split_content["entity"])
                response = await call_api("/v1/embedded/encode", "POST", {"sentences":split_contents})
                embeddings = b64embedding2np(response=response)
                # 準備向量資料庫資料 TODO: 支援更多向量資料庫
                
                # 存入向量資料庫          
                # 決策: 把不同來源存到不同collection會不會比較好?   
                try:
                    # TODO: 之後可以刪掉document，嵌入向量庫中不該存原始資訊
                    self.chromadb_collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=split_contents)
                except Exception as e:
                    print(Back.RED+"儲存到向量資料庫錯誤:", e)
                # 存入neo4j
                try:
                    for entity in entities:
                        #TODO: 測試分開來要花多少時間
                        print_var(entity)
                        response = await call_api("/v1/knowledge_base/entity", "POST", entity)
                except Exception as e:
                    print(Back.RED+"儲存到neo4j錯誤:", e)
            new_count = self.chromadb_collection.count()
            print(f"count:{origin_count}->{new_count}")
        return new_uuid_list
                
    
    
    async def delete_index(self, source=None, type=None, uuid_list=None):
        """刪除索引"""
        #TODO: 未完成，不知道怎麼取list比較合理(結構問題)
        from modules.utils import call_api, b64embedding2np
        from tqdm import tqdm
        from colorama import Back
        print(Back.RED+"刪除索引未完成")
        return
        if uuid_list is None:
            #TODO: 應該考慮交集
            if source is not None:
                pass
                # uuid_list = await call_api(f"/v1/knowledge_base/sources/{source}", "get")
            if type is not None:
                pass
                # uuid_list = await call_api(f"/v1/knowledge_base/types/{type}", "get")
        await self.init_chroma()
        print_var(uuid_list)
        for uuid in tqdm(uuid_list, desc="刪除索引進度"):
            try:
                self.chromadb_collection.delete(ids=[uuid])           
            except Exception as e:
                print("刪除向量資料庫錯誤:", uuid, e)
            try:
                call_api(f"/v1/knowledge_base/{uuid}", "DELETE")
            except Exception as e:
                print("刪除知識庫錯誤:", uuid, e)
    
    def retrieval(self, query:str, source_list)->list:
        
        retrieval_method = self.config["retrieval_method"]
        print("debug:retrieval_method: ", retrieval_method)
        retrieval_result = self.retriever.invoke(query)
        print("rag.py:retrieval:result:", retrieval_result)
        return retrieval_result[:self.config["top_k"]]
        
    def chroma_search(self, search_type, source_list:list=[], type_list:list=[]):
        from langchain_chroma import Chroma
        langchain_chroma = Chroma(client = self.chroma_client,
                                collection_name=self.collection_name,
                                #embedding_function=self.embedded_obj_for_chroma
                                embedding_function=MyEmbeddings())
        filter_condition = []
        for source in source_list:
            filter_condition.append({"parent_source":source})
        for type in type_list:
            filter_condition.append({"parent_type":type})
        if len(filter_condition) > 1:
            filter = {"$or":[]}
            for condition in filter_condition:
                filter["$or"].append(condition)
        elif len(filter_condition) == 1:
            filter = filter_condition[0]
        else: filter = None
        
        from modules.debug_utils import print_var
        print_var(filter_condition)
        print_var(filter)
        # elif len(source_list !=):
        #     filter = {"$or":[{"parent_source":source_list[0]}, {"parent_type":source_list[0]}]}
        return langchain_chroma.as_retriever(search_type=search_type, 
                                                search_kwargs={"k": self.config["search_k"],
                                                            "filter":filter})
    
        
    def check_embedded(self, uuid:str)->bool:
        """檢查是否已嵌入"""
        # if self.retriever == None:
        #     self.init_retriever()
        if self.chromadb_collection is None: self.init_chroma()
        result = self.chromadb_collection.get(ids=[uuid])
        return len(result["ids"])!=0
         
    def contextual_compression_retriever(self):
        from langchain_core.prompts import BasePromptTemplate, PromptTemplate
        from langchain.output_parsers.boolean import BooleanOutputParser
        from langchain_core.output_parsers import BaseOutputParser
        from langchain.retrievers.document_compressors.chain_filter import LLMChainFilter
        from langchain.retrievers import ContextualCompressionRetriever
        prompt_template = """如果「上下文」和「問題」有關聯，請回答「是」，否則請回答「否」。
        > 問題: {question}
        > 上下文:
        >>>
        {context}
        >>>
        > 回答 (是 / 否):"""
        # BUG: 使用chatmodel
        class FirstTenOutputParser(BaseOutputParser):
            def parse(self, output):
                try:
                    result = BooleanOutputParser(false_val="否", true_val="是").parse(output[:10])
                except:
                    result = True
                return result
        first_ten_output_parser = FirstTenOutputParser()
        # FIXME: 要把llm_chat改成http request
        _filter = LLMChainFilter.from_llm(self.llm.chat_model, 
                                          prompt=PromptTemplate(input_variables=["question", "context"], 
                                                                    output_parser=first_ten_output_parser,
                                                                    template=prompt_template),
                                          top_k=self.config["top_k"])
        return ContextualCompressionRetriever(base_compressor=_filter, base_retriever=self.retriever)
    
    def hyde(self, query):
        """根據查詢生成虛假的檔案用於嵌入檢索
        直接在self.retriever前串上hyde_chain
        """
        #TODO: 未完成
        from langchain.retrievers import ContextualCompressionRetriever, MergerRetriever
        from langchain_community.retrievers import TFIDFRetriever
        from langchain.retrievers.document_compressors.chain_filter import LLMChainFilter
        from langchain_core.output_parsers import StrOutputParser
        from langchain.chains import HypotheticalDocumentEmbedder, LLMChain
        from langchain_core.prompts import BasePromptTemplate, PromptTemplate
        # https://github.com/langchain-ai/langchain/blob/master/templates/hyde/hyde/prompts.py
        hyde_prompt = """請模擬一段markdown筆記來回答問題。例如：
        ===問題==
        有哪些常見的知識圖譜？
        ===markdown===
        # 常見的知識圖譜
        - Freebase
        - DBpedia
        ===問題===
        {question}
        ===markdown===
        """
        hyde_prompt = PromptTemplate.from_template(hyde_prompt)
        hyde_chain = hyde_prompt | model | StrOutputParser()
        from modules.utils import call_api
        # hyde_str = await call_api("llm/", "POST", {"query":query})
        return (hyde_chain | self.retriever)
        
    def bm25(self, query):
        if self.retriever == None:
            from .embedded import embedded
            from langchain_community.retrievers import BM25Retriever
            self.retriever = BM25Retriever.from_documents(self.embedded_obj.get_documents())
        result = self.retriever.invoke(query)
        return result
    
    def self_query(self, query:str):
        """用gpt-4o檢查查詢，若包含日期則過濾
        在此之前的retriever會保留，權重為0.5
        """
        from langchain.chains.query_constructor.base import AttributeInfo
        from langchain.retrievers import EnsembleRetriever
        from langchain.retrievers.self_query.base import SelfQueryRetriever
        from langchain_core.prompts import BasePromptTemplate, PromptTemplate
        from langchain_openai import ChatOpenAI
        gpt_4o_model = ChatOpenAI(model_name="gpt-4o", seed=1, temperature=0)
        metadata_field_info = [
        AttributeInfo(
            name="year",
            description="the year of date",
            type="integer",
        ),
        AttributeInfo(
            name="month",
            description="the mounth of date",
            type="integer",
        ),
        AttributeInfo(
            name="day",
            description="the day of date",
            type="integer",
        ),
        ]
        document_content_description = "note"
        
        self_query_retriever = SelfQueryRetriever.from_llm(
            gpt_4o_model,
            self.embedded_obj.vectorstore,
            document_content_description,
            metadata_field_info,
        )
        
        return EnsembleRetriever(retrievers=[self_query_retriever, self.retriever], weights=[0.5, 0.5])
        
    def format_docs(self, documents:list)->str:
        return "\n\n".join([document.page_content for document in documents])
    
    async def generate_answer(self, query:str, context:str, model_name:str)->str:
        from langchain_core.prompts import ChatPromptTemplate
        template = self.config["prompt_template"]
        
        prompt = ChatPromptTemplate.from_template(template)
        prompt = prompt.format(context=context, question=query)
        # print("format後的prompt:", prompt)
        
        from modules.utils import call_api
        llm_result = await call_api("/v1/llm/chat", "POST", {"input":prompt})
        llm_result = llm_result["content"]
        #llm_result = self.llm.chat(input=prompt, system_message="")
        # llm_result裡面的response_metadata["prompt_tokens"]可以用於計算生成速度
        return llm_result
    
    async def reference_synthesis(self, response):
        """將參考文獻與答案合併"""
        print_var(response)
        reference_str = ""
        from urllib.parse import quote_plus
        for reference in response["reference_list"]:
            parent_source = reference["parent_source"]
            formatted_reference = (await call_api(f"/v1/{parent_source}/reference_string", "post", reference))["reference_string"]
            reference_str += formatted_reference + "\n"
        

        # 舊版寫法
        # response_str = response["reference"]
        # import re
        # from modules.utils import call_api
        # reference_re = re.compile(r"參考:.*")
        # from modules.utils import read_config
        # obsidian_config = read_config()["obsidian"]
        # obsidian_vault_path = obsidian_config["path"].replace("\\", "/")
        # if obsidian_vault_path[-1] == "/": obsidian_vault_path = obsidian_vault_path[:-1]
        # re_str = obsidian_vault_path + "/.*"
        # file_re = re.compile(re_str)
        # for reference in re.findall(reference_re, response_str):
        #     for file_path in re.findall(file_re, reference):
        #         note_path = file_path.split(obsidian_vault_path)[1]
        #         link = await call_api("/v1/obsidian/path2link", "get", params={"path":note_path})
        #         link = link["result"]
        #         link = link.replace("\"", "")
        #         full_path = reference.split(":", 1)[1]
        #         response_str = response_str.replace(full_path, link + "\n")
        
        return response["answer_text"] + "\n" + reference_str
    
    def eval(self):
        # 載入資料集
        import datasets
        from tqdm import tqdm
        noteqa = datasets.load_dataset("json", data_files="./data/noteqa.json")
        noteqa_simple = noteqa.filter(lambda x: x["檢索類別"] == "每日筆記")
        noteqa_simple = noteqa_simple.filter(lambda x: x["問題類別"] != "複雜問題")
        # 開啟記錄用xlsx
        import pandas as pd
        from .utils import update_or_append_result, check_by_parameter
        df = pd.read_excel("./data/rag_eval.xlsx", index_col=0, dtype="str")
        df.fillna("", inplace=True)
        for column in ["LLM", "量化", "prompt_template", "嵌入模型", "query", "top_k", "檢索方法", "生成日期", "answer", "search_type", "search_k"]:
            if column not in df.columns.to_list():
                df[column]=""
        for query_index, query in enumerate(tqdm(noteqa_simple["train"]["問題"])):
            if check_by_parameter(df, {
                "LLM": self.config["llm_model"],
                "量化": "eetq",
                "prompt_template": self.config["prompt_template"],
                "嵌入模型": self.config["embedded_model"],
                "query": query,
                "top_k": str(self.config["top_k"]),
                "search_k": str(self.config["search_k"]),
                "檢索方法": "+".join(self.config["retrieval_method"]),
                "search_type":self.config["search_type"],
                "hnsw_space": self.config["hnsw_space"],}):
                continue
            result = self.query(query)
            # print(result)
            df = update_or_append_result(df, {
                "LLM": result["rag_parameter"]["LLM_model"],
                "量化": "eetq",
                "prompt_template": result["rag_parameter"]["prompt_template"],
                "嵌入模型": result["rag_parameter"]["embedded_model"],
                "query": query,
                "top_k": str(self.config["top_k"]),
                "search_k": str(self.config["search_k"]),
                "檢索方法": "+".join(self.config["retrieval_method"]),
                "search_type":self.config["search_type"],
                "hnsw_space": self.config["hnsw_space"],},
                {
                "生成日期": pd.Timestamp.now(),
                "answer": result["answer_text"],
            })
        df.to_excel("./data/rag_eval.xlsx")
        self.retriever = None

    def auto_eval(self):
        retrieval_method_list = [["similarity", 
                                  "mmr", 
                                  #"knn"
                                  ], 
                                 ["self_query", ""],
                                 ["LLM_filter", ""]]
        best_embedded_models = [
             {
             "embedded_model": "text-embedding-3-large",
             "hnsw_space": "cosine"
        }, 
            {
            "embedded_model": "BAAI/bge-m3",
            "hnsw_space": "cosine"
        }]
        llm_list = [#"MediaTek-Research/Breeze-7B-Instruct-v0_1", 
                    "gpt-4o"]# "qwen1_5-32b-chat"]
        embedded_model_list = ["infgrad/puff-base-v1", "BAAI/bge-m3", "text-embedding-ada-002"]
        # "infgrad/puff-base-v1"的similarity的recall更高
        from modules.llm import llm
        for llm_name in llm_list:
            self.config["llm_model"] = llm_name
            self.llm = llm(model_name=self.config["llm_model"], mode="openai")
            for embedded_model in best_embedded_models:
                self.config["embedded_model"] = embedded_model["embedded_model"]
                self.config["hnsw_space"] = embedded_model["hnsw_space"]
                self.config["retrieval_method"] = []
                for retrieval_method1 in retrieval_method_list[0]:
                    self.config["retrieval_method"].append(retrieval_method1)
                    for retrieval_method2 in retrieval_method_list[1]:
                        self.config["retrieval_method"].append(retrieval_method2)
                        for retrieval_method3 in retrieval_method_list[2]:
                            self.config["retrieval_method"].append(retrieval_method3)
                            for top_k in [1, 3, 5]:
                                print(self.config["llm_model"], self.config["retrieval_method"], top_k)
                                self.config["top_k"] = top_k
                                if "LLM_filter" in self.config["retrieval_method"]:
                                    self.config["search_k"] = 10
                                else:
                                    self.config["search_k"] = top_k
                                self.eval()
                            self.config["retrieval_method"].remove(retrieval_method3)
                        self.config["retrieval_method"].remove(retrieval_method2)
                    self.config["retrieval_method"].remove(retrieval_method1)

    def get_setting(self, key:str=None):
        """取得設定，若key存在則回傳key的值，否則回傳所有設定"""
        if key is None:
            return self.config
        else:
            return self.config.get(key, "無此設定")
        
    def change_setting(self, setting:dict):
        """修改設定，先檢查是否存在，接著修改
        回傳rag目前的所有設定。
        attribute優於config，若原本為int會轉成int"""
        # 先檢查是否有不合法的key
        for key in setting.keys():
            if key not in attribute and key not in self.config:
                return {"result": "錯誤，不合法的key"}
        for key in setting.keys():
            attribute = vars(self) # https://www.geeksforgeeks.org/how-to-get-a-list-of-class-attributes-in-python/
            if key in attribute:
                if type(getattr(self, key)) == int:
                    setting[key] = int(setting[key])
                setattr(self, key, setting[key])
            if key in self.config:
                if type(self.config[key]) == int:
                    setting[key] = int(setting[key])
                self.config[key] = setting[key]
        return {"result": vars(self)}
        
    async def get_data_in_vector_by_uuid(self, uuid:str):
        await self.init_chroma()
        result = dict(self.chromadb_collection.get(ids=[uuid], include=["metadatas", "documents"]))
        return result
    
    async def change_metadatas(self):
        """已用完，遍歷vectorDB中的所有資料，加上uuid"""
        from modules.utils import call_api
        uuids = (await call_api("/v1/knowledge_base/uuids", "get", params={"type":"chunk"}))["uuids"]
        await self.init_chroma()
        from tqdm import tqdm
        for uuid in tqdm(uuids):
            try: 
                metadatas = self.chromadb_collection.get(ids=[uuid], include=["metadatas"])["metadatas"][0]
                metadatas["uuid"] = uuid
                self.chromadb_collection.update(ids=[uuid], metadatas=[metadatas])
            except Exception as e:
                print(uuid, "錯誤", e)
        
        
class MyEmbeddings():
    def __call__(self, input):
        return self.embedded(list(input))
    def embedded(self, sentences:list, prefix:str=""):
        """嵌入
        """
        import requests
        from modules.utils import get_server_url, b64embedding2np
        url = get_server_url()+"/v1/embedded/encode"
        url = url.replace("27711", "27712")
        response = requests.post(url, json={"sentences":sentences, "prefix":prefix}).json()
        # from modules.utils import call_api
        # response = await call_api("/v1/embedded/encode", "post", data={"sentences":sentences, "prefix":prefix})
        return b64embedding2np(b64=response["base64"], dtype=response["dtype"], shape=response["shape"], sha256=response["sha256"])
    def embed_query(self, query:str):
        return self.embedded([query])[0].tolist()
async def test():
    from modules.utils import call_api
    #result = await call_api("rag/query", "POST", {"query":"FastAPI監聽哪個port?", "source_list":["筆記"]})
    # result = await call_api("/v1/rag/langchain/split_text", "POST")
    rag_obj = rag()
    #await rag_obj.init_chroma()
    #await call_api("/v1/rag/reload", "POST")
    await rag_obj.init_chroma()
    result = rag_obj.chromadb_collection.peek(5)
    result = rag_obj.chromadb_collection.count()
    print(result)
    #print(result)
    # result = await rag_obj.indexing(source="obsidian")
    # result = await call_api("/v1/obsidian/setting", "POST", {"path": "3"})
    result = rag_obj.chromadb_collection.get(where={"day":20})
    print(result)


if __name__ == "__main__":
    # import langchain

    # import os
    # langchain.debug=True
    # os.environ["LANGCHAIN_TRACING_V2"]="true"
    # os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
    # os.environ["LANGCHAIN_API_KEY"]="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"
    # os.environ["LANGCHAIN_PROJECT"]="RetrievalTest"
    import asyncio
    asyncio.run(test())
    
    
    pass
"""
本模組僅處理嵌入相關功能，包含嵌入伺服器的初始化、嵌入等
實際使用不會用到，而是FastAPI直接轉發請求
僅在實驗時使用。
"""
import requests
import numpy as np

from chromadb import Documents, EmbeddingFunction, Embeddings
from typing import List
from modules.debug_utils import error
# 用於自訂langchain的embeddings，目前用不到
class MyEmbeddedings:
    """
    參考 https://stackoverflow.com/questions/77217193/langchain-how-to-use-a-custom-embedding-model-locally
    """
    def __init__(self, model_name:str=None):
        self.model_name = model_name
        embedded_obj = embedded(model_name=model_name)
        self.embed_function = embedded_obj.embedded
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_function(text).tolist() for text in texts]
    
    def embed_query(self, query:str)-> List[float]:
        return self.embed_function([query])
        
# 嵌入模組的主要class
class embedded(object):
    def __init__(self, embedded_config:dict=None, model_name:str=None):
        print("embedded初始化中...")
        if embedded_config == None:
            from modules.utils import read_config
            self.config = read_config()["embedded"]
        else:
            self.config = embedded_config
        
        if model_name != None:
            self.model_name = model_name
            self.model_info = self.set_embedded_model(model_id=self.model_name)
            self.collection_name = self.model_name.replace("/", "-")+str(self.config["chunk_size"])+self.config["hnsw_space"]
        # self.vectorstore = None
        
    def init_vectorstore(self):
        """初始化langchain的vectorstore，用於langchain相關功能
        """
        error("嵌入模型不該接觸向量資料庫")
        return
        from langchain_community.vectorstores import Chroma
        self.vectorstore = Chroma(persist_directory=self.config["db_path"], 
                        embedding_function=self,
                        collection_name=self.collection_name,
                        collection_metadata={"hnsw:space":self.config["hnsw_space"]})
        
    def get_vectordb_info(self):
        """取得向量資料庫資訊
        """
        error("嵌入模型不該接觸向量資料庫")
        return
        print("get test")
        print(self.vectorstore.get().keys())
        print(self.vectorstore.search("如何使用FastAPI?", search_type="similarity", k=2))
        print(self.vectorstore.get(where_document={"$contains":"Fast"}))
        print(self.vectorstore.get(ids=['0']))
        return "get_test"
    
    def embedded(self, sentences:list, prefix:str="")->np.ndarray:
        """嵌入
        """
        if self.model_name in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
            from openai import OpenAI
            client = OpenAI()

            return np.array([client.embeddings.create(
                model=self.model_name,
                input=sentence,
            ).data[0].embedding for sentence in sentences])
            
        response = requests.post(
            self.config["url"],
            json={"sentences":sentences, "prefix":prefix}
        )    
        
        response_json = response.json()
        # from modules.utils import b64embedding2np
        # embedded_result = b64embedding2np(
        #     b64=response_json["base64"], 
        #     dtype=response_json["dtype"], 
        #     shape=response_json["shape"],
        #    sha256=response_json["sha256"])
        import base64
        
        b64 = response_json["base64"]
        sha256 = response_json["sha256"]
        embedded_result = np.frombuffer(base64.b64decode(b64), 
                        response_json["dtype"]).reshape(response_json["shape"])
        # import hashlib
        # result = "復原正確" if hashlib.sha256(embedded_result).hexdigest() == sha256 else "復原錯誤"
        # print(embedded_result[0][1])
        # print(embedded_result.dtype)
        return embedded_result

    # 用於chromadb的embedding function
    def embed_query(self, query:str)-> List[float]:
        error("嵌入模型不該接觸向量資料庫")
        return
        return self.embedded([query])[0].tolist()
    
    def set_embedded_model(self, model_id:str="moka-ai/m3e-small")->dict:
        """設定嵌入模型
        return (dict): 嵌入模型的最大長度和維度
        """
        self.model_name = model_id
        if self.model_name in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
            print("警告:設定使用要付費的openapi")
            return {"max_length": 8192, "dim":3072 if self.model_name == "text-embedding-3-large" else 1536}
        import time
        print("嵌入模型載入中...")
        
        # 如果包含url則使用遠端嵌入api
        if "url" in self.config and self.config["url"] != "":
            print("使用遠端嵌入api")
            response = requests.get(
                self.config["url"],
                params={
                    "model_id": model_id
                }
            )
            print("嵌入模型載入完成")
            self.max_length = response.json()["max_length"]
            self.dim = response.json()["dim"]
        # TODO: 使用本地嵌入模型
        else:
            print("使用本地嵌入模型")
            print("未完成")
            pass
        return response.json()
    
    def embedded_once(self):
        """將指定資料夾中的md檔一次性嵌入，並根據模型存成chroma
        """
        
        db_path = self.config["db_path"]    
        chunk_size = self.config["chunk_size"]
        self.collection_name = self.model_name.replace("/", "-")+str(chunk_size)+self.config["hnsw_space"]
        import chromadb
        self.chromadb_client = chromadb.PersistentClient(
            path= db_path
        )
        # 刪除，測試用
        # self.chromadb_client.delete_collection(name=self.collection_name)
        #exit()
        try: # 直接試是否已存在
            self.collection = self.chromadb_client.get_collection(
                name=self.collection_name)
            print("資料庫已存在")
            self.init_vectorstore()
            return db_path
        except:
            self.collection = self.chromadb_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": self.config["hnsw_space"]})
        # self.chromadb_client.delete_collection(name=self.model_name.replace("/", "-"))
        # self.collection = self.chromadb_client.get_or_create_collection(name=self.model_name.replace("/", "-"))
        split_documents = self.get_documents()
        embedded_result = self.embedded([document.page_content for document in split_documents], prefix="passage: ")
        self.collection.add(
            embeddings=embedded_result,
            documents=[document.page_content for document in split_documents],
            metadatas=[document.metadata for document in split_documents],
            ids=[str(id) for id in range(len(split_documents))]
        )
        self.init_vectorstore()
        return db_path
    
    def get_documents(self):
        """根據config中的path讀md檔，切開後回傳split_documents
        return (list): 切割後的documents
        """
        # TODO: 準備棄用，應移至rag模組
        print("!!!!準備棄用!!!!")
        from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader, TextLoader
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        documents = DirectoryLoader(self.config["path"], glob="*.md", loader_cls=TextLoader).load()
        headers_to_split_on = [
            ("#", "標題1"),
        ]
        # 用strip_headers=False，保留切割用的header
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)
        # 字分割器
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunk_size"], 
            chunk_overlap=0
        )
        split_documents = [] 
        # 將切完的檔案存成獨立的document，之後用特別的檢索方法時可能要修改這邊
        for document in documents:
            split_contents = markdown_splitter.split_text(document.page_content)
            # 再用文字切並將原本的source保留下來
            char_split_contents = text_splitter.split_documents(split_contents)
            for char_split_content in char_split_contents:
                char_split_content.metadata["source"] = document.metadata["source"]
                date = document.metadata["source"].replace("\\", "/").split("每日筆記/")[-1].split(".md")[0]
                char_split_content.metadata["year"] = int(date.split("-")[0])
                char_split_content.metadata["month"] = int(date.split("-")[1])
                char_split_content.metadata["day"] = int(date.split("-")[2])
                if "標題1" in char_split_content.metadata and char_split_content.page_content[0] != "#":
                    char_split_content.page_content = "來自筆記:" + document.metadata["source"] + "\n# " + char_split_content.metadata["標題1"] + "\n" + char_split_content.page_content
                else:
                    char_split_content.page_content = "來自筆記:" + document.metadata["source"] + "\n" + char_split_content.page_content
                split_documents.append(char_split_content)
        return split_documents
    
    def embedded_eval(self):
        """使用資料集評估嵌入模型"""
        # 載入資料集
        import datasets
        from tqdm import tqdm
        noteqa = datasets.load_dataset("json", data_files="./data/noteqa.json")
        noteqa_simple = noteqa.filter(lambda x: x["檢索類別"] == "每日筆記")
        noteqa_simple = noteqa_simple.filter(lambda x: x["問題類別"] != "複雜問題")
        mrr_5_result = []
        mrr_10_result = []
        top1_result = []
        rerank_top1 = []
        rerank_mmr = []
        recall_result = []
        """實驗bm25，結果超爛
        from .embedded import embedded
        from langchain_community.retrievers import BM25Retriever
        self.retriever = BM25Retriever.from_documents(self.get_documents(), k=5)
        
        for index, query in enumerate(noteqa_simple["train"]["問題"]):
            result = self.retriever.invoke(query)
            new_result = []
            for doc in result:
                new_result.append(doc.metadata)
            result = {}
            result["metadatas"] = [new_result]
        """
        from tqdm import tqdm
        for index, query in tqdm(enumerate(noteqa_simple["train"]["問題"])):
            # 改用langchain以實現mmr
            # result = self.collection.query(
            #     query_embeddings=self.embedded([query], prefix="query: "),
            #     n_results=5
            # )
            if self.config["search_type"] in ["similarity", "mmr"]:
                result = self.vectorstore.search(
                    search_type=self.config["search_type"],
                    query=query,
                    k=10
                )
            elif self.config["search_type"] == "bm25":
                result = self.retrieval.invoke(query, k=10)
            # 重排序測試
            """bce
            from sentence_transformers import CrossEncoder
            # init reranker model
            model = CrossEncoder('maidalun1020/bce-reranker-base_v1', max_length=512)
            
            from FlagEmbedding import FlagReranker
            reranker = FlagReranker('BAAI/bge-reranker-large', use_fp16=True)
            # calculate scores of sentence pairs
            first_rerank = 0
            second_rerank = 0
            rerank_source = ["", ""]
            for i, document in enumerate(result["documents"][0]):
                # score = model.predict((query, document))
                score = reranker.compute_score([query, document])
                if score > first_rerank:
                    first_rerank, second_rerank = score, first_rerank
                    rerank_source[1] = rerank_source[0]
                    rerank_source[0] = result["metadatas"][0][i]["source"].replace("\\", "/").split("ObsidianSync/")[-1]
                elif score > second_rerank:
                    second_rerank = score
                    rerank_source[1] = result["metadatas"][0][i]["source"].replace("\\", "/").split("ObsidianSync/")[-1]
            """
            # 計算MMR
            # 參考 https://towardsdatascience.com/openai-vs-open-source-multilingual-embedding-models-e5ccb7c90f05
            all_source = []
            for doc in result:
                # 這邊需要按照實際資料夾路徑切割
                source = doc.metadata["source"].replace("\\", "/").split("ObsidianSync/")[-1]
                all_source.append((source, doc.metadata["標題1"]))
            # print(noteqa_simple["train"]["參考"][index][0], noteqa_simple["train"]["標題1"][index])
            # print(all_source)
            rank = 1
            mrr = 0
            for source in all_source:
                if source[0] == noteqa_simple["train"]["參考"][index][0]+".md" and source[1] == noteqa_simple["train"]["標題1"][index]:
                    mrr = 1/rank
                    break
                rank += 1
            if rank == 1:
                top1_result.append(1)
            else:
                top1_result.append(0)
            if rank <= 5 :
                mrr_5_result.append(mrr)
                mrr_10_result.append(mrr)
            elif rank <= 10:
                mrr_5_result.append(0)
                mrr_10_result.append(mrr)
            else:
                mrr_5_result.append(0)
                mrr_10_result.append(0)
            recall_result.append(1 if mrr > 0 else 0)
        
            """
            if noteqa_simple["train"]["參考"][index][0]+".md" in rerank_source:
                rank = rerank_source.index(noteqa_simple["train"]["參考"][index][0]+".md")+1
                mrr = 1/rank
                if rank == 1:
                    rerank_top1.append(1)
                else:
                    rerank_top1.append(0)
            rerank_mmr.append(mrr)
            """
        print("collect:", self.collection_name)
        print("search_type:", self.config["search_type"])
        print("mrr@5\tmmr@10\tP@1\trecall@10", )
        print(np.average(mrr_5_result), np.average(mrr_10_result), np.average(top1_result), np.average(recall_result), sep="\t")
        print("================================")
        # print("rerank_mmr:", np.average(rerank_mmr))
        # print("rerank_top1:", np.average(rerank_top1))
        

    def auto_eval(self):
        import chromadb
        db_path = self.config["db_path"]
        chunk_size = self.config["chunk_size"]
        self.chromadb_client = chromadb.PersistentClient(
            path= db_path
        )
        # embedded_model_list = [ "BAAI/bge-m3", #"text-embedding-ada-002", 
        #                        "intfloat/multilingual-e5-large", "infgrad/puff-base-v1", "moka-ai/m3e-large",
        #                        "jinaai/jina-embeddings-v2-base-zh", #"text-embedding-3-large", "text-embedding-3-small",
        #                        "infgrad/stella-large-zh-v3-1792d", 
        #                        "maidalun1020/bce-embedding-base_v1"]
        embedded_model_list = ["text-embedding-ada-002","text-embedding-3-large", "text-embedding-3-small"]
        hnsw_space_list = ["cosine"]#, "l2", "ip"]
        search_type_list = ["mmr"]# ["similarity", "mmr"]
        for embedded_model_name in embedded_model_list:
            self.model_name = embedded_model_name
            self.set_embedded_model(embedded_model_name)
            for search_type in search_type_list:
                self.config["search_type"] = search_type
                if search_type == "bm25":
                    from langchain.retrievers import BM25Retriever
                    self.retrieval = BM25Retriever.from_documents(self.get_documents(), k=10)
                for hnsw_space in hnsw_space_list:
                    
                    self.config["hnsw_space"] = hnsw_space
                    self.collection_name = self.model_name.replace("/", "-")+str(chunk_size)+self.config["hnsw_space"]
                    # try:
                    #     self.chromadb_client.delete_collection(name=self.collection_name)
                    # except:
                    #     pass
                    self.embedded_once()
                    self.embedded_eval()
                    
if __name__ == "__main__":
    # intfloat/multilingual-e5-large infgrad/puff-base-v1 moka-ai/m3e-large infgrad/stella-large-zh-v3-1792d
    # jinaai/jina-embeddings-v2-base-zh BAAI/bge-m3 maidalun1020/bce-embedding-base_v1 
    # text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"
    embed = embedded()
    embed.auto_eval()
    # embed = embedded(model_name="BAAI/bge-m3")
    # embed.embedded_once()
    # print(embed.collection_name)
    # print(embed.vectorstore)
    # embed.embedded_eval()
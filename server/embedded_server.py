"""
提供嵌入API
"""
# 全域變數
embedded_model = None
model_name = None
tokenizer = None
from sentence_transformers import SentenceTransformer, util
from transformers import AutoTokenizer

import pandas as pd
from langsmith import traceable
from tqdm import tqdm
import time
def embedded_from_hf(model_name:str):
    """從huggingface取得嵌入模型
    Args:
        model_name (str): 模型名稱
    """
    print("錯誤：目前僅使用支援sentence-transformer的模型")
    raise

def embedded_from_st(sentences:list, query:str="", prefix:str=""):
    """從sentence-transformers取得嵌入模型

    Args:
        sentences (list): 要嵌入的句子
        query (str): 可能會用到的query

    Returns:
        ndarray: 嵌入結果
        int: token數
    """
    
    # 根據e5的說明，需要加上query或passage
    # 目前僅針對語意做處理，之後就要將問題放在query，訊息放在passage
    global model_name
    global embedded_model
    if "intfloat/e5" in model_name:
        for i in range(len(sentences)):
            sentences[i] = prefix + sentences[i]
    
    return embedded_model.encode(sentences), [len(tokenizer.encode(sentence)) for sentence in sentences ]
    
def embedded_from_openai(sentences:list,model_name:str="text-embedding-3-small"):
    """使用openai做嵌入

    Args:
        model_name (str): 模型名稱
        sentences (list): 要嵌入的句子

    Returns:
        list: 嵌入結果
    """
    from openai import OpenAI
    import tiktoken
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding("cl100k_base")
    client = OpenAI()
    
    return [client.embeddings.create(
        model=model_name,
        input=sentence,
    ).data[0].embedding for sentence in sentences], [len(encoding.encode(sentence)) for sentence in sentences ]

def embedded_from_cohere(sentences:list, model_name = "embed-multilingual-v3.0"):
    """使用cohere做嵌入
    參考: https://docs.cohere.com/reference/embed
    Args:
        sentences (list): 要嵌入的句子
        model_name (str, optional): 使用的模型名稱. Defaults to "embed-multilingual-v3.0".

    Returns:
        _type_: 嵌入結果
    """
    import cohere
    co = cohere.Client('5H6bi6DyRih9TKSCeeEV6DhlSylP5Mbn9eYFSFb2')
    print(sentences)
    response = co.embed(
        texts=sentences,
        model=model_name,
        input_type='search_query' # 針對檔案應使用search_document
    )
    print(response)
    return response.embeddings



def multiple_compare(model_name, sentences:list[str], question=""):
    """用於測試特定model的及測試句子的相似度
    參考：https://www.sbert.net/docs/quickstart.html
    半手刻版，之後可以用於和langchain包裝後的版本比較
    """
    print("準備測試嵌入，模型名稱:", model_name)
    #Encode all sentences
    if question!="":
        sentences.append(question)
    if model_name=="text-embedding-ada-002":
        embeddings = embedded_from_openai(model_name=model_name, sentences=sentences)
    if "embed-multilingual" in model_name:
        embeddings = embedded_from_cohere(model_name=model_name, sentences=sentences)
    else:
        embeddings = embedded_from_st(model_name, sentences)
    # 儲存嵌入結果，省錢
    # df = pd.read_csv("embedded.csv")
    # for sentence_no in range(len(sentences)):
    #     df.at[sentences[sentence_no], model_name] = embeddings[sentence_no]
    # df.to_csv("embedding.csv")
        
    #Compute cosine similarity between all pairs
    print("embeddings size:", len(embeddings))
    cos_sim = util.cos_sim(embeddings, embeddings)

    #Add all pairs to a list with their cosine similarity score
    all_sentence_combinations = []
    for i in range(len(cos_sim)-1):
        for j in range(i+1, len(cos_sim)):
            all_sentence_combinations.append([cos_sim[i][j], i, j])

    #Sort list by the highest cosine similarity score
    all_sentence_combinations = sorted(all_sentence_combinations, key=lambda x: x[0], reverse=True)
    print("cos結果:")
    for score, i, j in all_sentence_combinations:
        if question!="" and sentences[j]!=question:
            continue
        print("{} \t {} \t {:.4f}".format(i, sentences[j], cos_sim[i][j]))
    
    from langchain_community.embeddings import CohereEmbeddings
    from langchain.embeddings import HuggingFaceEmbeddings
    # langchain_embeddings = CohereEmbeddings(model="embed-multilingual-v3.0", cohere_api_key="5H6bi6DyRih9TKSCeeEV6DhlSylP5Mbn9eYFSFb2")
    langchain_embeddings = HuggingFaceEmbeddings(model_name="moka-ai/m3e-large")
    query_result = langchain_embeddings.embed_query(question)
    print((query_result==embeddings[-1]))
    print(util.cos_sim(query_result,embeddings[-1]))
    from langchain_community.document_loaders import ObsidianLoader
    loader = ObsidianLoader("/home/domaj/ObsidianSync/每日筆記")
    
    from langchain.indexes import VectorstoreIndexCreator
    from langchain.chains import retrieval_qa
    index = VectorstoreIndexCreator().from_loaders([loader])
    #doc_result = embeddings.embed_documents(loader.load())
    # print(index.query_with_sources(question)) # 這個要付錢，好像預設openai

def langchain_compare(embedded_model_name="moka-ai/m3e-large", 
                    llm_model_name="gpt-3.5-turbo-instruct", 
                    document_path="/home/domaj/ObsidianSync/每日筆記", 
                    query_list:list[str]=[],
                    ground_truth:list[list[str]]=[]):
    """盡量使用langchain框架執行整個RAG行為

    Args:
        embedded_model_name (str): 模型名稱 Defaults to "moka-ai/m3e-large".
        llm_model_name (str): Defaults to "gpt-3.5-turbo-instruct".
        document_path (str, optional): _description_. Defaults to "/home/domaj/ObsidianSync/每日筆記".
    """
    from langchain_community.vectorstores import DocArrayInMemorySearch
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.runnables import RunnableParallel, RunnablePassthrough
    from langchain_openai.chat_models import ChatOpenAI
    from langchain_openai.embeddings import OpenAIEmbeddings

    from langchain_community.document_loaders import ObsidianLoader
    loader = ObsidianLoader(document_path)
    docs = loader.load()

    from langchain_community.embeddings import HuggingFaceEmbeddings
    # langchain_embeddings = CohereEmbeddings(model="embed-multilingual-v3.0", cohere_api_key="5H6bi6DyRih9TKSCeeEV6DhlSylP5Mbn9eYFSFb2")
    if "text-embedding-ada-002" in embedded_model_name:
        langchain_embeddings = OpenAIEmbeddings()
    else:
        langchain_embeddings = HuggingFaceEmbeddings(model_name=embedded_model_name, model_kwargs={"trust_remote_code":True})
    print("model: ", embedded_model_name)
    from langchain_community.vectorstores import Chroma
    vectorstore = Chroma.from_documents(documents = docs, embedding=langchain_embeddings)
    
    from Lab_utils import eval_by_list
    for search_type in ["similarity", "mmr"]:
        print("搜尋法: ", search_type)
        for query, truth in zip(query_list, ground_truth):
            print("問題: ", query, end="")
            retriever = vectorstore.as_retriever(search_type=search_type)
            retriever_ans = retriever.invoke(query)
            ans = list()
            for doc in retriever_ans:
                # print(ans)
                ans.append(doc.metadata["path"].split("/")[-1].replace(".md", ""))
            # print(ans)
                
            print(eval_by_list(pred_list=ans, ground_truth=truth))
    vectorstore.delete_collection()

    return # 以下先跳過，不然要付錢:<
    template = """Answer the question based only on the following context:
    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = ChatOpenAI()
    output_parser = StrOutputParser()

    setup_and_retrieval = RunnableParallel(
        {"context": retriever, "question": RunnablePassthrough()}
    )
    chain = setup_and_retrieval | prompt | model | output_parser

    chain.invoke("where did harrison work?")


def model_test(model_name:str):
    """用於測試model是否正常運行

    Args:
        model_name (str): 要測試的model名稱(若為sentence_transformer開頭就可以省略)
    """
    sentences = [
        "這篇文章說明了什麼是語音辨識",
        "本研究使用語音識別技術來解決問題",
        "這篇論文沒什麼用",
        "這篇論文嘗試了三種模型，並比較他們的效果",
        "有些ontology不會被上傳到網路上",
        "本論文使用中醫知識圖譜來建立問答系統",
        "RAG技術可以用於專業領域的問答",
        "QA系統可以使用以下三種技術來實現",
        "這篇論文提出一個聊天機器人架構"
    ]
    question = [
        "什麼是語音辨識",
        "哪些論文與問答系統有關",
        "哪些研究與問答系統有關"
    ]
    # data = load_dataset("myQA.xlsx")
    # question = trans_dataset(data)
    # print(question)
    multiple_compare(model_name, sentences, question="llama支援中文嗎?")
    # multiple_compare(model_name, sentences, question)

def load_dataset(file_path:str)->pd.DataFrame:
    import pandas as pd
    if "xlsx" in file_path:
        # 讀取excel的第一張表
        df = pd.read_excel(io=file_path, index_col=0, sheet_name=0, keep_default_na=None)
    else:
        df = pd.read_csv(file_path=file_path, index_col=0)
    print("讀取完畢")
    print(df.info())
    return df



def trans_dataset(data:pd.DataFrame, col:str="問題")->list:
    """將pd.DataFrame中的特定行轉成list

    Args:
        data (pd.DataFrame): _description_

    Returns:
        list: df中特定行轉成list
    """
    import pandas as pd
    question_list = data[col].tolist()
    return question_list





from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse as urlparse

def my_func(query: str):
    result_dict = chain.invoke(query)
    final_result = result_dict["answer"] + "\n"
    for document in result_dict["context"]:
        final_result = final_result + "參考: " + document.metadata["source"] + "#" + document.metadata["標題1"] + "\n"
    return final_result


class RequestHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        # 用於處理嵌入server的相關初始化設定
        parsed_path = urlparse.urlparse(self.path)
        params_dict = urlparse.parse_qs(parsed_path.query)

        if "model_id" not in params_dict:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write('{"error": "缺少參數: model_id"}'.decode())
            
        else:
            global model_name
            global embedded_model
            global tokenizer
            # 正式開始載入嵌入模型
            new_model_name = params_dict["model_id"][0]
            print(new_model_name)
            if new_model_name in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
                print("警告:設定使用要付費的openapi")
                model_name = new_model_name
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                import json
                response = json.dumps({"max_length": 8192, "dim":3072 if model_name == "text-embedding-3-large" else 1536})
                self.wfile.write(response.encode())
            else:
                if model_name != new_model_name:
                    if embedded_model != None:
                        # 釋放
                        import torch
                        del embedded_model
                        torch.cuda.empty_cache()
                    model_name = new_model_name
                    trust_remote_code = True if "jina-embeddings-v2-base-zh" in new_model_name else False
                    embedded_model = SentenceTransformer(model_name, cache_folder="../Taiwan-LLM/data", trust_remote_code=trust_remote_code)
                    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_folder="../Taiwan-LLM/data")
                print(type(embedded_model))
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                import json
                response = json.dumps({"max_length": embedded_model.get_max_seq_length(), "dim":embedded_model.get_sentence_embedding_dimension()})
                self.wfile.write(response.encode())
    
    def do_POST(self):
        """用post接受嵌入請求
        """
        # 讀data，參考 https://www.cnblogs.com/howardwu/p/11160436.html
        import json
        request_data = self.rfile.read(int(self.headers['content-length']))
        request_data = json.loads(request_data.decode())
        # 考慮參數: sentences:list[str], query:str=None
        
        # 嵌入
        if model_name in ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"]:
            embedded_result, token_length = embedded_from_openai(request_data.get("sentences"), model_name)
        else:
            embedded_result, token_length = embedded_from_st(
                sentences=request_data.get("sentences"),
                query=request_data.get("query", ""),
                prefix=request_data.get("prefix","")
            )
        import hashlib
        print("token_len:", token_length)
        print(len(embedded_result))
        # print(hashlib.sha256(embedded_result).hexdigest())
        #print(embedded_result[0][1])
        # 將嵌入結果轉成base64確保傳輸正確
        # 參考 https://stackoverflow.com/questions/6485790/numpy-array-to-base64-and-back-to-numpy-array-python
        import base64
        import numpy as np
        b64 = base64.b64encode(embedded_result.tobytes())
        response = json.dumps({
            "base64":b64.decode(),
            "shape": embedded_result.shape,
            "dtype": str(embedded_result.dtype),
            "sha256": hashlib.sha256(embedded_result).hexdigest(),
            "token_length": token_length
        })
        # 回傳結果 (用base64)
        self.send_response(200) # 順序有差
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode())
        
        

def run(server_class=HTTPServer, handler_class=RequestHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting httpd server on port {port}')
    httpd.serve_forever()

if __name__ == "__main__":
    run()  
    # model_test("jinaai/jina-embeddings-v2-base-zh")
    # model_test("paraphrase-MiniLM-L3-v2")
    # model_test("all-mpnet-base-v2")
    # model_test("moka-ai/m3e-large") # large、base、small
    # model_test("all-MiniLM-L6-v2")
    # model_test("text-embedding-ada-002")
    # model_test("infgrad/stella-large-zh-v3-1792d")
    # model_test("intfloat/e5-large-v2")
    # model_test("embed-multilingual-v3.0")

"""
本module處理LLM相關功能
"""

import requests
# import os
# os.environ["LANGCHAIN_TRACING_V2"]="true"
# os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
# os.environ["LANGCHAIN_API_KEY"]="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"
# os.environ["LANGCHAIN_PROJECT"]="RetrievalTest"

class llm(object):
    """
    LLM模組，由FastAPI呼叫，以http提供服務，模擬外部功能
    """
    def __init__(self, config:dict=None, model_name:str=None, mode="openai"):
        """LLM模組初始化，提供給FastAPI使用
        """
        self.config = None
        self.model_name = model_name
        self.url = None
        # 如果初始化時未提供config則重新讀取
        if config == None: 
            from modules.utils import read_config
            self.config = read_config()["llm"]
        else:
            self.config = config
        
        # 設定mode，包含openai及transformers，目前僅實作openai
        self.mode = mode
        
    def set_model(self):
        """初始化langchain的chat model
        根據model_name決定使用openai的base_url還是config中的url
        """
        
        if self.mode == "openai":
            if "gpt" in self.model_name:
                self.base_url = "https://api.openai.com/v1" if self.url == None else self.url
            else:
                self.base_url = (self.config["tgi_url"] + "/v1" ) if self.url == None else self.url
            self.url = self.base_url
            from langchain_openai import ChatOpenAI
            import os
            os.environ["OPENAI_API_KEY"] = self.config["OPENAI_API_KEY"]
            self.chat_model = ChatOpenAI(openai_api_base=self.base_url, model_name=self.model_name, seed=1, temperature=0)
        
        elif self.mode == "tgi": # 使用tgi的generate (HuggingFaceEndpoint)
            tgi_url = self.config["tgi_url"] if self.url == None else self.url
            model_name = self.get_model_name(url=tgi_url)
            self.model_name = model_name 
            self.url = tgi_url
            from langchain_community.llms import HuggingFaceEndpoint
            stop_list = []
            if "Llama3" in model_name:
                stop_list = ["<|start_header_id|>", "<|end_header_id|>", "<|eot_id|>", "<|reserved_special_token"]
            llm = HuggingFaceEndpoint(
            endpoint_url=self.url,
            max_new_tokens=256,
            do_sample=False, # 關閉採樣
            top_k=1,
            top_p=0.1,
            temperature=0.1, # 已經關閉採樣了所以其實設多少都沒差
            # truncate=1024,  # 截斷 512 Tokens 以前的輸入
            seed=1,
            stop_sequences=stop_list
            # details=True, # stream比較常用?
            # return_full_text=True, # 回傳內容包含輸入(prompt)
            )
            from langchain_community.chat_models.huggingface import ChatHuggingFace
            self.chat_model = ChatHuggingFace(llm=llm, model_id=model_name)
        
        elif self.mode == None:
            print("未設定mode")
        else:
            print(f"未設定合法的mode:{self.mode}，LLM初始化失敗")
            exit()
            
    def chat(self, input, system_message:str="你是一位樂於助人的IA助手"):
        """聊天，以langchain的chat_model.invoke實現
        
        return (dict): 包含
        content='資訊不足' 
        response_metadata={'token_usage': 
                {'completion_tokens': 3, 
                'prompt_tokens': 207, 
                'total_tokens': 210}, 
            'model_name': 'MediaTek-Research/Breeze-7B-Instruct-v0_1', 
            'system_fingerprint': '2.0.2-sha-9546534', 
            'finish_reason': 'eos_token', 
            'logprobs': None} 
        id='run-be35777d-f829-4246-b652-c84f93ec0a63-0'
        """
        message_list = [{"role":"system", "content":system_message}, {"role":"user", "content":input}]
        if system_message == "" or system_message is None:
            message_list = [message_list[1]]
        if self.chat_model != None:
            return self.chat_model.invoke(message_list)
        else:
            self.set_model()
            return self.chat_model.invoke(message_list)
        
    def get_model_name(self, url="http://localhost:8080")->str:
        """回傳8080端口中運行的tgi中正在使用的模型名稱
        註：要求TGIv1.4^

        Returns:
            str: 模型名稱
        """
        import requests
        response = requests.get(url+"/info")
        model_name = response.json()["model_id"]
        dtype = response.json()["model_dtype"]
        print("model_id:", model_name)
        print("model_dtype: ", dtype)
        return model_name
    
    def is_type(self, input:str, type:list=["date"])->bool:
        """根據過濾type中列出的條件過濾input並回傳bool值
        基於langchain的bool

        Args:
            input (str): _description_
            type (list, optional): _description_. Defaults to ["date"].
        
        Returns:
            bool: 是否符合type中列出的條件
        """
        # TODO: 未完成，應該是使用langchain中實做self-query的方法。
        pass
    
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
    
def get_context(file_name: str, title:str) -> str:
    """用於載入真正的context，理論上之後不會用到"""
    print("1", file_name, title)
    file_name = file_name[0]
    file_path = "/home/domaj/ObsidianSync/" + file_name + ".md"
    with open(file_path, "r", encoding="utf-8") as f:
        blocks = f.read().split("# ") # 這樣切無法處理二階標題，目前採用手動處理
        for block in blocks:
            block = "# " + block
            if title in block:
                return block

def new_dataset(noteqa_simple):
    """用於載入真正的context，理論上之後不會用到"""
    dataset_df = noteqa_simple["train"].to_pandas()
    dataset_df["context"] = dataset_df.apply(lambda x: get_context(x["參考"], x["標題1"]), axis=1)
    dataset_df.to_csv("noteqa2.csv")

def lab_generate(model_name:str, rag_prompt:str):
    """生成llm模型缺少的回答，並將生成結果儲存成RAGAS格式
    return (dict): RAGAS處理格式
    """
    # 初始化llm
    llm_obj = llm(model_name=model_name)
    print("使用模型:", model_name)
    quan_method = input("量化方法:")
    # 載入資料集
    import pandas as pd
    from tqdm import tqdm
    noteqa_df = pd.read_csv("./data/noteqa2.csv", index_col=0)
    #df = pd.read_excel("./data/lab_llm.xlsx", index_col=0, dtype="str")
    df_result = pd.read_excel("./data/rag_prompt_test.xlsx", index_col=0)
    df_result.fillna("", inplace=True)
    # 初始化進度條
    progress = tqdm(total=len(noteqa_df), desc="生成進度")
    # RAGAS資料準備
    result = {"answer":[],
              "ground_truth":[],
              "question":[]}
    # 開始生成
    from modules.utils import check_by_parameter
    for index, row in noteqa_df.iterrows():
        progress.update(1)
        if check_by_parameter(df_result, {"模型": model_name, "量化":quan_method, "USER": row["問題"], "prompt": rag_prompt}):
            result["answer"].append(df_result.loc[(df_result["模型"]==model_name) & (df_result["量化"]==quan_method) & (df_result["USER"]==row["問題"]) & (df_result["prompt"]==rag_prompt), "回答"].values[0])
            result["ground_truth"].append(row["答案"])
            result["question"].append(row["問題"])
            continue
        # 取得正確context
        context = row["context"]
        # 生成
        from langchain_core.prompts import PromptTemplate
        prompt = PromptTemplate.from_template(rag_prompt)
        query = row["問題"]
        answer = llm_obj.chat(input=prompt.format(context=context, query=query)).content
        ## 儲存到dict
        result["question"].append(query)
        result["answer"].append(answer)
        result["ground_truth"].append(row["答案"])
        ## 儲存到df
        new_row_df = pd.DataFrame([{"模型": model_name,
                                    "量化": quan_method,
                                    "prompt": rag_prompt,
                                    "USER": query,
                                    "回答": answer}]) # https://stackoverflow.com/questions/75956209/error-dataframe-object-has-no-attribute-append
        df_result = pd.concat([df_result, new_row_df], ignore_index=True)
        df_result.to_excel("./data/rag_prompt_test.xlsx")
    return result
def lab_eval(eval_promt:str):
    """評估llm模型的準確度
    """
    # 初始化llm
    from openai import OpenAI
    openai_client = OpenAI()
    # 載入資料集
    import pandas as pd
    from tqdm import tqdm
    noteqa_df = pd.read_csv("./data/noteqa2.csv", index_col=0)
    result_df = pd.read_excel("./data/lab_llm.xlsx", index_col=0, dtype="str")
    result_df.fillna("", inplace=True)
    #for column in ["模型", "量化", "問題類別", "USER", "SYS", "prompt", "回答", "生成日期", "框架"]:
    #    if column not in df.columns.to_list():
    #        df[column]=""
    
    # 初始化進度條
    progress = tqdm(total=len(result_df), desc="評估進度")
    # 開始生成
    # 紀錄花費token
    total_input_tokens = 0 
    total_output_tokens = 0
    from modules.utils import check_by_parameter
    for index, row in result_df.iterrows():
        print(index)
        progress.update(1)
        # 評估
        if row["gpt-4o評估"] != "":
            continue
        ## 自訂評估
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": eval_promt.format(answer=row["答案"], result=row["回答"], query=row["query"])},
            ]
        )
        total_input_tokens += response.usage.prompt_tokens
        total_output_tokens += response.usage.completion_tokens
        ### 儲存到df
        row["gpt-4o評估"] = response.choices[0].message.content
        result_df.to_excel("lab_llm.xlsx")
    # 儲存excel
    print("評估結束")
    print(f"輸入tokens:{total_input_tokens}, 輸出tokens:{total_output_tokens}")
    from modules.utils import get_usdt_twd
    usdt_twd = get_usdt_twd()
    input_price = total_input_tokens / 1000000 * 5 * usdt_twd 
    output_price = total_output_tokens / 1000000 * 15 * usdt_twd
    print(f"分別花費{input_price}、{output_price}")
    
def lab_eval_ragas(result_dict:dict={}):
    # RAGAS評估
    # 須實驗RAGAS花費的token: 14727+119
    from datasets import Dataset 
    from ragas.metrics import answer_similarity, answer_correctness
    from ragas import evaluate
    import pandas as pd
    from langchain.chat_models import ChatOpenAI
    # dataset = Dataset.from_dict(result_dict)
    # score = evaluate(dataset,metrics=[answer_correctness], llm=llm)
    # ragas_result_df = score.to_pandas()
    # print(type(ragas_result_df))
    # print(ragas_result_df)
    # ragas_result_df.to_excel("./data/ragas_result_gpt_4o.xlsx")
    # 已經評估後
    ragas_result_df = pd.read_excel("./data/ragas_result.xlsx")
    
    llm_result_df = pd.read_excel("./data/rag_prompt_test.xlsx", index_col=0)
    print(ragas_result_df.info())
    from math import isnan
    from tqdm import tqdm
    
    for index, row in tqdm(llm_result_df.iterrows(), desc="移動資料"):
        # if row["answer_correctness"] != None:
        #     if not isnan(row["answer_correctness"]):
        #         continue
        answer = row["回答"]
        question = row["USER"]
        llm_result_df.at[index,"ragas-gpt-4o"] = ragas_result_df[(ragas_result_df["answer"]==answer)& (ragas_result_df["question"]==question)]["answer_correctness"].values[0]
    llm_result_df.to_excel("./data/rag_prompt_test_check.xlsx")

def auto_eval_by_ragas():
    # 載入資料集
    import pandas as pd
    qa_df = pd.read_csv("./data/noteqa2.csv", index_col=0)
    # 載入生成資料
    llm_result_df = pd.read_excel("./data/rag_prompt_test.xlsx", index_col=0)
    llm_result_df.fillna("", inplace=True)
    # # 載入評估資料
    # ragas_result_df = pd.read_excel("ragas_result1.xlsx", dtype="str")
    # llm_result_df.fillna("", inplace=True)
    # 格式初始化
    result_dict = {"answer":[],
              "ground_truth":[],
              "question":[]}
    
    # 格式轉換
    from tqdm import tqdm
    progress = tqdm(len(llm_result_df), desc="評估進度")
    for index, row in llm_result_df.iterrows():
        progress.update(1)
        question = row["USER"]
        ground_truth = qa_df[qa_df["問題"]==question]["答案"].values[0]
        answer = row["回答"]
        
        # llm_result_df.at[index,"answer_correctness"] = ragas_result_df[(ragas_result_df["answer"]==answer)& (ragas_result_df["question"]==question)]["answer_correctness"].values[0]
        result_dict["answer"].append(row["回答"])
        result_dict["ground_truth"].append(ground_truth)
        result_dict["question"].append(question)
        if len(row["回答"]) == 0 or len(ground_truth) == 0 or len(question) == 0:
            print(row)
    llm_result_df.to_excel("rag_prompt_test1.xlsx")
    # # 自動評估
    # import os
    # os.environ["OPENAI_API_KEY"] = self.config["OPENAI_API_KEY"]
    # from datasets import Dataset 
    # from ragas.metrics import answer_similarity, answer_correctness
    # from ragas import evaluate
    
    # dataset = Dataset.from_dict(result_dict)
    # score = evaluate(dataset,metrics=[answer_correctness], raise_exceptions=False)
    # result = score.to_pandas()
    # result.to_excel("ragas_result1.xlsx")
    # print(type(result))
    # print(result["answer_correctness"])

def fill_miss_data():
    # 載入生成資料
    import pandas as pd
    ragas_result = pd.read_excel("./ragas_result2.xlsx", index_col=0)
    ragas_result.fillna(-1, inplace=True)
    # 格式初始化
    result_dict = {"answer":[],
              "ground_truth":[],
              "question":[]}
    for index, row in ragas_result.iterrows():
        print(type(row["answer_correctness"]))
        print(row["answer_correctness"])
        if row["answer_correctness"] == -1:
            result_dict["answer"].append(row["answer"])
            result_dict["ground_truth"].append(row["ground_truth"])
            result_dict["question"].append(row["question"])
    import os
    os.environ["OPENAI_API_KEY"] = self.config["OPENAI_API_KEY"]
    from datasets import Dataset 
    from ragas.metrics import answer_similarity, answer_correctness
    from ragas import evaluate
    
    dataset = Dataset.from_dict(result_dict)
    score = evaluate(dataset,metrics=[answer_correctness], raise_exceptions=False)
    result = score.to_pandas()
    result.to_excel("ragas_result3.xlsx")
    print(type(result))
    print(result["answer_correctness"])
    
def statistics_ragas_result():
    # 載入資料
    import pandas as pd
    df = pd.read_excel("./data/rag_prompt_test.xlsx", index_col=0)
    df.fillna("", inplace=True)
    result = {}
    # 遍歷資料，儲存
    for index, row in df.iterrows():
        model = row["模型"]
        quan = row["量化"]
        score = row["answer_correctness"]
        if model not in result.keys():
            result[model] = {}
        if quan not in result[model].keys():
            result[model][quan] = {"題數":0, "總分":0}
        result[model][quan]["題數"] += 1
        result[model][quan]["總分"] += score
    print(result)
    for model in result.keys():
        for quan in result[model].keys():
            if result[model][quan]["題數"] != 36:
                print("error", model, quan)
            print(model, quan, result[model][quan]["總分"] / result[model][quan]["題數"])
    #{'qwen1_5-32b-chat': 
    #   {'q8_0': {'題數': 36, '總分': 15.464842405911147}, 
    #   'q2_k': {'題數': 36, '總分': 16.049334214912427}}, 
    # 'gpt-4o-2024-05-13': {nan: {'題數': 36, '總分': 14.846062112477535}}, 
    # 'gpt-4-turbo-2024-04-09': {nan: {'題數': 36, '總分': 16.373953899758604}}, 
    # 'gpt-3.5-turbo-0125': {nan: {'題數': 36, '總分': 15.406720368162548}}, 
    # 'yi-34b-chat': {'q2_k': {'題數': 36, '總分': 16.232704081913365}, 
    # 'q8_0': {'題數': 36, '總分': 14.630202901808067}}, 
    # 'taide/Llama3-TAIDE-LX-8B-Chat-Alpha1': {'eetq': {'題 數': 36, '總分': 15.004913548807062}},
    # 'MediaTek-Research/Breeze-7B-Instruct-v0_1': {'eetq': {'題數': 36, '總分': 16.254060950399985}},
    # 'meta-llama/Meta-Llama-3-8B-Instruct': {'eetq': {'題數': 36, '總分': 18.199501947770923}},
    # 'MediaTek-Research/Breeze-7B-Instruct-v1_0': {'eetq': {'題數': 36, '總分': 14.358136408772268}}}
    
    
    
if __name__ == "__main__":
    # ragas實驗
    # RAGAS評估
    # 須實驗RAGAS花費的token: 14727+119
    # fill_miss_data()
    #auto_eval_by_ragas()
    
    #statistics_ragas_result()
    # exit()
    
    # 以下為自動評估實驗
    print("llm模組評估")
    from modules.utils import read_config
    llm_list = ["gpt-4o-mini"] # gpt-4o-mini MediaTek-Research/Breeze-7B-Instruct-v0_1
    # result = lab_generate(model_name = llm_list[0], 
    #                       rag_prompt="不要使用參考文獻以外的知識或資訊。若資訊不足請回答「資訊不足」。\n==參考文獻==\n{context}\n\n==問題==\n根據上文，{query}\n請用20個字簡潔回答問題。")
    # lab_eval(model_name=llm_list[0],
    #     eval_promt="請幫我比對學生的回答與正確答案是否相符，不可包函正確答案以外的資訊。相符則輸出「O」，不符則輸出「X」，包含外部資訊則輸出「△」。問題:{query}\n正確答案:{answer}\n學生回答:{result}\n"
    # )
    # lab_eval_ragas() # 結果不好，可紀錄到論文中
        
    # 用了72096輸入，9809生成的GPT3.5，0.05美，還有嵌入


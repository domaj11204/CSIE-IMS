"""
作為使用者前端介面，考量到之後可能會有更細緻的操作(可選prompt、可移動模板)等，因此遲早要換成flask等更高自由度的框架。(2024/04/10)
可參考官方教學https://www.gradio.app/main/guides/quickstart#custom-demos-with-gr-blocks
"""

import gradio as gr
import random
import time
import requests
import datetime

# log文件設定
import logging
logFileName = "./log/webui_"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
logging.basicConfig(filename=logFileName, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')

# 動態特效XD
js = """
function createGradioAnimation() {
    var container = document.createElement('div');
    container.id = 'gradio-animation';
    container.style.fontSize = '2em';
    container.style.fontWeight = 'bold';
    container.style.textAlign = 'center';
    container.style.marginBottom = '20px';

    var text = '可重配置資訊管理系統';
    for (var i = 0; i < text.length; i++) {
        (function(i){
            setTimeout(function(){
                var letter = document.createElement('span');
                letter.style.opacity = '0';
                letter.style.transition = 'opacity 0.5s';
                letter.innerText = text[i];

                container.appendChild(letter);

                setTimeout(function() {
                    letter.style.opacity = '1';
                }, 50);
            }, i * 250);
        })(i);
    }

    var gradioContainer = document.querySelector('.gradio-container');
    gradioContainer.insertBefore(container, gradioContainer.firstChild);

    return 'Animation created';
}
"""

def data_generator(df):
    # 用生成器遍歷df
    for idx in df.index:
        yield df.loc[idx]

from modules.utils import read_config
from modules.debug_utils import print_var
from modules.utils import call_api
config = read_config()


"""暫時關閉評估結果
import pandas as pd
df_llm_test = pd.read_excel("./data/rag_prompt_test.xlsx", index_col=0, dtype=str) # padas的內存好像無法釋放，因此乾脆直接讀一個一直用?
df_llm_test.fillna("", inplace=True)
print("llm_test.xlsx讀取完成")
print(df_llm_test.info())
generator_eval = data_generator(df_llm_test)
"""
# df_eval = pd.read_excel("./data/llm_eval.xlsx", index_col=0)
# df_eval.fillna("", inplace=True)

with gr.Blocks(theme=gr.themes.Soft(), js=js) as demo:
    with gr.Tab(label="實驗"):
        cypher = gr.Textbox("Cypher")
        gr_df = gr.Dataframe()
        def run_cypher(cypher):
            from modules.neo4j import neo4jDB
            DB = neo4jDB(config["neo4j"]["url"], config["neo4j"]["user"], config["neo4j"]["password"])
            return DB.cypher_test(cypher)
        cypher.submit(run_cypher, [cypher], [gr_df])
    """暫時關閉之前的聊天設定
    with gr.Tab(label="聊天"):
        with gr.Row():
            with gr.Column():
                # 放各種設定
                model_name = gr.Dropdown(choices=["TGI", "ChatGPT-3.5-turbo", "LM Studio"], label="模型")
                mode = gr.Dropdown(choices=["一般聊天", "RAG"], label="模式", value="一般聊天")
                source = gr.CheckboxGroup(["論文", "摘錄", "筆記", "瀏覽紀錄"], label="資料來源", visible=False)
                text = gr.Text(label="輸入訊息")
                def mode_change(mode):
                    if mode == "RAG":
                        return gr.update(visible=True)
                    else:
                        return gr.update(visible=False)
                    
                    
                mode.change(mode_change, [mode], [source])
                        
            with gr.Column():
                # 放對話框        
                chat_bot = gr.Chatbot(show_copy_button=True, sanitize_html=False)
                msg = gr.Text()
                clear = gr.Button("Clear")

        def user(user_input, history):
            return "", history+[[user_input, None]]
        
        async def bot(history, model_name, mode, source):
            # bot_message = requests.get("http://localhost:27711/test", headers={'accept': 'text/*'}).text
            from modules.chat import chat
            
            if mode == "RAG":
                print("webui.py: query:", history[-1][0])
                print("webui.py: source_list:", source)
                from modules.utils import call_api
                response = await call_api("v1/rag/query", "post", {"query": history[-1][0], 
                                            "source_list": source})
                print("webui.py: response:", response)
                bot_message = await call_api("v1/rag/reference_synthesis", "post", data=response)
                bot_message = bot_message["result"]
            elif mode == "Search":
                chatter = chat(config=config["llm"])
                bot_message = chatter.chat(history=history, 
                                        setting={"model":model_name, "mode":mode, "source":source})
            history[-1][1] = bot_message
            
            return history
        
        msg.submit(user, [msg, chat_bot], [msg, chat_bot]).then(
            bot, [chat_bot, model_name, mode, source], chat_bot
        )
        clear.click(lambda: None, None, chat_bot, js="function (){console.log(\"OHHHHHHHHH\")}")
        """
    with gr.Tab(label="知識庫"):
        with gr.Row("知識庫搜尋"):
            with gr.Column("設定"):
                # TODO: 根據設定自動生成，或是跟知識庫確認
                # 好像無法直接用非同步，所以會卡住，考慮將gradio和fastapi分開
                source_list = gr.CheckboxGroup([
                    ("Obsidian", "obsidian"), 
                    ("Neo4j", "neo4j"), 
                    ("Bib", "bib"), 
                    ("History", "history"), 
                    ("Log", "log"),
                    ("RDF", "rdf")], 
                    label="來源")
                type_list = gr.CheckboxGroup([
                    "筆記", "摘錄", "參考文獻", "瀏覽紀錄", "終端機紀錄", "知識本體"], 
                    label="類別")
                search_type = gr.Dropdown(choices=[("關鍵字搜尋", "keyword"), ("模糊搜尋", "fuzzy"), "RAG", "UUID"], value="keyword", label="搜尋類型")
                with gr.Column("RAG設定", visible=False) as rag_setting:
                    with gr.Row("模型選擇"):
                        llm = gr.Dropdown(choices=["GPT-4o", "Breeze-7B"], label="LLM模型", value="GPT-4o")
                        embedded = gr.Dropdown(choices=["BAAI/bge-m3", "moka-ai/m3e-large"], label="嵌入模型", value="BAAI/bge-m3")
                    with gr.Row("檢索設定"):
                        top_k = gr.Slider(0, 10, value=3, label="Top-K", step=1)
                        pre_retriever = gr.CheckboxGroup([("Self Query", "self_query")], label="檢索前處理")
                        retriever = gr.Dropdown(choices=[("Cosine Similarity", "similarity"), ("MMR", "mmr")], label="檢索方法", value="similarity")
                        post_retriever = gr.CheckboxGroup([("LLM Filter", "LLM_filter")], label="檢索後處理")
                    # TODO: 把讀設定改成API，但有非同步問題
                    from modules.utils import read_config
                    prompt_config = read_config()["rag"]["prompt_template"]
                    prompt = gr.Textbox(prompt_config, label="Prompt")
                    
            with gr.Column("查詢"):
                def chat(user_input, history):
                    return "", history+[[user_input, None]]
                async def bot(history, search_type, source_list, type_list, llm, embedded, top_k, pre_retriever, retriever, post_retriever, prompt):
                    debug_mode = True
                    input = history[-1][0]
                    import time
                    if search_type == "RAG":
                        response = await call_api("v1/rag/query", "post", data={"source_list":source_list, 
                                                                           "type_list": type_list, 
                                                                           "query":input,
                                                                           "llm": llm,
                                                                           "embedded": embedded,
                                                                           "top_k":top_k,
                                                                           "pre_retriever":pre_retriever,
                                                                           "retriever":retriever,
                                                                           "post_retriever":post_retriever,
                                                                           "prompt": prompt}, debug_mode=debug_mode)
                        bot_message = (await call_api("v1/rag/reference_synthesis", "post", data=response, debug_mode=debug_mode))["result"]
        
                    elif search_type == "UUID":
                        url = "v1/knowledge_base/" + input
                        bot_message = await call_api(url, "get")
                    else:
                        print_var(source_list)
                        # TODO: 搜尋參數應該有一個介面可以馬上修改，可能更緩存有關
                        # get params無法傳遞list
                        source_str = ",".join(source_list)
                        type_str = ",".join(type_list)
                        bot_message = (await call_api(f"v1/knowledge_base/search", 
                                                      "get", params={"source_str":source_str, 
                                                                     "type_str":type_str, 
                                                                     "search_type":search_type, 
                                                                     "keyword":input, 
                                                                     "top_k":3}, debug_mode=debug_mode))["result"]
                    history[-1][1] = bot_message
                    return history
                
                def change_search_type(search_type):
                    if search_type == "RAG":
                        return gr.update(visible=True)
                    else:
                        return gr.update(visible=False)
                    
                chat_bot = gr.Chatbot(show_copy_button=True, sanitize_html=False)
                msg = gr.Text()
                msg.submit(chat, [msg, chat_bot], [msg, chat_bot]).then(
                    bot, [chat_bot, search_type, source_list, type_list, llm, embedded, top_k, pre_retriever, retriever, post_retriever, prompt], chat_bot
                )
                search_type.change(change_search_type, [search_type], [rag_setting])
        with gr.Row("知識庫管理"):
            # TODO: 改排版
            # TODO: 來源和類別可以用成類似樹狀圖的按鈕
            with gr.Column("來源"):
                # TODO: 和知識庫拿來源清單
                source_manage = gr.Dropdown(label="來源", choices=["obsidian", "neo4j", "rdf", "reference"], allow_custom_value=True)
            with gr.Column("類別"):
                # TODO: 和知識庫拿類別清單
                type_manage = gr.Dropdown(label="類別", choices=["筆記", "摘錄", "中醫知識本體", "文獻"], allow_custom_value=True)
        with gr.Row(visible=False) as row:
            entity_count = gr.Text(value=-1, label="實體數量")
            load_all_data_btn = gr.Button("載入所有資料") # TODO: 允許一次多個類型貨來源的indexing
            embedded_btn = gr.Button("建立索引")
            delete_index_btn = gr.Button("刪除索引")
            async def source_change(source_manage):
                from modules.utils import call_api
                result = await call_api(f"v1/knowledge_base/entity_count", "get", params={"source":source_manage})
                entity_count = str(result["entity_count"])
                return gr.update(visible=True), entity_count, gr.update(value="")
            async def type_change(type_manage):
                from modules.utils import call_api
                result = await call_api(f"v1/knowledge_base/entity_count", "get", params={"type":type_manage})
                entity_count = str(result["entity_count"])
                return gr.update(visible=True), entity_count, gr.update(value="")
            
            async def load_all_data(source_manage, type_manage):
                """將該來源的所有資料匯入"""
                # TODO: 初次使用時怎麼辦?如何更方便的從頭匯入資料
                from modules.utils import call_api
                if len(source_manage)>0:
                    await call_api(f"v1/knowledge_base/load_data", "post", {"source":source_manage})
                    result = await call_api(f"v1/knowledge_base/entity_count", "get", params={"source":source_manage})
                else:
                    await call_api(f"v1/knowledge_base/load_data", "post", {"type":type_manage})
                    result = await call_api(f"v1/knowledge_base/entity_count", "get", params={"type":type_manage})
                entity_count = str(result["entity_count"])
                return entity_count

            async def indexing(source_manage):
                """將該來源的所有資料切割並嵌入"""
                # TODO: 應該支援type，例如從kb拿到list後依序拿資料?
                from modules.utils import call_api
                print("source_manage:", source_manage)
                result = await call_api(f"v1/knowledge_base/indexing", "post", params={"source":source_manage})
                print("webui.py:indexing:result", result)
            
            async def delete_index(source_manage):
                # FIXME: 未完成
                from modules.utils import call_api
                from modules.debug_utils import print_var
                result = await call_api(f"v1/knowledge_base/indexing/", "delete", {"type":source_manage})
                print_var(result)
            # 必須用select，如果用change只要改變值就會觸發
            source_manage.select(source_change, [source_manage], [row, entity_count, type_manage])
            type_manage.select(type_change, [type_manage], [row, entity_count, source_manage])
            load_all_data_btn.click(load_all_data, [source_manage, type_manage], entity_count)
            embedded_btn.click(indexing, [source_manage], None)
            delete_index_btn.click(delete_index, [source_manage], None)
            
    with gr.Tab(label="嵌入測試"):
        model_name = gr.Dropdown(choices=["moka-ai/m3e-base", "moka-ai/m3e-large"], 
                                label="嵌入模型")
        set_button = gr.Button("載入模型")
        embedded_button = gr.Button("嵌入")
        
        file_path = gr.Textbox(config["embedded"]["path"], label="測試檔案路徑")
        dataset_path = gr.Textbox(config["embedded"]["dataset_path"], label="資料集路徑")
        
        def set_model(model_name):
            from modules.embedded import set_embedded_model
            try:
                set_embedded_model(model_name)
                gr.Info("設定完成")
            except:
                gr.Error("設定錯誤")
                
        def embedded():
            from modules.embedded import embedded
            
        
        set_button.click(set_model, [model_name], None)
        
    with gr.Tab(label="可視化設定"):
        """
        TODO: 用html實現可視化設定，允許拖曳或連線
        with gr.HTML():
        用gradio + 下拉式選單調整嵌入模型、LLM模型、RAG框架的參數
        """
        pass
        
    with gr.Tab(label="評估模型"):
        with gr.Tab(label="競技場"):
            with gr.Row():
                gr.Chatbot(label="A模型")
                    
            pass
        
        """暫時關閉評估結果
        with gr.Tab(label="生成結果評估"):
            question = gr.Dropdown(choices=df_llm_test["USER"].unique().tolist(),
                                   value=df_llm_test["USER"].unique().tolist(),
                                   multiselect=True,
                                   label="過濾問題")
            with gr.Row():
                text_id = gr.Text(label="當前對話id")
                text_model = gr.Text(label="模型")
            chat = gr.Chatbot()
            with gr.Row():
                btn_score_en = gr.Button(value="語言錯誤")
                btn_score_0 = gr.Button(value="不明所以")
                btn_score_1 = gr.Button(value="符合要求但有重大錯誤")
                btn_score_2 = gr.Button(value="輕微錯誤")
                btn_score_3 = gr.Button(value="有效且令人滿意")
                
            btn_next = gr.Button(value="下一筆")
            btn_save = gr.Button(value="儲存")
            index = 0
            
            
            # id_text.value = df.index[index]
            result_dict = {}

            def get_next_data(question):
                # 取得下一筆資料
                import html
                row = next(generator_eval)
                while (row["USER"] not in question) | (row["評分結果"] != ""):
                    row = next(generator_eval)
                prompt = html.escape(row["prompt"]) # 使用html.escape來避免<s>變成刪除線等
                response = html.escape(row["回答"])
                return [[prompt, response]], row.name, row["模型"]
            
            def eval_response(id, button, question):
                global df_llm_test
                df_llm_test.at[int(id), "評分結果"] = button
                df_llm_test.at[int(id), "評分時間"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return get_next_data(question)
            
            def save_df():
                global df_llm_test
                try:
                    gr.Info("儲存中......")
                    df_llm_test.to_excel("./data/llm_test.xlsx")
                    gr.Info("儲存完畢")
                except Exception as e:
                    raise gr.Error(f"儲存出錯{e}")

            
            btn_next.click(get_next_data, [question], [chat, text_id, text_model])
            btn_score_en.click(eval_response, [text_id, btn_score_en, question], [chat, text_id, text_model])
            btn_score_0.click(eval_response, [text_id, btn_score_0, question], [chat, text_id, text_model])
            btn_score_1.click(eval_response, [text_id, btn_score_1, question], [chat, text_id, text_model])
            btn_score_2.click(eval_response, [text_id, btn_score_2, question], [chat, text_id, text_model])
            btn_score_3.click(eval_response, [text_id, btn_score_3, question], [chat, text_id, text_model])
            btn_save.click(save_df, None, None)
        """
    with gr.Tab(label="知識圖譜"):
        btn = gr.Button(value="顯示最新的10個新增的節點")
        gr_df = gr.Dataframe()
        def get_latest_node_from_neo4j():
            from modules.neo4j import neo4jDB
            import pandas as pd
            DB = neo4jDB(config["neo4j"]["url"], config["neo4j"]["user"], config["neo4j"]["password"])
            records = DB.get_latest_node()
            print(records)
            df = pd.DataFrame(DB.records_to_df(records))
            columns_list = df.columns.to_list()
            columns_list.remove("標題")
            columns_list.insert(0, "標題")
            df = df[columns_list]
            return df

        btn.click(fn = get_latest_node_from_neo4j, outputs=gr_df)
        
    with gr.Tab(label="瀏覽紀錄"):
        btn = gr.Button(value="複製History")
        from modules.utils import call_api
        async def copy():
            result = (await call_api("v1/history", "post"))["result"]
            if result:    
                gr.Info("複製完畢")
            else:
                raise gr.Error("複製失敗")
        btn.click(copy, None, None)
        
    with gr.Tab(label="文字設定"):
        from copy import deepcopy
        # 設定頁面，以tabs將yaml中的各個項目分開
        temp_config = deepcopy(config) # 用於暫存設定
        # temp_config = config.copy() # 就算用copy函數也只有第一層是深拷貝，第二層之後還是會引用
        def save_setting():
            """儲存設定"""
            # FIXME: 儲存後要重新載入對應的模組。
            # TODO: 分成套用和儲存，分別只影響這次和修改設定檔
            global config
            config = deepcopy(temp_config) # 先將暫存設定存回config
            try:
                with open("config.yaml", "w") as f:
                    yaml.dump(config, f, allow_unicode=True, width=100)
                gr.Info("儲存完畢")
            except Exception as e:
                raise gr.Error(f"儲存出錯: {e}")
            return
        
        def change_setting(test):
            """何一項設定欄位改變就將值存到temp_config"""
            # 直接操作gradio.components.textbox.Textbox，type(comp)=gradio.components.textbox.Textbox
            comp = list(test.keys())[0] 
            temp_config[comp.elem_classes[0]][comp.label] = test[comp]
            # print(key.value) # 實驗證明，value的值和test[key]的值不同，value的值確實是不會改變的預設值
        
        with gr.Tabs():
            with gr.Tab(label="搜尋來源設定"):
                for k, item in config.items():
                    pass
            for k, item in config.items():
                with gr.Tab(label=k):
                    for key, value in item.items():
                        # 根據設定中的行數調整textbox的行數
                        setting=gr.Textbox(str(value), label=key, elem_classes=[k], lines=str(value).count("\n")+1)
                        setting.change(change_setting, inputs={setting}, outputs=None)
                    btn = gr.Button("Save")
                    btn.click(save_setting, None, None)


if __name__ == "__main__":
    demo.launch()
from modules.knowledge_base import source
import requests
from modules.debug_utils import print_func_name, print_var
from modules.utils import call_api
class obsidian_source(source):
    def __init__(self, name: str = "obsidian", config: dict = None) -> None:
        super().__init__(name="obsidian")
        self.authorization = self.config["authorization"] 
        self.url = self.config["url"]
        if "exclude_path" in self.config:
            self.exclude_path = self.config["exclude_path"]
        else:
            self.exclude_path = None

    def test(self):
        response = requests.get(url=self.url+"/active/", headers={"accept":"text/markdown", "Authorization": self.authorization})
        print(response.text)
        return response
        
        
    @print_func_name
    def get_abstract(self, content:str):
        from modules.markdown2 import markdown
        html = markdown(content)
        print(html)
        from lxml import etree
        html = etree.HTML(html)
        
        p = html.xpath("//h1[1]/following-sibling::p[1]/text()")[0]
        print("測試P",p)
        return p
    
    # @print_func_name
    # def search(self, keyword):
    #     markdown = self.get_note(filename=keyword+".md")
    #     return self.get_abstract(markdown)
    
    def get_note(self, filename:str="知識分類.md"):
        response = requests.get(url=self.url+"/vault/"+filename, headers={"accept":"text/markdown", "Authorization": self.authorization})
        if response.status_code != 200:
            raise
        return response.text
        
    @print_func_name
    def new_note(self, content:dict, note_type:str, title:str="標題")->bool:
        import requests
        if note_type == "github":
            with open("./data/obsidian_template/github.txt", "r") as f:
                template = f.read()
                # 取得當前時間，轉換成2024-01-18 13:33的格式
                from datetime import datetime
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                template = template.replace("date :", "date: "+str(now))
                template = template.replace("網址:", "網址: "+content["url"])
                template = template.replace("# 概述\n", "# 概述\n"+content["abstract"]+"\n")
                if len(content["tag"]) > 0:
                    tag_string = ",".join(content["tag"])
                    template = template.replace("tags : github_project","tags : github_project"+","+tag_string)
                url_list = content["url"].split("github.com/")[1].split("/")
                title = url_list[1]
                print(type(template))
                print(len(template))
            

                response = requests.put(url=self.url+"/vault/Github project/"+title+".md", headers={
                    "accept":"*/*",
                    "Content-Type": "text/markdown", # ; charset=UTF-8就算加上也沒用
                    "Authorization": self.authorization}, data=template.encode("utf-8"),
                    )
                if response.ok:
                    return True
                else:
                    response.raise_for_status() # https://docs.python-requests.org/en/latest/user/quickstart/
                    return False
        elif note_type == "term":
            with open("./data/obsidian_template/term.txt", "r") as f:
                template = f.read()
                # 取得當前時間，轉換成2024-01-18 13:33的格式
                from datetime import datetime
                now = datetime.now().strftime("%Y-%m-%d %H:%M")
                template = template.replace("date :", "date: "+str(now))
                template = template.replace("概述", "概述\n" + content["abstract"] + "\n")
                template = template.replace("# 詳細說明", "# 詳細說明\n" + content["description"] + "\n")
                if len(content["tag"]) > 0:
                    tag_string = ",".join(content["tag"])
                    template = template.replace("tags : 術語", "tags : 術語," + tag_string)
                response = requests.put(url=self.url+"/vault/"+title+".md", headers={
                    "accept":"*/*",
                    "Content-Type": "text/markdown", # ; charset=UTF-8就算加上也沒用
                    "Authorization": self.authorization}, data=template.encode("utf-8"),
                    )
                if response.status_code <= 204:
                    return True
                else:
                    print("obsidian error:", response.status_code, response.text)
                    return False
        else:
            response = requests.put(url=self.url+"/vault/實驗用/"+title+".md", headers={
                    "accept":"*/*",
                    "Content-Type": "text/markdown", # ; charset=UTF-8就算加上也沒用
                    "Authorization": self.authorization}, data=content["text"].encode("utf-8"),
                    )
            if response.ok:
                return True
            else:
                response.raise_for_status() # https://docs.python-requests.org/en/latest/user/quickstart/
                return False
        return False
        
    async def get_file_list(self, path:str="/"):
        """遞迴取得所有markdown檔案的路徑"""
        result_list = []
        # 以下內容是OK的，但是口試前只考慮到每日筆記/及實驗用/的筆記
        # result_file = requests.get(url=f"{self.url}/vault{path}", headers={"accept":"application/json", "Authorization": self.authorization}).json()["files"]
        # for result in result_file:
        #     if result.endswith(".md"):
        #         result_list.append({"path":path+result, "name":result.split("/")[-1].replace(".md","")})
        #     if result.endswith("/"):
        #         result_list += self.get_note_list(path+result)
        
        note_file = requests.get(url=f"{self.url}/vault/每日筆記/", headers={"accept":"application/json", "Authorization": self.authorization}).json()["files"]
        lab_file = requests.get(url=f"{self.url}/vault/實驗用/", headers={"accept":"application/json", "Authorization": self.authorization}).json()["files"]
        for note in note_file:
            result_list.append({"path":"每日筆記/"+note, "name":"每日筆記/"+note})
        for lab in lab_file:
            result_list.append({"path":"實驗用/"+lab, "name":"實驗用/"+lab})
        return result_list
    
    async def get_data(self, uuid:str, **kwargs):
        if "path" in kwargs:
            path = kwargs["path"]
        elif "params" in kwargs and "path" in kwargs["params"]:
            path = kwargs["params"]["path"]
        else:
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["path"]
        return self.get_data_by_path(path)
    
    def get_data_by_path(self, path:str):
        response = requests.get(url=self.url + "/vault/" + path, 
            headers={
                "accept": "application/vnd.olrapi.note+json",
                "Authorization": self.authorization
            })
        return response.json()["content"]
    
    def split(self, split_data:source.split_data):
        entity, chunk_size, text, parent_uuid, parent_name, parent_source = super().split_preprocess(split_data)
        if len(text) == 0:
            return []
        from langchain_text_splitters import MarkdownHeaderTextSplitter
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        from uuid import uuid4
        from hashlib import md5
        split_result = [] 
        headers_to_split_on = [
            ("#", "標題1"),
        ]
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on, strip_headers=False)# 用strip_headers=False，保留切割用的header
        # TODO: 改用token切割 https://api.python.langchain.com/en/latest/base/langchain_text_splitters.base.TokenTextSplitter.html
        text_splitter = RecursiveCharacterTextSplitter( # 字分割器
            chunk_size=chunk_size, 
            chunk_overlap=0
        )
        markdown_results = markdown_splitter.split_text(text) # 先用markdown切
        # 再用文字切並將原本的source保留下來
        for markdown_result in markdown_results:
            char_split_contents = text_splitter.split_text(markdown_result.page_content)
            last_uuid = ""
            for index in range(len(char_split_contents)):
                char_split_content = char_split_contents[index]
                char_split_entity = char_split_contents.copy()
                # 建立要儲存在知識庫中的內容
                uuid = str(uuid4())
                if "標題1" in markdown_result.metadata:
                    name = markdown_result.metadata["標題1"] + "_" + str(index)
                    description = parent_name + "-" + markdown_result.metadata["標題1"] + "-" + str(index)
                    head = markdown_result.metadata["標題1"]
                else: # 需要考慮筆記中可能不包含任何標題的情況
                    name = parent_name + "_" + str(index)
                    description = parent_name + "-" + str(index)
                    head = ""
                # TODO: 存入Collection資訊
                # TODO: 將UUID以外的資訊一併hash，包含周圍chunk以外的資訊
                char_split_entity = {
                    "name": name,
                    "description": description,
                    "uuid": uuid,
                    "data_hash": md5(char_split_content.encode()).hexdigest(),
                    "relation": [{"uuid1":uuid, "uuid2":parent_uuid, "relation":"屬於", "properties":{"chunk_size":chunk_size}}],
                    "type": "chunk",
                    "標題1": head
                }
                if index > 0:
                    char_split_entity["relation"].append({"uuid1":uuid, "uuid2":last_uuid, "relation":"上一段"})
                    char_split_entity["relation"].append({"uuid2":uuid, "uuid1":last_uuid, "relation":"下一段"})
                last_uuid = uuid
                # 要儲存在VectorDB中的內容
                metadata = {}
                metadata["uuid"] = uuid
                if "每日筆記" in parent_name: # 每日筆記的話加上metadata
                    # char_split_content.metadata["source"] = char_split_contents["path"]
                    date = entity["path"].replace("\\", "/").split("每日筆記/")[-1].split(".md")[0]
                    try:
                        metadata["year"] = int(date.split("-")[0])
                        metadata["month"] = int(date.split("-")[1])
                        metadata["day"] = int(date.split("-")[2])
                    except:
                        print("日期解析失敗:", date)
                    metadata["parent_source"] = entity["source"]
                    metadata["parent_type"] = entity["type"]
                    if "標題1" in markdown_result.metadata:
                        metadata["標題1"] = markdown_result.metadata["標題1"]
                # TODO: 之後用於實驗markdown改良
                # if "標題1" in char_split_content.metadata and char_split_content.page_content[0] != "#":
                #     char_split_content.page_content = "來自筆記:" + document.metadata["source"] + "\n# " + char_split_content.metadata["標題1"] + "\n" + char_split_content.page_content
                # else:
                #     char_split_content.page_content = "來自筆記:" + document.metadata["source"] + "\n" + char_split_content.page_content
                split_result.append({"entity":char_split_entity, "document":char_split_content, "metadata":metadata})
        return split_result
    def path2uri(self, path:str):
        from urllib.parse import quote_plus
        prefix = "obsidian://open?file="
        path = path.replace('[', '&#91;').replace(']', '&#93;')
        encoded_path = quote_plus(path, safe="/")
        return f"[{path}]({prefix}{encoded_path})"

    async def chunk2uri(self, uuid:str):
        # 取得該chunk所屬
        from urllib.parse import quote_plus
        chunk_data = (await call_api(f"/v1/rag/vectordb/{uuid}", "get"))["data"]
        print_var(chunk_data)
        chunk_relation_list = (await call_api(f"/v1/knowledge_base/relations/{uuid}", "get"))["relations"]
        for relation in chunk_relation_list:
            if relation["r"]["type"] == "屬於":
                path = relation["to"]["path"]
        full_path = path # TODO:理論上應該要加上vault名稱或完整路徑比較好
        if "標題1" in chunk_data["metadatas"][0]:
            # TODO: 這邊依賴chromadb的格式，待改進
            # 可以在rag那邊保留所有list的第一筆
            full_path = full_path + "# " + chunk_data["metadatas"][0]["標題1"]
        full_path = full_path.replace("\\", "/")
        prefix = "obsidian://open?file="
        return prefix + quote_plus(full_path, safe="/")
    
    async def reference_string(self, reference_data:dict):
        uri = await self.chunk2uri(reference_data["uuid"])
        path = reference_data["path"]
        if "head" in reference_data:
            path += "#" + reference_data["head"]
        return f"參考筆記: <a href=\"{uri}\" target=\"_blank\">{path}</a>"
    
    async def get_url(self, uuid:str=None, **kwargs):
        if "path" in kwargs:
            path = kwargs["path"]
        else:
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["path"]
        prefix = "obsidian://open?file="
        path = path.replace('[', '&#91;').replace(']', '&#93;')
        from urllib.parse import quote_plus
        encoded_path = quote_plus(path, safe="/")
        return prefix+encoded_path
        

if __name__ == "__main__":
    obsidian_obj = obsidian_source()
    result_list = obsidian_obj.get_data("每日筆記/2023-07-25.md")
    print(result_list)
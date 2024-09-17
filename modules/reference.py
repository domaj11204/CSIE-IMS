"""
本模組負責將bib等文獻資料儲存到知識庫中
由於文獻資料需要當作摘要的來源，因此需匯入到知識庫中作為節點
TODO: 其實也不一定要當作節點，若來源是API則可能沒有節點?
"""

from modules.knowledge_base import source
class ReferenceSource(source):
    def __init__(self, name:str="reference", file_path:str=None, config:dict=None) -> None:
        super().__init__(name=name)
        # library用於儲存解析完的文獻資料，以list(dict)格式儲存
        # dict中的key包含['Key', 'Item Type', 'Publication Year', 'Author', 'Title', 'Publication Title', 'ISBN', 
        # 'ISSN', 'DOI', 'Url', 'Abstract Note', 'Date', 'Date Added', 'Date Modified', 'Access Date', 'Pages', 
        # 'Num Pages', 'Issue', 'Volume', 'Number Of Volumes', 'Journal Abbreviation', 'Short Title', 'Series', 
        # 'Series Number', 'Series Text', 'Series Title', 'Publisher', 'Place', 'Language', 'Rights', 'Type', 
        # 'Archive', 'Archive Location', 'Library Catalog', 'Call Number', 'Extra', 'Notes', 'File Attachments', 
        # 'Link Attachments', 'Manual Tags', 'Automatic Tags', 'Editor', 'Series Editor', 'Translator', 'Contributor', 
        # 'Attorney Agent', 'Book Author', 'Cast Member', 'Commenter', 'Composer', 'Cosponsor', 'Counsel', 'Interviewer', 
        # 'Producer', 'Recipient', 'Reviewed Author', 'Scriptwriter', 'Words By', 'Guest', 'Number', 'Edition', 'Running Time', 
        # 'Scale', 'Medium', 'Artwork Size', 'Filing Date', 'Application Number', 'Assignee', 'Issuing Authority', 
        # 'Country', 'Meeting Name', 'Conference Name', 'Court', 'References', 'Reporter', 'Legal Status', 'Priority Numbers', 
        # 'Programming Language', 'Version', 'System', 'Code', 'Code Number', 'Section', 'Session', 'Committee', 'History', 'Legislative Body']
        self.library = []
        if file_path != None:
            self.parse_file(file_path)
        elif config != None:
            self.parse_file(config["path"])
        else:
            import yaml
            with open("config.yaml", "r") as f:
                config = yaml.safe_load(f) # 使用safe來避免在yaml中藏惡意程式碼
                file_path = config["reference"]["path"]
                self.parse_file(file_path)
                
    def parse_file(self, file_path:str):
        """根據副檔名讀取文獻檔案
        Args:
            file_path (str): 檔案路徑
        """
        format = file_path.split(".")[-1]
        # bib檔
        if format == "bib":
            # TODO:未完成，由於bibtex的格式問題需要處理比較多東西
            # TODO:可以參考https://github.com/fluffels/bibtex-csv 將bib轉成csv
            import bibtexparser
            # https://bibtexparser.readthedocs.io/en/main/quickstart.html
            self.library = bibtexparser.parse_file(file_path)
            if len(self.library.failed_blocks) > 0:
                print(f"Failed to parse {len(self.library.failed_blocks)} blocks")
            print(f"Parsed {len(self.library.blocks)} blocks, including:"
                f"\n\t{len(self.library.entries)} entries"
                f"\n\t{len(self.library.comments)} comments"
                f"\n\t{len(self.library.strings)} strings and"
                f"\n\t{len(self.library.preambles)} preambles")
        # csv檔
        if format == "csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            df.fillna("", inplace=True)
            # 轉成dict比較好處理
            df_dict = df.to_dict(orient="records")
            self.library = df_dict
            print(df_dict[0].keys())
            print(df_dict[0])
            
    def search(self, keyword:str, field_list:list=["Title"]):
        result = []
        if field_list == None:
            print("未設定field")
        else:
            for record in self.library:
                for field in field_list:
                    if keyword in record[field]:
                        result += [record]
                        print(record)
                        break
        return result
    
    def load_entities(self):
        """將文獻資料轉換成entity格式
        """
        entities = []
        for row in self.library:
            entity = dict(row)
            entity["name"] = row["Title"]
            # TODO: 將一般文獻、軟體等分類
            entity["type"] = "文獻"
            entity["source"] = self.name
            entity["description"] = row["Abstract Note"] if len(row["Abstract Note"]) > 0 else row["Title"]
            for key in list(entity.keys()):
                if entity[key] == "":
                    entity.pop(key)
            entities.append(entity)
        return entities
            
async def test():
    from modules.utils import call_api
    await call_api("v1/reference/reload", "post")
    result = await call_api("v1/reference/", "post", {"path": "./data/reference.csv"})
    print(result)
    await call_api("v1/reference/load/entity", "get")
if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
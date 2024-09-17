from modules.knowledge_base import source 
from modules.debug_utils import print_var
class HistorySource(source):
    def __init__(self, name:str="history", config:dict=None):
        super().__init__(name=name, config=config)
        # self.parse_sqlite(file_path="./data/History.db")
    
    def copy_history(self)->bool:
        """根據history_path複製history檔到data資料夾

        Args:
            config (dict): 只包含chrome的config

        Returns:
            bool: 是否成功複製
        """
        import getpass
        import os
        import platform
        try:
            history_path = self.config["history_path"]
            import shutil
            if history_path == "default" or history_path == "":
                # 設定檔中未使用default或空字串，需使用預設路徑
                user_name = getpass.getuser()
                os_name = platform.system()
                print(os_name)
                # 針對不同平台使用不同的預設路徑
                # 參考: https://www.foxtonforensics.com/browser-history-examiner/chrome-history-location
                if os_name == "Windows":
                    history_path = f"C:/Users/{user_name}/AppData/Local/Google/Chrome/User Data/Default/History"
                elif os_name == "Linux":
                    history_path = f"/home/{user_name}/.config/google-chrome/Default/History"
                elif os_name == "Mac":
                    history_path = f"/Users/{user_name}/Library/Application Support/Google/Chrome/Default/History"
            self.config["history_path"] = history_path
            shutil.copy(history_path, "./data/")
            if os.path.exists("./data/History.db"):
                os.remove("./data/History.db")
            os.rename("./data/History", "./data/History.db")
            print(f"從{history_path}複製History完畢")
        except Exception as e:
            print(f"複製History出錯: {e}")
            return False
        return True
    
    def get_origin_md5(self):
        path = self.config["history_path"]
        from hashlib import md5
        return md5(open(path, "rb").read()).hexdigest()

    def parse_sqlite(self):
        try:
            import sqlite3
            import pandas as pd
            con = sqlite3.connect("./data/History.db")
            # 讀取urls、visits，visited_links意義不明
            # https://datacarpentry.org/python-ecology-lesson/instructor/09-working-with-sql.html
            
            # urls包含id, url, title
            self.urls_df = pd.read_sql_query("SELECT * FROM urls", con, index_col="id")
            # visits包含id, url(id), visit_time, from_visit(id), opener_visit(id)
            self.visits_df = pd.read_sql_query("SELECT * FROM visits", con, index_col="id")
            self.visited_links_df = pd.read_sql_query("SELECT * FROM visited_links", con, index_col="id")
            con.close()
            return True
        except Exception as e:
            print(f"解析History錯誤: {e}")
            return False
    
    def get_title_by_url_id(self, url:int)->str:
        """根據urls的index取得title
        """
        title = self.urls_df.at[url, "title"]
        return title
    
    def get_title_by_url(self, url:str)->str:
        """根據網址取得標題
        """
        mask = self.urls_df["url"].values == url
        title = self.urls_df[mask]["title"].values
        return title
    
    def search_by(self, keyword:str, field:str):
        """搜尋
        """
        mask = self.urls_df[field].str.contains(keyword)
        result = self.urls_df[mask]
        return result
    def get_from(self, url_id:int):
        """根據url_id取得from
        """
        mask = self.visits_df["url"] == url_id
        visits = self.visits_df.loc[mask]
        for _, visit in visits.iterrows():
            if visit["opener_visit"] != 0:
                from_visit_id = visit["opener_visit"]
            if visit["from_visit"] != 0:
                from_visit_id = visit["from_visit"]
            else:
                continue
        try:
            from_url_id = self.visits_df.at[from_visit_id, "url"]
        except:
            return "無法取得", "無法取得"
        return self.urls_df.at[from_url_id, "title"], self.urls_df.at[from_url_id, "url"]
    
    def get_data(self, id:str, preprocess:bool=True):
        """根據id取得該瀏覽紀錄"""
        data = self.visits_df.loc[int(id)]
        print(data.to_dict())
        if preprocess is False:
            return data.to_dict()
        url = self.urls_df.at[data["url"], "url"]
        title = self.get_title_by_url_id(data["url"])
        from_title, from_url = self.get_from(int(id))
        visit_time = data["visit_time"]
        timestamp = (visit_time/1000000)-11644473600
        return {
            "url": url,
            "title": title,
            "from_title": from_title,
            "from_url": from_url,
            "timestamp": timestamp,
        }
        
    def search(self, keyword):
        """實作來源的搜尋方法
        關鍵字可能是網址或標題(可能是部分，回傳最類似的)
        """
        # TODO: 不能這樣寫，可以再找辦法減少讀寫次數 if self.urls_df == None:
        self.parse_sqlite()
        # 先搜尋標題
        title_result = self.search_by(keyword, "title")
        # 再搜尋網址
        url_result = self.search_by(keyword, "url")
        # 整合結果
        min_len = 9999
        min_result = {}
        import pandas as pd
        for url_id, result in pd.concat([title_result, url_result]).iterrows():
            if len(result["url"]) < min_len:
                min_len = len(result["url"])
                min_result["url"] = result["url"]
                min_result["title"] = result["title"]
                min_result["from_title"], min_result["from_url"] = self.get_from(url_id)
        from_url = self
        return f"標題:{min_result['title']}\n網址:{min_result['url']}\n來自標題:{min_result['from_title']}\n來自網址:{min_result['from_url']}"

if __name__ == "__main__":
    history = HistorySource()
    history.parse_sqlite()
    print(history.search("PyTorch"))
    print(history.visits_df.index[:3])
    history.get_data("721341")
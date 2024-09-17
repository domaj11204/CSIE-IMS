from .debug_utils import print_func_name
def read_config():
    """讀取設定檔"""
    import yaml
    config = None
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f) # 使用safe來避免在yaml中藏惡意程式碼
    return config

def get_host_name():
    """使用socket套件取得主機名稱
    預計用於應用程式路徑相關的功能
    """
    import socket
    return socket.gethostname()


def update_or_append_result(df, parameter:dict, result:dict):
    import pandas as pd
    mask = pd.Series(True, index=df.index)
    new_row_dict = {**parameter, **result} # https://stackoverflow.com/questions/1781571/how-to-concatenate-two-dictionaries-to-create-a-new-one
    for key, value in parameter.items():
        if key in df.columns:
            mask &= (df[key]==value)
    if df[mask].empty:
        new_row_df = pd.DataFrame([new_row_dict]) # https://stackoverflow.com/questions/75956209/error-dataframe-object-has-no-attribute-append
        return pd.concat([df, new_row_df], ignore_index=True)
    else:
        for col in new_row_dict.keys():
            df.loc[mask, col] = new_row_dict[col]
        return df

def check_by_parameter(df, parameter:dict):
    import pandas as pd
    # print(parameter)
    mask = pd.Series(True, index=df.index)
    for key, value in parameter.items():
        if key in df.columns:
            mask &= (df[key]==value)
    if df[mask].empty:
        # print("無相符資訊")
        return False
    # print("已有，跳過")
    return True

def get_server_url():
    """從config.yaml取得FastAPI的URL，包含http://但不包含結尾的/
    """
    config = read_config()
    return f"http://{config['FastAPI']['url']}"

def get_usdt_twd():
    # https://vocus.cc/article/64e60932fd8978000128ea10
    try:
        import requests
        import json

        url = "https://api.bitopro.com/v3/tickers/usdt_twd"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            usdt_twd = float(data.get("data").get("lastPrice"))
            print("utils.py:", usdt_twd)
            return usdt_twd
        else:
            return 30
    except:
        return 30

async def call_api(path:str, method:str, data:dict=None, params:dict=None, debug_mode=False):
    try:
        import aiohttp
        if path[0] == "/":
            path = path[1:]
        url = get_server_url() + "/" + path
        if "/embedded/" in url:
            url = url.replace("27711", "27712")
            print("27712!")
        print("call_api:path:", url)
        async with aiohttp.request(method=method, url=url, json=data, params=params) as response:
            result = await response.json()
        if debug_mode:
            from colorama import Fore, init
            import time
            import json
            print(Fore.BLUE + "url:", json.dumps(url, indent=4, ensure_ascii=False))
            print(Fore.BLUE + "data:", json.dumps(data, indent=4, ensure_ascii=False))
            print(Fore.BLUE + "params:", json.dumps(params, indent=4, ensure_ascii=False))
            print(Fore.YELLOW + "call_api:result:", json.dumps(result, indent=4, ensure_ascii=False))
            print(Fore.RESET)
            time.sleep(3)
        return result
    except Exception as e:
        return {"錯誤":"call_api錯誤，"+str(e)}
    
def b64embedding2np(response:dict=None, b64:str=None, dtype=None, shape=None, sha256=None):
    import base64
    import numpy as np
    if response != None:
        b64 = response["base64"]
        dtype = response["dtype"]
        shape = response["shape"]
        sha256 = response["sha256"]
    embedded_result = np.frombuffer(base64.b64decode(b64), dtype).reshape(shape)
    import hashlib
    if hashlib.sha256(embedded_result).hexdigest() != sha256:
        print("嵌入還原錯誤")
        return None
    # print(embedded_result[0][1])
    # print(embedded_result.dtype)
    return embedded_result

def convert_to_absolute_uri(relative_uri:str, base_uri:str=None):
    """將相對(參考)URI轉為絕對URI

    Args:
        relative_uri (str): 相對URI
        base_uri (str, optional): 用於合成的base URI. 預設會根據設定檔設定base
    """
    if "./" in relative_uri:
        import os
        return os.getcwd() + "/" + relative_uri.replace("./", "")
    else:
        return relative_uri
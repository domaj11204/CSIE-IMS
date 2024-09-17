import json
import logging
from modules.neo4j import neo4jDB, pageStruct
import re
import asyncio
from aiohttp import web
APIVersion = 2.1
DB:neo4jDB = None

def set_DB(db):
    """用於將DB資料傳到MessageHandle.py

    Args:
        db (neo4j.GraphDatabase): DB
    """
    
    global DB
    print("set_DB1:", DB, db)
    DB = db
    
    print("set_DB2:", DB, db)
    

def messageHandle(message, DB=DB):
    """用於處理websocket收到的訊息

    Args:
        message (str): 訊息內容
    """
    
    print("messageHandle1: ", DB)
    returnJson = None
    # try Json解析
    try:
        returnJson = json.loads(message)
        logging.debug(returnJson)
    except:
        if message == "ping":
            return
        if returnJson is None:
            print("收到不合法的message")
            logging.error("不合法的message:"+message)
            return
        if returnJson is not None and "APIVersion" in returnJson:
            print("ServerAPI版本:"+APIVersion+"，擴充元件API版本:"+returnJson["APIVersion"])
            logging.error("ServerAPI版本:"+APIVersion+"，擴充元件API版本:"+returnJson["APIVersion"])
            return
        elif "predicate" not in returnJson:
            print("API格式錯誤，原因不明。")
            logging.error("API格式錯誤，原因不明。"+ message)
            return
    
    #action包含: Update, Activate, refresh, Open
    match returnJson["predicate"]:
        case "UpdateTo":
            tabUpdate(returnJson)        
        case "Activate":
            tabTouch(returnJson)
        case "Refresh":
            tabRefresh(returnJson)
        case "Open":
            tabCreate(returnJson)
        case "Close":
            tabClose(returnJson)
        case "Connect":
            logging.info(returnJson["subject"]["name"]+"Connect")
        case "Disconnect":
            logging.info(returnJson["subject"]["name"]+"Disconnect")
        case "ImportGithub":
            asyncio.create_task(importGithub(returnJson))
        case "ExportWebPage":
            print("ExportWebPage: ", DB)
            exportWebPage(returnJson, DB)
        case "ExcerptFrom":
            excerptFrom(returnJson, DB)
            
        case _:
            print("其餘狀況:",str(returnJson))
            logging.error("其餘狀況"+ str(returnJson))
            
               
def tabUpdate(returnJson):
    '''
    更新時要做的處理，未實作
    '''
    showRDF(returnJson)
    return 0

def tabTouch(returnJson):
    '''
    touch，未實作，應該也沒什麼好做的
    '''
    showRDF(returnJson)
    return 0

def tabRefresh(returnJson):
    showRDF(returnJson)
    return 0

def tabCreate(returnJson):
    showRDF(returnJson)
    return 0

def tabClose(returnJson):
    showRDF(returnJson)
    return 0

async def importGithub(returnJson):
    '''
    處理匯入Github專案時的邏輯，將所有API訊息傳給obsidianClient
    returnJson: API所有訊息
    '''
    global obsidianClient
    showRDF(returnJson)
    
    await obsidianClient.send(json.dumps(returnJson))
    return 0

def excerptFrom(returnJson, DB=DB):
    """
    處理匯出摘錄時的邏輯
    - returnJson 所有API相關資訊
    """
    print("excerpt from:",returnJson)
    print("excerptfrom1: ", DB)
    try:
        # DB = neo4jDB(data["neo4j"]["url"], data["neo4j"]["user"], data["neo4j"]["password"])
        DB.createWebFullInfo(pageStruct(0, returnJson["object"]["tabURL"], returnJson["object"]["tabTitle"]))
        tag_list = [s for s in re.split(',| |，',returnJson["subject"]["TagString"]) if s]
        DB.excerptFromTriple(returnJson, tag_list=tag_list)
    except Exception as e:
        print("neo4jDB新增錯誤")
        print(e.with_traceback())
    
def exportWebPage(returnJson, DB=DB):
    '''
    處理匯出整個網頁時的邏輯，其實和excerptFrom幾乎一模一樣\n
    可以考慮合併
    '''
    print("ExportWebPage: ", DB)
    showRDF(returnJson)
    print(returnJson)
    try:
        object = returnJson["object"]
        tag_list = [s for s in re.split(',| |，',object["TagString"]) if s]
        DB.createWebFullInfo(pageStruct(0, object["tabURL"], object["tabTitle"]), description=object["description"], tag_list=tag_list)
        if "github.com" in object["tabURL"]:
            from modules.obsidian import obsidian_source
            obsidian = obsidian_source()
            obsidian.new_note(content={
                "url": object["tabURL"],
                "abstract": object["description"],
                "tag": object["TagString"].split(",")
            }, note_type="github")
    except Exception as e:
        print("neo4jDB新增錯誤")
        import traceback
        print(traceback.format_exc())
    
    
def showRDF(RDFJson):
    '''
    用於處理所有RDF顯示邏輯，以INFO等級將結果輸出到log
    '''
    outputString = ''
    outputString += "("
    
    # Subject
    if "name" in RDFJson["subject"]:
        outputString += RDFJson["subject"]["name"] + ", "
    elif "tabTitle" in RDFJson["subject"]:
        outputString += RDFJson["subject"]["tabTitle"] + ", "
    else:
        outputString += "#RDFERROR, "
        logging.warning("#RDFERROR: "+ str(RDFJson))
    
    # predicate
    if "predicate" in RDFJson:
        outputString += RDFJson["predicate"] + ", "
    else:
        outputString += "#RDFERROR, "
        logging.warning("#RDFERROR: "+ str(RDFJson))
    
    # object
    if "name" in RDFJson["object"]:
        outputString += RDFJson["object"]["name"] + ", "
    elif "tabTitle" in RDFJson["object"]:
        outputString += RDFJson["object"]["tabTitle"] + ", "
    else:
        outputString += "#RDFERROR, "
        logging.warning("#RDFERROR: "+str(RDFJson))
    
    outputString += ")"
    print(outputString)
    logging.info(outputString)
    
async def triple_handler(request):
    """處理http + triple
    TODO: 待處理
    """
    request_json = await request.json()
    print("triple_handler:", request_json)
    print(request_json["subject"])

    global DB
    app_title = request_json["object"]["name"]
    app_name = request_json["object"]["app_name"]
    app_path = request_json["object"]["app_path"]
    
    # 建立軟體節點 軟體->有路徑->摘錄?
    # DB.create_node(name=request_json["subject"]["name"], label = "app", ) # 寫在triple裡面了
    tag_list = [s for s in re.split(',| |，',request_json["subject"]["TagString"]) if s]
    DB.excerptFromTriple(request_json, tag_list=tag_list, app_name = app_name, app_path = app_path, app_title=app_title)
    return web.Response(text="YOYOYO")
    """
        appNames = ["Zotero", "Google Chrome", "Visual Studio Code"]
    for appName in appNames:
        if windowTitle.endswith(f" - {appName}"):
            trueTitle = windowTitle.rsplit(" - ", 1)[0]
            break
    else:
        trueTitle = windowTitle
    """

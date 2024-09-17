/**
 * 整個chrome-extension的背景JS，具體說明請參考chrome-extension service worker
 */

/* 已知的連線事件
1. 瀏覽器內建的開啟分頁功能(和右鍵新分頁不同)，例如開啟擴充功能頁面
    open -> touch -> update -> refresh (翻譯?)
2. 一般的右鍵開啟分頁(但是不切過去)
    open -> update
3. 一般的換頁
    update
4. 換頁但是會另開分頁
    open -> touch -> update
5. 關閉分頁
    close -> touch
6. 從外部連結開啟分頁
TODO: 改成使用webNavigation API
*/

import {sendTriple, callAPI} from "./RNSApi.js";

/**
 * @description 用來記錄record_status
 */
let record_status = false;
let debugMode = true;
let heartBeatInterval

/**
 * 用來記錄所有已知的tab資訊，主要用於紀錄URL和標題，和update的訊息搭配
 */
let allTab = {};

let APIVersion = "1.0"
let userName = "USER"
let returnJson = {}
returnJson["APIVersion"] = APIVersion

// 與知識庫溝通使用的API 
// TODO: server資訊應該額外儲存或有界面可以設定 
function sendEntity(entity){
  console.log("sendEntity")
  let server_host = "10.147.19.2"
  let server_port = "27711"
  fetch('http://' + server_host + ':' + server_port + '/v1/chrome/entity', {
    method: "POST",
    body: JSON.stringify(entity),
    headers: new Headers({'content-type': 'application/json'}),
  }).then((response) => {
    console.log({response})
  });
}

function sendAction(actionInfo, tabInfo={}, openerTabInfo={}){
  console.log("sendAction")
  let server_host = "10.147.19.205"
  let server_port = "27711"
  fetch('http://' + server_host + ':' + server_port + '/v1/chrome/action', {
    method: "POST",
    body: {"action_info": JSON.stringify(actionInfo),
            "tab_info": JSON.stringify(tabInfo),
            "opener_tab_info": JSON.stringify(openerTabInfo)
    },
    headers: new Headers({'content-type': 'application/json'}),
  }).then((response) => {
    console.log({response})
  });
}

// 綁定 toolbar 中 extension 的按鈕活動，用於開關連線
chrome.action.onClicked.addListener(async () => {

  if (record_status) {
    // 關閉連線，並改變icon
    disconnect();
  } else {
    // 開啟連線，並改變icon
    connect();
  }
});

/**
 * 連線時要開啟的監聽器，包含Created、Updated、Activated、Removed、Highlighted、Replaced
 */
function startListener(){
  // 監聽tab被聚焦，此時URL有可能還沒確定，需要再監聽Update
  chrome.tabs.onActivated.addListener(activateTab); 
  

  // 監聽tab的建立，此時URL和group可能還沒確定，需要再監聽Update
  chrome.tabs.onCreated.addListener(createTab);

  // 監聽Highlight，意義未明
  chrome.tabs.onHighlighted.addListener(highlightTab);

  // 監聽replace，意義未明
  chrome.tabs.onReplaced.addListener(replaceTab);

  // 監聽tab更新
  chrome.tabs.onUpdated.addListener(updatedTab);

  // 監聽tab被關閉
  chrome.tabs.onRemoved.addListener(closedTab);
  
  // 監聽導航訊息
  chrome.webNavigation.onCommitted.addListener(navigatedCommitted);
}

/**
 * 關閉連線時停止監聽器，包含Created、Updated、Activated、Removed、Highlighted、Replaced
 */
function stopListener(){
  // 監聽tab的建立
  chrome.tabs.onCreated.removeListener(createTab);
  // 監聽tab更新
  chrome.tabs.onUpdated.removeListener(updatedTab);
  // 監聽tab被聚焦
  chrome.tabs.onActivated.removeListener(activateTab); 
  // 監聽tab被關閉
  chrome.tabs.onRemoved.removeListener(closedTab);
  chrome.tabs.onHighlighted.removeListener(highlightTab)
  chrome.tabs.onReplaced.removeListener(replaceTab)
  chrome.webNavigation.onCommitted.removeListener(navigatedCommitted);
}


/**
 * 連線並啟動錄製
 */
async function connect() {
  if(debugMode) console.dir(allTab)
  
  // 原本使用三元體處理所有API，後來改用RESTful
  // sendTriple({"name": appName}, "Connect", {"name" : serverName})
  // 改成使用RESTful API查詢伺服器是否已開啟
  callAPI("v1/chrome/", "get")
    .then((response) => {
      console.log({response})
      if(response["status"]=="ok"){
        chrome.notifications.create({
          type: 'basic',
          message: "連線成功",
          iconUrl: 'icons/socket-inactive.png',
          title: '成功'
        })
        record_status = true
        chrome.action.setIcon({ path: 'icons/socket-active.png' });
        // 初始化所有tab資訊
        chrome.tabs.query({})
        .then((tabList) => {
          console.dir(tabList)
          for( let i = 0 ; i < tabList.length ; i++){
            let tabInfo = tabList[i];
            allTab[tabInfo["id"].toString()] = {
              "title": tabInfo["title"],
              "url": tabInfo["url"]
            }
          }
        });
        // 開啟監聽器
        startListener();
      }
      // 連線失敗則跳出未連線訊息
      else{
        chrome.notifications.create({
          type: 'basic',
          message: "連線失敗，請確認伺服器是否已開啟",
          iconUrl: 'icons/socket-inactive.png',
          title: '連線錯誤'
        })
      }
    })
}


/**
 * 關閉連接函數
 */
function disconnect() {
  
  if (record_status) {
    //sendTriple({"name": appName}, "Disconnect", {"name" : serverName})
    // 釋放記憶體
    allTab = {};
    chrome.action.setIcon({ path: 'icons/socket-inactive.png' })
    record_status = false
    //clearInterval(heartBeatInterval)
    stopListener();
  }
  else{
    console.warn("record_status為false仍嘗試關閉連線")
    chrome.action.setIcon({ path: 'icons/socket-inactive.png' });
  }
}


// Create tab
function createTab(tab) {
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"createTab")
    console.dir(tab)
    console.log("test")
  }
  if (tab.openerTabId != undefined)
  {
    allTab[tab.id] = {
      "title": tab.title,
      "url": tab.url
    }
    sendTriple( 
      {
        "tabId": tab.openerTabId,
        "tabURL": allTab[tab.openerTabId].url,
        "name": allTab[tab.openerTabId].title
      },
      "create",
      {
        "tabId": tab.id,
        "tabURL": tab.url,
        "name": tab.title
      }
    )
  }
  else{
    allTab[tab.id] = {
      "title": tab.title,
      "url": tab.url
    }
    sendTriple( 
      {
        "tabId": -1,
        "tabURL": "Unknown",
        "name": "Unknown"
      },
      "create",
      {
        "tabId": tab.id,
        "tabURL": tab.url,
        "name": tab.title
      }
    )
  }
}

// 取得當前焦點視窗ID
function getFocusWindow(){
  chrome.windows.getLastFocused()
    .then((windows) => {
      return windows.id, windows
    })
}

// Closed tab
function closedTab(tabId) {
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"closedTab")
    console.dir(tabId)
  }
  sendTriple(
    {
      "name": userName
    },
    "Close",
    {
      "tabId": tabId,
      "tabURL": allTab[tabId].url,
      "name": allTab[tabId].title
    }
  )
  delete allTab[tabId];
  return;
}


// Updated tab
function updatedTab(tabId, info, tab) {
  if( debugMode == true){
    console.log("=====update相關=====")
    console.log(new Date(Date.now()).toLocaleTimeString(),"updatedTab")
    console.dir({info})
    console.dir({tab})
    console.log("status(tab/info):", tab.status, info.status)
    console.log("title:", tab.title,"\n", info.title)
    console.log("url:", tab.url,"\n", info.url)
  }
  // update完成
  if(info.status=="complete"){
    console.log("info complete!!")
    if(info.activate == false){
      console.log("非焦點分頁更新完成")
      console.dir(tab)
      console.dir(info)
    }
    // 
    // 只有在update complete時才把action info傳給server
    // 如果是新分頁
    if (allTab[tabId] == undefined){
      // sendAction(info, tab)
      sendTriple( 
        {
          "tabId": tab.openerTabId,
          "tabURL": allTab[tab.openerTabId].url,
          "name": allTab[tab.openerTabId].title
        },
        "update_to",
        {
          "tabId": tab.id,
          "tabURL": tab.url,
          "name": tab.title
        })
      allTab[tab.id] = {
        "title": tab.title,
        "url": tab.url
      }
    }
    // 如果不是新分頁，是相同分頁的更新
    else{
      // 忽略相同網址的情況，可能是重新整理或翻譯
      if (allTab[tabId].url == tab.url) return
      // sendAction(info, tab)
      sendTriple(
        {
          "tabId": tab.id,
          "tabURL": allTab[tab.id].url,
          "name": allTab[tab.id].title
        },
        "update_to",
        {
          "tabId": tab.id,
          "tabURL": tab.url,
          "name": tab.title
        })
      allTab[tabId].url = tab.url;
      allTab[tabId].title = tab.title;
    }
  }
  // TODO: 也許會出現更新的tab沒有存在allTab中的情況，例如還沒complete之類的
}

// Activate tab
function activateTab(activeInfo){
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"activateTab")
    console.dir(activeInfo)
  }
  // sendAction(activeInfo)
  chrome.tabs.get(activeInfo.tabId, function(tab){
    if (tab.url==undefined && activeInfo.openerTabId != undefined){
      // url未被設定，需要等update
      allTab[tabId]["info"] = {
        "status":"justActivate",
        "openerTabId":activeInfo.openerTabId
      }
      return
    }
    console.dir({tab})
    sendTriple(
      {
        "name": userName
      },
      "Active",
      {
        "name": tab.title,
        "tabId": tab.id,
        "tabURL": tab.url
      }
    )
  });
}

// highlight tab
function highlightTab(info){
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"highlightTab")
    console.dir(info)
  }
  sendAction(info)
}

// replace tab
function replaceTab(info){
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"replaceTab")
    console.dir(info)
  }
}

// 處理導航訊息，捕捉上一頁與下一頁
function navigatedCommitted(details){
  console.log("navigationCommitted!!")
  console.dir(details)
  if (details.transitionType == "auto_subframe"){
    // 屬於自動加載的子畫面？不需要紀錄
    return
  }
  // transitionType: reload=重新整理、link=點擊連結或上一頁
  sendAction(details)
}
// chrome.webNavigation.onCommitted.addListener(function(details) {
//   if (details.transitionQualifiers.includes('forward_back')) {
//       console.log('User navigated back or forward to:', details.url);
//   }
// });


// 以下關於context menu
chrome.contextMenus.onClicked.addListener(genericOnClick);

// 關於context按下後的對應function在這邊定義
function genericOnClick(info, tab) {
  switch (info.menuItemId) {
    case 'ExportWebPage':
      exportWebPage(info, tab);
      break;
    case 'ExportExcerpt':
      ExportExcerpt(info, tab);
      break;
    default:
      // Standard context menu item function
      console.log(info.menuItemId + 'Standard context menu item clicked.');
      console.dir(info)
  }
}

/**
 * 在安裝extension時增加關於右鍵選單的監聽器
 */
chrome.runtime.onInstalled.addListener(function () {
  // 註解暫時沒打算做的項目
  /*
  let contexts = [
    'page',
    // 'link',
    // 'editable',
    // 'image',
    // 'video',
    // 'audio',
  ];
  for (let i = 0; i < contexts.length; i++) {
    let context = contexts[i];
    let title = "匯出網頁";
    chrome.contextMenus.create({
      title: title,
      contexts: [context],
      id: i + context,
    });
  } 
  */
  chrome.contextMenus.create({
    title: "匯出網頁",
    id: "ExportWebPage"
  })
  chrome.contextMenus.create({
    title: "匯出摘錄",
    id: "ExportExcerpt",
    contexts: ["selection"]
  })
});

/**
 * 處理context menu的匯出網頁功能，建立彈出視窗
 * 後續由常駐監聽器接手(SaveWeb)
 * @param {*} info 
 * @param {*} tab 
 */
function exportWebPage(info, tab){

  // TODO: 如果網址包含github則有特殊行為，也許應該移到後端py來處理?
  if (tab.url.includes("github.com"))
    fromGithub(info, tab)
  
  // 檢查是否有連線，若未連線則報錯
  // TODO: 也許可以嘗試自動連線?
  if (record_status === false){
    console.warn("未連線時嘗試匯出摘錄")
    chrome.notifications.create({
      type: 'basic',
      message: "未連線",
      iconUrl: 'icons/socket-inactive.png',
      title: '錯誤'
    })
    return
  }
  // 關於跳出視窗的程式碼==
  // 計算置中的位置
  let left, top;
  const width = 320;
  const height = 500;

  // TODO: 自動使視窗置中
  // currentWindow = chrome.windows.getCurrent()
  // left = currentWindow.left + (currentWindow.width - width) / 2;
  // top = currentWindow.top + (currentWindow.height - height) / 2;
  left = (1920-320)/2
  top = (1080-500)/2
  chrome.windows.create(
    {
      url: chrome.runtime.getURL("ExportWeb.html"),
      type: "popup",
      width: width,
      height: height,
      left: left,
      top: top
    }, function(newWindow){
    // 建立視窗後傳送資料到html，彈出視窗結束後由常駐監聽器觸發neo4j相關行為(SaveWeb)
    console.log("waiting ready...")
    chrome.runtime.onMessage.addListener(createExportWebListener(tab.url, tab.title));
  });
}

/**
 * 處理context menu的匯出摘要功能，建立彈出視窗
 * 後續由常駐監聽器接手(SaveExcerpt)
 * @param {*} OnClickData 
 * @param {*} tab 
 */
function ExportExcerpt(OnClickData, tab){
  if (debugMode == true){
    console.log("===ExportExcerpt===")
    console.log("OnClickData")
    console.dir(OnClickData)
    console.log("tabInfo")
    console.dir(tab)
  }
  
  let text = "";
  if (OnClickData.selectionText != undefined){
    // 檢查是否有連線，若未連線則嘗試連線
    if (record_status === false){
      console.warn("未連線時嘗試匯出摘錄")
      chrome.notifications.create({
        type: 'basic',
        message: "未連線",
        iconUrl: 'icons/socket-inactive.png',
        title: '錯誤'
      })
      return
    }
    text = OnClickData.selectionText
    // 關於跳出視窗的程式碼==
    // 計算置中的位置
    let left, top;
    const width = 320;
    const height = 500;

    // todo: 自動使視窗置中
    // currentWindow = chrome.windows.getCurrent()
    // left = currentWindow.left + (currentWindow.width - width) / 2;
    // top = currentWindow.top + (currentWindow.height - height) / 2;
    left = (1920-320)/2
    top = (1080-500)/2
    chrome.windows.create(
      {
        url: chrome.runtime.getURL("excerpt.html"),
        type: "popup",
        width: width,
        height: height,
        left: left,
        top: top
      }, function(newWindow){
      // 建立視窗後傳送資料到html
      console.log("waiting ready...")
      chrome.runtime.onMessage.addListener(createExcerptListener(text, tab.url, tab.title));
    });
    // ==================
  }
  else{
    console.error("匯出摘錄時無法取得選擇的字串。")
  }
}
function fromGithub(info, tab){
  console.log("fromGithub");
  console.dir(info);
  console.dir(tab);
  if (!record_status) {
    connect();
    ready = true;
  }
  sendTriple({
    "name": userName
  },"ImportGithub",
  {
    "pageURL": info.pageUrl
  }
  );
}

function setGoal(){
  if (debugMode == true){
    console.log("===setGoal===")
  }
    // 檢查是否有連線，若未連線則嘗試連線
    if (record_status === false){
      console.warn("未連線時嘗試設定目標")
      chrome.notifications.create({
        type: 'basic',
        message: "未連線",
        iconUrl: 'icons/socket-inactive.png',
        title: '錯誤'
      })
      return
    }
    let left, top;
    const width = 320;
    const height = 500;

    // todo: 自動使視窗置中
    // currentWindow = chrome.windows.getCurrent()
    // left = currentWindow.left + (currentWindow.width - width) / 2;
    // top = currentWindow.top + (currentWindow.height - height) / 2;
    left = (1920-320)/2
    top = (1080-500)/2
    chrome.windows.create(
      {
        url: chrome.runtime.getURL("setGoal.html"),
        type: "popup",
        width: width,
        height: height,
        left: left,
        top: top
      }, function(newWindow){
    });
    // ==================
}

// 關於背景和前面的溝通
chrome.runtime.onMessage.addListener(
  function(request, sender, sendResponse) {
    if(debugMode) {
      console.log("SW端常駐listener收到訊息") 
      console.dir(request)
    }
    if (request === "connect"){
      if (record_status) {
        // 關閉連線，並改變icon
        disconnect();
        sendResponse("disconnect");
      } else {
        // 開啟連線，並改變icon
        connect();
        sendResponse("connect");
      }
    }
    if (request === "check"){
      sendResponse(record_status!=false?"connect":"disconnect");
    }
    if (request === "setGoal"){
      // 處理瀏覽器popup傳來的設定目標請求
      setGoal();
    }

    // 處理excerpt.js中回傳的摘錄訊息及描述、標籤
    if (request['action']!=undefined){
      if (request['action']==="SaveExcerpt"){
        console.dir(request)
        sendResponse("ok")
        fetch("http://127.0.0.1:27711/v1/chrome/excerpt", {
          method: "POST",
          body: {"text": request.text,
                  "description": request.description,
                  "tag_string": request.tagString,
                  "url": request.url,
                  "title": request.title
          },
          headers: new Headers({'content-type': 'application/json'}),
        })
        .then((response) => {
         
          console.log(response);
          
          return response.json(); 
        }).catch((err) => {
          console.log('錯誤:', err);
        });
      }
      // 處理excerpt.js傳來的匯出網頁
      if (request['action']==="SaveWeb"){
        console.dir(request)
        sendResponse("ok")
        fetch("http://127.0.0.1:27711/v1/chrome/web", {
          method: "POST",
          body: { "description": request.description,
                  "tag_string": request.tagString,
                  "url": request.url,
                  "title": request.title
          },
          headers: new Headers({'content-type': 'application/json'}),
        })
        .then((response) => {
          console.log(response);
          return response.json(); 
        }).catch((err) => {
          console.log('錯誤:', err);
        });
      }
      // 處理excerpt.js傳來的TagInput更新
      if (request['action']==="TagInput"){
        console.dir(request['TagString'])
        let lastTagString = request['TagString'].split(/,| /).slice(-1)
        console.log(lastTagString)
        let query = "http://127.0.0.1:27711/tag_recommend?keyword=" + lastTagString // 改用fastapi server
        fetch(query,{})
        .then((response) => {
          console.log(response.type)
          
          return response.json();
        }).then((response) => {
          console.log(response.type)
          console.log("真response")
          console.dir(response)
          sendResponse(response)
        }).catch((err)=>{
          console.error("未知錯誤",err)
        })

        // 因為這邊涉及非同步行為，需要通知chrome以保留sendResponse函數
        return true
      }
      // 處理儲存目標
      if (request['action']==="SaveGoal"){
        console.dir(request)
        fetch('http://127.0.0.1:27711/v1/chrome/goal', {
          method: "POST",
          body: JSON.stringify({"goal": request.goal}),
          headers: new Headers({'content-type': 'application/json'}),
        })
        .then((response) => {
          console.log(response);
          return response.json(); 
        }).catch((err) => {
          console.log('錯誤:', err);
      });
      }
      
      
    }
    // 測試用
    if (request === "test"){
      sendResponse("Hi, by back")
    }
  }
);

/**
 * 處理摘錄時和popup的溝通，藉由工廠函數來傳遞額外的參數
 * @param {*} message 
 * @param {*} sender 
 * @param {*} sendResponse 
 */
function createExcerptListener(text, url, title) {
  var excerptListener = function(message, sender, sendResponse) {
    if(debugMode) {
      console.log("SW端ExcerptListener收到訊息") 
      console.dir(message)
    }
    if (message.ready) {
      sendResponse({"text": text, "url": url, "title": title});
      // 傳送訊息後移除監聽器
      chrome.runtime.onMessage.removeListener(excerptListener);
    }
  };
  return excerptListener;
}

/**
 * 處理網頁匯出時和popup的溝通，藉由工廠函數來傳遞額外的參數
 * @param {*} message 
 * @param {*} sender 
 * @param {*} sendResponse 
 */
function createExportWebListener(url, title) {
  var exportWebListener = function(message, sender, sendResponse) {
    if(debugMode) {
      console.log("SW端ExportWebListener收到訊息") 
      console.dir(message)
    }
    if (message.ready) {
      sendResponse({"url": url, "title": title});
      // 傳送訊息後移除監聽器
      chrome.runtime.onMessage.removeListener(exportWebListener);
    }
  };
  return exportWebListener;
}



/**
 * 整個chrome-extension的背景JS，具體說明請參考chrome-extension service worker
 */


// TODO: 改成使用webNavigation API

import {sendTriple, callAPI} from "./RNSApi.js";


let recordStatus = false;
let debugMode = true;

/**
 * 用來記錄所有已知的tab資訊，主要用於紀錄URL和標題，和update的訊息搭配
 * 改成webNavigation後應該可以刪除
 */
let allTab = {};

let userName = "USER"


// 與知識庫溝通使用的API 
// TODO: 準備棄用，此extension僅將action傳送到知識庫，因此實體相關資訊應由知識庫管理
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

/** 
用於傳輸所有分頁動作(action)，目前伺服器端未實作完成
想不起來為什麼使用action這個詞
*/
function sendAction(actionInfo, tabInfo={}, openerTabInfo={}){
  console.warn("sendAction，但伺服器端未實作完成。")
  return
  // TODO: 將伺服器相關設定改成讀取設定檔或建立一個修改設定的介面
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

// 綁定 toolbar 中 extension 的按鈕活動，用於開關連線並改變按鈕顏色
chrome.action.onClicked.addListener(async () => {
  if (recordStatus) disconnect();  // 關閉連線、改變icon
  else connect();                   // 開啟連線、改變icon
});

/**
 * 連線時要開啟的監聽器，包含Created、Updated、Activated、Removed、Highlighted、Replaced
 */
function startListener(){
  // 先將不需要追蹤的動作註解掉，未來再視情況刪除程式碼

  // 監聽tab被聚焦，此時URL有可能還沒確定，需要再監聽Update
  // chrome.tabs.onActivated.addListener(activateTab); 
  
  // 監聽tab的建立，此時URL和group可能還沒確定，需要再監聽Update
  // chrome.tabs.onCreated.addListener(createTab);

  // 監聽Highlight，意義未明
  // chrome.tabs.onHighlighted.addListener(highlightTab);

  // 監聽replace，意義未明
  // chrome.tabs.onReplaced.addListener(replaceTab);

  // 監聽tab更新
  chrome.tabs.onUpdated.addListener(updatedTab);

  // 監聽tab被關閉
  // chrome.tabs.onRemoved.addListener(closedTab);
  
  // 監聽導航訊息，未完成
  chrome.webNavigation.onCommitted.addListener(navigatedCommitted);
}

/**
 * 關閉連線時停止所有監聽器
 */
function stopListener(){
  // TODO: 不知道能不能一次性關閉所有監聽器，例如將所有監聽器放到一個陣列中?
  // 先將不需要追蹤的動作註解掉，未來再視情況刪除程式碼

  // 監聽tab的建立
  //chrome.tabs.onCreated.removeListener(createTab);
  // 監聽tab更新
  chrome.tabs.onUpdated.removeListener(updatedTab);
  // 監聽tab被聚焦
  //chrome.tabs.onActivated.removeListener(activateTab); 
  // 監聽tab被關閉
  //chrome.tabs.onRemoved.removeListener(closedTab);
  //chrome.tabs.onHighlighted.removeListener(highlightTab)
  //chrome.tabs.onReplaced.removeListener(replaceTab)
  chrome.webNavigation.onCommitted.removeListener(navigatedCommitted);
}


/**
 * 連線並啟動錄製
 */
async function connect() {
  if(debugMode) console.dir(allTab)
  // 改成使用RESTful API查詢伺服器是否已開啟
  callAPI("v1/chrome/", "get")
    .then((response) => {
      console.log({response})
      if(response["status"]=="ok"){
        // 通過OS通知顯示連線成功
        chrome.notifications.create({
          type: 'basic',
          message: "連線成功",
          iconUrl: 'icons/socket-inactive.png',
          title: '成功'
        })
        recordStatus = true
        chrome.action.setIcon({ path: 'icons/socket-active.png' });
        // 初始化所有tab資訊，儲存於allTab中
        chrome.tabs.query({})
        .then((tabList) => {
          console.dir(tabList)
          for( let i = 0 ; i < tabList.length ; i++){
            let tabInfo = tabList[i];
            allTab[tabInfo["id"].toString()] = {
              "title": tabInfo["title"],
              "url": tabInfo["url"].split("#")[0] // 忽略井字號後的所有部分
            }
          }
        });
        // 開啟監聽器
        startListener();
      }
      // 連線失敗則用OS顯示失敗訊息
      else{
        chrome.notifications.create({
          type: 'basic',
          message: "連線失敗，請確認伺服器是否已開啟",
          iconUrl: 'icons/socket-inactive.png',
          title: '連線錯誤'
        })
        // 保險起見，可能需要關閉監聽器，但也有可能出現問題(如嘗試關閉不存在的監聽器等)
        stopListener();
      }
    })
}


/**
 * 關閉連接函數
 */
function disconnect() {
  if (recordStatus) {
    allTab = {}; // 釋放記憶體
    chrome.action.setIcon({ path: 'icons/socket-inactive.png' }) // 改變icon顏色
    recordStatus = false // 改變狀態
    stopListener(); // 關閉監聽器
  }
  else{
    console.warn("recordStatus為false仍嘗試關閉連線")
    chrome.action.setIcon({ path: 'icons/socket-inactive.png' });
  }
}


// Create tab，已棄用，不再需要追蹤
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

// Closed tab，已棄用，不再需要追蹤
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


/**
 * 處理tab出現updatedTab動作時的行為
 * @param {*} tabId 用於識別allTab中對應的tab
 * @param {*} info updated的相關資訊，忽略complete以外的情況
 * @param {*} tab 被更新分頁的最新資訊
 */
function updatedTab(tabId, info, tab) {
  if( debugMode == true){
    console.log("=====update相關=====")
    console.log(new Date(Date.now()).toLocaleTimeString(),"updatedTab")
    console.dir({info})
    console.dir({tab})
    console.log("status(tab/info):", tab.status, info.status)
    console.log("title:", tab.title,"\n", info.title)
    console.log("url:", tab.url,"\n", info.url)
    console.log("allTab[tabId.openerTabId]")
    console.dir(allTab[tabId.openerTabId])
  }
  // 根據W3C標準https://www.w3.org/TR/2011/WD-html5-20110525/urls.html#interfaces-for-url-manipulation，
  // #號應被用於同頁面的片段標示，因此可以部分忽略
  // 尤其是#號後為空的情況，基本沒有意義但在tag推薦時會頻繁出現
  tab.url = tab.url.split("#")[0]
  if(tab.url.length == 0) return // 空白網址則不處理
  // update完成
  if(info.status=="complete"){
    console.log("info complete!!")
    if(info.activate == false){
      console.log("非焦點分頁更新完成")
      console.dir(tab)
      console.dir(info)
    }
    // 只有在update complete時才把action info傳給server
    // 如果是新分頁
    if (allTab[tabId] == undefined){
      // sendAction(info, tab)
      // 將分頁更新資訊傳遞到Server
      sendTriple( 
        {
          "tabId": tab.openerTabId,
          "tabURL": allTab[tab.openerTabId].url, //FIXME: 匯出摘錄或網頁時\會報錯
          "name": allTab[tab.openerTabId].title
        },
        "update_to",
        {
          "tabId": tab.id,
          "tabURL": tab.url,
          "name": tab.title
        })
      // 更新資訊到allTab
      allTab[tab.id] = {
        "title": tab.title,
        "url": tab.url
      }
    }
    // 不是新分頁，而是已存在分頁的更新
    else{

      // 忽略相同網址的情況，例如重新整理、翻譯或同頁面跳轉(#)
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
}

// Activate tab，已棄用，不再需要追蹤
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

// highlight tab，已棄用，不再需要追蹤
function highlightTab(info){
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"highlightTab")
    console.dir(info)
  }
  sendAction(info)
}

// replace tab，已棄用，不再需要追蹤
function replaceTab(info){
  if( debugMode == true){
    console.log(new Date(Date.now()).toLocaleTimeString(),"replaceTab")
    console.dir(info)
  }
}

// 處理導航訊息，捕捉上一頁與下一頁
function navigatedCommitted(details){
  //TODO: 改成導航
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
chrome.contextMenus.onClicked.addListener(function(info, tab){
  exportExcerpt(info, tab)
  // 根據匯出網頁及匯出摘錄兩種不同的動作呼叫不同函數
  // switch (info.menuItemId) {
  //   case 'ExportWebPage':
  //     exportWebPage(info, tab);
  //     break;
  //   case 'ExportExcerpt':
  //     ExportExcerpt(info, tab);
  //     break;
  // }
})

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
    title: "儲存網頁",
    id: "ExportWebPage"
  })
  chrome.contextMenus.create({
    title: "匯出摘錄",
    id: "ExportExcerpt",
    contexts: ["selection"]
  })
});

/**
 * 處理context menu的匯出摘要功能，建立彈出視窗
 * 後續由常駐監聽器接手(SaveExcerpt)
 * @param {*} info contextmenu的相關資訊OnClickData
 * @param {*} tab 觸發contextmenu的tab
 */
function exportExcerpt(info, tab){
  if (debugMode == true){
    console.log("===ExportExcerpt===")
    console.log("info")
    console.dir(info)
    console.log("tabInfo")
    console.dir(tab)
  }
  // TODO: 如果網址包含github則有特殊行為，也許應該移到後端py來處理?
  // 但可能會涉及CSS選擇器，因此應該還是要由Extension處理
  if (tab.url.includes("github.com"))
    fromGithub(info, tab)
  let excerptUiUrl = ""
  switch (info.menuItemId) {
    case 'ExportWebPage':
      excerptUiUrl = "exportWeb.html"
      break;
    case 'ExportExcerpt':
      excerptUiUrl = "excerpt.html"
      break;
  }
  let excerpt = info.selectionText
  // 檢查是否有連線，若未連線則嘗試連線
  if (recordStatus === false){
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
  // 建立摘錄視窗
  chrome.windows.create(
    {
      url: chrome.runtime.getURL(excerptUiUrl),
      type: "popup",
      width: width,
      height: height,
      left: left,
      top: top
    }, function(newWindow){
    // 視窗建立完成後(callback)建立message監聽器，準備將tab相關資訊傳送到摘錄視窗
    console.log("waiting ready...")
    chrome.runtime.onMessage.addListener(createExcerptListener(tab.url, tab.title, excerpt));
  });
}
function fromGithub(info, tab){
  console.log("fromGithub");
  console.dir(info);
  console.dir(tab);
  if (!recordStatus) {
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
    if (recordStatus === false){
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
      if (recordStatus) {
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
      sendResponse(recordStatus!=false?"connect":"disconnect");
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
          body: JSON.stringify({"text": request.text,
                  "description": request.description,
                  "tag_string": request.tagString,
                  "url": request.url,
                  "title": request.title
          }),
          headers: new Headers({'content-type': 'application/json'}),
        })
        .then((response) => {
         
          console.log(response);
          
          return response.json(); 
        }).catch((err) => {
          console.log('錯誤:', err);
        });
      }
      // 處理excerpt.js傳來的儲存網頁
      if (request['action']==="SaveWeb"){
        console.dir(request)
        sendResponse("ok")
        fetch("http://127.0.0.1:27711/v1/chrome/web", {
          method: "POST",
          body: JSON.stringify({ "description": request.description,
                  "tag_string": request.tagString,
                  "url": request.url,
                  "title": request.title
          }),
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
      // TODO: 未完成
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
 * 在摘錄時將摘錄資訊傳送給popup視窗，藉由工廠函數來傳遞額外的參數
 * @param {*} message 
 * @param {*} sender 
 * @param {*} sendResponse 
 */
function createExcerptListener(url, title, text = undefined) {
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
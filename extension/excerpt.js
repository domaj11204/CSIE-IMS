/**
 * 在摘錄頁面中管理使用者輸入、tag推薦、按鈕等事件
 * 2024/11/27，完成所有功能的檢查
 * 本js無直接與Server溝通，因此沒有寫測試
 */
let elem
// 監聽html載入完成的事件，向SW要求摘錄相關訊息
document.addEventListener('DOMContentLoaded', function() {
    chrome.runtime.sendMessage({"ready":true}, function(msg){
        // 將收到的訊息放入對應位置
        document.getElementById('title').innerHTML = msg.title;
        document.getElementById('url').innerHTML = msg.url;
        if(msg.text != undefined) // 由於匯出摘錄和匯出網頁都會使用，因此要判斷是否有text
            document.getElementById('excerpt').innerHTML = msg.text;

        // 準備完成，將資料往下傳並等待使用者輸入
        waitUser(msg.text, msg.url, msg.title);
    });
})

/**
 * 監聽按鈕click事件，待使用者輸入完成後將補充訊息傳到SW
 * @param {String} text 
 * @param {String} url 
 * @param {String} title 
 */
function waitUser(text, url, title){
    // FIXME: 在儲存網頁時，在tag輸入框按下Enter會直接關閉視窗，摘錄不確定
    // 根據不同的按鈕綁定匯出摘錄或匯出網頁，按鈕時將資訊傳回SW
    let SaveExcerptButton = document.getElementById('SaveExcerpt')
    let SaveWebButton = document.getElementById('SaveWeb')
    if (SaveExcerptButton) { // 匯出摘錄
        SaveExcerptButton.addEventListener('click', function() { 
            chrome.runtime.sendMessage({
                "action":"SaveExcerpt", 
                "description":document.getElementById('Description').value, 
                "tagString":document.getElementById('TagString').value, 
                "text":text, 
                "url":url,
                "title":title
            })
            window.close() // 關閉視窗
        })
    }
    else if (SaveWebButton) { // 匯出網頁
        SaveWebButton.addEventListener('click', function() {
        chrome.runtime.sendMessage({
            "action":"SaveWeb", 
            "description":document.getElementById('Description').value, 
            "TagString":document.getElementById('TagString').value, 
            "url":url,
            "title":title
            })
            window.close() // 關閉視窗
        })
    }
    // 綁定tag輸入修改的監聽
    let tagInput = document.getElementById('TagString')
    tagInput.addEventListener('input', function() { // 監聽修改，用於tag建議
        tagRecommend()
    })
    tagInput.addEventListener("keypress", function(event) { // 監聽Enter，效果同按下按鈕
        if (event.key === "Enter") {
            event.preventDefault();
            if (SaveWebButton)
                SaveWebButton.click();
            if (SaveExcerptButton)
                SaveExcerptButton.click();
        }
    })
}

/**
 * 向SW要求tag建議(SW再向Server要求建議)
 * 讀取TagString的內容，將建議的tag及超連結放入TagRecommend
*/
async function tagRecommend(){
    let tagInput = document.getElementById('TagString').value
    chrome.runtime.sendMessage({
        "action":"TagInput", 
        "TagString": tagInput
    }, (response) =>{

        let tagRecommend = document.getElementById('TagRecommend')
        tagRecommend.innerHTML = ""
        if (response === undefined){
            console.error("TagRecommend的response為undefined")
        }
        for (var i = 0 ; i < response.length ; i++){ // 將建議的tag加上超連結，讓文字看起來可以點擊
            tagRecommend.innerHTML = tagRecommend.innerHTML + " " + "<a href=\"#\" class=\"tagRecommendLink\" id=\"test" + i + "\">"+response[i]+"</a>";        
        }
        elem = document.getElementsByClassName("tagRecommendLink");
        for (var i = 0; i < elem.length; i++) { // 為建議tag的虛假超連結綁定真正的click事件
            elem[i].addEventListener('click', tagUpdate ,false)
        }  
    })
}

function tagUpdate(){
    // 先切逗號，再根據最後一個ele是否為空判斷splice的覆蓋數量
    // 最後一個ele為空 -> 為直接點擊
    let tagInput = document.getElementById('TagString').value
    inputList = tagInput.split(/[,| ]+/) // 以逗號或空格切割字串
    if (inputList[inputList.length-1]==""){ // tag輸入在分隔符後沒有內容，代表直接點擊推薦tag而沒有任何新輸入
         inputList.splice(inputList.length, 0, this.innerText + ", ") // 插入新的tag到list
    } else{
        inputList.splice(inputList.length-1, 1, this.innerText + ", ") // 取代list的最後一個元素(不完整的tag)
    }   
    inputList = inputList.filter(function(ele){ // 將空字串過濾掉
        return ele != "";
    })
    document.getElementById('TagString').value = inputList.join(", ") // 合併list
    document.getElementById('TagString').focus() // 點擊後將輸入焦點切回輸入框
    // return false 加上了也無法避免超連結跳轉
}
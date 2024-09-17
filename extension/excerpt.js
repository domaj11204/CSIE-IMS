let elem
// 當完成html時
document.addEventListener('DOMContentLoaded', function() {

    // 完成基本載入後要求摘錄相關訊息
    chrome.runtime.sendMessage({"ready":true}, function(msg){
        // 將收到的訊息放入對應位置
        var title = document.getElementById('title');
        var url = document.getElementById('url');
        try{
            var excerpt = document.getElementById('excerpt');
        }catch{console.warn("無摘錄訊息，可能是正常現象")}
        
        title.innerHTML = msg.title;
        url.innerHTML = msg.url;
        try{
            excerpt.innerHTML = msg.text;
        }catch{console.warn("無摘錄訊息，可能是正常現象")}
        
        // 準備完成，等待使用者輸入
        waitUser(msg.text, msg.url, msg.title);
    });
    console.log("ready!!")
})



/**
 * 監聽按鈕click事件，待使用者輸入完成後將補充訊息傳到SW
 * @param {String} text 
 * @param {String} url 
 * @param {String} title 
 */
function waitUser(text, url, title){
    // 綁定儲存摘錄的監聽
    let SaveExcerptButton = document.getElementById('SaveExcerpt');
    if (SaveExcerptButton) {
        SaveExcerptButton.addEventListener('click', function() {
            (async () => {
                // 按下按鈕後的事件
                let description = document.getElementById('Description').value
                let tagString = document.getElementById('TagString').value
                const response = await chrome.runtime.sendMessage({
                    "action":"SaveExcerpt", 
                    "description":description, 
                    "tagString":tagString, 
                    "text":text, 
                    "url":url,
                    "title":title
                });
                // 關閉視窗
                window.close()
            })();
        });
    }
    // 綁定儲存網頁的監聽
    let SaveWebButton = document.getElementById('SaveWeb');
    if (SaveWebButton) {
        SaveWebButton.addEventListener('click', function() {
            (async () => {
                // 按下按鈕後的事件
                let description = document.getElementById('Description').value
                let tagString = document.getElementById('TagString').value
                const response = await chrome.runtime.sendMessage({
                    "action":"SaveWeb", 
                    "description":description, 
                    "TagString":tagString, 
                    "url":url,
                    "title":title
                });
                // 關閉視窗
                window.close()
            })();
        });
    }

    // 綁定tag輸入修改的監聽
    let tagInput = document.getElementById('TagString')
    if (tagInput){
        // 有修改的監聽器，用於觸發tag建議
        tagInput.addEventListener('input', function() {
            tagRecommend()
        });
        // Enter監聽器，綁定到對應的按鈕上
        tagInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                if (SaveWebButton)
                    SaveWebButton.click();
                if (SaveExcerptButton)
                    SaveExcerptButton.click();
            }
        });
    }
    
}

async function tagRecommend(){
    // 用空格或頓號分隔?
    let tagInput = document.getElementById('TagString').value
    chrome.runtime.sendMessage({
        "action":"TagInput", 
        "TagString": tagInput
    }, (response) =>{
        console.log("response:")
        console.dir(response)
        let tagRecommend = document.getElementById('TagRecommend')
        tagRecommend.innerHTML = ""
        if (response === undefined){
            console.warn("response為undefined")
        }
        for (var i = 0 ; i < response.length ; i++){
            console.log(response[i])
            tagRecommend.innerHTML = tagRecommend.innerHTML + " " + "<a href=\"#\" class=\"tagRecommendLink\" id=\"test" + i + "\">"+response[i]+"</a>";        
        }
        elem = document.getElementsByClassName("tagRecommendLink");
        for (var i = 0; i < elem.length; i++) {
            (function () {
                elem[i].addEventListener('click',test ,false)
            }()); // immediate invocation
        }
        
    });
    
}

function test(){
    // 先切逗號，再根據最後一個ele是否為空判斷splice的覆蓋數量
    // 最後一個ele為空 -> 為直接點擊
    console.log("test function")
    console.log(this.innerText)
    let tagInput = document.getElementById('TagString').value
    inputList = tagInput.split(/[,| ]+/)
    console.log("inputList after split")
    console.log(inputList)
    if (inputList[inputList.length-1]==""){
        // 直接點擊而沒有輸入新字
        inputList = inputList.filter(function(ele){
            return ele!=null && ele != "";
        })
        inputList.splice(inputList.length, 0, this.innerText + ", ")
    } else{
        inputList = inputList.filter(function(ele){
            return ele!=null && ele != "";
        })
        inputList.splice(inputList.length-1, 1, this.innerText + ", ")
    }   
    document.getElementById('TagString').value = inputList.join(", ")
    document.getElementById('TagString').focus() // 點擊後將輸入焦點切回輸入框
}
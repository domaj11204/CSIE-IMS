// 當使用popup.html時
document.addEventListener('DOMContentLoaded', function() {

    // 宣告並綁定按鈕監聽
    let button = document.getElementById('wantConnect');
    if (button) {
        button.addEventListener('click', function() {
            (async () => {
                const response = await chrome.runtime.sendMessage("connect");
                button.innerHTML = response==="connect"?"斷線":"連線";
                window.close();
              })();
        });
        // 檢查連線情況
        chrome.runtime.sendMessage("check",(response)=>{
            var button = document.getElementById('wantConnect');
            if(button)
                button.innerHTML = response==="connect"?"斷線":"連線";
        })
    }
    let setGoalButton = document.getElementById('setGoal');
    if (setGoalButton) {
        // 設定當前目標
        setGoalButton.addEventListener('click', function() {
            (async () => {
                const response = await chrome.runtime.sendMessage("setGoal");
                window.close();
              })();
        });
    }

    // 測試用
    let buttonTest = document.getElementById('test');
    if (buttonTest) {
        buttonTest.addEventListener('click', function() {
            (async () => {
                const response = await chrome.runtime.sendMessage("test");
                buttonTest.innerHTML = response;
              })();
        });
    }
});

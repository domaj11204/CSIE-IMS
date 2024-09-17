// 綁定取消按鈕
document.addEventListener('DOMContentLoaded', function() {
    let cancelButton = document.getElementById('cancelButton');
    if (cancelButton) {
        cancelButton.addEventListener('click', function() {
            // 按下取消則關閉視窗
            window.close();
        });
    }
    // 綁定確定按鈕的監聽
    let confirmButton = document.getElementById('confirmButton');
    if (confirmButton) {
        confirmButton.addEventListener('click', function() {
            (async () => {
                // 按下確定按鈕後的事件
                let goal = document.getElementById('goal').value;
                const response = await chrome.runtime.sendMessage({
                    "action": "SaveGoal",
                    "goal": goal
                });
                // 關閉視窗
                window.close();
            })();
        });
    }
})
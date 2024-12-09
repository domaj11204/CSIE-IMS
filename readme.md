論文[基於檢索增強生成技術的可重配置資訊管理系統](https://hdl.handle.net/11296/f8yfjk)的CSIE-IMS實作

- 為了Debug方便，目前module/debug_utils.py:print_var內包含暫停三秒(sleep(3))，需特別注意。
- 預設使用Chroma向量資料庫、Neo4j圖形資料庫、obsidian-local-rest-api
- Chrome Extension安裝資料夾為/extension

# 計畫
- 完成測試案例
- 完善API說明
    - 更具體的範例
    - 更具體的錯誤訊息
- 結合API說明自動生成部分測試案例
    - 基於Fastapi.app實現
- 刪除debug用輸出
- 增加搜尋速度/使用來源內建的搜尋功能
- 將Chrome Extension API的基本單位從Triple改成Action，以更好理解並提升可擴充性
- 結合其他軟體(notion)或程式語言(如RUST等)，以說明使用HTTP API而非一般函數呼叫的好處
# 其他
- 更彈性的知識圖譜(屬性名稱等)

# 使用FastAPI實現模組間溝通的優缺點
## 優點
- 可跨平台、跨程式語言
- 可與任何提供HTTP API的服務結合 (類似微服務)
- 可用網頁介面或HTTP API測試模組
## 缺點
- 不容易Debug，API呼叫歷史不像一般的call stack清楚
- IDE支援不佳，HTTP API皆為字串而非關鍵字，因此無法使用自動完成(Auto Complete)

# 更新紀錄
- 將Fastapi從0.110.0更新至0.115.5，以支援[更彈性的參數處理](https://fastapi.tiangolo.com/tutorial/query-param-models/)
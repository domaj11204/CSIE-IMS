/**
 * 以類似RDF三元體的格式包裝成JSON傳到fastapi
 * @param {*} subject RDF三元體中的主詞
 * @param {*} predicate RDF三元體中的謂詞
 * @param {*} object RDF三元體中的受詞
 */
function sendTriple(subject, predicate, object){
  let returnJson = {
    "predicate":unknownTypeToString(predicate), 
    "subject":unknownTypeToString(subject),
    "object":unknownTypeToString(object)
  }
  // TODO: 這個host應該要可以更改，因此可能需要設定頁面
  let url = ""
  if (predicate == "ExcerptFrom") url = "http://127.0.0.1:27711/v1/chrome/excerpt"
  if (predicate == "ExportWeb") url = "http://127.0.0.1:27711/v1/chrome/web"
  else url = "http://127.0.0.1:27711/v1/chrome/triple"
  fetch(url, {
    method: "POST",
    body: JSON.stringify(returnJson),
    headers: new Headers({'content-type': 'application/json'}),
  })
  .then((response) => {
   
    console.log(response);
    
    return response.json(); 
  }).catch((err) => {
    console.log('錯誤:', err);
});
}
/**
 * 關於RNSAPI的分析器，未實作
 * @param {*} objectString 
 * @param {*} predicateString 
 * @param {*} subjectString 
 */
function parse(objectString, predicateString, subjectString){
  
}

/**
 * 將任何資料轉成string，包含JSON、null及undefined
 * @param {*} Data 
 * @returns 
 */
function unknownTypeToString(Data){
  if (Data == null)    return ""
  if (Data == undefined)    return ""
  if (Data.constructor === "test".constructor)    return Data
  try {
    let testIfJson = JSON.parse(Data);
    if (typeof testIfJson == "object")  return JSON.stringify(testIfJson);
    else  return ""
  }
  catch {}
  return Data
}

function callAPI(url, method, data=null, params=null){
  // TODO: 改成可以讀設定
  let serverURL = "http://127.0.0.1:27711"
  if (url[0] != "/")  url = "/" + url
  serverURL += url

  // 處理get查詢參數
  const query = ""
  if(params != null){
    query = new URLSearchParams(params);
    query = query.toString()
  } 

  // 處理post參數及方法
  const apiOption = {
    method: method.toLowerCase(),
    headers: {
      'Content-Type': 'application/json'
    }
  }
  if (method.toLowerCase() == "post") {
    apiOption.body = JSON.stringify(data)
  }
  // 呼叫API
  return fetch(serverURL+query, apiOption)
  .then((response) => {
    console.log({response})
    return response.json();
  })
  .catch((error) => {
    console.error('Error:', error);
  });
}

export {sendTriple, callAPI}
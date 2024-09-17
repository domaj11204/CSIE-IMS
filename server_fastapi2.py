"""此檔案管理系統中關於fastapi的內容
預期的呼叫方式為
`$uvicorn server_fastapi:app --host 0.0.0.0 --port 27711 --reload`
"""
# TODO: 改檔名
from typing import Annotated

from fastapi import FastAPI, Query, HTTPException, Response, status
from fastapi.responses import JSONResponse
from typing import Dict
import subprocess
import asyncio
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel, HttpUrl
from router import embedded
import time
import threading
import os
import psutil
from modules.MessageHandle import messageHandle, set_DB

from modules.utils import read_config
config = read_config()

# log文件設定
import logging
logFileName = "./log/fastapi_"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
logging.basicConfig(filename=logFileName, encoding='utf-8', level=logging.DEBUG, format='%(asctime)s %(levelname)s: %(message)s')
app2 = FastAPI()
app2.include_router(embedded.router)


from fastapi.middleware.cors import CORSMiddleware
origins = [
    "*"
]

app2.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

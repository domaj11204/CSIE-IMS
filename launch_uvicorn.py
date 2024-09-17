import uvicorn
import signal
import os
import sys
def signal_handler(signum):
    print("sig:", signum)

signal.signal(signal.SIGINT, signal_handler)
if __name__ == "__main__":
    host = sys.argv[1]
    port = sys.argv[2]
    print("launch_uvicorn.py:", os.getpid())
    # 若有需要可以將workers設定為2以上
    if int(port) == 27712:
        uvicorn.run("server_fastapi2:app2", host=host, port=int(port), log_level="debug", workers=1)
    else:    
        uvicorn.run("server_fastapi:app", host=host, port=int(port), log_level="debug", workers=1)
    print("launch_uvicorn.py end")
"""本檔案用於錄製terminal中的任何指令
subprocess的stdin為當前的stdin
subprocess的stdout錄製並轉到當前的stdout
使用方法: 執行後就會記錄所有的stdin和stdout
缺點: 無法使用tab自動完成、tqdm的紀錄會怪怪的
TODO: 自訂log檔名等
"""
import subprocess
import sys
import os
import signal
import threading
import queue
import time

pid = None

def signal_handler(signum, frame):
    """用於捕捉ctrl+c的handler，進行關閉連線及廣播後才關閉程式

    Args:
        signum (_type_): _description_
        frame (_type_): _description_
    """
    if signum == signal.SIGINT.value:
        print(f"正在關閉{pid}......".format(pid))
        pid.kill()
        print("關閉完成")
        exit()
    else:
        exit()

def listen_stdin(input_queue):
    while True:
        input_queue.put(sys.stdin.read(1))


def listen_stdout(output_queue, pid):
    while True:
        output_queue.put(pid.stdout.read1().decode("utf-8"))

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    print(os.getpid())
    pid = subprocess.Popen("%windir%\System32\cmd.exe \"/K\" D:\ProgramData\Anaconda3\Scripts\\activate.bat D:\ProgramData\Anaconda3", 
                           shell=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT) # 考慮到一般使用terminal時不會特別把stdout和stderr分開來
    
    print(pid)
    input_queue = queue.Queue()
    output_queue = queue.Queue()
    listen_thread = threading.Thread(target=listen_stdin, args=(input_queue, ), daemon=True)
    listen_thread.start()
    stdout_thread = threading.Thread(target=listen_stdout, args=(output_queue,pid, ), daemon=True)
    stdout_thread.start()
    pid.stdin.write(b"chcp 65001\n")
    pid.stdin.flush()
    import time
    filename = "./data/log/"+ time.strftime("%Y-%m-%d", time.localtime()) + ".log"
    with open(filename, "ab") as f: # 加上b參數後就不會有多餘的換行了
        new_command = False
        while pid.poll() is None:
            time.sleep(0.01) # 稍微暫停，在不那麼影響使用的情況下降低CPU使用率
            if not output_queue.empty():
                text = output_queue.get()
                
                print(text, end="", flush=True)
                if new_command:
                    text = f"[{time.strftime('%H:%M:%S', time.localtime())}]" + text
                    new_command = False
                
                f.write(text.encode("utf-8"))
            if not input_queue.empty():
                text = input_queue.get()
                if not new_command and text == "\n":
                    new_command = True
                # print("get!, ", text, flush=True)
                pid.stdin.write(text.encode("utf-8"))
                pid.stdin.flush()
    pid.wait()
    print("紀錄完成")


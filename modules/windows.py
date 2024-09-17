import platform
if platform.system() == "Windows":
    import win32gui
    import win32process
    import win32api
    import win32con
if platform.system() == "Linux":
    import subprocess

def get_foreground_window_title():
    """
    回傳前台窗口的標題，若無法取得則回傳空字串

    Returns:
        str: 視窗標題
        str: process名稱
    """
    if platform.system() == "Windows":
        def get_process_path_by_hwnd(hwnd:int):
            """
            將hwnd轉成process的路徑
            
            Args:
                hwnd (int): _description_

            Returns:
                str: _description_
            """
            # hwnd to pid
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            # 將pid及要求的權限轉成PyHANDLE
            process_handle = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            # 取得完整路徑
            app_path = win32process.GetModuleFileNameEx(process_handle, 0)
            # exe_name = exe_path.split("\\")[-1] # 只在windows有用?
            # 關閉PyHANDLE
            win32api.CloseHandle(process_handle)
            # 用斜線代替反斜線
            app_path = app_path.replace("\\", "/")
            return app_path
        window_handle = win32gui.GetForegroundWindow()
        # print(window_handle)
        # print(type(window_handle))
        
        if window_handle:
            return win32gui.GetWindowText(window_handle), get_process_path_by_hwnd(window_handle)
        else:
            return "", ""
    if platform.system() == "Linux":
        # 以下為基於 X11等Ubuntu上的作法
        
        # 取得焦點窗口 ID
        win_id = subprocess.check_output(["xprop", "-root", "_NET_ACTIVE_WINDOW"]).decode("utf-8")
        win_id = win_id.strip().split()[-1]
        if win_id == "0x0":
            return None, None, None
        
        # 取得窗口標題
        win_name = subprocess.check_output(["xprop", "-id", win_id, "WM_NAME"]).decode("utf-8")
        win_name = win_name.strip().split('=')[-1].strip().strip('"')

        # 取得進程 ID
        pid = subprocess.check_output(["xprop", "-id", win_id, "_NET_WM_PID"]).decode("utf-8")
        pid = pid.strip().split()[-1]

        # 取得進程名稱
        proc_name = subprocess.check_output(["ps", "-p", pid, "-o", "comm="]).decode("utf-8").strip()

        return win_name, proc_name
    
    else:
        print(platform.system())
        return "", ""
    

if __name__ == "__main__":
    print(get_foreground_window_title())
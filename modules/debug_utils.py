def print_func_name(func):
    def warp(*args, **kwargs): # 要把func的參數往下傳
        print("DEBUG: function start: '{}'".format(func.__name__))
        result = func(*args, **kwargs)
        print("DEBUG: function end: '{}'".format(func.__name__))
        return result # 忘記設回傳值
    return warp

def timer(func):
    def wrap(*args, **kwargs):
        import time
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print("DEBUG: function '{}' cost: {}s".format(func.__name__, end-start))
        return result
    return wrap

def print_var(var):
    import inspect

    caller_frame = inspect.currentframe().f_back
    frame_info = inspect.getframeinfo(caller_frame)
    line_number = frame_info.lineno

    filename = caller_frame.f_globals['__file__']

    var_name = inspect.getframeinfo(caller_frame).code_context[0].strip().split('(')[-1].strip(')').split(',')[0].strip()
    var_value = var
    var_type = type(var_value).__name__
    
    # 取得當前時間
    from datetime import datetime
    currentTime = datetime.now().strftime("%H:%M:%S")
    print(f"==={currentTime}===")
    print(f"{filename}({line_number}):{var_name} - {var_type}")
    print(f"{var_value}")
    print("====")
    
def error(info:str):
    from colorama import Fore
    print(Fore.Red+info+Fore.RESET)
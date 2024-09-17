from modules.knowledge_base import source
from modules.debug_utils import print_func_name
class LogSource(source):
    def __init__(self, name:str="log", config:dict=None):
        if config == None:
            from modules.utils import read_config
            config = read_config()["log"]
        super().__init__(name="log", config=config)
        self.path = config["path"]
        self.parse_file()
    @print_func_name
    def search(self, keyword):
        for file in self.final_result:
            for command in self.final_result[file]:
                if keyword in command["command"]:
                    return "執行時間: {time}\n虛擬環境: {virtual_env}\n路徑: {path}\n指令: {command}\n輸出: {output}".format(
                        time=command["time"], virtual_env=command["virtual_env"], path=command["path"], command=command["command"], output=command["output"]
                    )
        return "log search: {keyword}".format(keyword=keyword)
    @print_func_name        
    def parse_file(self):
        # 根據資料夾路徑讀取所有的log檔
        import os, re
        self.log_file_list = os.listdir(self.path)
        # 設定parse出指令的正規表達式
        command_pattern = {}
        command_pattern["windows"] = re.compile(r"[(]?.*[)]?.*[A-Z]:\\(?:[\w\s-]+\\)*[\w\s-]*>\[.*:.*:.*\].*\n")
        # D:\research>%windir%\system32\cmd.exe "/K" C:\ProgramData\mambaforge\Scripts\activate.bat C:\ProgramData\mambaforge
        # (base) D:\research>conda env list
        final_result = {}
        for log_file in self.log_file_list:
            final_result[log_file] = []
            print("1", log_file)
            with open(self.path+"/"+log_file, "r") as f:
                log_text = f.read()
                commands = re.findall(command_pattern["windows"], log_text, )
                print(commands)
                
                for index, command in enumerate(commands):
                    # 不斷只保留command後面的文字
                    log_text = log_text.split(command, 1)[1]
                    command = command.replace("\n", "")
                    if index < len(commands) - 1:
                        final_result[log_file].append({
                            "time": command.split("[", 1)[1].split("]", 1)[0],
                            "virtual_env": command.split(")", 1)[0].split("(", 1)[1],
                            "path": command.split(">", 1)[0].split(")", 1)[1],
                            "command": command.split("]", 1)[1],
                            "output":  log_text.split(commands[index+1])[0]
                            })
                    else:
                        final_result[log_file].append({
                            "time": command.split("[", 1)[1].split("]", 1)[0],
                            "virtual_env": command.split(")", 1)[0].split("(", 1)[1],
                            "path": command.split(">", 1)[0].split(")", 1)[1],
                            "command": command.split("]", 1)[1],
                            "output":  log_text
                            })
                # print(result)
        self.final_result = final_result
        

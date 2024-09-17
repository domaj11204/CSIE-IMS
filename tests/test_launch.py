from launch import add_term, export_hotkey, search_key_word
from modules.utils import read_config
config = read_config()
def test_about_shortcut():
    shortcuts = config["shortcuts"]
    export_hotkey(shortcuts["export"])
    search_key_word(shortcuts["search"])
    add_term(shortcuts["add"])
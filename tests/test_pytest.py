from modules.knowledge_base import knowledge_base    # The code to test

import yaml
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f) # 使用safe來避免在yaml中藏惡意程式碼

def test_search_by_keyword():
    # 查不到
    assert knowledge_base.search_by_keyword("飛的很高", config) == ""
    # obsidian中查的到
    assert "來自obsidian:\n直譯器\n" in knowledge_base.search_by_keyword("Python", config) 
    # neo4j中查的到(論文)
    assert knowledge_base.search_by_keyword("中醫方劑配伍系統", config) == "來自neo4j:\n本研究團隊已研製一個中醫辨證系統及一個中醫藥材配伍系統。本論文在前兩個系統的基礎上，研製一個中醫方劑配伍系統。這三個系統實踐中醫「辨證論治」的資訊化。中醫辨證系統實踐中醫「辨證」的資訊化，目前支援67個證候。中醫方劑配伍系統及中醫藥材配伍系統協力實踐中醫「論治」的兩階段資訊化。第一個階段，中醫方劑配伍系統根據辨證的證候，推薦治療效力最強的方劑，目前支援186帖方劑。第二個階段，中醫藥材配伍系統根據辨證的證候及推薦的方劑，進行加減藥材，推薦治療效力最強的藥材，目前支援334味藥材。本論文也進行新增藥材及方劑的標準化，並依標準化的藥材及方劑更新中醫藥材知識本體及中醫藥材辭庫。本論文也訂定各方劑治療各證候的效力值，運用多目標最佳化技術，推薦治療多證候效力最強的方劑。\n"
    # neo4j中查的到(人物)
    assert knowledge_base.search_by_keyword("Huajun Chen", config) == "來自neo4j:\nHuajun Chen\n"
    # 不完整查詢(目前設計成查不到)
    assert knowledge_base.search_by_keyword("Huajun Che", config) == ""

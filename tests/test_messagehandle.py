from modules.MessageHandle import exportWebPage
def test_import_github():
    exportWebPage({
        'APIVersion': '3.0', 
        'predicate': 'ExportWebPage', 
        'subject': {'name': 'USER'}, 
        'object': {'tabURL': 'https://github.com/netease-youdao/QAnything', 
                   'tabTitle': 'netease-youdao/QAnything: Question and Answer based on Anything.', 
                   'description': '一個新潮的QA系統', 
                   'TagString': '問答系統, RAG'}})
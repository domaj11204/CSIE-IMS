"""
由fastapi.py呼叫
處理論文、會議逐字稿、筆記軟體、筆記、log檔
"""

class parser_paper():
    """
    處理論文相關的資訊。
    讀取pdf檔，回傳研究方法、研究目的等
    讀檔、切割、LLM/筆記
    """
    
    def extract_text_from_rect(pdf_path, page_num, rect):
        reader = PdfReader(pdf_path)
        page = reader.pages[page_num]
        # Rect is defined as [left, bottom, right, top]
        x0, y0, x1, y1 = rect

        text = ""
        for content in page.get_contents():
            text += content.get_text()
            
        # Filter text within the rectangle
        lines = text.split('\n')
        extracted_text = [line for line in lines if is_within_rect(line, x0, y0, x1, y1)]

        return " ".join(extracted_text)

    def is_within_rect(line, x0, y0, x1, y1):
        # Dummy function: Implement this function to check if the text line is within the rectangle
        # This function should check the text's position and compare it with the rectangle coordinates
        return True  # Placeholder, you need to implement this

    def parser_pypdf(name:str=None, id:str=None, file_path:str=None):
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        number_of_pages = len(reader.pages)
        page = reader.pages[1]
        text = page.extract_text()
        print(text)
        print("=====================================")
        destinations = reader._get_named_destinations()
        print(destinations)
        page = reader.pages[-1]
        text = page.extract_text()
        obj = reader.resolved_objects
        print(page.annotations)
        print("========")
        # https://github.com/py-pdf/pypdf/issues/2651
        page = reader.pages[0]
        for annotation in page.annotations:
            print(type(annotation))
            print(annotation)
            obj = annotation.get_object()
            print(type(obj))
            print(obj)
            if obj.get('/Subtype') == '/Link':
                if "/URI" in obj.get('/A').keys():
                    print("包含連結")
                    print('Link : ', obj.get('/A').get('/URI'))
                if "/D" in obj.get('/A').keys():
                    print("包含跳轉")
                    print(obj)
                    dest = obj.get('/A').get('/D')
                    print(dest)
                    page_index = reader.get_destination_page_number(dest)
                    rect = obj.get('/Rect')
                    x0, y0, x1, y1 = rect
                    
                    
    def parse_pymu(self, file_path:str):
        import pymupdf
        doc = pymupdf.open(file_path)
        print("======link======")
        for page in doc: # iterate the document pages
            links = page.get_links()
            for link in links:
                if "nameddest" in link:
                    print(link["nameddest"])
                else:
                    print(link)
                from_rect = link["from"]
                text = page.get_textbox(from_rect)
                print("TTT")
                print(type(text))
                
                print(text)
                exit()
        print("=======cite======")
        for page in doc:
            for annot in page.annots():
                print(f'Annotation on page: {page.number} with type: {annot.type} and rect: {annot.rect}')
    def parse_tex(self, file_path:str):
        with open(file_path, "r") as f:
            data = f.read()
            # https://stackoverflow.com/questions/57064771/extract-cited-bibtex-keys-from-tex-file-using-regex-in-python
            # TODO
                        
class parser_transcript():
    """
    處理逐字稿相關的資訊。
    讀取txt或srt檔，解決問題
    """
    pass

class parser_note_tool():
    """
    處理筆記軟體的溝通。
    開啟api文件、取得tag、讀取筆記、搜尋筆記
    修改tag、新增筆記、修改筆記、修改筆記tag
    """
    pass

if __name__ == "__main__":
    parser = parser_paper()
    #parser.parse_pymu(file_path="./data/test2.pdf")
    #parser.parser(file_path="./data/test.pdf")
    parser.parse_latex(file_path="./data/test.tex")
    
    

from modules.knowledge_base import source
from modules.utils import call_api
from modules.debug_utils import print_var
class rdf_source(source):
    filter_query = """
        SELECT ?subject ?predicate ?object
        WHERE {{
            ?subject ?predicate ?object .
            FILTER (regex(str(?subject), "{keyword}", "i") || regex(str(?predicate), "{keyword}", "i") || regex(str(?object), "{keyword}", "i"))
        }}
        """
    local_name_query = """
        PREFIX ontology: <{base_iri}>
        SELECT ?subject ?predicate ?object
        WHERE {{
		{{
			?subject ?predicate ontology:{keyword} .
		}}
		UNION
		{{
			ontology:{keyword} ?predicate ?object .
		}}
		}}
        """
        

    def __init__(self, name="rdf", config=None):
        super().__init__(name, config)
        self.owl_dict = {}

    async def get_file_list(self):
        file_list = []
        for key, value in self.config.items():
            file_list.append({"name":key, "path":value, "type":"知識本體"})
        return file_list
    
    
    async def get_data(self, uuid:str=None, path:str=None, uri:str=None, depth:int=1, **kwargs):
        """根據uuid或path取得資料"""
        # 一個知識本體一個uuid
        # TODO: 應該使用type來區分不同的知識本體嘛？type的定義或意義到底是什麼？
        print_var(path)
        if uri is not None:
            return self.get_data_by_uri(uri, depth)
        if path is None:
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["uri"]            
        if "http" in path:
            import requests
            response = requests.get(path)
            return response.text
        else:
            import aiofiles
            async with aiofiles.open(path, "r") as f:
                content = await f.read()
                return content
    


    async def keyword_search(self, keyword, **kwargs):
        """使用filter過濾出包含該keyword的所有三元體
        由於使用filter，效能較差。另外有一個使用local_name的版本，效能會好很多但不夠通用。
        TODO: 目前僅考量一個知識本體，因此結果中不會記錄來源
        """
        from rdflib import Graph
        from owlready2 import get_ontology, default_world # 用於取得base_iri
        # 決策: 不選擇owlready2是因為owlready2內建的搜尋無法使用keyword query，會報錯
        # sqlite3.OperationalError: user-defined function raised exception
        # 因此owlready2只用來取得base_iri
        g = Graph()
        uuids = []
        result = []
        uuids.extend((await call_api(f"/v1/knowledge_base/uuids", "get", params={"source":self.name}))["uuids"])
        for uuid in uuids:
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["path"]
            g.parse(path, format="xml") # TODO: 格式(如xml)不該寫死，應該包含在info中
            # local_name的版本，暫時先取消
            # owl = get_ontology(path).load()
            # base_iri = owl.base_iri
            # query = self.keyword_query.format(keyword=keyword, base_iri=base_iri)
            # query_results = list(g.query(query))
            # for i, query_result in enumerate(query_results):
            #     query_results[i] = list(query_result)
            #     for j, temp_result in enumerate(query_results[i]):
            #         if temp_result is None:
            #             query_results[i][j] = base_iri+keyword
            query_results = list(g.query(self.filter_query.format(keyword=keyword)))
            for index, query_result in enumerate(query_results):
                query_results[index] = " ".join(query_result)
            # 將結果從短到長排序
            query_results.sort(key=len)
        result = query_results # 如果考慮多個知識本體來源，會修改這邊
        print_var(kwargs)
        if "top_k" in kwargs:
            return result[:kwargs["top_k"]]
        else: return result
    
    async def fuzzy_search(self, keyword, top_k, **kwargs):
        """取得所有個體(individuals)後，使用fuzzy search找出相似的個體。"""
        from rdflib import Graph
        from thefuzz.process import extract
        from thefuzz import fuzz
        result = []
        g = Graph()
        # TODO: 之後需要考量多個知識本體時的情況
        uuids = []
        # for type in type_list:
        uuids.extend((await call_api(f"/v1/knowledge_base/uuids", "get", params={"source":self.name}))["uuids"])
        for uuid in uuids: # 考慮符合條件的知識本體(一個UUID對應一個知識本體)
            path = (await call_api(f"/v1/knowledge_base/{uuid}", "get"))["info"]["path"] # 從知識庫取得路徑
            all_individuals = await self.get_all_individuals(path) # 取得知識本體的個體列表
            result_list = extract(keyword, all_individuals, limit=top_k, scorer=fuzz.UWRatio) # 這樣的寫法只考慮一個本體
            # 決策: QRatio的效果比partial_ratio和WRatio好
            result_uuids = []
            for result in result_list:
                result_uuids.append(result[2])
            result.extend(result_uuids)
        return result
        
    # 565->18735 切出18200份，跑了兩天？ 18170
    def split(self, split_data:source.split_data):
        print_var(split_data)
        entity, chunk_size, text, parent_uuid, parent_name, parent_source = super().split_preprocess(split_data)
        line_split_results = text.split("\n\n")
        split_result = []
        for line_split_result in line_split_results:
            temp_split_data = split_data.copy()
            temp_split_data.entity["data"] = line_split_result
            split_result.extend(super().split(temp_split_data))
            
        return split_result
        
    def get_data_by_uri(self, path:str, uri:str, depth:int=1):
        """根據URI取得相關的triple
        TODO: 目前僅考慮depth為1的情況，難以想像depth>1的時候資料量會多大
        """
        import rdflib
        g = rdflib.Graph()
        g.parse(path, format="xml")
        query = f"""
            SELECT ?subject ?predicate ?object
            WHERE {{
            {{
                ?subject ?predicate {uri} .
            }}
            UNION
            {{
                {uri} ?predicate ?object .
            }}
            }}
        """
        query_results = list(g.query(query))
        for i, query_result in enumerate(query_results):
            query_results[i] = list(query_result)
            for j, temp_result in enumerate(query_results[i]):
                if temp_result is None:
                    query_results[i][j] = uri
        return query_results

    async def get_all_individuals(self, path, base_iri=None):
        """回傳該base_iri下的所有individuals"""
        if base_iri is None:
            from owlready2 import get_ontology
            owl = get_ontology(path).load()
            base_iri = owl.base_iri
        import rdflib
        g = rdflib.Graph()
        g.parse(path, format="xml")
        query = """
        PREFIX my: <http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT DISTINCT ?entity
        WHERE 
        { ?entity a owl:NamedIndividual. }
        """
        all_individuals = list(g.query(query))
        print(all_individuals[:10])
        for i, individual in enumerate(all_individuals):
            all_individuals[i] = individual.entity.split("#")[1]
        print(all_individuals[:10])
        return all_individuals
    
def owl_test():
    print("lab3")
    import owlready2
    # obj = rdf_source()
    # obj.get_owl(name="test1", uri="./data/symptoms.owl")
    
    # owl = obj.owl_dict["test1"]
    owl = owlready2.get_ontology("./data/symptoms.owl").load()
    base_iri = owl.base_iri
    query = rdf_source.keyword_query.format(keyword="血虛證類", base_iri=base_iri)
    print(query)
    graph = owlready2.default_world.as_rdflib_graph()
    print(list(graph.query(query)))
    print(list(owlready2.default_world.sparql(query)))
    import rdflib
    g = rdflib.Graph()
    g.parse("./data/symptoms.owl", format="xml")
    print(list(g.query(query)))
    print("a-da-da-da-d")
    owl.base_iri = "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#"
    print(type(owl))
    print(owl.baseiri)
    print(owl.search_one(label="血虛證類"))
    print(owl.search(iri="*血虛證類"))
    for annot_prop in owl.metadata:
        print(annot_prop, ":", annot_prop[owl.metadata])

    result1 = list(g.query(query))
    print(len(result1))
    print(result1)
    
    
    graph = default_world.as_rdflib_graph()
    print("2", list(graph.query(sparql_query)))
    
def split_data_test():
    """測試怎麼切資料比較好
    用turtle切還是會有一個長度3000的chunk
    用ntriple會有節點屬性
    """
    path = "./data/symptoms.owl"
    # from owlready2 import get_ontology
    # owl = get_ontology(path).load()
    # base_iri = owl.base_iri
    base_iri = "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#"
    with open(path, "r") as file:
        text = file.read()
    split_data = text.split("\n\n")
    
    max_len = 0
    result = ""
    for split in split_data:
        if len(split) > max_len:
            max_len = len(split)
            result = split
    import rdflib
    g = rdflib.Graph()
    g.parse(path, format="xml")
    g.serialize("./data/symptoms_test.trig", format="trig")
    print(len(split_data))
    print(max_len)
    print(result)
    print(result.replace(base_iri, ""))
    print(len(result.replace(base_iri, "")))
    
async def repair_chromadb():
    """用於修正load_data時忘記補上的UUID"""
    from tqdm import tqdm
    from modules.rag import rag
    rag_obj = rag()
    await rag_obj.init_chroma()
    # 嵌入的時候忘記加上uuid，補上
    # 從neo4j取得所有chunk的uuids
    uuids = (await call_api("v1/knowledge_base/uuids", "get", params={"type":"chunk"}))["uuids"]
    for split in split_data[1:]:
        print(split[:uuid_len])
        uuids.append(split[:uuid_len])
    # 取得relation，過濾出知識本體的相關chunk
    rdf_chunk_uuids = []
    to_do_uuids = []
    for uuid in tqdm(uuids):
        relation_list = (await call_api(f"v1/knowledge_base/relations/{uuid}", "get"))["relations"]
        for relation in relation_list:
            if relation["to"]["type"] == "知識本體":
                rdf_chunk_uuids.append(uuid)
                to_do_uuids.append(uuid)
                if len(to_do_uuids) > 100:
                    metadata_list = [{"uuid":uuid} for uuid in to_do_uuids]
                    for _ in range(3):
                        try:
                            rag_obj.chromadb_collection.update(ids=to_do_uuids, metadatas=metadata_list)
                            break
                        except:
                            import time
                            print(_)
                            time.sleep(2)
                            pass
                    to_do_uuids = []
                    break
    metadata_list = [{"uuid":uuid} for uuid in to_do_uuids]
    rag_obj.chromadb_collection.update(ids=to_do_uuids, metadatas=metadata_list)
    print(len(rdf_chunk_uuids))

async def test():
    uuid = "01ed9ce2-6bab-43a1-bccd-432298719331"
    entity = (await call_api(f"/v1/knowledge_base/entity/{uuid}", "GET"))["entity"]
    split_data = (await call_api("v1/rdf/split", "post", 
                                    data={"entity":entity, "chunk_size":1024}))["split_result"]
    print(split_data[0])
    print("=======")
    print(split_data[-1])
if __name__ == "__main__":
    import asyncio
    # asyncio.run(repair_chromadb())
    asyncio.run(test())
    
    exit(999)
    #=================================
    owl_test()
    print("lab2")
    from rdflib import Graph
    from rdflib import namespace
    # 讀取RDF
    rdf_file_path = "https://zeus.cs.ccu.edu.tw/tcm_latest/symptomsSearch/ontology/symptoms.owl"  
    g = Graph()
    g.parse(rdf_file_path, format="xml")
    print(g.n3())
    print("====")
    print(list(g[:namespace.RDFS.label]))
    from owlready2 import get_ontology, default_world
    base_iri = "http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#"
    owl = get_ontology("./data/symptoms.owl").load()
    query = rdf_source.keyword_query.format(keyword="血虛證類", base_iri=base_iri)
    print(list(default_world.sparql(query)))
    print(list(g.query(query)))
    exit(999)
    # g.parse(rdf_file_path)
    # 錯誤訊息: 
      # rdflib.exceptions.ParserError: Could not guess RDF format for 
      # https://zeus.cs.ccu.edu.tw/tcm_latest/symptomsSearch/ontology/symptoms.owl from 
      # file extension so tried Turtle but failed.You can explicitly specify format using the format argument.
    # 使用副檔名分析格式，可手動補上format 參考:https://rdflib.readthedocs.io/en/stable/intro_to_parsing.html
    
    
    
    keyword="血虛證類"
    # 定義SPARQL查詢語句
    sparql_query1 = f"""
    PREFIX ex: <http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#>
    SELECT ?subject ?predicate ?object
    WHERE {{
        ?subject ?predicate ?object .
        FILTER (regex(str(?subject), "{keyword}", "i") || regex(str(?predicate), "{keyword}", "i") || regex(str(?object), "{keyword}", "i"))
    }}
    """

    sparql_query2 = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX ontology: <http://www.semanticweb.org/pllab/ontologies/2013/11/untitled-ontology-2#>

    SELECT ?subject ?predicate ?object
    WHERE {
    {
        ?subject ?predicate ontology:血虛證類 .
    }
    UNION
    {
        ontology:血虛證類 ?predicate ?object .
    }
    UNION
    {
        ?subject rdfs:subClassOf ontology:血虛證類 .
    }
    }
    """
    sparql3 = "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n" + (
    """SELECT DISTINCT ?cls ?com\n"""
    """WHERE { \n"""
    """    ?instance a ?cls . \n"""
    """    OPTIONAL { ?cls rdfs:comment ?com } \n"""
    """}"""
    )
    # 執行SPARQL查詢
    result = g.query(sparql_query1)
    # 輸出結果
    for row in result:
        print(row[0], row[1], row[2])
    print("===============")
    result = g.query(sparql_query2)
    # 輸出結果
    for row in result:
        print(row[0], row[1], row[2])
    
    # print("=========3======")
    # result = g.query(sparql3)
    # # 輸出結果
    # for row in result:
    #     print(row[0], row[1])
    # #  ================================
    
    
    
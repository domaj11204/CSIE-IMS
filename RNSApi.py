import requests
import json
from dataclasses import dataclass

@dataclass
class triple:
    subject: dict
    predicate: str
    object: dict
    
    
    
def send_triple(subject:dict, predicate:str, object:dict):
    triple = {
        "subject": subject,
        "predicate": predicate,
        "object": object
    }
    triple_json = json.dumps(triple)
    response = requests.post("http://localhost:27711/upload_triple", data=triple_json)
    print("send_triple: response:", response)


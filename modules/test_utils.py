def remove_uuids(data):
    """遞迴地從字典中移除 uuid 鍵。"""
    if isinstance(data, dict):
        keys_to_remove = [key for key in data.keys() if "uuid" in key.lower()]
        print(keys_to_remove)
        for key in keys_to_remove:
            data.pop(key, None)
        for value in data.values():
            remove_uuids(value)
    elif isinstance(data, list):
        for item in data:
            remove_uuids(item)
            
def remove_host(data):
    import re
    if type(data) == dict:
        for key in data:
            data[key] = remove_host(data[key])
        return data
    else:
        return re.sub(r"[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}:[0-9]{1,5}","", data)
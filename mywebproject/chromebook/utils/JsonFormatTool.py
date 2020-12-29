import json

def WritingJSONdata(file,data):
    # Writing JSON data
    with open('data.json', 'w') as f:
        json.dump(data, f)
def Readingdataback(file):
    # Reading data back
    with open('data.json', 'r') as f:
        data = json.load(f)
    return data

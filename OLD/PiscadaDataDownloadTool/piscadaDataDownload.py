import requests
import json

def PiscadaWebSocketGet(tagName,timeStart):
    api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
    response = requests.get(api_url)
    return response.json()

def convertData(rawData):
    print("Converting data")
    data = {'timeseries':[], 'values':[]}
    for point in rawData:
        data['timeseries'].append(point['ts'])
        data['values'].append(point['v'])
    return data

def PiscadaGetMultipleTags(tagNames,timeStart):
    out = dict()
    length,i = len(tagNames), 0
    for tag in tagNames:
        data = PiscadaWebSocketGet(tag, timeStart)
        out[tag] = convertData(data)
        i += 1
        print("Succesfully retrieved: " + tag + "("+str(i)+"/" + str(length)+")")
    data_to_json(out)
    print("Got all data")

def data_to_json(data):
    data = json.dumps(data)
    f = open("data.json",'x')
    f.write(data)
    f.close()
    print('Data is found in data.json')


def main():
    f = open("settings.json",'r')
    settings = json.loads(f.read())
    print("Settings: " + str(settings))
    PiscadaGetMultipleTags(settings["tags"],settings["timeStart"])

main()
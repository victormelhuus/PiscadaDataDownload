from logging import exception
from datetime import datetime
import requests
import json
import os

def PiscadaWebSocketGet(tagName,timeStart):
    print("     Asking for: ",tagName)
    api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
    response = requests.get(api_url)
    return response.json()

def convertData(rawData):
    data = {'timeseries':[], 'values':[]}
    for point in rawData:
        data['timeseries'].append(point['ts'])
        data['values'].append(point['v'])
    return data

def isError(rawData):
    if len(rawData)==0:
        return True
    else:
        return False

    

def PiscadaGetMultipleTags(settings):
    rooms = settings['rooms']
    timeStart = settings["timeStart"]
    length,i = len(rooms), 0
    errors, warnings = 0, 0
    for room in rooms:
        out = dict()
        i+=1
        data, warning = PiscadaGetRoom(room, settings, timeStart,i,length)
        warnings += warning
        if len(data)>0:
            out['room' + room] = data
            print("  storing to file")
            save_data(out,room)
            print("  Done with room " + room + " ("+str(i)+"/" + str(length)+")")
        else:
            errors += 1
            print('No data for room '+ room + " ("+str(i)+"/" + str(length)+")")
        
    print("Finished with " + str(errors) + " errors and " + str(warnings)+" warnings")

def data_to_json(data):
    data = json.dumps(data)
    try:
        f = open("data.json",'x')
    except:
        f = open("data.json",'w') 

    f.write(data)
    f.close()
    print('Data is found in data.json')

def save_data(data, name):
    f=open("data_room_"+name+".json",'x')
    f.write(json.dumps(data))
    f.close()

def append_data_to_json(data):
    isNew = False
    try:
        f = open("data.json",'r+')
    except:
        isNew = True
        f = open("data.json",'x')

    if not isNew:
        file_data = json.loads(f.read()) 
        keys = list(data.keys())
        for key in keys:
            file_data[key] = data[key]
    else:
        file_data = data

    f.write(json.dumps(file_data))
    f.close()

def PiscadaGetRoom(room, settings, timestart, i, num_rooms):
    roomData = dict()
    print("Room " + room +" ("+str(i)+"/"+str(num_rooms)+")"+":")
    prefix = settings['system_prefix']
    #Get temperature
    print("  (1/4) collecting temperature data")
    warning = 0
    tag = prefix +settings['prefix_temp']+room+settings['temp_end']
    rawData = PiscadaWebSocketGet(tag, timestart)
    if not isError(rawData):
        print("     SUCCESS!")
        print("     converting data")
        roomData["room_temp"] = convertData(rawData)
    else:
        warning += 1
        print("     WARNING! no temperature data")
    
    #Get temperature reference data
    print("  (2/4) collecting temperature reference data")
    tag = prefix + settings['prefix_temp'] + room + settings['temp_sp_end']
    rawData = PiscadaWebSocketGet(tag, timestart)
    if not isError(rawData):
        print("     SUCCESS!")
        print("     converting data")
        roomData["room_temp_ref"] = convertData(rawData)
    else:
        warning += 1
        print("     WARNING! no temperature reference data")
    
    #Get heating output
    print("  (3/4) collecting heating output data")
    tag = prefix + settings['prefix_temp_c'] + room + settings['end_temp_c']
    rawData = PiscadaWebSocketGet(tag, timestart)
    if not isError(rawData):
        print("     SUCCESS!")
        print("     converting data")
        roomData["room_heat_output"] = convertData(rawData)
    else:
        warning += 1
        print("     WARNING! no heating output data")
    
    #Get CO2 data
    print("  (4/4) collecting CO2 measurement data")
    tag = prefix +settings['prefix_co2']+room+settings['end_co2']
    rawData = PiscadaWebSocketGet(tag, timestart)
    if not isError(rawData):
        print("     SUCCESS!")
        print("     converting data")
        roomData["room_co2"] = convertData(rawData)
    else:
        warning += 1
        print("     WARNING! no CO2 data")

    return roomData, warning

    


def main():
    f = open("settings.json",'r')
    settings = json.loads(f.read())
    f.close()
    print("Settings: " + str(settings))

    try:
        os.chdir("Rooms")
    except:
        os.mkdir("Rooms")
        os.chdir("Rooms")
    PiscadaGetMultipleTags(settings)

main()
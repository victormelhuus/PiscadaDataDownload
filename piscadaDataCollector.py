from requests import get
from json import loads, dumps
from time import sleep
from threading import Thread, Lock
from datetime import datetime
from sys import stdout
from time import time
from math import floor
from os import chdir, mkdir, listdir
info_lock = Lock()
info = {"tags":0, "completed":0, "fault":0, "status":"waiting", "saverStatus":"waiting"}

run = True
run_lock = Lock()

faulty_tags_list = []

def main():
    f = open("settings.json",'r')
    settings = loads(f.read())
    f.close()
    timeStart = settings["timeStart"]
    seriesSettings = settings["series"]

    #Check if we have previous data
    try: files = listdir("data")
    except: mkdir("data")
    chdir("data")
    cache = []
    for file in files: cache.append(file.split(".")[0]) 

    #Find out what to download
    if seriesSettings['enable']: tags = getSeries(seriesSettings)
    else: tags = list()

    for tag in settings['tags']: tags.append(tag)
    info["tags"] = len(tags)

    #Remove what we already have downloaded
    removed = []
    for tag in cache:
        if tag in tags: 
            tags.remove(tag)
            removed.append(tag)

    completed = len(removed)

    if completed > 0:
        print("Previously completed: " + str(removed))

    info["completed"] = len(removed)        
    print("Will download: " + str(tags))

    sleep(10)

    #Start download and agent
    downloaderThread = Thread(target= downloader, args= (timeStart, tags))
    agentThread = Thread(target = agent)
    downloaderThread.start()
    agentThread.start()
    downloaderThread.join()
    agentThread.join()

    
    
def downloader(timeStart, tags):
    for tag in tags:
        piscadaWebSocketGet(timeStart, tag)

    if len(faulty_tags_list) >0: saveData("faulty_tags", faulty_tags_list)

    run_lock.acquire()
    run = False
    run_lock.release()


def piscadaWebSocketGet(timeStart, tagName):
    info_lock.acquire()
    info["status"] = "Collecting " + tagName
    info_lock.release()

    api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
    response = get(api_url).json()
    
    data = {'timeseries':[], 'values':[]}

    
    info_lock.acquire()
    info["status"] = "Restructuring and converting " + tagName
    info_lock.release()

    i = 0
    isZero = True
    for point in response:
        i += 1
        if point['v'] > 0: isZero = False
        newTime = datetime.strptime(point['ts'],"%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)
        data['timeseries'].append(newTime.strftime("%Y-%m-%dT%H:%M:%S"))
        data['values'].append(point['v'])
        

    info_lock.acquire()
    if isZero:
        faulty_tags_list.append(tagName)
        info["completed"] += 1
        info["fault"] += 1
        info["status"] = "Saving " + tagName
        info_lock.release()
    else:
        info["completed"] += 1
        info["status"] = "Saving " + tagName
        info_lock.release()
        saveData(tagName,data)
    
   

def generateSeries(start:str,end:str):
    series = []
    nStart = int(start)
    nEnd = int(end)
    for i in range(nStart,nEnd +1):
        series.append(str(i).zfill(3))
    return series

def getSeries(settings):
    #rooms = generateSeries(settings["series_start"], settings["series_end"])
    rooms = settings["rooms"]
    series = []
    for room in rooms:
        series.append(settings["system_prefix"] + "RT01_ " + room + "_MV")
        series.append(settings["system_prefix"] + "RT01_ " + room + "_SPK")
        series.append(settings["system_prefix"] + "KA01_ " + room + "_C")
        series.append(settings["system_prefix"] + "RY01_ " + room + "_MV")
        series.append(settings["system_prefix"] + "SQ401_ " + room + "C")
    return series
        


def agent():
    xRun = run
    start_time = time()
    while xRun:
        sleep(0.5)
        
        #Get info
        info_lock.acquire()
        ainfo = info
        info_lock.release()

        #Print
        print(progressString(percent = int((ainfo["completed"]/ainfo["tags"])*100), name="Progress       "))
        print("Collected: " +str(ainfo["completed"]) + "/" + str(ainfo["tags"]))
        print("Status: " + ainfo["status"])
        print("Saver: "  + ainfo["saverStatus"])
        elapsed = int(time()-start_time)
        if elapsed < 60:
            print("time elapsed: " + str(elapsed) + "s")
        else:
            minutes = floor(elapsed/60)
            seconds = elapsed - minutes*60
            print("time elapsed: " + str(minutes) + " minutes and " + str(seconds) + "s")
        stdout.write("\033[F")
        stdout.write("\033[F")
        stdout.write("\033[F")
        stdout.write("\033[F")
        stdout.write("\033[F")
        run_lock.acquire()
        xRun = run
        run_lock.release()

def progressString(percent=0, width=40, name = "progress",end=""):
    left = width * percent // 100
    right = width - left
    
    tags = "#" * left
    spaces = " " * right
    percents = f"{percent:.0f}%"
    return name+": " + "[" + tags + spaces + "]" + percents +end

def saveData(tagname, data):
    try:
        f = open(tagname + ".json",'w')
    except:
        f = open(tagname + ".json",'x')
    f.write(dumps(data))
    f.close()



main()
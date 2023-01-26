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
info = {"tags":0, "completed":0, "fault":0, "status 1":"waiting","status 2":"waiting", "saverStatus":"waiting"}

run = True
run_lock = Lock()

tags_lock = Lock()
faulty_tags_list = []
tags = []
com_lock = Lock()
save_lock = Lock()

def main():
    print("Starting...")
    f = open("settings.json",'r')
    settings = loads(f.read())
    f.close()
    timeStart = settings["timeStart"]
    seriesSettings = settings["series"]

    #Check if we have previous data
    cache = []
    try: 
        files = listdir("data")
        for file in files: 
            cache.append(file.split(".")[0]) 
    except: mkdir("data")
    chdir("data")
    
    #Find out what to download
    if seriesSettings['enable']: 
        series = getSeries(settings)
        for tag in series:
            tags.append(tag)

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
    downloaderThread1 = Thread(target= downloader, args= (timeStart, 1))
    downloaderThread2 = Thread(target= downloader, args= (timeStart, 2))
    agentThread = Thread(target = agent)
    print("Starting threads")
    downloaderThread1.start()
    downloaderThread2.start()
    agentThread.start()
    downloaderThread1.join()
    downloaderThread2.join()
    agentThread.join()

    if len(faulty_tags_list) >0: saveData("faulty_tags", faulty_tags_list)

    
    
def downloader(timeStart, ID):
    print("Thread " + str(ID) +" starting")
    while True:
        tags_lock.acquire()
        if len(tags) > 0:
            tag = tags.pop()
            tags_lock.release()
            piscadaWebSocketGet(timeStart, tag, ID)
        else:
            print("Thread " + str(ID) +" found no tags")
            tags_lock.release()
            break        

    run_lock.acquire()
    run = False
    run_lock.release()
    print("Thread " + str(ID) +" exiting")


def piscadaWebSocketGet(timeStart, tagName, ID):
    api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
    info_lock.acquire()
    info["status " + str(ID)] = "Waiting to download " + tagName
    info_lock.release()

    com_lock.acquire()
    info_lock.acquire()
    info["status " + str(ID)] = "Downloading " + tagName
    info_lock.release()
    response = get(api_url).json()
    com_lock.release()

    data = {'timeseries':[], 'values':[]}

    
    info_lock.acquire()
    info["status " + str(ID)] = "Restructuring and converting " + tagName
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
        info["status " + str(ID)] = "Saving " + tagName
        info_lock.release()
    else:
        info["completed"] += 1
        info["status " + str(ID)] = "Waiting to save " + tagName
        info_lock.release()
        save_lock.acquire()
        info_lock.acquire()
        info["status " + str(ID)] = "Saving " + tagName
        info_lock.release()
        saveData(tagName,data)
        save_lock.release()
    
   

def generateSeries(start:str,end:str):
    series = []
    nStart = int(start)
    nEnd = int(end)
    for i in range(nStart,nEnd +1):
        series.append(str(i).zfill(3))
    return series

def getSeries(settings):
    #rooms = generateSeries(settings["series_start"], settings["series_end"])
    seriesSettings = settings["series"]
    rooms = settings["rooms"]
    series = []
    for room in rooms:
        series.append(seriesSettings["system_prefix"] + "RT01_" + room + "_MV")
        series.append(seriesSettings["system_prefix"] + "RT01_" + room + "_SPK")
        series.append(seriesSettings["system_prefix"] + "KA01_" + room + "_C")
        series.append(seriesSettings["system_prefix"] + "RY01_" + room + "_MV")
        series.append("LS_N_360_002_SQ401_" + room + "_C")
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
        print("Status T1: " + ainfo["status 1"])
        print("Status T2: " + ainfo["status 2"])
        print("Faulty: "  + str(ainfo["fault"]))
        elapsed = int(time()-start_time)
        if elapsed < 60:
            print("time elapsed: " + str(elapsed) + "s")
        else:
            minutes = floor(elapsed/60)
            seconds = elapsed - minutes*60
            print("time elapsed: " + str(minutes) + " minutes and " + str(seconds) + "s")
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
from requests import get
from json import loads, dumps
from time import sleep
from threading import Thread, Lock
from datetime import datetime
from sys import stdout
from time import time
info_lock = Lock()
info = {"tags":0, "completed":0, "fault":0, "status":"waiting", "saverStatus":"waiting"}

run = True
run_lock = Lock()

store_lock = Lock()
data_to_store = {}

faulty_tags_list = []
completed_tags_list = []
save_data = dict()
previous_data = dict()

def main():
    f = open("settings.json")
    settings = loads(f.read())
    f.close()
    timeStart = settings["timeStart"]
    seriesSettings = settings["series"]

    #Open previous data
    try:
        f = open("data.json",'w')
    except:
        f = open("data.json",'x')
    previous_data = loads(f.read())
    f.close()

    #Open previously completed list
    try:
        f= open("completed.json",'w')
    except:
        f= open("completed.json",'x')
    completed_tags_list = loads(f.read())
    f.close() 

    #Find out what to download
    tags = getSeries(seriesSettings)

    for tag in settings['tags']:
        tags.append(tag)
    
    info["tags"] = len(tags)


    #Start download and agent
    downloaderThread = Thread(target= downloader, args= (timeStart, tags))
    agentThread = Thread(target = agent)
    saverThread = Thread(target = saver)
    downloaderThread.start()
    agentThread.start()
    saverThread.start()
    downloaderThread.join()
    agentThread.join()
    saverThread.join()

    save()
    
    
def downloader(timeStart, tags):
    for tag in tags:
        piscadaWebSocketGet(timeStart, tag)
    run_lock.acquire()
    run = False
    run_lock.release()


def piscadaWebSocketGet(timeStart, tagName):
    if tagName in completed_tags_list:
        store_lock.acquire()
        try:
            data_to_store[tagName] = previous_data.pop(tagName)
        except:
            faulty_tags_list.append(tagName)
            info_lock.acquire()
            info["fault"] += 1
            info_lock.release()
        store_lock.release()
    else:
        info_lock.acquire()
        info["status"] = "Collecting " + tagName
        info_lock.release()

        api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
        response = get(api_url).json()
        
        data = {'timeseries':[], 'values':[]}

        if len(response)==0:
            store_lock.acquire()
            faulty_tags_list.append(tagName)
            store_lock.release
            info_lock.acquire()
            info["fault"] += 1
            info_lock.release()
        else:
            info_lock.acquire()
            info["status"] = "Restructuring and converting " + tagName
            info_lock.release()

            for point in response:
                newTime = datetime.strptime(point['ts'],"%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)
                data['timeseries'].append(newTime.strftime("%Y-%m-%dT%H:%M:%S"))
                data['values'].append(point['v'])
        store_lock.acquire()
        completed_tags_list.append(tagName)
        data_to_store[tagName] = data
        store_lock.release()

    info_lock.acquire()
    info["completed"] += 1
    info_lock.release()
   

def generateSeries(start:str,end:str):
    series = []
    nStart = int(start)
    nEnd = int(end)
    for i in range(nStart,nEnd +1):
        series.append(str(i).zfill(3))
    return series

def getSeries(settings):
    rooms = generateSeries(settings["series_start"], settings["series_end"])
    series = []
    for room in rooms:
        series.append(settings["system_prefix"] + room + settings["temp_end"])
        series.append(settings["system_prefix"] + room + settings["temp_sp_end"])
        series.append(settings["system_prefix"] + room + settings["temp_sp_act_end"])
        series.append(settings["system_prefix"] + room + settings["heat_output_end"])
    return series
        


def saver(sleep_minutes = 10):
    xRun = run
    while xRun:
        sleep(sleep_minutes*60)
        run_lock.acquire()
        xRun = run
        run_lock.release()
        if xRun:
            info_lock.acquire()
            info["saverStatus"] = "Saving"
            info_lock.release()
            save()
            info_lock.acquire()
            info["saverStatus"] = "Waiting"
            info_lock.release()

def save():
        #Save downloaded data
        store_lock.acquire()
        try:
            f = open("data.json",'w')
        except:
            f = open("data.json",'x')
        f.write(dumps(data_to_store))
        f.close()

        #Save completed jobs
        try:
            f= open("completed.json",'w')
        except:
            f= open("completed.json",'x')
        f.write(dumps(completed_tags_list))
        f.close()

        #Save completed jobs
        try:
            f= open("faulty.json",'w')
        except:
            f= open("faulty.json",'x')
        f.write(dumps(faulty_tags_list))
        f.close()
        store_lock.release()


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
        print("Status: " + ainfo["status"])
        print("Saver: "  + ainfo["saverStatus"])
        print("time elapsed: " + str(int(time()-start_time)) + "s")
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

main()
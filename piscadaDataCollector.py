from requests import get
from json import loads, dumps
from time import sleep
from threading import Thread, Lock

info_lock = Lock()
info = {"tags":0, "completed":0}
run = True
data = {}

def PiscadaWebSocketGet(tagName,timeStart):
    print("     Asking for: ",tagName)
    api_url = "http://localhost:3134/timeseries/" + tagName + "?from=" + timeStart + "&intervall=1m"
    response = get(api_url)
    return response.json()







def main():
    f = open("settings.json")
    settings = loads(f.read())
    f.close()


def agent():
    while run:
        sleep(0.5)
        
        #Get info
        info_lock.acquire()
        ainfo = info
        info_lock.release()





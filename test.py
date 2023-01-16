from json import loads

f= open("data.json")
data = loads(f.read())

keys = data.keys()
for key in keys:
    print(key + "   " +str(len(data[key]['values'])))
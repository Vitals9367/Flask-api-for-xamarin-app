import requests

BASE = "http://127.0.0.1:5000/"

data = [
    {"note": " First note"},
    {"note": " Second note"},
    {"note": " Third note"}
]
for i in range(len(data)):
    response = requests.put(BASE + "note/" + str(i), data[i])
    print(response.json())

input()

response = requests.get(BASE + "note/2")
print(response.json())

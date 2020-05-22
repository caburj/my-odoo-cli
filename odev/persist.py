import json
from pathlib import Path


HOME = Path("~").expanduser()
jsonfile = HOME / ".odev.json"


def save(key, val):
    if not jsonfile.exists():
        with open(jsonfile, "w+") as file:
            file.write("{}")

    with open(jsonfile) as rfile:
        obj = json.load(rfile) or dict()

    with open(jsonfile, "w") as wfile:
        obj[key] = val
        json.dump(obj, wfile)


def remove(key):
    if not jsonfile.exists():
        return

    with open(jsonfile) as rfile:
        obj = json.load(rfile) or dict()

    with open(jsonfile, "w") as file:
        obj[key] = False 
        json.dump(obj, file)


def get(key):
    with open(jsonfile) as file:
        obj = json.load(file)
        return obj.get(key, False)

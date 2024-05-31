#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 /home/vherrmann/repos/-#python3With.json5 --command python

# Replace table col in collection.anki21 with the data from new-col.json. This table contains the meta data from the deck.

import sqlite3
import time
import json
import json5
import itertools
import common as cm

def replaceValOfKeyNested(dic, key, val):
    for k, v in dic.items():
        if k == key:
            dic[k] = val
        elif isinstance(v, dict):
            replaceValOfKeyNested(v, key, val)

def replaceKeyNested(dic, key, new_key):
    if key in dic:
        dic[new_key] = dic[key]
        del dic[key]

    for k, v in dic.items():
        if isinstance(v, dict):
            replaceKeyNested(v, key, new_key)

def replaceValNested(dic, val, new_val):
    for k, v in dic.items():
        if val == v:
            dic[k] = new_val
        elif isinstance(v, dict):
            replaceValNested(v, val, new_val)

database = "collection.anki21"
con = sqlite3.connect(database)
cur = con.cursor()

with open(cm.scriptDir + '/new-col.json', 'r') as fp:
    newCol = json5.load(fp)

print(f"newCol: {newCol}")

mod_date = int(time.time())
replaceValOfKeyNested(newCol, 'mod', mod_date)

prevDecksCol = cur.execute("SELECT decks FROM col").fetchone()[0]
prevDecksColList = list(json.loads(prevDecksCol).keys())
prevDecksColList.remove("1")
did = prevDecksColList[0]
replaceKeyNested(newCol, '<did>', str(did))
replaceValNested(newCol, '<did-num>', did)

# rebuild card templates
cm.runScript("../cards2/build.bash")
# read card templates
tmpls = newCol["models"]["1342696037256"]["tmpls"]
for i, tmpl in zip(itertools.count(1), tmpls):
    with open(cm.scriptDir + f"/../cards2/build/card{i}/frontside.html", "r") as fp:
        tmpl["qfmt"] = fp.read()
    with open(cm.scriptDir + f"/../cards2/build/card{i}/backside.html", "r") as fp:
        tmpl["afmt"] = fp.read()

i = 0
for key, val in newCol.items():
    print(f"key: {key}")
    print(f"val: {json.dumps(val)}")
    cur.execute(f"UPDATE col SET {key}=?", (json.dumps(val),))
    i += 1

con.commit()

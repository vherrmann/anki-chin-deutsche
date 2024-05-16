#!/usr/bin/env -S nix shell nixos#python3 --command python

import json
import sqlite3
import common as cm

con = sqlite3.connect("collection.anki21")
charactersFile = "characters.json"
cur = con.cursor()
data = cur.execute('SELECT id, flds FROM notes').fetchall()
json_val = []

for (id, flds) in data:
    print(id, flds)
    char = flds.split(cm.sep)[0]
    json_val += [char]

with open(charactersFile, encoding='UTF8', mode='w') as fp:
    json.dump(json_val, fp)

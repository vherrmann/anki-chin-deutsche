#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 nixpkgs#opencc --command python
# made to convert the characters in https://ankiweb.net/shared/info/2485307055
# from simplified to traditional
# to use it, you first have to unzip the deck, then cd into the directory of collection.anki2

import sqlite3
import tempfile
import subprocess
import common as cm
import os
import urllib.parse

scriptDir = os.path.dirname(__file__)

openccCacheDir = scriptDir + "/../cache/opencc/"

def convert_to_trad(string):
    stringList = string.split(cm.sep)
    char = stringList[0]
    oFile = openccCacheDir + urllib.parse.quote(char, safe='')
    # We need to check if the cached file is empty for the
    # case that the process got interrupted the last time it has run.
    if os.path.isfile(oFile) and not cm.fileEmptyP(oFile):
        with open(oFile, 'r') as fpo:
            return fpo.read()
    else:
        if not os.path.isfile(oFile):
            open(oFile, 'x').close()
        with open(oFile, 'r') as fpo:
            with tempfile.NamedTemporaryFile(mode='w') as fpi:
                fpi.write(string)
                fpi.flush()

                subprocess.run(["opencc", "-i", fpi.name, "-o", fpo.name])

                fpo.seek(0)
                return fpo.read()

con = sqlite3.connect("collection.anki21")
cur = con.cursor()
data = cur.execute('SELECT id, flds, sfld FROM notes').fetchall()
for (id, flds, sfld) in data:
    print(id, flds, sfld)
    new_flds = convert_to_trad(flds)
    new_sfld = new_flds.split(cm.sep)[0]
    print(id, new_flds, new_sfld)
    cur.execute("UPDATE notes SET flds=?, sfld=? WHERE id=?", (new_flds, new_sfld, id))
con.commit()

# Test quality of sentences by copying the given characters and the generated sentences to variables a,b:
# ist(map((lambda y: list(map((lambda x: x in "".join(a)), list(y)))), b))

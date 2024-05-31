import subprocess
import os
from pathlib import Path
import hashlib
import sqlite3

sep = '\u001f' # seperats fields in database
scriptDir = os.path.dirname(__file__)

def replaceFirst(ls, x, y):
    ls = ls.copy()
    ls[ls.index(x)] = y
    return ls

def runScript(script, args=[]):
    subprocess.run([scriptDir + "/" + script] + args).check_returncode()

def fileEmptyP(path):
    return Path(path).stat().st_size == 0

def yesno(prompt):
    while True:
        user_input = input(f'{prompt} yes/no: ')

        if user_input.lower() in ['yes', 'y']:
            return True
            continue
        elif user_input.lower() in ['no', 'n']:
            break
            return False

def mkdirp(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def interact(lcls):
    import code
    code.InteractiveConsole(locals=lcls).interact()

def charDicDeck(deck):
    con = sqlite3.connect(deck)
    cur = con.cursor()
    data = cur.execute('SELECT id, flds FROM notes').fetchall()
    json_val = []

    for (id, flds) in data:
        char = flds.split(sep)[0]
        json_val += [char]
    return json_val

def hash(data):
    return hashlib.sha1(str(data).encode()).hexdigest()

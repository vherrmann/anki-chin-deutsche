#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 /home/vherrmann/repos/-#python3With.gtts --command python

# made to add audio to https://ankiweb.net/shared/info/2485307055
# you first have to prepare the deck by adding a field to the cards, then export the deck from anki (in the old, compatible version)
# then you have to unzip it

import sqlite3
import json
import os
import os.path
from gtts import gTTS
import urllib.parse
import common as cm
import sys
import shutil

mediaFile = "media"
database = "collection.anki21"
media_dic = {}

cacheDir = sys.argv[1] + "/tts/"
cm.mkdirp(cacheDir)
locale = sys.argv[2]

def add_sound(i, flds):
    fldsList = flds.split(cm.sep)
    char = fldsList[0]
    charEnc = urllib.parse.quote(char, safe='')  # Encode just in case
    deck_file_name = f"./{i}"
    name = f"Chinesisch_für_Deutsche_Audio({charEnc}).mp3"
    cache_file_name = cacheDir + "/" + name

    if not os.path.isfile(cache_file_name) or cm.fileEmptyP(cache_file_name):
        tts = gTTS(char, slow=True, lang=locale)
        tts.save(cache_file_name)

    shutil.copy(cache_file_name, deck_file_name)

    media_dic[i] = name

    return cm.sep.join(cm.replaceFirst(fldsList, '', "[sound:" + name + "]"))


con = sqlite3.connect(database)
cur = con.cursor()
data = cur.execute('SELECT id, flds FROM notes').fetchall()
for (i, (id, flds)) in enumerate(data):
    print(i, id, flds)
    new_flds = add_sound(i, flds)
    print(i, id, new_flds)
    cur.execute("UPDATE notes SET flds=? WHERE id=?", (new_flds, id))

with open(mediaFile, encoding='UTF8', mode='w') as fp:
    json.dump(media_dic, fp)

print(media_dic)
con.commit()


# You could also use piper or coqui-ai:
# s = subprocess.run("nix run nixos#piper-tts -- --length_scale 1 --model Downloads/zh_CN-huayan-medium.onnx --config Downloads/zh_zh_CN_huayan_medium_zh_CN-huayan-medium.onnx.json --output_file /tmp/test.wav && mpv /tmp/test.wav", shell=True, input="媽媽", encoding="UTF8")

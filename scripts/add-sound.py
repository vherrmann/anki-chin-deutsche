#!/usr/bin/env -S nix shell --override-input nixpkgs nixos /home/vherrmann/repos/-#python3With.gtts --command python

# made to add audio to https://ankiweb.net/shared/info/2485307055
# you first have to prepare the deck by adding a field to the cards, then export the deck from anki (in the old, compatible version)
# then you have to unzip it

import sqlite3
import itertools
import json
import os
import os.path
from gtts import gTTS
import urllib.parse
import common as cm


mediaFile = "media"
database = "collection.anki21"
media_dic = {}


def add_sound(i, flds):
    fldsList = flds.split(cm.sep)
    char = fldsList[0]
    charEnc = urllib.parse.quote(char, safe='')  # Encode just in case
    media_file_name = str(i)
    name = f"Chinesisch_für_Deutsche_Audio({charEnc})"

    if not os.path.isfile(media_file_name):
        tts = gTTS(char, slow=True, lang='zh-TW')
        tts.save(media_file_name)

    media_dic[i] = name

    return cm.sep.join(cm.replaceFirst(fldsList, '', "[sound:" + name + "]"))


con = sqlite3.connect(database)
cur = con.cursor()
data = cur.execute('SELECT id, flds FROM notes').fetchall()
for (i, (id, flds)) in zip(itertools.count(), data):
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

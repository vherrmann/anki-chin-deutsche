#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 --command python

import json
import common as cm
import tempfile
import urllib.request
import shutil
from pathlib import Path
import glob
import itertools
import os

mediaIndex = 0
mediaJson = {}
charsJson = []

with open("media", encoding='UTF8', mode='r') as fp:
    mediaJson = json.load(fp)

mediaIndex = max(map(int, mediaJson.keys())) + 1
with tempfile.TemporaryDirectory() as tmpdir:
    tmpAr = tmpdir + "/data.zip"
    urllib.request.urlretrieve("https://github.com/chanind/hanzi-writer-data/archive/refs/tags/v2.0.1.zip" ,
                               tmpAr)

    unpackDir = tmpdir + "/data/"
    Path(unpackDir).mkdir(parents=True)
    shutil.unpack_archive(tmpAr, extract_dir=unpackDir, format="zip")
    dataDir = unpackDir + "hanzi-writer-data-2.0.1/data/"
    Path.unlink(dataDir + "all.json") # We don't want all.json in collection.media
    for filename in glob.iglob(f'{dataDir}/*'): # iterate over files
        shutil.move(filename, f"./{mediaIndex}")
        mediaJson[mediaIndex] = "_hanzi_writer_" + os.path.basename(filename)
        charsJson.append(Path(filename).stem)
        mediaIndex += 1

with open(str(mediaIndex), encoding="UTF8", mode="w") as fp:
    json.dump(charsJson, fp)
mediaJson[mediaIndex] = "_hanzi_writer_list.json"

with open("media", encoding="UTF8", mode="w") as fp:
    json.dump(mediaJson, fp)

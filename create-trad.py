#!/usr/bin/env -S nix shell nixos#python3 --command python
# Works with rev f1010e0469db743d14519a1efd37e23f8513d714 of nixpkgs

import pathlib
from contextlib import chdir
import shutil
import os
import importlib
import scripts.common as cm

scriptDir = os.path.dirname(__file__)

deckPath = scriptDir + "/data/Chinesisch_für_Deutsche_1+2.apkg"

class DeckWriter(object):
    def __init__(self, proccStepName, path):
        self.path = path
        self.proccStepName = proccStepName
        self.workDir = scriptDir + "/cache/steps/" + proccStepName

    def __enter__(self):
        pathlib.Path(self.workDir).mkdir(parents=True, exist_ok=True)

        self.workdirCM = chdir(self.workDir)
        self.workdirCM.__enter__()
        shutil.unpack_archive(self.path, format="zip")

        return self.workDir

    def __exit__(self, *args):
        shutil.make_archive(self.workDir, "zip")
        self.workdirCM.__exit__()


with DeckWriter("update_mod_date", deckPath) as wDir:
    print("section: update_mod_date")
    cm.runScript("update_mod_date.py")
    deckPath = wDir + ".zip"

with DeckWriter("to-trad", deckPath) as wDir:
    print("section: to-trad")
    cm.runScript("convert-short-to-long.py")
    deckPath = wDir + ".zip"

with DeckWriter("add-sound", deckPath) as wDir:
    print("section: add-sound")
    cm.runScript("add-sound.py")
    deckPath = wDir + ".zip"

with DeckWriter("add-sentences", deckPath) as wDir:
    print("section: add-sentences")
    cm.runScript("create-example-sentences.py")
    deckPath = wDir + ".zip"

#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 --command python

import pathlib
from contextlib import chdir
import shutil
import os
import scripts.common as cm

scriptDir = os.path.dirname(__file__)

class DeckWriter(object):
    def __init__(self, proccStepName, path, name):
        self.path = path
        self.proccStepName = proccStepName
        self.workDir = (scriptDir
                        + f"/cache/{name}/steps/"
                        + proccStepName)

    def __enter__(self):
        pathlib.Path(self.workDir).mkdir(parents=True, exist_ok=True)

        self.workdirCM = chdir(self.workDir)
        self.workdirCM.__enter__()
        shutil.unpack_archive(self.path, format="zip")

        return self.workDir

    def __exit__(self, *args):
        shutil.make_archive(self.workDir, "zip")
        self.workdirCM.__exit__()

def createDeck(config):
    deckPath = scriptDir + "/data/Chinesisch_für_Deutsche_1+2.apkg"

    cacheDir = scriptDir + f"/cache/{config['name']}"

    # Remove stepsdir for better reproducibility
    shutil.rmtree(cacheDir + "/steps", ignore_errors=True)

    with DeckWriter("update_mod_date", deckPath, config["name"]) as wDir:
        print("section: update_mod_date")
        cm.runScript("update_mod_date.py")
        deckPath = wDir + ".zip"

    if 'openccConfigFile' in config.keys():
        with DeckWriter("to-trad", deckPath, config["name"]) as wDir:
            print("section: to-trad")
            cm.runScript("convert-short-to-long.py", [cacheDir, config["openccConfigFile"]])
            deckPath = wDir + ".zip"

    with DeckWriter("add-sound", deckPath, config["name"]) as wDir:
        print("section: add-sound")
        cm.runScript("add-sound.py", [cacheDir, config["locale"]])
        deckPath = wDir + ".zip"

    # FIXME: Depending on tradp, instruct chatgpt to make the sentences more taiwanese or mainlandish
    with DeckWriter("add-sentences", deckPath, config["name"]) as wDir:
        print("section: add-sentences")
        cm.runScript("create-example-sentences.py",
                     [cacheDir])
        deckPath = wDir + ".zip"

    with DeckWriter("add-hanzi-writer-data", deckPath, config["name"]) as wDir:
        print("section: add-hanzi-writer-data")
        cm.runScript("add-hanzi-writer-data.py", [cacheDir])
        deckPath = wDir + ".zip"

    with DeckWriter("replace-col", deckPath, config["name"]) as wDir:
        print("section: replace-col")
        cm.runScript("replace-col.py")
        deckPath = wDir + ".zip"

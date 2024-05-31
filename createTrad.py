#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 --command python

from createDeck import createDeck

createDeck({ "name": "taiwan", "locale": "zh-TW", "openccConfigFile": "s2tw.json" })

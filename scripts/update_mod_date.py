#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 --command python

import sqlite3
import time


database = "collection.anki21"
con = sqlite3.connect(database)
cur = con.cursor()
data = cur.execute('SELECT id FROM notes').fetchall()
mod_date = int(time.time())
for (id,) in data:
    cur.execute("UPDATE notes SET mod=? WHERE id=?", (mod_date, id))

con.commit()

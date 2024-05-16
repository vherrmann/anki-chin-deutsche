#!/usr/bin/env -S nix shell nixos#python3 --command python

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

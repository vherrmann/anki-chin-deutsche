#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 nixpkgs#python3 --command python

import sqlite3
import sys
import common as cm
import time
import itertools


database = "collection.anki21"

trad = sys.argv[1] == "taiwan"


def updateNote(con, nid, modFn):
    flds = cur.execute("SELECT flds FROM notes WHERE id = ?;", (nid,)).fetchone()[0]

    try:
        new_flds = modFn(flds)
        if new_flds:
            cur.execute("UPDATE notes SET flds = ? where id=?;", (new_flds, nid))
        else:
            raise Exception("Empty new_flds")
    except Exception as e:
        print(f"Error while updating note {nid}: {e}")


def addNote(con, tags, hanzi, pinyin, translation):
    flds = (hanzi, pinyin, translation, "", "", "", "")
    id_gen = itertools.count(int(time.time() * 1000))

    sfld = flds[0]
    id = next(id_gen)
    guid = cm.guid_for(flds)
    mid = 1342696037256  # model id
    mod = 0
    usn = -1
    csum = 0
    flags = 0
    data = ""
    cur.execute(
        "INSERT INTO notes VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (id, guid, mid, mod, usn, tags, cm.sep.join(flds), sfld, csum, flags, data),
    )
    nid = id
    for ord in range(0, 3):
        id = next(id_gen)
        did = 1718204731542
        mod = 0
        usn = -1
        type = 0
        queue = 0
        due = 0
        ivl = 0
        factor = 0
        reps = 0
        lapses = 0
        left = 0
        odue = 0
        odid = 0
        flags = 0
        data = "{}"
        cur.execute(
            "INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);",
            (
                id,
                nid,
                did,
                ord,
                mod,
                usn,
                type,
                queue,
                due,
                ivl,
                factor,
                reps,
                lapses,
                left,
                odue,
                odid,
                flags,
                data,
            ),
        )


with sqlite3.connect(database) as con:
    cur = con.cursor()

    updateNote(con, 1253233319640, lambda x: x.replace("zuòtiān", "zuótiān"))

    if trad:
        updateNote(con, 1252888453500, lambda x: x.replace("chuānghu", "chuānghù"))
    con.commit()

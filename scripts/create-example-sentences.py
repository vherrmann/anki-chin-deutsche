#!/usr/bin/env -S nix shell --override-input nixpkgs github:NixOS/nixpkgs/f1010e0469db743d14519a1efd37e23f8513d714 /home/vherrmann/repos/-#python312With.openai.pypinyin --command python

# first use extract json from deck by using extract-json.py

from openai import OpenAI
import json
import itertools as it
import common as cm
import os
import sqlite3
import urllib.parse
import sys
import re
import subprocess

client = OpenAI()

charactersData = cm.charDicDeck("collection.anki21")

cacheDir = sys.argv[1] + "/create-example-sentences/"
cm.mkdirp(cacheDir)

latestmsg = ""
def askGPT(msg):
    global latestmsg
    latestmsg = msg
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a skilled chinese teacher, who only responds in machine-readable json without unnecessary characters like line breaks or whitespace."},
            {"role": "user", "content": msg
       }
        ]
    )

def askGPTDeutsch(msg):
    global latestmsg
    latestmsg = msg
    return client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "Du bist ein exzellenter Chinesischlehrer."},
            {"role": "user", "content": msg
       }
        ]
    )

tokens = 0
def getCompletion(charactersToUse, extraMessage):
    msg = f"""Please create very short example sentences for each of the words/prases in {chunk}.
            Please use 。for the end of the sentences.
            Please use exactly the given hanzi in your sentences (In particular, pay attention to numerals).
            Please give the sentences some originality.
            {extraMessage}
            Please return the data in machine-readable json without line breaks and whitespace. The json should have the given words/prases as key and the example sentences as value.
            The example sentence should only use the following hanzi (If there are no fitting hanzi among them, use very simple ones.):
            {charactersToUse}"""
            # Please return the data in compact json without any line breaks and whitespace using the hanzi as key with the sentences.\n
            # Your entire response is going to consist of a single JSON object, and you will NOT wrap it within JSON md markers\n
    completion = askGPT(msg)

    res = completion.choices[0].message.content
    print(f"Chunk: {chunk}")
    print(f"Used data: {charactersToUse}")
    print(f"Res: {res}")
    print(f"Used tokens: {completion.usage.total_tokens}")
    global tokens; tokens += completion.usage.total_tokens
    print(f"Used tokens total: {tokens}")
    print(f"Est. total cost: {tokens/1000000*50}ct")

    return res


class BadResponse(Exception):
    pass


chunkSize = 10
sentences = {}
def checkCompletionRes(resDic, chunk):
    if list(resDic.keys()) != list(chunk):
        raise BadResponse("The keys of the returned json don't fit the requested words.")
    def checkKey(k):
        kWOParens = re.sub("（.*）", "", k)
        return re.search(kWOParens.replace("…", ".*"), resDic[k])

    # theoretically we could use
    #   not all(map(lambda k: k in resDic[k], resDic.keys()))
    # but some characters are of the form "報（紙）". Due to good reason chatgpt doesn't include
    # this exact sequence in the sentence. We also have characters with /.
    # We also have characters with … as a wildcard.
    if not all(map(checkKey, resDic.keys())):
        badKeys = list(filter(lambda k: not (checkKey(k)), resDic.keys()))
        raise BadResponse(f"The example sentence for \"{badKeys}\" doesn't mention the corresponding word!")

### create example sentences
for (i, chunk) in enumerate(it.batched(charactersData, chunkSize)):
    print(f"Progress: {i}")
    hashedChunk = cm.hash(chunk)
    chunkCacheFile = cacheDir + f"chunk_{hashedChunk}.json"
    if os.path.isfile(chunkCacheFile) and not cm.fileEmptyP(chunkCacheFile):
        with open(chunkCacheFile) as fp:
            resDic = json.load(fp)
    else:
        charactersToUse = charactersData[0:(i+1)*chunkSize]

        while True:
            try:
                try:
                    res = getCompletion(charactersToUse, "")
                    resDic = json.loads(res)
                    checkCompletionRes(resDic, chunk)

                except json.decoder.JSONDecodeError:
                    print("BadJSON, trying again")
                    res = getCompletion(charactersToUse, "The last time I asked you for this, your response was malformmed json. Please be more careful this time.")
                    resDic = json.loads(res)
                    checkCompletionRes(resDic, chunk)
                except BadResponse as e:
                    print(f"BadResponse, trying again. Error: {e}")
                    res = getCompletion(charactersToUse, f"The last time I asked you for this, I got the error '{e.args[0]}'. Please be more careful this time.")
                    resDic = json.loads(res)
                    checkCompletionRes(resDic, chunk)
            except (json.decoder.JSONDecodeError, BadResponse) as e:
                print(f"Error: {e}")
                # if cm.yesno("Ask for gpt motives?"):
                #     msg = f"""I requested „{latestmsg}“.

                #               You responded with „{res}“.

                #               This response created the error „{e}“

                #               Please explain the motives behind your response.
                #             """
                #     completion = askGPT(msg)
                #     res = completion.choices[0].message.content
                #     print(latestmsg)
                #     print(res)
                #     break
                if not cm.yesno("Continue?"):
                    raise e
                if cm.yesno("Try Again?"):
                    continue
                else:
                    break
            break


        listedCharactersUsage = sum(list(map((lambda y: list(map((lambda x: x in "".join(charactersToUse)),
                                                                    list(y.replace("。", ""))))),
                                                resDic.values())),
                                    [])

        print(f"Quality: {len(list(filter((lambda x: x), listedCharactersUsage)))/len(listedCharactersUsage)}")
        with open(chunkCacheFile, mode='w') as fp:
            json.dump(resDic, fp)
    sentences.update(resDic)

# Get pinyin for all sentences

pinyin_of_sentences = {}

# FIXME: This translates 這隻貓很可愛 to zhè zhī māo hěn kě ài 。,
# instead of zhè zhī māo hěn kě'ài 。.
for (i, (char, sentence)) in enumerate(sentences.items()):
    hashedChunk = cm.hash(sentence)
    pinyinCacheFile = cacheDir + f"/pinyin_{hashedChunk}.json"
    if os.path.isfile(pinyinCacheFile) and not cm.fileEmptyP(pinyinCacheFile):
        with open(pinyinCacheFile, mode='r') as fp:
            pinyin = fp.read()
    else:
        subprocess.run(f"pypinyin > {pinyinCacheFile}", input=sentence, text=True, shell=True)
        with open(pinyinCacheFile) as fp:
            pinyin = fp.read()

    print(f"Index: {i}")
    print(f"Char: {char}")
    print(f"Original: {sentence}")
    print(f"Pinyin: {pinyin}")
    pinyin_of_sentences[char] = pinyin


sentenceFile = cacheDir + "sentences.json"
with open(sentenceFile, encoding='UTF8', mode='w') as fp:
    json.dump(sentences, fp)

### Translate sentences

translated_sentences = {}

for (i, (char, sentence)) in enumerate(sentences.items()):
    charEnc = urllib.parse.quote(char, safe='')  # Encode just in case
    cacheFile = cacheDir + "/translation_" + charEnc + ".json"
    if (not os.path.isfile(cacheFile)) or cm.fileEmptyP(cacheFile):
        # cache translating sentences
        completion = askGPTDeutsch(f"""Bitte übersetze den Satz "{sentence}" ins Deutsche.
                                Antworte bitte nur mit der Übersetzung ohne weitere Erläuterungen oder Kommentare zur Aufgabe.
                                Verwende insbesondere keine Anführungszeichen oder andere unnötige Zeichen.
                                Deine Antwort sollte kein JSON-Objekt sein.
                                Danke!""")
        translation = completion.choices[0].message.content

        tokens += completion.usage.total_tokens
        print(f"Used tokens total: {tokens}")
        print(f"Est. total cost: {tokens/1000000*50}ct")

        with open(cacheFile, encoding='UTF8', mode='w') as fp:
            json.dump(translation, fp)
    else:
        with open(cacheFile, encoding='UTF8', mode='r') as fp:
            translation = json.load(fp)

    print(f"Index: {i}")
    print(f"Char: {char}")
    print(f"Original: {sentence}")
    print(f"Translation: {translation}")
    translated_sentences[char] = translation

### Publish to database

database = "collection.anki21"

con = sqlite3.connect(database)
cur = con.cursor()
data = cur.execute('SELECT id, flds FROM notes').fetchall()
for (i, (id, flds)) in enumerate(data):
    fldsList = flds.split(cm.sep)
    char = fldsList[0]
    sentence = sentences[char]
    translation = translated_sentences[char]
    pinyin = pinyin_of_sentences[char]
    fldsWithSentence = cm.replaceFirst(fldsList, '', sentence)
    fldsWithTranslation = cm.replaceFirst(fldsWithSentence, '', translation)
    new_flds = cm.sep.join(cm.replaceFirst(fldsWithTranslation, '', pinyin))
    cur.execute("UPDATE notes SET flds=? WHERE id=?", (new_flds, id))

con.commit()

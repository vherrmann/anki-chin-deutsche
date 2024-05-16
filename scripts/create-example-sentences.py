#!/usr/bin/env -S nix shell --override-input nixpkgs latest /home/vherrmann/repos/-#python312With.openai --command python

# first use extract json from deck by using extract-json.py

from openai import OpenAI
import json
import itertools as it
import common as cm
import os
import sqlite3
import itertools
import urllib.parse

cm.runScript("extract-json.py")

client = OpenAI()

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


charactersFile = "characters.json"
charactersData = []
with open(charactersFile) as fp:
    charactersData = json.load(fp)

chunkSize = 10
sentences = {}
def checkCompletionRes(resDic, chunk):
    if list(resDic.keys()) != list(chunk):
        raise BadResponse("The keys of the returned json don't fit the requested words.")
    # outdated:
    # theoretically we could use
    #   not all(map(lambda k: k in resDic[k], resDic.keys()))
    # but some characters are of the form "報（紙）". Due to good reason chatgpt doesn't include
    # this exact sequence in the sentence. We also have characters with /.
    # We also have characters with … as a wildcard.
    # We further have following problematic characters:
    # 嗎
    # not all(map(lambda k: k in resDic[k],
                   # filter((lambda k: not ("（" in k or "/" in k or "…" in k)),
                   #        resDic.keys()))):
    if not all(map(lambda k: k in resDic[k], resDic.keys())):
        badKeys = list(filter(lambda k: not (k in resDic[k]), resDic.keys()))
        raise BadResponse(f"The example sentence for \"{badKeys}\" doesn't mention the corresponding word!")


### create example sentences
for (i, chunk) in zip(it.count(), it.batched(charactersData, chunkSize)):
    print(f"Progress: {i}")
    chunkCacheFile = f"chunk{i}.json"
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

with open("sentences.json", encoding='UTF8', mode='w') as fp:
    json.dump(sentences, fp)

### Translate sentences

translated_sentences = {}
translated_sentencesFile = "translated_sentences.json"

for (i, (char, sentence)) in zip(itertools.count(), sentences.items()):
    charEnc = urllib.parse.quote(char, safe='')  # Encode just in case
    cacheFile = charEnc + ".json"
    if (not os.path.isfile(cacheFile)) or cm.fileEmptyP(cacheFile):
        # cache translating sentences
        completion = askGPT(f"""Please translate the sentence "{sentence}" into German.
                                Please return the translation without elaboration or further comments on the task.
                                In particular, don't wrap the sentence into a json object. Return just a string without adding quotes.""")
        res = completion.choices[0].message.content

        tokens += completion.usage.total_tokens
        print(f"Used tokens total: {tokens}")
        print(f"Est. total cost: {tokens/1000000*50}ct")

        translation = res

        with open(cacheFile, encoding='UTF8', mode='w') as fp:
            json.dump(res, fp)
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
for (i, (id, flds)) in zip(itertools.count(), data):
    fldsList = flds.split(cm.sep)
    char = fldsList[0]
    sentence = sentences[char]
    translation = translated_sentences[char]
    new_flds = cm.sep.join(cm.replaceFirst(cm.replaceFirst(fldsList,
                                                           '',
                                                           sentence),
                                      '',
                                      translation))
    cur.execute("UPDATE notes SET flds=? WHERE id=?", (new_flds, id))

con.commit()

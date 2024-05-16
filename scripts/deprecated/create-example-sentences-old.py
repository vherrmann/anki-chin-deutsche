#!/usr/bin/env -S nix shell --override-input nixpkgs latest /home/vherrmann/repos/-#python3With.openai --command python

# first use extract json from deck by using extract-json.py

from openai import OpenAI
import json

client = OpenAI()

charactersFile = "/home/vherrmann/tmp/anki/Chinesisch_für_Deutsche_traditional_12/characters.json"
charactersData = ""

with open(charactersFile) as fp:
    charactersData = fp.read()

# completion = client.chat.completions.create(
#   model="gpt-3.5-turbo",
#   messages=[
#     {"role": "system", "content": "You are a skilled chinese teacher."},
#     {"role": "user", "content": """Please use the following json data to create example sentences for each word.\n
#                                    The example sentence should idealy use words that appear in the data earlier.\n
#                                    Please return the data in json using the hanzi as key with the sentences.\n"""
#                                    + charactersData
#      }
#   ]
# )

# print(completion.choices[0].message)

# with open("/tmp/testchat", encoding='UTF8', mode='w') as fp:
#     json.dump(completion.choices[0].message, fp)

# Create a vector store caled "Financial Statements"
vector_store = client.beta.vector_stores.create(name="Character json")

# Ready the files for upload to OpenAI
file_paths = [charactersFile]
file_streams = [open(path, "rb") for path in file_paths]

# Use the upload and poll SDK helper to upload the files, add them to the vector store,
# and poll the status of the file batch for completion.
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)

# You can print the status and the file counts of the batch to see the result of this operation.
print(file_batch.status)
print(file_batch.file_counts)

assistant = client.beta.assistants.create(
  name="Chinese teacher",
  instructions="You are a skilled chinese teacher.",
  model="gpt-3.5-turbo",
  tools=[{"type": "file_search"}],
)

assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

thread = client.beta.threads.create()

message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content= """Please use the json data from characters.json to create example sentences for each word.\n
           The example sentence should idealy use words that appear in the data earlier.\n
           Please return the data in json using the hanzi as key with the sentences.\n"""
)

run = client.beta.threads.runs.create_and_poll(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="You are a skilled chinese teacher."
)

if run.status == 'completed':
  messages = client.beta.threads.messages.list(
    thread_id=thread.id
  )
  print(messages)
else:
  print(run.status)

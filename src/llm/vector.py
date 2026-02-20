import os
import json
from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ----------------------------------------------
#  Setup for Retrieval of Transcripts
# ----------------------------------------------

path_to_transcripts = Path(__file__).parent.parent.parent / 'data' / 'transcripts'

transcripts_files = [pos_transcript for pos_transcript in os.listdir(path_to_transcripts) if pos_transcript.endswith('.json')]

# ----------------------------------------------
#  Setup for Embeddings and VectorDB
# ----------------------------------------------

# fast (low parameter) embedding model from Ollama
embeddings = OllamaEmbeddings(model = "all-minilm")

# the instantiation of the vector store and db location
db_location = "./chroma_langchain_db"

vector_store = Chroma(
    collection_name = "transcripts",
    persist_directory = db_location,
    embedding_function = embeddings
)

# ----------------------------------------------
#  Get Logging
# ----------------------------------------------

# create a log path to save files that have been embedded already
embedded_log_path = Path("./embedded_files.json")
already_embedded = set()

# load teh alread_embedded set with the information from the log file
if embedded_log_path.exists():
    try:
        already_embedded = set(json.loads(embedded_log_path.read_text()))
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: count not read embedded log, starting fresh: {e}")

# ----------------------------------------------
#  Get New Files/Documents and Parse and Embed
# ----------------------------------------------

# check for new files
new_files = [file for file in transcripts_files if file not in already_embedded]

if not new_files:
    print("No new transcript files to embed.")
else:
    print(f"Embedding {len(new_files)} new transcript file(s)...")

    # initialize the new documents and their ids to add
    documents, ids = [], []

    # go through each file in new files
    for js in new_files:
        filepath = os.path.join(path_to_transcripts, js)

        # get chunks from filepath
        try:
            with open(filepath, 'r') as file:
                chunks = json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Skipping {js} - could not read file: {e}")
            continue

        # check that there exists at least one chunk and that there is a chunk list
        if not isinstance(chunks, list) or len(chunks) == 0:
            print(f"Skipping {js} - empty or malformed content.")
            continue

        # parse the channel_id and video_index from filename for metadata
        # expected format: {channel_id}_transcript_{video_index}.json

        # ----------------------------------------------------
        #  NOTE ***: Additional metadata will be provided soon
        # ----------------------------------------------------

        # replace nonmetadata info with pipe |, then split around it
        parts = js.replace("_transcript_", "|").replace(".json", "").split("|")

        channel_id = parts[0] if len(parts) == 2 else "unkown"
        video_index = parts[1] if len(parts) == 2 else "unkown"

        # then iterate through the pandas dataframe made from the trnascript file
        for i, chunk in enumerate(chunks):
            # guard against malformed chunks, missing fields
            text = chunk.get('text', '').strip()

            # don't bother adding empty text to documents
            if not text:
                continue

            doc = Document(
                # the content to be embedded for the vector db
                page_content = text,

                # the metadata
                metadata = {
                    "start": chunk.get("start", 0.0),
                    "duration": chunk.get("duration", 0.0),
                    "channel_id": channel_id,
                    "video_index": video_index,

                    # -----------------------
                    #  Additional metadata...
                    # -----------------------

                    "source_file": js
                },

                # id for transcript chunk
                id = f"{js}_{i}"
            )
            # add to ids and documents
            ids.append(f"{js}_{i}")
            documents.append(doc)

    # if chunks were found and written to documents
    if documents:
        # then add the documents and ids to vector db
        vector_store.add_documents(documents=documents, ids=ids)

        # add the files to already embedded set and then save to log file
        already_embedded.update(new_files)

        try:
            embedded_log_path.write_text(json.dumps(list(already_embedded)))
        except IOError as e:
            print(f"Warning: could not update embedded log: {e}")
    else:
        print("No valid chunks found in new files")

# -----------------------------------------
#  K chunk retrieval for RAG
# -----------------------------------------

retriever = vector_store.as_retriever(
    # How many docs to look up
    search_kwargs = {"k": 5}
)


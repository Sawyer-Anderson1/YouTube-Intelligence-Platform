import os
import json
from pathlib import Path

from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ----------------------------------------------
#  Setup for Embeddings and VectorDB
# ----------------------------------------------

# embedding model from Ollama
embeddings = OllamaEmbeddings(model = "mxbai-embed-large")

# the instantiation of the vector store and db location
db_location = Path(__file__).parent.parent.parent / "chroma_langchain_db"

vector_store = Chroma(
    collection_name = "transcripts",
    persist_directory = str(db_location),
    embedding_function = embeddings
)

# -----------------------------------------
#  K chunk retrieval for RAG
# -----------------------------------------

retriever = vector_store.as_retriever(
    search_type="mmr", # favors diversity over purely similarity
    # How many docs to look up
    search_kwargs = {
        "k": 15, # the number of chunks to return
        "fetch_k": 300, # the candidate pool to select from
        "lambda_mult": 0.3 # 0 = max diversity, 1 = max similarity
    }
)

# -----------------------------------------
#  Embed Transcripts
# -----------------------------------------

def embed_transcripts():
    # ----------------------------------------------
    #  Setup for Retrieval of Transcripts
    # ----------------------------------------------

    path_to_transcripts = Path(__file__).parent.parent.parent / 'data' / 'transcripts'

    transcripts_files = [pos_transcript for pos_transcript in os.listdir(path_to_transcripts) if pos_transcript.endswith('.json')]

    # ----------------------------------------------
    #  Get Logging
    # ----------------------------------------------

    # create a log path to save files that have been embedded already
    embedded_log_path = Path(__file__).parent.parent.parent / 'data' / "embedded_files.json"
    already_embedded = set()

    # load the already_embedded set with the information from the log file
    if embedded_log_path.exists():
        try:
            already_embedded = set(json.loads(embedded_log_path.read_text()))
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: count not read embedded log, starting fresh: {e}")

    # ----------------------------------------------
    #  Get New Files/Documents and Parse and Embed
    # ----------------------------------------------

    new_files = []
    for file in transcripts_files:
        filepath = os.path.join(path_to_transcripts, file)

        # get chunks from filepath
        try:
            with open(filepath, 'r') as file:
                chunks = json.load(file)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Skipping {file} - could not read file: {e}")
            continue

        # get video id
        video_metrics = chunks[-1]
        video_id = video_metrics['video_id']

        # check if this video has already been embedded
        if video_id not in already_embedded:
            new_files.append(os.path.basename(filepath))

    print(new_files)
    if not new_files:
        print("No new transcript files to embed.")
    else:
        print(f"Embedding {len(new_files)} new transcript file(s)...")

        total_chunks_embedded = 0

        # go through each file in new files
        for file_num, js in enumerate(new_files):
            print(f"[{file_num + 1}/{len(new_files)}] Embedding {js}...", flush=True)

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

            # --------------------------
            #  Get Metadata
            # --------------------------

            # parse the channel_id and video_index from filename for metadata
            # expected format: {channel_id}_transcript_{video_index}.json
            # replace nonmetadata info with pipe |, then split around it
            parts = js.replace("_transcript_", "|").replace(".json", "").split("|")

            channel_id = parts[0] if len(parts) == 2 else "unknown"
            video_index = parts[1] if len(parts) == 2 else "unknown"

            # video metrics are in a dictionary at the end of the list of transcripts
            video_metrics = chunks[-1]
            title = video_metrics['title']
            video_id = video_metrics['video_id']
            published_at = video_metrics['published_at']
            view_count = video_metrics['view_count']
            like_count = video_metrics["like_count"]
            comment_count = video_metrics["comment_count"]
            total_duration = video_metrics["duration"]

            file_docs = []
            file_ids = []
            # then iterate through the pandas dataframe made from the trnascript file
            for i, chunk in enumerate(chunks):
                # ignore final chunk (i.e. the metadata dictionary from video metrics)
                if i == len(chunks) - 1:
                    continue

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
                        "video_id": video_id,
                        "video_index": video_index,
                        "title": title,
                        "published_at": published_at,
                        "view_count": view_count,
                        "like_count": like_count,
                        "comment_count": comment_count,
                        "total_duration": total_duration,
                        "source_file": js
                    },

                    # id for transcript chunk
                    id = f"{js}_{i}"
                )
                file_ids.append(f"{js}_{i}")
                file_docs.append(doc)

            # ----------------------------------------
            #  Embed and Save Video Ids into Log File
            # ----------------------------------------

            if not file_docs:
                print(f"No valid chunks found in {js}, skipping.", flush=True)
                continue

            try:
                print(f" Built {len(file_docs)} docs, starting embed...", flush=True)
                # embed this file's chunks immediatley - do not batch across files
                vector_store.add_documents(documents=file_docs, ids=file_ids)
                print(f"Add documents returned", flush=True)

                # update sidecar log
                already_embedded.add(video_id)

                # if this is the first run and the embedded_log_path doesn't exist yet, then it is created here
                embedded_log_path.write_text(json.dumps(list(already_embedded)))

                total_chunks_embedded += len(file_docs)
                print(f"Embedded {len(file_docs)} chunks", flush=True)

            except Exception as e:
                print(f" Failed to embed {js}: {e}", flush=True)
                continue

if __name__ == '__main__':
    embed_transcripts()

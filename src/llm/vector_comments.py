import os
import json
import time
from pathlib import Path

from langchain_cohere import CohereEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# ----------------------------------------------
#  Setup for Embeddings and VectorDB
# ----------------------------------------------

# embedding model from HuggingFace 
# changed from a local embedding model through Ollama to Cohere cloud API through HuggingFace
COHERE_BATCH_SIZE = 96
embeddings = CohereEmbeddings(
        model = "embed-english-v3.0",
        cohere_api_key = os.getenv("COHERE_API_KEY")
    )

# the instantiation of the vector store and db location
db_location = Path(__file__).parent.parent.parent / "chroma_langchain_db"

vector_store = Chroma(
    collection_name = "comments",
    persist_directory = str(db_location),
    embedding_function = embeddings
)

# -----------------------------------------
#  K chunk retrieval for RAG
# -----------------------------------------

def retrieval(query, k_chunks = 15):
    if k_chunks > 300:
        k_chunks = 300

    retrieved = vector_store.as_retriever(
        search_type="mmr", # favors diversity over purely similarity
        # How many docs to look up
        search_kwargs = {
            "k": k_chunks, # the number of chunks to return
            "fetch_k": 300, # the candidate pool to select from
            "lambda_mult": 0.3 # 0 = max diversity, 1 = max similarity
        }
    ).invoke(query)

    return retrieved

# -----------------------------------------
#  Embed comments
# -----------------------------------------

def embed_comments():
    # ----------------------------------------------
    #  Setup for Retrieval of Comments
    # ----------------------------------------------

    path_to_comments = Path(__file__).parent.parent.parent / 'data' / 'comments'

    comments_files = [pos_comment for pos_comment in os.listdir(path_to_comments) if pos_comment.endswith('.json')]

    # ----------------------------------------------
    #  Get Logging
    # ----------------------------------------------

    # create a log path to save files that have been embedded already
    embedded_log_path = Path(__file__).parent.parent.parent / 'data' / "embedded_comments.json"
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
    for file in comments_files:
        filepath = os.path.join(path_to_comments, file)

        # check if this file has already been embedded
        if file not in already_embedded:
            new_files.append(file)

    if not new_files:
        print("No new comment files to embed.")
    else:
        print(f"Embedding {len(new_files)} new comment file(s)...")

        all_docs = []
        all_ids = []

        # go through each file in new files
        for file_num, js in enumerate(new_files, start=1):
            print(f"[{file_num + 1}/{len(new_files)}] Embedding {js}...", flush=True)

            filepath = os.path.join(path_to_comments, js)

            # get chunks from filepath
            try:
                with open(filepath, 'r') as file:
                    chunks = json.load(file)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Skipping {js} - could not read file: {e}")
                continue

            # check that there exists at least one comment and that there is a comment list
            if not isinstance(chunks, list) or len(chunks) == 0:
                print(f"Skipping {js} - empty or malformed content.")
                continue

            # --------------------------
            #  Get Metadata
            # --------------------------

            # parse the video_id from filename for metadata
            # expected format: {video_id}_comments.json
            video_id = js.replace("_comments.json", "")

            # then iterate through the chunks
            for i, chunk in enumerate(chunks):
                # guard against malformed comments, missing fields
                comment = chunk.get('text', '').strip()

                # don't bother adding empty text to documents
                if not comment:
                    continue

                doc = Document(
                    # the content to be embedded for the vector db
                    page_content = comment,

                    # the metadata
                    metadata = {
                        "video_id": video_id,
                        "commentId": chunk.get("commentId", "unknown"),
                        "author": chunk.get("author", "unknown"),
                        "likes": chunk.get("likes", 0),
                        "published_at": chunk.get("published_at", ""),
                        "source_file": js
                    },

                    # id for comment chunk
                    id = f"{js}_{i}"
                )
                all_ids.append(f"{js}_{i}")
                all_docs.append(doc)

        try:
            print(f" Built {len(all_docs)} docs, starting embed...", flush=True)
            # embed this file's chunks immediatley - do not batch across files

            # -----------------------
            #  Batch Documents
            # -----------------------

            for i in range(0, len(all_docs), COHERE_BATCH_SIZE):
                batch_docs = all_docs[i: i + COHERE_BATCH_SIZE]
                batch_ids = all_ids[i: i + COHERE_BATCH_SIZE]
                vector_store.add_documents(documents=batch_docs, ids=batch_ids)
                print(f"Batch: {i // COHERE_BATCH_SIZE + 1}: Embedded: {len(batch_docs)}", flush=True)

                MIN_SECONDS_PER_CALL = 0.8

                num_batches = max(1, len(all_docs) // 96 + 1)
                sleep_time = num_batches * MIN_SECONDS_PER_CALL
                time.sleep(sleep_time)

            # update sidecar log
            already_embedded.update(new_files)

            # if this is the first run and the embedded_log_path doesn't exist yet, then it is created here
            embedded_log_path.write_text(json.dumps(list(already_embedded)))

            print(f"All embedded {len(all_docs)} chunks", flush=True)

        except Exception as e:
            print(f" Failed to embed: {e}", flush=True)

if __name__ == '__main__':
    embed_comments()

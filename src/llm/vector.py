from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
import os
import pandas as pd

path_to_transcripts = "transcripts/"
transcripts_files = [pos_transcript for pos_transcript in os.listdir(path_to_transcripts) if pos_transcript.endswith('.json')]

dfs = []
for index, js in enumerate(transcripts_files):
    dfs.append(pd.read_json(os.path.join(path_to_transcripts, js)))
df = pd.concat(dfs, ignore_index=True)

embeddings = OllamaEmbeddings(model = "mxbai-embed-large")

# Need to delete chroma_langchain_db folder if you want to add documents and update vector db with new documents. 
# Otherwise it will just load the existing vector db without adding new documents.
db_location = "./chroma_langchain_db"
add_documents = not os.path.exists(db_location)

if add_documents:
    documents = []
    ids = []
    # Go row by row through file and create indivual documents then add to vector db
    for i, row in df.iterrows():
        document = Document(
            # page_content is what will be vectorized and looked up and used for query
            # Specific for files.json
            page_content = row["text"],

            # metadata is data grabbed along with the document but not used for query
            # Specific for files.json
            metadata = {
                "start": row["start"],
                "duration": row["duration"],

            },

            id = str(i)
        )
        ids.append(str(i))
        documents.append(document)

vector_store = Chroma(
    collection_name = "transcripts",
    persist_directory = db_location,
    embedding_function = embeddings
)

if add_documents:
    vector_store.add_documents(documents = documents, ids = ids)

retriever = vector_store.as_retriever(
    # How many docs to look up
    search_kwargs = {"k": 5}
)


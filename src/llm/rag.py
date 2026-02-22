# imports:
import os
from datetime import datetime, timezone

# import Ollama and Langchain (prompting)
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# import MongoDB
from pymongo import MongoClient

# import retriever from vector.py
from vector import retriever

# ----------------------------------
#  MongoDB Setup
# ----------------------------------

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['youtube_intelligence']
results_collection = db['results']

# ----------------------------------
#  Ollama LLM setup
# ----------------------------------

model = OllamaLLM(model = "llama3.2")

template = """
You are an expert in finding claims, trends, narratives, and risk factors in the AI field from transcripts from YouTube videos.
Here are some relevant transcripts from those videos: {transcripts}
Here is a question from the user: {question}
"""

prompt = ChatPromptTemplate.from_template(template)
chain = prompt | model

# ----------------------------------
#  Standard Weekly Queries
# ----------------------------------

# Weelky scheduled prompts - add to main.py scheduled_job_sequence()
SCHEDULED_QUERIES = {
    "claims": "What specific claims are being made about AI?",
    "trends": "What trneds are emerging in AI discussions?",
    "narratives": "What dominant narratives exist around AI right now?",
    "risk_factors": "What risks or concerns about AI are being raised?",
}

# -----------------------------------
#  Core Query Function
# -----------------------------------

# args:
#       - Takes question, which is static for SCHEDULED_QUERIES, but dynamic in testing or if users query themselves
#       - Takes query type, given in SCEDULED_QUERIES, but stated in user query (testing)
def run_query(question, query_type):
    # get relevant transcript chunks from ChromaDB
    transcript_chunks = retriever.invoke(question)

    # build context string from retrieved chunks
    transcripts = "\n\n".join([chunk.page_content for chunk in transcript_chunks])

    # invoke the LLM chain
    result = chain.invoke({"transcripts": transcripts, "question": question})

    # Build source chunk references from metadas
    source_chunks = [
        {
            'channel_id': chunk.metadata.get('channel_id', 'unknown'),
            'video_index': chunk.metadata.get('video_index', 'unkown'),
            'start': chunk.metadata.get('start', 0.0),
            'duration': chunk.metadata.get('duration', 0.0),
            'source_file': chunk.metadata.get('source_file', 'unkown')
        }
        for chunk in transcript_chunks
    ]

    #  Insert the result into MongoDB
    # format schema to MongoDB
    document = {
            'run_data': datetime.now(timezone.utc),
            'query_type': query_type,
            'question': question,
            'result_text': result,
            'source_chunks': source_chunks,
            'model': 'llama3.2',
            'retrieval_k': len(transcript_chunks)
    }

    # then insert new result
    insert_result = results_collection.insert_one(document)

    return {
        'id': str(insert_result.inserted_id()),
        'query_type': query_type,
        'result_text': result,
        'source_chunks': source_chunks
    }

# ----------------------------------
#  Weekly Scheduled Queries
# ----------------------------------

def run_scheduled_queries():
    # get the query type and query for each of the weekly queries
    for query_type, question in SCHEDULED_QUERIES.items():
        try:
            # run query through LLM (using RAG)
            result = run_query(query_type, question)

            # print results
            print(f"{query_type} query stored with id: {result['id']}")
        except Exception as e:
            print(f"Error with running query of type:{query_type} and question: {question}: {e}")

    print("Scheduled Queries Run")

# main function for testing
if __name__ == '__main__':
    print("RAG interactive mode (local testing)")
    while True:
        print("\n\n-----------------------------")
        question = input("Ask your question (q to quit): ")
        print("\n\n")
        if question.lower() == "q":
            break

        # get the query type (specified by user/tester)
        query_type = input("Query type (claims/trends/narratives/risk factors)")

        # then run query
        try:
            result = run_query(query_type, question)

            print(f"{query_type} query stored with id: {result['id']}")
            print(f"\nResults: {result['result_text']}")
            print(f"\nSources: {len(result['source_chunks'])} chunks retrieved")
        except Exception as e:
            print(f"Error with running query of type:{query_type} and question: {question}: {e}")

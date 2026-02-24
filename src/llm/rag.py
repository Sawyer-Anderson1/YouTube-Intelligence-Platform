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

# --------------------------------
#  Templates for each Query type
# --------------------------------

TEMPLATES = {
    # --------------
    #  Claim Prompt
    # --------------

    'claims': """
You are an expert in finding claims in the AI field from transcripts from YouTube transcripts.

Here are some relevant transcript chunks: 
{transcripts}

Question: {question}

Extract distinct claims actually present in the transcripts above. Do not invent claims not supported by the text.

### Output Format
Return the response as a valid JSON object:
{{
    "Claim Title": "Direct description of the claim as made in the transcripts",
    "Another Claim Title": "Description..."
}}
""",

    # --------------
    #  Trend Prompt
    # --------------

    'trends': """
You are an expert in finding emerging trends in AI discussions from YouTube transcripts.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Identify trends that are clearly present across multiple transcript chunks.

Return a valid JSON object:
{{
    "Trend title": "Description of the trend and evidence from the transcripts",
    "Another trend": "Description..."
}}
""",

    # -----------------
    #  Narrative Prompt
    # -----------------

    'narratives': """
You are an expert in finding dominant narratives around AI in YouTube video transcripts.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

A narrative is a recurring framing or story being told about AI. Identify narratives present in the transcripts.

Return a valid JSON object:
{{
    "Narrative title": "Description of the narrative and how it appears in the transcripts",
    "Another narrative": "Description..."
}}
""",

    # --------------------
    #  Risk Factor Prompt
    # --------------------

    'risk_factors': """
You are an expert in finding risks and concerns about AI raised in YouTube video transcripts.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Identify specific risks or concerns explicitly raised in the transcripts.

Return a valid JSON object:
{{
    "Risk title": "Description of the risk as discussed in the transcripts",
    "Another risk": "Description..."
}}
"""
}

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

MAX_CONTEXT_CHARS = 6000

# args:
#       - Takes question, which is static for SCHEDULED_QUERIES, but dynamic in testing or if users query themselves
#       - Takes query type, given in SCEDULED_QUERIES, but stated in user query (testing)
def run_query(query_type, question):
    # get the template from the TEMPLATES dictionary and then create the prompt model chain
    template = TEMPLATES.get(query_type, TEMPLATES['claims'])
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model

    # get relevant transcript chunks from ChromaDB
    transcript_chunks = retriever.invoke(question)

    # build context string from retrieved chunks
    transcripts = "\n\n".join([chunk.page_content for chunk in transcript_chunks])
    # transcripts = transcripts[:MAX_CONTEXT_CHARS]

    # invoke the LLM chain
    result = chain.invoke({"transcripts": transcripts, "question": question})

    # Build source chunk references from metadatas
    source_chunks = [
        {
            'channel_id': chunk.metadata.get('channel_id', 'unknown'),
            'video_index': chunk.metadata.get('video_index', 'unkown'),
            'start': chunk.metadata.get('start', 0.0),
            'duration': chunk.metadata.get('duration', 0.0),
            "title": chunk.metadata.get('title', ''),
            "published_at": chunk.metadata.get('published_at', 0.0),
            "view_count": chunk.metadata.get('view_count', 0),
            "like_count": chunk.metadata.get('like_count', 0),
            "comment_count": chunk.metadata.get('comment_coun', 0),
            "total_duration": chunk.metadata.get('total_duration', ''),
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
        'id': str(insert_result.inserted_id),
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
        query_type = input("Query type (claims/trends/narratives/risk_factors): ")

        # then run query
        try:
            result = run_query(query_type, question)

            print(f"{query_type} query stored with id: {result['id']}")
            print(f"\nResults: {result['result_text']}")
            print(f"\nSources: {len(result['source_chunks'])} chunks retrieved")
        except Exception as e:
            print(f"Error with running query of type:{query_type} and question: {question}: {e}")

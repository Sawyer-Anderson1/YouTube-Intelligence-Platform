# imports:
import os
import json
import re
from datetime import datetime, timezone
from pathlib import Path

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

claims_file = json.load(open(Path(__file__).parent.parent.parent / "example_output" / "claims.json", "r"))[0]
narratives_file = json.load(open(Path(__file__).parent.parent.parent / "example_output" / "narratives.json", "r"))[0]
trends_file = json.load(open(Path(__file__).parent.parent.parent / "example_output" / "trends.json", "r"))[0]
risk_factors_file = json.load(open(Path(__file__).parent.parent.parent / "example_output" / "risk_factors.json", "r"))[0]

TEMPLATES = {
    # --------------
    #  Claim Prompt
    # --------------

    'claims': """
You are an expert in finding claims in the AI field from transcripts from YouTube transcripts.
A claim is a specific factual or opinion statement made in a video transcript. Claims are granular, concrete, and often verifiable.

Here are some relevant transcript chunks: 
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Claims:
{claims_examples}

Extract distinct claims actually present in the transcripts above. Do not invent claims not stated in the text.

### RULES:
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Use this exact structure where each key is the claim title and each value is the description:

### Output Format
{{"Claim title here": "Description of the claim here", "Another claim title": "Description here"}}
""",

    # --------------
    #  Trend Prompt
    # --------------

    'trends': """
You are an expert in finding emerging trends in AI discussions from YouTube transcripts.
Trends are the temporal pattern of activity around a narrative — how discussion grows, peaks, or declines over time.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Trends:
{trends_examples}

Identify trends (i.e. shared claims) that are clearly present across multiple transcript chunks.

### RULES:
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Use this exact structure where each key is the trend title and each value is the description:

### Output Format
{{"Trend title here": "Description of the trend here", "Another trend title": "Description here"}}
""",

    # -----------------
    #  Narrative Prompt
    # -----------------

    'narratives': """
You are an expert in finding dominant narratives around AI in YouTube video transcripts.
A narrative is a high-level story, theme, or topic that connects multiple claims across videos. Narratives summarize the semantic meaning of clustered claims.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Narratives:
{narratives_examples}

### RULES:
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Use this exact structure where each key is the narrative title and each value is the description:

### Output Format
{{"Narrative title here": "Description of the narrative here", "Another narrative title": "Description here"}}
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

### RULES:
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Use this exact structure where each key is the risk factor title and each value is the description:

### Output Format
{{"Risk factor title here": "Description of the risk factor here", "Another risk factor title": "Description here"}}
"""
}

# ----------------------------------
#  Standard Weekly Queries
# ----------------------------------

# Weelky scheduled prompts - add to main.py scheduled_job_sequence()
SCHEDULED_QUERIES = {
    "claims": "What specific claims are being made about AI?",
    "trends": "What trends are emerging in AI discussions?",
    "narratives": "What dominant narratives exist around AI right now?",
    "risk_factors": "What risks or concerns about AI are being raised?",
}

# -----------------------------------
#  Function to Extract JSON
# -----------------------------------

def extract_json_from_response(text: str, query_type: str) -> dict:
    # strip any trailing text after } (or ] in the case where its a list)
    last_brace = max(text.rfind('}'), text.rfind(']'))
    if last_brace != -1: # the case where ther is trailing text
        text = text[:last_brace + 1]

    # direct parse
    try:
        parsed = json.loads(text)

        # if an array is returned (not the dict), then convert to dict
        if isinstance(parsed, list):
            return {
                    item.get(f'{query_type[:-1]} Title') or item.get(f'{query_type[:-1]} title') or item.get('title') or f"{query_type[:-1]} {i+1}": 
                    item.get('Description') or item.get('description') or item.get('text') or str(item)
                    for i, item in enumerate(parsed)
                    if isinstance(item, dict)
            }
        return parsed
    except json.JSONDecodeError:
        pass

    # if we get codeblocks
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
    if code_block:
        try:
            parsed = json.loads(code_block.group(1))
            if isinstance(parsed, list):
                return {
                    item.get(f'{query_type[:-1]} Title') or item.get(f'{query_type[:-1]} title') or item.get('title') or f"{query_type[:-1]} {i+1}": 
                    item.get('Description') or item.get('description') or item.get('text') or str(item)
                    for i, item in enumerate(parsed)
                    if isinstance(item, dict)                }
            return parsed
        except json.JSONDecodeError:
            pass

    # then try finding a JSON object
    json_obj = re.search(r'\{[\s\S]*\}', text)
    if json_obj:
        try:
            return json.loads(json_obj.group())
        except json.JSONDecodeError:
            pass

    # try finding a JSON array
    json_arr = re.search(r'\[[\s\S]*\]', text)
    if json_arr:
        try:
            parsed = json.loads(json_arr.group())
            if isinstance(parsed, list):
                return {
                    item.get(f'{query_type[:-1]} Title') or item.get(f'{query_type[:-1]} title') or item.get('title') or f"{query_type[:-1]} {i+1}": 
                    item.get('Description') or item.get('description') or item.get('text') or str(item)
                    for i, item in enumerate(parsed)
                    if isinstance(item, dict)                }
            return parsed
        except json.JSONDecodeError:
            pass

    # last resort return raw text
    return {"raw_response": text}

# -----------------------------------
#  Core Query Function
# -----------------------------------

MAX_CONTEXT_CHARS = 3000

# args:
#       - Takes question, which is static for SCHEDULED_QUERIES, but dynamic in testing or if users query themselves
#       - Takes query type, given in SCEDULED_QUERIES, but stated in user query (testing)
def run_query(query_type, question):
    # get the template from the TEMPLATES dictionary and then create the prompt model chain
    template = TEMPLATES.get(query_type, TEMPLATES['claims'])
    prompt = ChatPromptTemplate.from_template(template)

    # inject the format instructions from the parser into the prompt
    chain = prompt | model

    # get relevant transcript chunks from ChromaDB
    transcript_chunks = retriever.invoke(question)

    # build context string from retrieved chunks
    transcripts = "\n\n".join([chunk.page_content for chunk in transcript_chunks])
    transcripts = transcripts[:MAX_CONTEXT_CHARS]

    if query_type == "claims":
        result = chain.invoke({"transcripts": transcripts, "question": question, "claims_examples": claims_file})
    elif query_type == "narratives":
        result = chain.invoke({"transcripts": transcripts, "question": question, "narratives_examples": narratives_file})
    elif query_type == "trends":
        result = chain.invoke({"transcripts": transcripts, "question": question, "trends_examples": trends_file})
    elif query_type == "risk_factors":
        result = chain.invoke({"transcripts": transcripts, "question": question, "risk_factors_examples": risk_factors_file})

    # put the result through a parser to extract the json from the resonse
    parsed_result = extract_json_from_response(result, query_type)

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
            'result_text': parsed_result,
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
    print(claims_file)
    print(narratives_file)
    print(risk_factors_file)

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

# imports:
import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone

# import Ollama and Langchain (prompting)
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate

# import MongoDB
from pymongo import MongoClient

# import retriever from vector.py
from .vector import retriever

# import AI terms from constants file
from ..constants import AI_TERMS

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

model = OllamaLLM(
        model = "llama3.1:8b",
        num_predict = 1200, # max tokens that can be generated
        temperature = 0.3, # lower temperature makes the response faster and more focused
    )

#----------------------------------
#  Load Example Output Files for Few-Shot Prompting
#----------------------------------

try:
    claims_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "claims.json", "r"))
    narratives_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "narratives.json", "r"))
    trends_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "trends.json", "r"))
    risk_factors_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "risk_factors.json", "r"))
except Exception as e:
    print(f"Error loading example output files: {e}")
    claims_file = "Error loading claims examples"
    narratives_file = "Error loading narratives examples"
    trends_file = "Error loading trends examples"
    risk_factors_file = "Error loading risk factors examples"

# --------------------------------
#  Templates for each Query type
# --------------------------------

TEMPLATES = {
    # --------------
    #  Claim Prompt
    # --------------

    'claims': """
You are an expert in finding claims in the AI field from transcripts from YouTube transcripts.

Each transcript chunk below includes some metadata, such as title, publish date, engagement metrics, and content.
Use the publish date to note whether claims are recent or older.
Use view and like counts as a signal of how widely a claim is being circulated.

Here are some relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Claims:
{claims_examples}

### RULES:
- Extract distinct claims actually present in the transcripts above. Do not invent claims not stated in the text.
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Aim for 5-8 findings maximum — do not generate more entries than you can complete
- Always close the JSON object with }} before stopping
- Use this exact structure where each KEY is the claim TITLE and each VALUE is the DESCRIPTION or QUOTE.

### Output Format
{{"Claim title here": "quote of the claim here", "Another claim title": "quote here"}}

Do not reference speaker in description/quote.
""",

    # --------------
    #  Trend Prompt
    # --------------

    'trends': """
You are an expert in finding emerging trends in AI discussions from YouTube transcripts.

Each transcript chunk below includes some metadata, such as title, publish date, engagement metrics, and content.
Use the publish date to identify trends, and note whether trends are recent or older.
Use view and like counts as a signal of how widely a trend is being circulated.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the trends.
### Examples of Trends:
{trends_examples}

### RULES:
- Identify trends (i.e. shared claims) that are clearly present across multiple transcript chunks.
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Aim for 5-8 findings maximum — do not generate more entries than you can complete
- Always close the JSON object with }} before stopping
- Use this exact structure where each KEY is the trend TITLE and each VALUE is the DESCRIPTION of trend.

### Output Format
{{"Trend title here": "Description of the trend here", "Another trend title": "Description here"}}

Do not reference speaker in description.
""",

    # -----------------
    #  Narrative Prompt
    # -----------------

    'narratives': """
You are an expert in finding dominant narratives around AI in YouTube video transcripts.

Each transcript chunk below includes some metadata, such as title, publish date, engagement metrics, and content.
Use the publish date to identify, and note whether narratives are recent or older.
Use view and like counts as a signal of how widely a narrative is being circulated.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the narratives.
### Examples of Narratives:
{narratives_examples}

### RULES:
- A narrative is a recurring framing or story being told about AI. Identify narratives present in the transcripts.
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Aim for 5-8 findings maximum — do not generate more entries than you can complete
- Always close the JSON object with }} before stopping
- Use this exact structure where each KEY is the narrative TITLE and each VALUE is the DESCRIPTION of narrative.

### Output Format
{{"Narrative title here": "Description of the narrative here", "Another narrative title": "Description here"}}

Do not reference speaker in description.
""",

    # --------------------
    #  Risk Factor Prompt
    # --------------------

    'risk_factors': """
You are an expert in finding risks and concerns about AI raised in YouTube video transcripts.

Each transcript chunk below includes some metadata, such as title, publish date, engagement metrics, and content.
Use the publish date to identify, and note whether risk factors are recent or older.
Use view and like counts as a signal of how widely a risk factor is being circulated.

Here are relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the risks.
### Examples of Risk Factors:
{risks_examples}

### RULES:
- Identify specific risks or concerns explicitly raised in the transcripts.
- Respond with ONLY a JSON object, nothing else
- No markdown, no code blocks, no backticks
- No introduction, no explanation, no notes after the JSON
- Aim for 5-8 findings maximum — do not generate more entries than you can complete
- Always close the JSON object with }} before stopping
- Use this exact structure where each KEY is the risk factor TITLE and each VALUE is the DESCRIPTION of risk factor.

### Output Format
{{"Risk factor title here": "Description of the risk factor here", "Another risk factor title": "Description here"}}

Do not reference speaker in description.
"""
}

# ----------------------------------
#  Query Enrichment &
#  Standard Weekly Queries
# ----------------------------------

BASE_TERMS = ' '.join(AI_TERMS)

QUERY_ENRICHMENT = {
    'claims': f'claims assertions arguments statements positions {BASE_TERMS}',
    'trends': f'trends patterns emerging developments growing {BASE_TERMS}',
    'narratives': f'narrative framing story perspective discourse {BASE_TERMS}',
    'risk_factors': f'risk concerns dangers threats warnings safety {BASE_TERMS}'
}

# Weelky scheduled prompts - add to main.py scheduled_job_sequence()
SCHEDULED_QUERIES = {
    "claims": "What specific claims are being made about AI?",
    "trends": "What trends are emerging in AI discussions?",
    "narratives": "What dominant narratives exist around AI right now?",
    "risk_factors": "What risks or concerns about AI are being raised?",
}

# -------------------------------------
#  Functions to Repair and Extract JSON
# -------------------------------------

def repair_json(text: str) -> str:
    """
    Attempt to fix common JSON truncation issues before parsing.
    """
    text = text.strip()

    # Count opening and closing braces
    open_braces   = text.count('{')
    close_braces  = text.count('}')
    open_brackets  = text.count('[')
    close_brackets = text.count(']')

    # If the last character is a comma (truncated mid-entry), remove it
    if text.endswith(','):
        text = text[:-1]

    # If the last character is an incomplete value, remove the last entry
    if not text.endswith(('}', ']', '"')):
        # Find the last complete key-value pair
        last_complete = max(text.rfind('",'), text.rfind('"}'))
        if last_complete != -1:
            text = text[:last_complete + 1]

    # Append missing closing braces/brackets
    text += '}' * (open_braces - close_braces)
    text += ']' * (open_brackets - close_brackets)

    return text

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

    # repair then parse
    try:
        repaired_text = repair_json(text)
        parsed = json.loads(repaired_text)

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

    repaired_text = repair_json(text)

    # if we get codeblocks
    code_block = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', repaired_text)
    if code_block:
        try:
            repaired = repair_json(code_block.group(1))
            parsed = json.loads(repaired)
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
    json_obj = re.search(r'\{[\s\S]*\}', repaired_text)
    if json_obj:
        try:
            return json.loads(json_obj.group())
        except json.JSONDecodeError:
            pass

    # try finding a JSON array
    json_arr = re.search(r'\[[\s\S]*\]', repaired_text)
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
#  Function to Format the Trnascript
#  Chunks with Metadata
# -----------------------------------

MAX_CHARS_PER_CHUNK = 1500

def format_chunk_with_metadata(doc):
    m = doc.metadata
    content = doc.page_content[:MAX_CHARS_PER_CHUNK]
    return (
        f"Title: {m.get('title', 'unkown')}\n"
        f"Published At: {m.get('published_at', 0.0)}\n"
        f"View Count: {m.get('view_count', 0)}\n"
        f"Like Count: {m.get('like_count', 0)}\n"
        f"Comment Count: {m.get('comment_count', 0)}\n"
        f"Duration: {m.get('total_duration', 'Unkown')}\n"
        f"{content}"
    )

# -----------------------------------
#  Core Query Function
# -----------------------------------

# changed the limit from max chars to max chars per chunk, since using max_context_chars would only leave about one transcript chunk in the actual RAG
# MAX_CONTEXT_CHARS = 3000

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

    # -----------------------------------
    #  Use Enriched Query with Key Terms
    # -----------------------------------
    enriched_query = f"{question} {QUERY_ENRICHMENT.get(query_type, '')}"
    transcript_chunks = retriever.invoke(enriched_query)

    # build context string from retrieved chunks
    # added a delimiter since the model will need to distinguish between them now that theres metadata
    transcripts = "\n\n###\n\n".join([
        format_chunk_with_metadata(chunk) for chunk in transcript_chunks
    ])

    # --------------------------------------------
    #  Invoke based off query_type, for few-shot
    # --------------------------------------------

    match query_type:
        case 'claims':
            result = chain.invoke({"transcripts": transcripts, "question": question, 'claims_examples': claims_file})
        case 'trends':
            result = chain.invoke({"transcripts": transcripts, "question": question, 'trends_examples': trends_file})
        case 'narratives':
            result = chain.invoke({"transcripts": transcripts, "question": question, 'narratives_examples': narratives_file})
        case 'risk_factors':
           result = chain.invoke({"transcripts": transcripts, "question": question, 'risks_examples': risk_factors_file})
        case _:
            result = chain.invoke({"transcripts": transcripts, "question": question, 'claims_examples': claims_file})

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
            "comment_count": chunk.metadata.get('comment_count', 0),
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
            'model': 'llama3.1:8b',
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

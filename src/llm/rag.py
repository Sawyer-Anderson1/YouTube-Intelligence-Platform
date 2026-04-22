# imports:
import os
import json
import re
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, Dict, List

# import MongoDB
from pymongo import MongoClient

# import retriever from vector.py
from .vector import retrieval

# import AI terms from constants file
from ..constants import AI_TERMS

# import Groq  and Langchain (prompting)
from langchain_core.prompts import ChatPromptTemplate

# import groq
from langchain_groq import ChatGroq

# import Exa for fact-checking
from exa_py import Exa

# import requests and BeautifulSoup for webpage fetching
import requests
from bs4 import BeautifulSoup

# -------------------------
#  Import the Groq Api Key
# -------------------------

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_KEY_2 = os.getenv('GROQ_API_KEY_2')

# -------------------------
#  Initialize Exa for Fact Checking
# -------------------------

EXA_API_KEY = os.getenv('EXA_API_KEY')
exa_client = Exa(api_key=EXA_API_KEY) if EXA_API_KEY else None

# ---------------------------------
#  ChatGroq with Lamma Setup
# ---------------------------------

model = ChatGroq(
    model = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_tokens=1024,
    api_key = GROQ_API_KEY
)

factchecking_model = ChatGroq(
    model = "llama-3.3-70b-versatile",
    temperature = 0.7,
    max_tokens=1024,
    api_key = GROQ_API_KEY_2
)

# ----------------------------------
#  MongoDB Setup
# ----------------------------------

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['youtube_intelligence']
results_collection = db['results']

#----------------------------------
#  Load Example Output Files for Few-Shot Prompting
#----------------------------------

try:
    claims_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "claims.json", "r"))
    narratives_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "narratives.json", "r"))
    trends_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "trends.json", "r"))
    # risk_factors_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "risk_factors.json", "r"))
    comments_feedback_file = json.load(open(Path(__file__).parent.parent.parent / "data" / "example_output" / "comment_feedback.json", "r"))
except Exception as e:
    print(f"Error loading example output files: {e}")
    claims_file = "Error loading claims examples"
    narratives_file = "Error loading narratives examples"
    trends_file = "Error loading trends examples"
    # risk_factors_file = "Error loading risk factors examples"
    comments_feedback_file = "Error loading comment feedback examples"

# --------------------------------
#  Templates for each Query type
# --------------------------------

TEMPLATES = {
    # --------------
    #  Claim Prompt
    # --------------

    'claims': """
You are an expert in finding claims in the AI field from transcripts from YouTube transcripts.

Each transcript chunk below includes some metadata, such as title, video id, publish date, engagement metrics,and content.
Use the publish date to note whether claims are recent or older.
Use view and like counts as a signal of how widely a claim is being circulated.
Use comments to identify any additional claims

Here are some relevant transcript chunks:
{transcripts}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Claims:
{claims_examples}

### RULES:
- Extract distinct claims actually present in the transcripts above. DO NOT invent claims not stated in the text.
- Use EVERY video/transcript chunk to form you responses.
- Respond with ONLY a JSON object, nothing else.
- No markdown, no code blocks, no backticks.
- No introduction, no explanation, no notes after the JSON.
- Aim for 1 claim per transcript chunks minimum — do not generate more entries than you can complete.
- Always close the JSON object with }} before stopping.
- Use this exact structure where each KEY is the claim TITLE and each VALUE is the dictionary of DESCRIPTION or QUOTE, video_id, view_count, like_count, and comment_count.
- Following description or quote of the claim, provide the video id where the claim comes from.
- From the video id(s) provide the the video's view_count, like_count, comment_count.
- Do not have newlines or other tags in the response.

### Output Format
{{"Claim title here": {{"Quote": "quote of the claim here", "video_id": "video_id here", "view_count": "view_count here", "like_count": "like_count here", "comment_count": "comment_count here"}}, "Another claim title": {{"Quote": "quote here", "video_id": "video_id here", "view_count": "view_count here", "like_count": "like_count here", "comment_count": "comment_count here"}}}}

Do not reference speaker in description/quote.
""",

    # --------------
    #  Trend Prompt
    # --------------

    'trends': """
You are an expert in finding emerging trends in AI discussions from YouTube transcripts.

Each transcript chunk below includes some metadata, such as title, video id, publish date, engagement metrics, and content.
Use the publish date to identify trends, and note whether trends are recent or older.
Use view and like counts as a signal of how widely a trend is being circulated.

Here are relevant transcript chunks:
{transcripts}

Here are claims:
{claims}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the trends.
### Examples of Trends:
{trends_examples}

### RULES:
- Identify trends (i.e. shared claims) that are clearly present across multiple transcript chunks.
- Use EVERY video/transcript chunk to form your responses.
- Respond with ONLY a JSON object, nothing else.
- No markdown, no code blocks, no backticks.
- No introduction, no explanation, no notes after the JSON.
- Aim for 5-8 findings maximum — do not generate more entries than you can complete.
- Always close the JSON object with }} before stopping.
- Use this exact structure where each KEY is the trend TITLE and each VALUE is the dictionary of DESCRIPTION, video_ids, total view_count, total like_count, and total comment_count.
- Following description or quote of the trend, provide the video id(s) where the trend comes from.
- From the video id(s) provide all the video's total view_count, total like_count, total comment_count.
- Do not have newlines or other tags in the response.

### Output Format
{{"Trend title here": {{"Description: "description of trend here", "video_ids": ["video_id here", "another video_id"], "total_view_count": "total view_count here", "total_like_count": "total like_count here", "total_comment_count": "total comment_count here"}}, "Another trend title": {{"Description: "description here", "video_ids": ["video_id here", "another video_id"], "total_view_count": "total view_count here", "total_like_count": "total like_count here", "total_comment_count": "total comment_count here"}}}}

Do not reference speaker in description.
""",

    # -----------------
    #  Narrative Prompt
    # -----------------

    'narratives': """
You are an expert in finding dominant narratives around AI in YouTube video transcripts.

Each transcript chunk below includes some metadata, such as title, video id, publish date, engagement metrics, and content.
Use the publish date to identify, and note whether narratives are recent or older.
Use view and like counts as a signal of how widely a narrative is being circulated.

Here are relevant transcript chunks:
{transcripts}

Here are claims:
{claims}

Here are trends:
{trends}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the narratives.
### Examples of Narratives:
{narratives_examples}

### RULES:
- A narrative is a recurring framing or story being told about AI. Identify narratives present in the transcripts.
- Use EVERY video/transcript chunk to form your responses.
- Respond with ONLY a JSON object, nothing else.
- No markdown, no code blocks, no backticks.
- No introduction, no explanation, no notes after the JSON.
- Aim for 5-8 findings maximum — do not generate more entries than you can complete.
- Always close the JSON object with }} before stopping
- Use this exact structure where each KEY is the narrative TITLE and each VALUE is the dictionary of DESCRIPTION, video_ids, total view_count, total like_count, and total comment_count.
- Following description or quote of the narrative, provide the video id(s) where the narrative comes from.
- From the video id(s) provide all the video's total view_count, total like_count, total comment_count.
- Do not have newlines or other tags in the response.

### Output Format
{{"Narrative title here": {{"Description: "description of narrative here", "video_ids": ["video_id here", "another video_id"], "total_view_count": "total view_count here", "total_like_count": "total like_count here", "total_comment_count": "total comment_count here"}}, "Another narrative title": {{"Description: "description here", "video_ids": ["video_id here", "another video_id"], "total_view_count": "total view_count here", "total_like_count": "total like_count here", "total_comment_count": "total comment_count here"}}}}

Do not reference speaker in description.
""",

    # --------------------
    #  Risk Factor Prompt
    # --------------------

    'risk_factors': """
You are an expert in finding risks and concerns about AI raised in YouTube video transcripts.

Each transcript chunk below includes some metadata, such as title, video id, publish date, engagement metrics, and content.
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
- Use EVERY video/transcrip chunk to form you responses.
- Respond with ONLY a JSON object, nothing else.
- No markdown, no code blocks, no backticks.
- No introduction, no explanation, no notes after the JSON.
- Aim for 5-8 findings maximum — do not generate more entries than you can complete.
- Always close the JSON object with }} before stopping.
- Use this exact structure where each KEY is the risk factor TITLE and each VALUE is the DESCRIPTION of risk factor.
- In description of the risk factors, provide the video id(s) where the risk factors comes from.
- From the video id(s) provide the the video's view_count, like_count, comment_count.
- Do not have newlines or other tags in the response.

### Output Format
{{"Risk factor title here": "Description of the risk factor here", "Another risk factor title": "Description here"}}

Do not reference speaker in description.
""",
    # -------------------------
    #  Comment Feedback Prompt
    # -------------------------

    'comments': """
You are an expert in discerning feedback from comments of a YouTube video.

Each comment below includes some metadata, such as comment id, author, publish date, likes, and comment content.
Use the publish date to note whether a comment is recent or older.
Use view as a signal of how widely a claim is being circulated.
Do sentiment analysis, with a classification score (positive, negative, neutral) and polarity score (-1.0 to 1.0)

Here are some comments to a video with id: {video_id}:
{comments}

Question: {question}

Use the examples below as a reference as to what the analysis should look like. But do not use these examples as part of your answer - they are only for reference to understand how to word the claims.
### Examples of Comment feedback:
{comments_examples}

### RULES:
- Extract distinct feedback actually present in the comments above. DO NOT invent comments and feedback not stated in the text.
- Use EVERY comment to form you responses.
- Respond with ONLY a JSON object, nothing else.
- No markdown, no code blocks, no backticks.
- No introduction, no explanation, no notes after the JSON.
- Always close the JSON object with }} before stopping.
- Use this exact structure where each KEY is the feedback TITLE and each VALUE is the dictionary of COMMENT or QUOTE, video_id, comment_id, and like_count.
- Following description or quote of the comment, provide the video idand comment id where the comment comes from.
- From the video id and comment id(s) provide the the video's like_count.
- Do not have newlines or other tags in the response.

### Output Format
{{"Comment feedback title here": {{"Quote": "quote from comment here", "sentiment_class": "the sentiment classification score here", "polarity_score": "the sentiment polarity score here", "video_id": "video_id here", "comment_id": "commentId here", "like_count": "like_count here"}}, "Another comment feedback title here": {{"Quote": "quote from comment here", "video_id": "video_id here", "comment_id": "comment_id here", "like_count": "like_count here"}}}}

Do not reference speaker in description/quote.
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
    "comments": "What feedback is given in comments of YouTube video?"
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
#  Load Comments by Video ID
# -----------------------------------

def load_comments(video_id: str) -> List[Dict]:
    """
    Load comments for a given video ID from the comments directory.
    Returns an empty list if file doesn't exist or can't be read.
    """
    comments_path = Path(__file__).parent.parent.parent / "data" / "comments" / f"{video_id}_comments.json"

    if not comments_path.exists():
        return []

    try:
        with open(comments_path, 'r', encoding='utf-8') as f:
            comments = json.load(f)
            return comments if isinstance(comments, list) else []
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not load comments for {video_id}: {e}")
        return []

def build_comments_dict(chunks: List) -> Dict[str, List[Dict]]:
    """
    Build a dictionary of {video_id: comments} for all unique video IDs in chunks.
    This avoids loading the same comments file multiple times.
    """
    comments_dict = {}
    unique_video_ids = set()

    # Extract unique video IDs from chunks
    for chunk in chunks:
        video_id = chunk.metadata.get('video_id')
        if video_id and video_id not in unique_video_ids:
            unique_video_ids.add(video_id)

    # Load comments for each unique video ID
    for video_id in unique_video_ids:
        comments_dict[video_id] = load_comments(video_id)

    return comments_dict

def format_comments(comments: List[Dict], max_comments: int = 5) -> str:
    """
    Format comments into a readable string for the LLM.
    Limits to top N comments by likes to keep token count manageable.
    Includes only comment text (no author or like count).
    """
    if not comments:
        return "No comments available."

    # Sort by likes descending and take top N
    sorted_comments = sorted(comments, key=lambda x: x.get('likes', 0), reverse=True)[:max_comments]

    formatted = "Comments:\n"
    for i, comment in enumerate(sorted_comments, 1):
        text = comment.get('text', '')
        formatted += f"{i}. {text}\n"

    return formatted

# -----------------------------------
#  Function to Format the Transcript
#  Chunks with Metadata
# -----------------------------------

# originally had max chars per chunk when using ollama locally, because it would take too long but now have a better model through a cloud api so don't need it
# MAX_CHARS_PER_CHUNK = 1500

def format_chunk_with_metadata(doc):
    m = doc.metadata
    content = doc.page_content
    video_id = m.get('video_id', 'unknown')

    return (
        f"[Title: {m.get('title', 'unknown')}]\n"
        f"[Video Id: {video_id}]\n"
        f"[Published At: {m.get('published_at', 'unknown')}]\n"
        f"[View Count: {m.get('view_count', 0):,}]\n"
        f"[Like Count: {m.get('like_count', 0):,}]\n"
        f"[Duration: {m.get('total_duration', 'unknown')}]\n"
        f"[Comment Count: {m.get('comment_count', 0):,}]\n"
        f"{content}\n\n"
    )

def format_comment_with_metadata(comment_data):
    return (
        f"[Comment Id: {comment_data['commentId']}]\n"
        f"[Author: {comment_data['author']}]\n"
        f"[Likes: {comment_data['likes']}]\n"
        f"[Published At: {comment_data['published_at']}]\n"
        f"{comment_data['text']}"
    )

# -----------------------------------
#  Calculate Chunk Budget
# -----------------------------------

# Approximate token budgets per query type
# Groq llama-3.3-70b TPM limit: 12,000
# reserve 400 tokens for prompt, 1024 for responses, 100 for few-shot examples

BASE_TOKEN_BUDGETS = {
    'claims': 9500,
    'prompt': 400,
    'response_limit': 1024,
    'few-shot': 100,
    'trends': 8000,
    'narratives': 6000
}

TOKENS_PER_CHUNK = 500

def get_max_chunks(query_type: str) -> int:
    # adujust the chunks per call based on how much claims or trends may fill the TPM (will not split the claims or trends response in their following queries)
    if query_type == 'claims':
        # for claims: 400 token prompt + 100 token few-shot + 1024 token max response => leaves about 10,476 tokens for chunks (use the 9500 in base_token_budgets)
        max_transcript_call_budget = BASE_TOKEN_BUDGETS.get('claims', 0) // TOKENS_PER_CHUNK

    elif query_type == 'trends':
        # for trends: 1024 (max) claims response + 400 token prompt + 100 token few-shot + 1024 (max) token response => leaves max of 9,452 tokens for chunks

        # return the maximum of 9000 for trends
        max_transcript_call_budget = BASE_TOKEN_BUDGETS.get('trends', 0) // TOKENS_PER_CHUNK

    elif query_type == 'narratives':
        # for narratives: 1024 (max) claims response + 1024 (max) trends response + 400 token prompt + 100 token few-shot + 1024 (max) token resposne => leaves max of 8,428 tokens for chunks

        # return the maximum of 8000 for narratives
        max_transcript_call_budget = BASE_TOKEN_BUDGETS.get('narratives', 0) // TOKENS_PER_CHUNK

    else:
        max_transcript_call_budget = BASE_TOKEN_BUDGETS.get('claims', 0)

    return max_transcript_call_budget

# -------------------------------------------------
#  Function to get Token Count (of Claims, Trends)
# -------------------------------------------------

def count_nested(d):
    count = 0
    for value in d.values():
        if isinstance(value, dict):
            count += count_nested(value)
        elif isinstance(value, list):
            count += count_nested(value)
        else:
            count += len(value.split())

    return count + len(d.split())

# -----------------------------------
#  Calculate Chunk Budget
# -----------------------------------

# Approximate token budgets per query type
# Groq llama-3.3-70b TPM limit: 12,000
# reserve 400 tokens for prompt, 1024 for responses, 100 for few-shot examples

BASE_TOKEN_BUDGETS = {
    'claims': 9500,
    'prompt': 400,
    'response_limit': 1024,
    'few-shot': 100,
    'trends': 8000,
    'narratives': 6000
}

TOKENS_PER_CHUNK = 500

# -----------------------------------
#  Take url and get text from the webpage
# -----------------------------------

def fetch_webpage_content(url: str, max_chars: int = 2000) -> str:
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)

        return text[:max_chars]

    except Exception as e:
        print(f"Error fetching webpage {url}: {e}")
        return ""

# -----------------------------------
#  Using LLM to fact check a claim against webpage content
# -----------------------------------

# Provides a verdict and confidence score on how much webpage content supports/refutes the claim
# LLM provides reasoning on why verdict is given

def llm_fact_check_verdict(claim: str, webpage_content: str) -> Dict:
    try:
        fact_check_prompt = ChatPromptTemplate.from_template("""
You are a fact-checking expert. Analyze the following claim against the provided webpage content.

CLAIM: {claim}

WEBPAGE CONTENT: {content}

Based on the webpage content, determine:
1. VERDICT: Does the content SUPPORT, REFUTE, or provide NO EVIDENCE for the claim? (pick one)
2. CONFIDENCE: Your confidence score from 0.0 (no confidence) to 1.0 (very confident)
3. REASONING: Brief explanation (1-2 sentences)

Respond in JSON format only:
{{"verdict": "SUPPORT|REFUTE|NO_EVIDENCE", "confidence": 0.0-1.0, "reasoning": "explanation"}}

Do not include any text outside the JSON object.
""")

        chain = fact_check_prompt | factchecking_model
        result = chain.invoke({
            "claim": claim,
            "content": webpage_content[:1500]  # Limit content to avoid token overflow
        })

        # Parse the JSON response
        try:
            parsed = json.loads(result.text)
            return {
                "verdict": parsed.get("verdict", "NO_EVIDENCE"),
                "confidence": float(parsed.get("confidence", 0.0)),
                "reasoning": parsed.get("reasoning", "")
            }
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r'\{.*\}', result.text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    "verdict": parsed.get("verdict", "NO_EVIDENCE"),
                    "confidence": float(parsed.get("confidence", 0.0)),
                    "reasoning": parsed.get("reasoning", "")
                }
            return {
                "verdict": "NO_EVIDENCE",
                "confidence": 0.0,
                "reasoning": "Could not parse LLM response"
            }

    except Exception as e:
        print(f"Error in LLM fact-checking: {e}")
        return {
            "verdict": "NO_EVIDENCE",
            "confidence": 0.0,
            "reasoning": f"Error analyzing content: {str(e)}"
        }

# -----------------------------------
#  Perform the fact checking process using functions above
# -----------------------------------

# Searches for sources surrounding the claim
# For each source, fetches webpage content and uses LLM to analyze whether it supports/refutes the claim

def fact_check_claims(claims_dict: Dict, query_type: str = 'claims') -> Dict:
    if not exa_client:
        print("Warning: Exa API key not configured, skipping fact-checking")
        return {}

    fact_check_results = {}

    try:
        for claim_title, claim_content in claims_dict.items():
            # Search for evidence supporting or refuting the claim
            try:
                search_query = claim_title
                search_results = exa_client.search(search_query, num_results=3, type='keyword')

                sources_list = []

                # Analyze each source
                for result in search_results.results:
                    # Skip YouTube links
                    if 'youtube.com' in result.url.lower() or 'youtu.be' in result.url.lower():
                        continue

                    source_data = {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.text[:300] if hasattr(result, 'text') else result.summary[:300] if hasattr(result, 'summary') else "No snippet available",
                        "published_date": getattr(result, 'published_date', 'Unknown')
                    }

                    # Fetch and analyze webpage content
                    webpage_content = fetch_webpage_content(result.url)

                    if webpage_content:
                        verdict_data = llm_fact_check_verdict(claim_title, webpage_content)
                        source_data["verdict"] = verdict_data["verdict"]
                        source_data["confidence"] = verdict_data["confidence"]
                        source_data["reasoning"] = verdict_data["reasoning"]
                    else:
                        source_data["verdict"] = "NO_EVIDENCE"
                        source_data["confidence"] = 0.0
                        source_data["reasoning"] = "Could not fetch webpage content"

                    sources_list.append(source_data)
                    time.sleep(0.5)  # Rate limiting

                # Calculate aggregate verdict and confidence
                verdicts = [s.get("verdict") for s in sources_list]
                confidences = [s.get("confidence", 0.0) for s in sources_list]

                # Aggregate verdict: if majority support, overall is SUPPORT, etc.
                support_count = verdicts.count("SUPPORT")
                refute_count = verdicts.count("REFUTE")
                partial_count = verdicts.count("PARTIAL")

                if support_count >= len(verdicts) / 2:
                    aggregate_verdict = "SUPPORT"
                elif refute_count >= len(verdicts) / 2:
                    aggregate_verdict = "REFUTE"
                elif partial_count > 0:
                    aggregate_verdict = "PARTIAL"
                else:
                    aggregate_verdict = "NO_EVIDENCE"

                # Average confidence
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

                
                # Weighted verdict calculation based on confidence scores
                support_weight = sum(s.get("confidence", 0.0) for s in sources_list if s.get("verdict") == "SUPPORT")
                refute_weight = sum(s.get("confidence", 0.0) for s in sources_list if s.get("verdict") == "REFUTE")
                no_evidence_weight = sum(s.get("confidence", 0.0) for s in sources_list if s.get("verdict") == "NO_EVIDENCE")
                
                # Determine aggregate verdict based on weighted scores
                verdict_weights = {
                    "SUPPORT": support_weight,
                    "REFUTE": refute_weight,
                    "NO_EVIDENCE": no_evidence_weight
                }
                
                # Pick verdict with highest weight, or NO_EVIDENCE if all weights are 0
                if max(verdict_weights.values()) > 0:
                    aggregate_verdict = max(verdict_weights, key=verdict_weights.get)
                else:
                    aggregate_verdict = "NO_EVIDENCE"
                
                fact_check_results[claim_title] = {
                    "original_claim": claim_title,
                    "evidence_found": len(sources_list) > 0,
                    "num_sources": len(sources_list),
                    "sources": sources_list,
                    "aggregate_verdict": aggregate_verdict
                }

                # Small delay to avoid rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"Error fact-checking claim '{claim_title}': {e}")
                fact_check_results[claim_title] = {
                    "error": str(e),
                    "original_claim": claim_title,
                }

    except Exception as e:
        print(f"Error in fact-checking process: {e}")
        return {"error": str(e)}

    return fact_check_results

# -----------------------------------
#  Core Query Function
# -----------------------------------

# changed the limit from max chars to max chars per chunk, since using max_context_chars would only leave about one transcript chunk in the actual RAG
# MAX_CONTEXT_CHARS = 3000

# args:
#       - Takes question, which is static for SCHEDULED_QUERIES, but dynamic in testing or if users query themselves
#       - Takes query type, given in SCEDULED_QUERIES, but stated in user query (testing)
#       - Takes K chunks to be retrieved, default value of 15
#       - Takes claims, optional dict with claims from claim query
#       - Takes trends, optional dict with trends from trend query
#       - Takes previously used transcript chunks, option list with transcripts chunks used in claims query for trends query then chunks used in claims and trends query for narratives query
#       - Takes include_comments, optional boolean to include comments from videos (default True)
def run_query(query_type, question, claims: Optional[Dict] = None, trends: Optional[Dict] = None, previous_chunks: Optional[List] = None, k_chunks = 15, include_comments: bool = True):
    # get the template from the TEMPLATES dictionary and then create the prompt model chain
    template = TEMPLATES.get(query_type, TEMPLATES['claims'])
    prompt = ChatPromptTemplate.from_template(template)

    # inject the format instructions from the parser into the prompt
    chain = prompt | model

    # -----------------------------------
    #  Use Enriched Query with Key Terms
    # -----------------------------------
    enriched_query = f"{question} {QUERY_ENRICHMENT.get(query_type, '')}"

    # calculate the token/chunk budget per call
    token_chunk_budget = get_max_chunks(query_type)

    # get relevant transcript chunks from ChromaDB
    transcript_chunks = retrieval(enriched_query, k_chunks)

    # Build comments dictionary (loads each file once)
    if previous_chunks != None:
        # keep previous chunks (to get comments of)
        total_chunks = previous_chunks + transcript_chunks
    else:
        total_chunks = transcript_chunks
    comments_dict = build_comments_dict(total_chunks) if include_comments else {}

    # create of list of the concatenated chunks to later be iterated through to call the llm
    concatenated_chunks = []

    # -----------------------------------
    #  If Previous Chunks Exist then Add
    # -----------------------------------

    if previous_chunks != None:
        chunk_counter = 1

        curr_chunks = []
        for chunk in previous_chunks:
            if chunk_counter <= token_chunk_budget:
                # build context string from retrieved chunks
                # added a delimiter since the model will need to distinguish between them now that theres metadata
                curr_chunks.append(format_chunk_with_metadata(chunk))
                chunk_counter += 1

            else:
                # add to the concatenated chunks list
                concatenated_chunks.append("\n\n###\n\n".join(curr_chunks))

                curr_chunks = [format_chunk_with_metadata(chunk)]
                chunk_counter = 1
    else:
        previous_chunks = []

    # ------------------------------------------------
    #  Add new chunks fetched, not in Previous Chunks
    # ------------------------------------------------

    # every 15 chunks we get a new create start with on a new concatenated string of chunks and metadata (so the request won't be blocked for exceeding the TPM of Groq's llama-3.3-70b-versatile model)
    chunk_counter = 1

    curr_chunks = []
    for chunk in transcript_chunks:
        if chunk not in previous_chunks:
            if chunk_counter <= token_chunk_budget:
                # build context string from retrieved chunks
                # added a delimiter since the model will need to distinguish between them now that theres metadata
                formatted_chunk = format_chunk_with_metadata(chunk)
                curr_chunks.append(formatted_chunk)

                chunk_counter += 1

            else:
                # add to the concatenated chunks list
                concatenated_chunks.append("\n\n###\n\n".join(curr_chunks))

                curr_chunks = [format_chunk_with_metadata(chunk)]
                chunk_counter = 1

            # add the current chunk to previous chunks to provide the source chunks in mongodb with the chunks and the next queries (trends and narratives after claims)
            previous_chunks.append(chunk)
    concatenated_chunks.append("\n\n###\n\n".join(curr_chunks))

    # --------------------------------------------
    #  Invoke based off query_type, for few-shot
    # --------------------------------------------

    # then for each concatenated transcripts in the list (maximum of 15 chunks + their metadata each) iterate and invoke the llm query
    # store results in this dictionary
    results = {}

    # -----------------------------------------------------------------------------
    #  Between each query we need to wait a minute,
    #  since there is a TPM (Tokens per Minute) limit/rate in Groq for this model
    # -----------------------------------------------------------------------------

    match query_type:
        case 'claims':
            for transcripts in concatenated_chunks:
                result = chain.invoke({"transcripts": transcripts, "question": question, 'claims_examples': claims_file})

                # put the result through a parser to extract the json from the resonse
                parsed_result = extract_json_from_response(result.text, query_type)

                results.update(parsed_result)

                # wait 60 seconds between queries to avoid the TPM
                time.sleep(60)

        case 'trends':
            for transcripts in concatenated_chunks:
                # Check if there are claims (from the prior scheduled queries) to provide context, with the transcripts from the claims query and additional transcripts
                if claims != None:
                    result = chain.invoke({"transcripts": transcripts, "claims": claims, "question": question, 'trends_examples': trends_file})

                    # put the result through a parser to extract the json from the resonse
                    parsed_result = extract_json_from_response(result.text, query_type)

                    results.update(parsed_result)

                else:
                    # else just run generic trends query
                    result = chain.invoke({"transcripts": transcripts, "claims": None, "question": question, 'trends_examples': trends_file})

                    # put the result through a parser to extract the json from the resonse
                    parsed_result = extract_json_from_response(result.text, query_type)

                    results.update(parsed_result)

                # wait 60 seconds between queries to avoid the TPM
                time.sleep(60)

        case 'narratives':
            for transcripts in concatenated_chunks:
                # Check if there are claims and trends (from the prior scheduled queries) to provide context, with the transcripts from the claims query, trends query, and additional transcripts
                if claims != None and trends != None:
                    result = chain.invoke({"transcripts": transcripts, "claims": claims, "trends": trends, "question": question, 'narratives_examples': narratives_file})

                    # put the result through a parser to extract the json from the resonse
                    parsed_result = extract_json_from_response(result.text, query_type)

                    results.update(parsed_result)

                else:
                    # else just run generic narratives query
                    result = chain.invoke({"transcripts": transcripts, "claims": None, "trends": None, "question": question, 'narratives_examples': narratives_file})

                    # put the result through a parser to extract the json from the resonse
                    parsed_result = extract_json_from_response(result.text, query_type)

                    results.update(parsed_result)

                # wait 60 seconds between queries to avoid the TPM
                time.sleep(60)

        case 'risk_factors':
            for transcripts in concatenated_chunks:
                result = chain.invoke({"transcripts": transcripts, "question": question, 'risks_examples': risk_factors_file})

                # put the result through a parser to extract the json from the resonse
                parsed_result = extract_json_from_response(result.text, query_type)

                results.update(parsed_result)

                # wait 60 seconds between queries to avoid the TPM
                time.sleep(60)

        case _:
            for transcripts in concatenated_chunks:
                result = chain.invoke({"transcripts": transcripts, "question": question, 'claims_examples': claims_file})

                parsed_result = extract_json_from_response(result.text, query_type)

                results.update(parsed_result)

                # wait 60 seconds between queries to avoid the TPM
                time.sleep(60)

    # Build source chunk references from metadatas
    source_chunks = []
    for chunk in previous_chunks:
        video_id = chunk.metadata.get('video_id', 'unknown')

        # get comments for chunk, based off video id
        if comments_dict and video_id in comments_dict:
            comments_section = comments_dict[video_id]
        else:
            comments_section = ["No comments available"]

        source_chunks.append({
            'channel_id': chunk.metadata.get('channel_id', 'unknown'),
            'video_id': chunk.metadata.get('video_id', 'unknown'),
            'video_index': chunk.metadata.get('video_index', 'unknown'),
            'start': chunk.metadata.get('start', 0.0),
            'duration': chunk.metadata.get('duration', 0.0),
            "title": chunk.metadata.get('title', ''),
            "published_at": chunk.metadata.get('published_at', 0.0),
            "view_count": chunk.metadata.get('view_count', 0),
            "like_count": chunk.metadata.get('like_count', 0),
            "comment_count": chunk.metadata.get('comment_count', 0),
            "comments": comments_section,
            "total_duration": chunk.metadata.get('total_duration', ''),
            "source_file": chunk.metadata.get('source_file', 'unknown'),
            "chunk_content": chunk.page_content
        })

    # Fact-check the results before storing
    fact_check_data = fact_check_claims(results, query_type)
    
    # Add fact_check to each individual claim/result
    results_with_factcheck = {}
    for claim_title, claim_content in results.items():
        if isinstance(claim_content, dict) and 'fact_check' not in claim_content:
            # If it's a dict without fact_check yet, add it
            results_with_factcheck[claim_title] = {
                **claim_content,
                'fact_check': fact_check_data.get(claim_title, {})
            }
        elif isinstance(claim_content, dict):
            # If it already has fact_check (from previous query), keep as is
            results_with_factcheck[claim_title] = claim_content
        else:
            # If it's a string or other type, wrap it
            results_with_factcheck[claim_title] = {
                'content': claim_content,
                'fact_check': fact_check_data.get(claim_title, {})
            }

    #  Insert the result into MongoDB
    # format schema to MongoDB

    document = {
            'run_date': datetime.now(timezone.utc),
            'query_type': query_type,
            'question': question,
            'result_text': results_with_factcheck,
            'source_chunks': source_chunks,
            'model': 'llama-3.3-70b-versatile',
            'retrieval_k': len(previous_chunks)
    }

    # then insert new result
    insert_result = results_collection.insert_one(document)

    # if the last of the queries for insights (so narratives), then return the comments dict as well
    if query_type == 'narratives':
        return {
            'id': str(insert_result.inserted_id),
            'query_type': query_type,
            'result_text': results_with_factcheck,
            'source_chunks': previous_chunks
        }, comments_dict

    return {
        'id': str(insert_result.inserted_id),
        'query_type': query_type,
        'result_text': results_with_factcheck,
        'source_chunks': previous_chunks
    }

# ----------------------------------
#  Retrieve Feedback from Comments
# ----------------------------------

# args:
#   - Takes the question/query from the SCHEDULED_QUERIES
#   - Takes the accumulated comment_dict from the previous calls (claims, trends, narratives)
#   - Has query_type comments
#   - Default value 10 for max_videos that we get feedback for (to manage the TPD and RPD
def comment_feedback(question, comment_dict, query_type = 'comments', max_videos = 10):
    # sort videos by total comment likes, and only process up to max_videos
    sorted_vids = sorted(
        [vid for vid in comment_dict if comment_dict[vid]], # filters out the empty comment lists!
        key = lambda vid: sum(c.get('likes', 0) for c in comment_dict[vid]),
        reverse = True
    )[:max_videos]

    # get the template from the TEMPLATES dictionary and then create the prompt model chain
    template = TEMPLATES['comments']
    prompt = ChatPromptTemplate.from_template(template)

    # inject the format instructions from the parser into the prompt
    chain = prompt | model

    # get relevant comments from ChromaDB
    # comments = retrieval(enriched_query, k_chunks)

    # --------------------------------------------------------
    #  Iterate through Videos by Id and call Queries for each
    # --------------------------------------------------------

    inserted_results = []
    for vid in sorted_vids:
        concatenated_comments = ""
        source_chunks = []

        # then iterate through the comments for the video
        for c_num, comment in enumerate(comment_dict[vid]):
            concatenated_comments += format_comment_with_metadata(comment) + "\n\n###\n\n"

            # Build source comment references from metadatas
            source_chunks.append({
                'video_id': vid,
                "author": comment_dict[vid][c_num]["author"],
                "comment_id": comment_dict[vid][c_num]["commentId"],
                "published_at": comment_dict[vid][c_num]["published_at"],
                "like_count": comment_dict[vid][c_num]["likes"],
                "comment_content": comment_dict[vid][c_num]["text"]
            })

        # --------------------------------------------
        #  Invoke based off query_type, for few-shot
        # --------------------------------------------
        # ...

        # -----------------------------------------------------------------------------
        #  Between each query we need to wait a minute,
        #  since there is a TPM (Tokens per Minute) limit/rate in Groq for this model
        # -----------------------------------------------------------------------------

        result = chain.invoke({
            "video_id": vid,
            "comments": concatenated_comments,
            "question": question,
            'comments_examples': comments_feedback_file
        })

        # put the result through a parser to extract the json from the resonse
        parsed_result = extract_json_from_response(result.text, query_type)

        # Insert the result into MongoDB
        # format schema to MongoDB
        document = {
                'run_date': datetime.now(timezone.utc),
                'query_type': query_type,
                'question': question,
                'video_id': vid,
                'result_text': parsed_result,
                'source_chunks': source_chunks,
                'model': 'llama-3.3-70b-versatile',
                #'retrieval_k':
            }

        # then insert new result
        insert_result = results_collection.insert_one(document)

        inserted_results.append({
            'id': str(insert_result.inserted_id),
            'query_type': query_type,
            'result_text': parsed_result,
            'source_chunks': source_chunks
        })

        # wait 60 seconds between queries to avoid the TPM
        time.sleep(60)

    return inserted_results

# ----------------------------------
#  Weekly Scheduled Queries
# ----------------------------------

def run_scheduled_queries(k_c = 15, k_t = 15, k_n = 15):
    # get the query type and query for each of the weekly queries

    # ---------------------------------------------------------
    #  Store the Claims and Use to Build Trends and Narratives
    # ---------------------------------------------------------

    try:
        # run claim query through LLM (using RAG) and keep results for the trends and narratives
        claims = run_query('claims', SCHEDULED_QUERIES['claims'], k_chunks = k_c)

        # print results
        print(f"claims query stored with id: {claims['id']}")

        # then run the trend query using the claims, and prior transcripts
        prev_chunks = claims['source_chunks']
        trends = run_query('trends', SCHEDULED_QUERIES['trends'], claims = claims['result_text'], previous_chunks = prev_chunks, k_chunks = k_t)

        # print results
        print(f"trends query stored with id: {trends['id']}")

        # then run the narratives query using the claims, trends, and prioor transcripts
        prev_chunks = trends['source_chunks']
        narratives, comment_dict = run_query('narratives', SCHEDULED_QUERIES['narratives'], claims = claims['result_text'], trends = trends['result_text'], previous_chunks = prev_chunks, k_chunks = k_n)

        # print results
        print(f"narratives query stored with id: {narratives['id']}")

        # then run the comments query using the comments dictionary
        feedback = comment_feedback(SCHEDULED_QUERIES['comments'], comment_dict)

        # print results
        print(f"Feedback queries: {feedback}")

    except Exception as e:
        print(f"Error with running query of types claims/trends/narratives: {e}")

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
            print(f"Error with running query of type: {query_type} and question: {question}: {e}")

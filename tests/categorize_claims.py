#!/usr/bin/env python3
import os
import json
import dotenv
from pathlib import Path
from langchain_groq import ChatGroq

dotenv.load_dotenv()

# LLM
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
model = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.1,
    max_tokens=200
)

CLAIM_CATEGORIES = [
    "factual", 
    "scientific", 
    "statistical", 
    "opinion" 
]

def categorize_claim(title: str, quote: str) -> dict:
    prompt_text = f"""Classify this AI claim into ONE category from this list ONLY: factual, scientific, statistical, opinion.

Claim: "{title}": "{quote}"

Reply with ONLY this JSON format (no extra text):
{{
  "category": "one word category",
  "reason": "brief explanation"
}}

Example:
{{
  "category": "opinion", 
  "reason": "subjective view"
}}"""
    result = model.invoke(prompt_text)
    content = result.content.strip()
    print("=== RAW LLM ===")
    print(repr(content))
    print("=== END RAW ===")
    
    # Simple parse - find first { ... }
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        json_str = content[start:end+1]
        # Fix escaped quotes
        json_str = json_str.replace('\\"', '"')
        try:
            parsed = json.loads(json_str)
            return parsed
        except Exception as e:
            print("Parse fail:", str(e))
            print("JSON str:", repr(json_str))
    
    return {
        "error": "Parse failed",
        "raw": content
    }

if __name__ == "__main__":
    
    # Loads claims
    claims_path = Path(__file__).parent.parent / "data" / "example_output" / "claims.json"
    with open(claims_path, 'r') as f:
        claims = json.load(f)
   
    # Categorize claims
    claim_titles = list(claims.keys())
    for title in claim_titles:
        quote = claims[title]["Quote"]
        print(f"Testing '{title}': {quote[:100]}...")
        cat = json.dumps
        cat = categorize_claim(title, quote)
        cat = {"claim_title": title, "quote": quote, **cat}
        print("\nRESULT:")
        print(json.dumps(cat, indent=2))


from fastapi import APIRouter, HTTPException, Depends
from typing import Literal, Optional
from src.llm.rag import run_query
import os
from pymongo import MongoClient
from src.repository.vectortranscripts import ResultsRepository

MONGO_URI = "mongodb+srv://maksimzlatkin_db_user:xDUhhcga2GaAQ6N4@vector-transcripts.ftu4ykq.mongodb.net/?appName=vector-transcripts"
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['youtube_intelligence']
results_collection = db['results']

router = APIRouter()

def get_results_repository():
    return ResultsRepository(results_collection)

@router.get("/prompt")
def prompt_question(
    question: str,
    query_type: Literal["claims", "trends", "narratives", "risk_factors"] = "trends"
):
    try:
        result = run_query(query_type, question)

        return {
            "status": "success",
            "query_type": query_type,
            "question": question,
            "result": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# default app route
@router.get("/")
def placeholder():
    pass

@router.get("/results", response_model=None)
def get_results(
    query_type: Optional[str] = None,
    limit: int = 5,
    repo: ResultsRepository = Depends(get_results_repository)
):
    return repo.get_results(query_type, limit)





#IGNORE:

# route to get narratives
@router.get("/narratives")
def get_narratives(limit: int = 3):
    results = list(
        results_collection
        .find({'query_type': 'narratives'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get risk factors
@router.get("/risk_factors")
def get_risk_factors(limit: int = 5):
    results = list(
        results_collection
        .find({'query_type': 'risk_factors'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results
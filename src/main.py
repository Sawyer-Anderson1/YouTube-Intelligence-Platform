# import the fastapi, scheduler, mongoDB, etc.
import os
import datetime
import subprocess
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from pymongo import MongoClient

# import scheduled RAG query runner
from llm.rag import run_scheduled_queries

# ----------------------------------
#  Setup MongoDB
# ----------------------------------

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
mongo_client = MongoClient(MONGO_URI)
db = mongo_client['youtube_intelligence']
results_collection = db['results']

# ----------------------------------
#  Cron Job Scheduler
# ----------------------------------

# implementing the cron jobs
# the function that runs scripts passed to it
def run_script(script_name):
    result = subprocess.run(['python3', script_name], capture_output=True, text=True)
    result.check_returncode()

# the function that defines the scripts that will be run once a week
def scheduled_job_sequence():
    try:
        # run the script to get the channels that have videos relevant to the category
        run_script('/services/youtube_api_channel_search.py')

        # run the script to get the videos from the channels that have to do with the category
        run_script('/services/youtube_api_channel_vids.py')

        # then run the script to get the transcripts from the channels
        run_script('/services/transcripts.py')

        # add the comments retrieval here
        # ...

        # then run the vector.py and rag.py (run_scheduled_queries())
        run_script('/llm/vector.py')

        run_scheduled_queries()
    except Exception as e:
        print(f"Transcript retrieval scripts failed to run: {e}")

# create the scheduler to run in an interval of a week
@asynccontextmanager
async def weeklylifespan(app: FastAPI):
    scheduler = BackgroundScheduler()

    # have the scripts that take the data from the YouTube API to run once every week
    scheduler.add_job(
            scheduled_job_sequence, 
            trigger="cron", 
            day_of_week='mon',
            hour=0, # run at midnight
            minute=0,
            timezone='US/Central', # run on UTC timezone (would run 6pm in CST), or run in central time (so 6am UTC)
            next_run_time=datetime.datetime.now() # run once on startup, then follow the cron job schedule
    )
    scheduler.start()

    yield
    scheduler.shutdown()

app = FastAPI(lifespan=weeklylifespan)

# ----------------------
#  API routes
# ----------------------

# default app route
@app.get("/")
def placeholder():
    pass

# get all results or by query_type
@app.get("/results")
def get_results(query_type: Optional[str] = None, limit: int = 5):
    query_filter = {}
    if query_type:
        query_filter['query_type'] = query_type

    results = list(
        results_collection
        .find(query_filter, {'_id': 0})  # exclude MongoDB's _id field
        .sort('run_date', -1)            # most recent first
        .limit(limit)
    )

    return results

# route to get claims
@app.get("/claims")
def get_claims(limit: int = 20):
    results = list(
        results_collection
        .find({'query_type': 'claims'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get trends
@app.get("/trends")
def get_trends(limit: int = 7):
    results = list(
        results_collection
        .find({'query_type': 'trends'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get narratives
@app.get("/narratives")
def get_narratives(limit: int = 3):
    results = list(
        results_collection
        .find({'query_type': 'narratives'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get risk factors
@app.get("/risk_factors")
def get_risk_factors(limit: int = 5):
    results = list(
        results_collection
        .find({'query_type': 'risk_factors'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# import the fastapi, scheduler, mongoDB, etc.
import os
import datetime
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from pymongo import MongoClient

# import scheduled RAG query runner
from .llm.rag import run_scheduled_queries

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
    scheduler.add_job(scheduled_job_sequence, "interval", weeks=1)
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

# get all results
@app.get("/results")
def get_results(query_type=None, limit=5):
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
def get_claims(limit=20):
    results = list(
        results_collection
        .find('claims', {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get trends
@app.get("/trends")
def get_trends(limit=7):
    results = list(
        results_collection
        .find('trends', {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get narratives
@app.get("/narratives")
def get_narratives(limit=3):
    results = list(
        results_collection
        .find('narratives', {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get risk factors
@app.get("/risk_factors")
def get_risk_factors(limit=5):
    results = list(
        results_collection
        .find('risk_factors', {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

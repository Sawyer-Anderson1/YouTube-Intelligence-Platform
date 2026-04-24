# import the fastapi, scheduler, mongoDB, etc.
import os
import datetime
import subprocess
import sys
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from pymongo import MongoClient

# logging imports
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# import scheduled RAG query runner
from .llm.rag import run_scheduled_queries

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
    # ----------------------------
    #  Run the Scripts as Modules
    # ----------------------------

    result = subprocess.run(
            [sys.executable, '-m', script_name],
            capture_output=True,
            text=True,
            cwd = PROJECT_ROOT,
            env = {**os.environ, 'PYTHONPATH': PROJECT_ROOT}
    )

    if result.returncode != 0:
        print(f"stderr: {result.stderr}")
        print(f"stdout: {result.stdout}")

    result.check_returncode()

# the function that defines the scripts that will be run once a week
def scheduled_job_sequence():
    logger.info("scheduled_job_sequence started")

    try:
        # ------------------------------
        #  Give Module Path of Scripts
        # ------------------------------

        # run the script to get the channels that have videos relevant to the category
        logger.info("Start retrieving channel ids")
        # run_script('src.services.youtube_api_channel_search')

        # run the script to get the videos from the channels that have to do with the category
        logger.info("Start retrieving channel vids")
        # run_script('src.services.youtube_api_channel_vids')

        # then run the script to get the transcripts from the channels
        logger.info("Start retrieving transcripts from the vids of the choosen channels")
        # run_script('src.services.transcripts')

        # add the comments retrieval here
        logger.info("Start retrieving comments from the vids of the choosen channels")
        # run_script('src.services.comments')

        # then run the vector.py and rag.py (run_scheduled_queries())
        logger.info("Start vectorizing the transcript data")
        run_script('src.llm.vector')

        logger.info("Run the scheduled queries for claims, trends, narratives, and comment feedback")
        run_scheduled_queries(k_c = 15, k_t = 5, k_n = 5)

        logger.info("Pipeline completed successfully")
    except Exception as e:
        logger.info(f"Transcript retrieval scripts failed to run: {e}")

# create the scheduler to run in an interval of a week
@asynccontextmanager
async def weeklylifespan(app: FastAPI):
    logger.info("Starting APScheduler...")
    scheduler = AsyncIOScheduler()

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
    logger.info(f"Scheduler started. Jobs: {scheduler.get_jobs()}")

    yield
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

# -------------------------
#  Instantiate FastAPI App
# -------------------------

app = FastAPI(lifespan=weeklylifespan)

# ----------------------------------------------
#  Enable CORS between Frontend and Backend API
# ----------------------------------------------

# list of the origins that are allowed to access the Backend API
origins = [
    "https://wonderful-dune-0050c5f0f.1.azurestaticapps.net", # the front end app (Azure Static Web App)
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

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

# route to get all comment feedback
@app.get("/comment_feedback")
def get_comment_feedback(limit: int = 10):
    results = list(
        results_collection
        .find({'query_type': 'comments'}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# route to get comment feedback by video ids
@app.get("/comment_feedback/{video_id}")
def get_comment_feedback_by_vid(video_id: str, limit: int = 5):
    results = list(
        results_collection
        .find({'query_type': 'comments', 'video_id': video_id}, {'_id': 0})
        .sort('run_date', -1)
        .limit(limit)
    )

    return results

# import the fastapi and scheduler
import datetime
import subprocess
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

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

        #...
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

@app.get("/")
def placeholder():
    pass

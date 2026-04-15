#!/bin/bash
pip install -r /home/site/wwwroot/requirements.txt
uvicorn src.main:app --host 0.0.0.0 --port $PORT
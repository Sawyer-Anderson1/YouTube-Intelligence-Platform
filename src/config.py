import os
from pathlib import Path

# works with Azure file share when on Azure and use project directory locally
DATA_PATH = Path(os.getenv('DATA_PATH', str(Path(__file__).parent.parent / 'data')))

CHROMA_DB_PATH = Path(os.getenv('CHROMA_DB_PATH', str(Path(__file__).parent.parent / 'chroma_langchain_db')))
EMBEDDED_LOG_PATH = Path(os.getenv('EMBEDDED_LOG_PATH', str(Path(__file__).parent.parent / 'data' / 'embedded_files.json')))
TRANSCRIPTS_PATH = DATA_PATH / 'transcripts'
COMMENTS_PATH = DATA_PATH / 'comments'
CHANNELS_PATH = DATA_PATH / 'channels.json'
CHANNEL_VIDS_PATH = DATA_PATH / 'channel_vids.json'
VIDEO_METRICS_PATH = DATA_PATH / 'video_metrics.json'
EXAMPLE_OUTPUT_PATH = DATA_PATH / 'example_output'

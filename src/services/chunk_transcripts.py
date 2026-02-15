# imports
# json to read transcript files and Path to define the path to the transcript folder
# concurrent.futures and ThreadPoolExecutor for concurrency (for use on full, static transcript folder)
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# define the path to the folder with the transcripts
folder_path = Path(__file__).parent.parent.parent / 'data' / 'transcripts'

# function that reads content of transcript
def read_and_chunk_transcript(filepath):
    try:
        with open(filepath, 'r') as file:
            transcript = json.load(file)

        # combine the very small chunks (snippets) from the youtube-transcript-api into larger chuncks
        larger_chunks = []

        # define the max size of the chunks and how much they'll overlap
        overlap_amount = 50
        max_chunk_count = 500

        # then create the chunks and add the metadata (start and duration)
        current_chunk = ""
        current_start = transcript[0]['start']
        current_duration = 0.0
        for snippet in transcript:
            if len(current_chunk.split()) + len(snippet['text'].split()) <= max_chunk_count:
                current_chunk += (" " + snippet['text'])
                current_duration += snippet['duration']
            else:
                larger_chunks.append({"text": current_chunk, "start": current_start, "duration": current_duration})
                current_start = snippet['start']

                # have current_chunk include past text for overlap
                current_chunk = " ".join((current_chunk.split())[-overlap_amount:])

        if current_chunk:
            larger_chunks.append({"text": current_chunk, "start": current_start, "duration": current_duration})

        # then write the new transcript back
        try:
            with open(filepath, 'w') as json_file:
                json.dump(larger_chunks, json_file, indent=4)

            return f"Successfully wrote to .json the larger chunks"

        except IOError as e:
            return f"Error with writing to json file {file_path}: {e}"

    except Exception as e:
        return f"Error reading {filepath}: {e}"

if __name__ == '__main__':
    filepaths = []
    for file_path in folder_path.glob('*.json'):
        if file_path.is_file():
            filepaths.append(file_path)

    # execute the reading of the transcripts in parrel with threads
    with ThreadPoolExecutor(max_workers=25) as executor:
        chunking_results = executor.map(read_and_chunk_transcript, filepaths)

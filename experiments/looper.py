import os
import json

def loop_through_transcription_cache(file_path):
    if file_path.endswith(".json"):
        with open(file_path, 'r') as f:
            data = json.load(f)
            segments = data.get("segments", [])
            for segment in segments:
                print(f"Segment {segment['id']} from {file_path}:")
                print(segment['words'])
                print("-" * 40)

# Provide the JSON file path directly
file_path = "./Kendrick Lamar - squabble up (Official Audio)_transcription_cache.json"
loop_through_transcription_cache(file_path)
import json
import os

def stream_candidates(file_path):
    """
    Memory-efficient generator that yields parsed JSON candidate records.
    Yields parsed dicts one by one.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Candidate database file not found: {file_path}")
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

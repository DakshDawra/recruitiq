import json
import os

def stream_candidates(file_path):
    """
    Memory-efficient generator that yields parsed JSON candidate records.
    Yields parsed dicts one by one.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Candidate database file not found: {file_path}")
        
    # Read the first non-whitespace character to determine if it is a JSON list
    is_json_list = False
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Read first few characters to skip any leading whitespace
            head = f.read(100).strip()
            if head and head[0] == '[':
                is_json_list = True
    except Exception:
        pass
        
    if is_json_list:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for item in data:
                yield item
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError as e:
                        print(f"Warning: Skipped malformed JSON line: {e}")

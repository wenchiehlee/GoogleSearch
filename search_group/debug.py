# Create debug_env.py
import os
from pathlib import Path

print("=== Current Environment Variables ===")
print(f"API Key: '{os.getenv('GOOGLE_SEARCH_API_KEY', 'NOT FOUND')}'")
print(f"CSE ID: '{os.getenv('GOOGLE_SEARCH_CSE_ID', 'NOT FOUND')}'")

print(f"\nAPI Key length: {len(os.getenv('GOOGLE_SEARCH_API_KEY', ''))}")
print(f"Expected length: 39")

# Check .env file parsing
env_file = Path('.env')
if env_file.exists():
    print("\n=== Manual .env parsing ===")
    with open(env_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if 'GOOGLE_SEARCH_API_KEY' in line:
                print(f"Line {i}: {repr(line)}")
            if 'GOOGLE_SEARCH_CSE_ID' in line:
                print(f"Line {i}: {repr(line)}")
from dotenv import load_dotenv
import os

load_dotenv()
key = os.environ.get('LANGSMITH_API_KEY')
print('Key found:', key is not None)
print('Key repr:', repr(key))
print('Key length:', len(key) if key else 0)
print('Starts with ls__:', key.startswith('ls__') if key else False)
from dotenv import load_dotenv
import os

load_dotenv()
from langsmith import Client

client = Client(api_key=os.environ.get('LANGSMITH_API_KEY'))
try:
    projects = list(client.list_projects(limit=1))
    print('SUCCESS - key is valid. Projects:', projects)
except Exception as e:
    print('FAILED:', e)
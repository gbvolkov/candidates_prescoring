from dotenv import load_dotenv
import os

from pathlib import Path

documents_path = Path.home() / ".env"

load_dotenv(os.path.join(documents_path, 'gv.env'))

class Config:
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
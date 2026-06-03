# config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Please set GEMINI_API_KEY in a .env file")

os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

MODEL_NAME = "gemini-2.0-flash"
MAX_TOKENS = 4000
TEMPERATURE = 0.1

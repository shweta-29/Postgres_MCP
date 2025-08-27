"""
config.py

Central place to load environment variables.
Keeps secrets out of code and avoids repeating os.getenv everywhere.
"""

import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "testdb")

# Simple check (optional, useful for debugging)
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is missing. Set it in your .env file.")

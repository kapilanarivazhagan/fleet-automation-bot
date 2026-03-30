from dotenv import load_dotenv
from openai import OpenAI
import os

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

SHEET_URL = "https://docs.google.com/spreadsheets/d/15xaEk5dqdfBjgFu4Auhr-HKioYsbhb0TrSw-eblOlEI/edit"

CREDS_FILE = "credentials.json"

# AI Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)
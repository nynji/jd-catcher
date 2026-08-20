import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LINKAREER_URL = os.getenv(
	"LINKAREER_URL",
	"https://linkareer.com/list/recruit",
)
CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "5"))

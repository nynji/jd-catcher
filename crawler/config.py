import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name(".env"))

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

LINKAREER_RECRUIT_URL = os.getenv(
	"LINKAREER_RECRUIT_URL",
	"https://linkareer.com/list/recruit?filterBy_activityTypeID=5&filterBy_status=OPEN&orderBy_direction=DESC&orderBy_field=RECENT&page=1",
)
LINKAREER_INTERN_URL = os.getenv(
	"LINKAREER_INTERN_URL",
	"https://linkareer.com/list/intern?filterBy_activityTypeID=5&filterBy_jobTypes=INTERN&filterBy_status=OPEN&orderBy_direction=DESC&orderBy_field=RECENT&page=1",
)
LINKAREER_URLS = [LINKAREER_RECRUIT_URL, LINKAREER_INTERN_URL]

CRAWL_MAX_PAGES = int(os.getenv("CRAWL_MAX_PAGES", "10"))

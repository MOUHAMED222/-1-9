import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # Your Telegram user ID
DATABASE_NAME = "bot_database.db"
DOWNLOAD_PATH = "downloads"
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Supported platforms (for display)
SUPPORTED_SITES = [
    "YouTube", "Instagram", "Facebook", "TikTok", "Twitter (X)", "Snapchat",
    "Pinterest", "Likee", "SoundCloud", "Telegram (stories)", "Vimeo",
    "Dailymotion", "Kwai", "Triller", "Dubsmash", "CapCut", "FameBit", "PMC Music"
]

# yt-dlp options
YDL_OPTIONS = {
    'format': 'best[filesize<{}]'.format(MAX_FILE_SIZE_BYTES),
    'outtmpl': os.path.join(DOWNLOAD_PATH, '%(id)s.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'cookiefile': None,
}
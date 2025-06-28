import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    PATH_TO_DATA = "core/storage/data/data"
    DATA_FORMAT = "csv"
    DATETIME_FORMAT_FROM = "%Y-%m-%dT%H:%M:%S.%fZ"
    DATETIME_FORMAT_TO = "%H:%M %d.%m.%Y"
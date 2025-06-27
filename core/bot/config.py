import os
from dotenv import load_dotenv

load_dotenv()

class BotConfig:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    PATH_TO_DATA = "core/storage/data/data"
    DATA_FORMAT = "csv"
import os
from dotenv import load_dotenv
from ..config import MainConfig

load_dotenv()

class BotConfig:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    PATH_TO_DATA: str = "core/storage/data/data"
    DATA_FORMAT: str = "csv"
    DATETIME_FORMAT: str = MainConfig.DATETIME_FORMAT
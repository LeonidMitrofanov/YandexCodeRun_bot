import os
from dotenv import load_dotenv
from ..config import MainConfig

load_dotenv()

class BotConfig:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN")
    PATH_TO_DATA: str = MainConfig.STORAGE_DIR / "data" / "data"
    DATA_FORMAT: str = "csv"
    DATETIME_FORMAT: str = MainConfig.DATETIME_FORMAT
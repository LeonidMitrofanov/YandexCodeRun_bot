from typing import List, Dict
from ..config import MainConfig

class ParserConfig:
    
    BASE_URL: str = 'https://coderun.yandex.ru/seasons/2025-summer/tracks/common/rating'
    REQUEST_TIMEOUT: int = 10
    DELAY_BETWEEN_REQUESTS: float = 0.5
    MAX_RETRIES: int = 3
    
    HEADERS: Dict[str, str] = {
        "User-Agent": "CodeRun_stat_bot"
            "(+https://github.com/LeonidMitrofanov/YandexCodeRun_bot)"
    }
    
    INCLUDE_GENERAL: bool = MainConfig.INCLUDE_GENERAL
    DEFAULT_LANGUAGES: List[str] = MainConfig.LANGUAGES
    
    DEFAULT_FILE_FORMAT: str = 'csv'  # 'csv' или 'excel'
    DEFAULT_FILENAME: str = 'yandex_coderun_rating'
    
    TIME_ZONE: str = 'Europe/Moscow'
    DATETIME_FORMAT: str = MainConfig.DATETIME_FORMAT
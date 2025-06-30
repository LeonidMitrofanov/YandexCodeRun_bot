from typing import List, Dict
from ..config import MainConfig

class ParserConfig:
    
    BASE_URL: str = 'https://coderun.yandex.ru/seasons/2025-summer/tracks/common/rating'
    REQUEST_TIMEOUT: int = 10
    DELAY_BETWEEN_REQUESTS: float = 1.0
    MAX_RETRIES: int = 3
    
    HEADERS: Dict[str, str] = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/125.0.0.0 Safari/537.36"
    }
    
    DEFAULT_LANGUAGES: List[str] = MainConfig.LANGUAGES
    
    DEFAULT_FILE_FORMAT: str = 'csv'  # 'csv' или 'excel'
    DEFAULT_FILENAME: str = 'yandex_coderun_rating'
    
    TIME_ZONE: str = 'Europe/Moscow'
    DATETIME_FORMAT: str = MainConfig.DATETIME_FORMAT
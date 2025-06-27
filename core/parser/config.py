from typing import List, Dict

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
    
    DEFAULT_LANGUAGES: List[str] = [
        'python', 'c', 'c-plus-plus', 'c-sharp', 'java', 'javascript',
        'kotlin', 'swift', 'go', 'rust', 'dart', 'pascal'
    ]
    
    DEFAULT_FILE_FORMAT: str = 'csv'  # 'csv' или 'excel'
    DEFAULT_FILENAME: str = 'yandex_coderun_rating'
    
    @classmethod
    def get_languages(cls) -> List[str]:
        """Возвращает список языков для парсинга."""
        return cls.DEFAULT_LANGUAGES
    
    @classmethod
    def get_headers(cls) -> Dict[str, str]:
        """Возвращает HTTP-заголовки для запросов."""
        return cls.HEADERS.copy()
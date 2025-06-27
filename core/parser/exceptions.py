class ScraperError(Exception):
    """Базовый класс для всех ошибок парсера"""
    pass


class UpdateInProgressError(ScraperError):
    """Ошибка при попытке запустить обновление во время выполнения другого обновления"""
    def __init__(self):
        super().__init__("Обновление уже выполняется, пожалуйста подождите")


class DataCollectionError(ScraperError):
    """Ошибка при сборе данных"""
    def __init__(self, language: str = None, message: str = None):
        if language and message:
            super().__init__(f"Ошибка сбора данных для языка {language}: {message}")
        elif language:
            super().__init__(f"Ошибка сбора данных для языка {language}")
        else:
            super().__init__(message or "Ошибка сбора данных")


class PageProcessingError(ScraperError):
    """Ошибка при обработке страницы"""
    def __init__(self, language: str = None, page: int = None, message: str = None):
        if language and page:
            super().__init__(f"Ошибка обработки страницы {page} для языка {language}: {message}")
        elif language:
            super().__init__(f"Ошибка обработки страницы для языка {language}: {message}")
        else:
            super().__init__(message or "Ошибка обработки страницы")


class EmptyDataError(ScraperError):
    """Ошибка при отсутствии данных"""
    def __init__(self, message: str = "Нет данных для обработки"):
        super().__init__(message)


class NetworkError(ScraperError):
    """Ошибка сетевого взаимодействия"""
    def __init__(self, message: str = "Ошибка сети"):
        super().__init__(message)
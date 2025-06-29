from typing import Dict

class StatConfig:
    LANGUAGES = [
    'python',
    'c',
    'c-plus-plus',
    'c-sharp',
    'java',
    'javascript',
    'kotlin',
    'swift',
    'go',
    'rust',
    'dart',
    'pascal'
    ]

    COMMON_COLUMNS = {
        'Задачи': 'first',
        'Дата': 'max'
    }

    @classmethod
    def get_language_columns(cls, prefix: str) -> Dict[str, str]:
        """Возвращает словарь с колонками для конкретного префикса (Место_ или Баллы_), исключая общий зачет"""
        return {
            f'{prefix}{lang}': 'first'
            for lang in cls.LANGUAGES
            if lang != 'Общий'  # Исключаем общий зачет
        }

    @classmethod
    def build_agg_config() -> Dict[str, str]:
        """Генерирует конфигурацию для агрегации данных, исключая общий зачет"""
        return {
            **StatConfig.get_language_columns('Место_'),
            **StatConfig.get_language_columns('Баллы_'),
            **StatConfig.COMMON_COLUMNS
        }
import pandas as pd
from typing import Dict
from .config import StatConfig

class StatsCalculator:
    @staticmethod
    def _get_language_columns(prefix: str) -> Dict[str, str]:
        """Возвращает словарь с колонками для конкретного префикса"""
        return {
            f'{prefix}{lang}': 'first'
            for lang in StatConfig.LANGUAGES
        }

    @classmethod
    def _build_agg_config(cls) -> Dict[str, str]:
        """Генерирует конфигурацию для агрегации данных"""
        config = {}
        config.update(cls._get_language_columns('Место_'))
        config.update(cls._get_language_columns('Баллы_'))
        config.update(StatConfig.COMMON_COLUMNS)
        return config

    @classmethod
    def group_by_user(cls, df: pd.DataFrame) -> pd.DataFrame:
        """Группирует DataFrame по участникам с заданной агрегацией"""
        return df.groupby('Участник').agg(cls._build_agg_config()).reset_index()
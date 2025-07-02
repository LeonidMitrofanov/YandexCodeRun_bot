import pandas as pd
from typing import Dict
from .config import StatConfig

class StatsCalculator:
    @staticmethod
    def _get_language_columns(prefix: str) -> Dict[str, str]:
        """Возвращает словарь с колонками для конкретного префикса
        
        Args:
            prefix: Префикс для колонок (например, 'Место_' или 'Баллы_')
            
        Returns:
            Словарь в формате {название_колонки: метод_агрегации}
        """
        columns = {f'{prefix}{lang}': 'first' for lang in StatConfig.LANGUAGES}
        if StatConfig.INCLUDE_GENERAL:
            columns[f'{prefix}Общий'] = 'first'
        return columns

    @classmethod
    def _build_agg_config(cls) -> Dict[str, str]:
        """Генерирует конфигурацию для агрегации данных"""
        config = {}
        config['Дата'] = 'max'
        config.update(cls._get_language_columns('Место_'))
        config.update(cls._get_language_columns('Баллы_'))
        config.update(StatConfig.COMMON_COLUMNS)
        return config

    @classmethod
    def group_by_user(cls, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.loc[:, 'Дата'] = pd.to_datetime(df['Дата'], errors='coerce')
        df = df.dropna(subset=['Дата'])
        for col in df.columns:
            if col.startswith('Баллы_'):
                df.loc[:, col] = pd.to_numeric(df[col], errors='coerce')
        
        return df.groupby('Участник').agg(cls._build_agg_config()).reset_index()
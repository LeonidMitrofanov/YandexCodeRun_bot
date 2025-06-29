import pandas as pd
from typing import Dict
from .config import StatConfig

def build_agg_config() -> Dict[str, str]:
    """Генерирует конфигурацию для агрегации данных"""
    return {
        **{f'Место_{lang}': 'first' for lang in StatConfig.LANGUAGES},
        **{f'Баллы_{lang}': 'first' for lang in StatConfig.LANGUAGES},
        **StatConfig.COMMON_COLUMNS
    }

class StatsCalculator:
    @staticmethod
    def group_by_user(df: pd.DataFrame) -> pd.DataFrame:
        """Группирует DataFrame по участникам с заданной агрегацией"""
        return df.groupby('Участник').agg(build_agg_config()).reset_index()

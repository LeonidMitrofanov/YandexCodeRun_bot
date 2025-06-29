import pandas as pd
from .config import StatConfig

class StatsCalculator:
    @staticmethod
    def group_by_user(df: pd.DataFrame) -> pd.DataFrame:
        """Группирует DataFrame по участникам с заданной агрегацией"""
        return df.groupby('Участник').agg(StatConfig.build_agg_config()).reset_index()

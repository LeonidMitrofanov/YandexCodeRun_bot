import pandas as pd

class StatsCalculator:
    @staticmethod
    def group_by_user(df: pd.DataFrame):
        grouped = df.groupby('Участник').agg({
            'Место_python': 'first',
            'Баллы_python': 'first',
            'Место_c': 'first',
            'Баллы_c': 'first',
            'Место_c-plus-plus': 'first',
            'Баллы_c-plus-plus': 'first',
            'Место_c-sharp': 'first',
            'Баллы_c-sharp': 'first',
            'Место_java': 'first',
            'Баллы_java': 'first',
            'Место_javascript': 'first',
            'Баллы_javascript': 'first',
            'Место_kotlin': 'first',
            'Баллы_kotlin': 'first',
            'Место_swift': 'first',
            'Баллы_swift': 'first',
            'Место_go': 'first',
            'Баллы_go': 'first',
            'Место_rust': 'first',
            'Баллы_rust': 'first',
            'Место_dart': 'first',
            'Баллы_dart': 'first',
            'Место_pascal': 'first',
            'Баллы_pascal': 'first',
            'Задачи': 'first',
            'Дата': 'max'
        }).reset_index()
        return grouped
    
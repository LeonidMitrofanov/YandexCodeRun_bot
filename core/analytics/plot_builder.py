import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .stats_calculator import StatsCalculator

class PlotBuilder:
    @staticmethod
    def plot_users_by_language_pie(df: pd.DataFrame) -> plt.Figure:
        """Строит круговую диаграмму распределения участников по языкам программирования
        на основе наличия баллов в колонках формата 'Баллы_<язык>'.
        
        Args:
            df: DataFrame с данными участников, содержащий колонки с баллами по языкам
            
        Returns:
            Figure: Объект matplotlib Figure с построенной диаграммой
            
        Raises:
            ValueError: Если нет данных для построения диаграммы
        """
        language_counts = {}
        
        for col in df.columns:
            if col.startswith('Баллы_'):
                language = col.split('_')[1]
                language_counts[language] = (df[col] > 0).sum()
        
        language_counts = {lang: count for lang, count in language_counts.items() if count > 0}
        
        if not language_counts:
            raise ValueError("Нет данных для построения диаграммы - все участники имеют нулевые баллы по всем языкам")
        
        languages = list(language_counts.keys())
        counts = list(language_counts.values())
        
        fig = plt.figure(figsize=(10, 8))
        plt.pie(
            counts,
            labels=languages,
            autopct='%1.1f%%',
            startangle=140,
            wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
        )
        plt.title('Распределение участников по языкам программирования', pad=20)
        plt.axis('equal')

        return fig
    
    @staticmethod
    def plot_users_by_language_bar(df: pd.DataFrame) -> plt.Figure:
        """Строит столбчатую диаграмму распределения участников по языкам программирования
        на основе наличия баллов в колонках формата 'Баллы_<язык>'.
        
        Args:
            df: DataFrame с данными участников, содержащий колонки с баллами по языкам
            
        Returns:
            Figure: Объект matplotlib Figure с построенной диаграммой
            
        Raises:
            ValueError: Если нет данных для построения диаграммы
        """
        language_counts = {}
        
        for col in df.columns:
            if col.startswith('Баллы_'):
                language = col.split('_')[1]
                language_counts[language] = (df[col] > 0).sum()
        
        language_counts = {lang: count for lang, count in language_counts.items() if count > 0}
        
        if not language_counts:
            raise ValueError("Нет данных для построения диаграммы - все участники имеют нулевые баллы по всем языкам")
        
        languages = list(language_counts.keys())
        counts = list(language_counts.values())

        fig, ax = plt.subplots(figsize=(12, 6))
        bars = ax.bar(languages, counts, color='skyblue', edgecolor='black')
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom')
        
        ax.set_title('Распределение участников по языкам программирования', pad=20, fontsize=14)
        ax.set_xlabel('Языки программирования', fontsize=12)
        ax.set_ylabel('Количество участников', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
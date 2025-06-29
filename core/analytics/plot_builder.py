import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .stats_calculator import StatsCalculator
from .config import StatConfig
from typing import Dict

class PlotBuilder:
    @staticmethod
    def _get_language_counts(df: pd.DataFrame) -> Dict[str, int]:
        """Вспомогательный метод для получения количества участников по языкам (исключая общий зачет)"""
        language_counts = {}
        for col in df.columns:
            if col.startswith('Баллы_'):
                language = col.split('_')[1]
                if language in StatConfig.LANGUAGES and language != 'Общий':  # Исключаем общий зачет
                    language_counts[language] = (df[col] > 0).sum()
        return language_counts

    @staticmethod
    def plot_users_by_language_pie(df: pd.DataFrame) -> plt.Figure:
        """Строит круговую диаграмму распределения участников по языкам программирования
        (исключая общий зачет)"""
        language_counts = PlotBuilder._get_language_counts(df)
        language_counts = {lang: count for lang, count in language_counts.items() if count > 0}
        
        if not language_counts:
            raise ValueError("Нет данных для построения диаграммы - все участники имеют нулевые баллы по всем языкам")
        
        sorted_languages, sorted_counts = zip(*sorted(language_counts.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette('viridis', len(sorted_languages))
        
        explode = [0.03] * len(sorted_languages)
        startangle = 90
        
        wedges, texts, autotexts = ax.pie(
            sorted_counts,
            labels=sorted_languages,
            autopct='%1.1f%%',
            startangle=startangle,
            colors=colors,
            explode=explode,
            textprops={'fontsize': 12},
            pctdistance=0.85,
            wedgeprops={'edgecolor': 'white', 'linewidth': 1}
        )
        
        plt.setp(autotexts, size=10, weight='bold', color='white')
        ax.set_title('Распределение участников по языкам программирования', 
                    pad=20, fontsize=14, fontweight='bold')
        
        legend_labels = [f'{l} - {c} чел.' for l, c in zip(sorted_languages, sorted_counts)]
        ax.legend(wedges, legend_labels,
                title="Языки программирования",
                loc="center left",
                bbox_to_anchor=(1, 0, 0.5, 1),
                fontsize=10)
        
        ax.axis('equal')
        plt.tight_layout()
        return fig
    
    @staticmethod
    def plot_users_by_language_bar(df: pd.DataFrame) -> plt.Figure:
        """Строит столбчатую диаграмму распределения участников по языкам программирования
        (исключая общий зачет)"""
        language_counts = PlotBuilder._get_language_counts(df)
        language_counts = {lang: count for lang, count in language_counts.items() if count > 0}
        
        if not language_counts:
            raise ValueError("Нет данных для построения диаграммы - все участники имеют нулевые баллы по всем языкам")
        
        sorted_languages, sorted_counts = zip(*sorted(language_counts.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(12, 6))
        
        ax = sns.barplot(x=list(sorted_languages), 
                        y=list(sorted_counts), 
                        hue=list(sorted_languages),
                        palette='viridis',
                        legend=False,
                        ax=ax)
        for p in ax.patches:
            ax.annotate(f'{int(p.get_height())}', 
                        (p.get_x() + p.get_width() / 2., p.get_height()),
                        ha='center', va='center', 
                        xytext=(0, 5), 
                        textcoords='offset points')
        
        ax.set_title('Распределение участников по языкам программирования', pad=20, fontsize=14)
        ax.set_xlabel('Языки программирования', fontsize=12)
        ax.set_ylabel('Количество участников', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        return fig
    
    @staticmethod
    def plot_languages_per_user_distribution(df: pd.DataFrame) -> plt.Figure:
        """Строит столбчатую диаграмму распределения количества языков программирования,
        на которых пишет один участник (исключая общий зачет)"""
        language_columns = [col for col in df.columns 
                        if col.startswith('Баллы_') and 
                        col.split('_')[1] in StatConfig.LANGUAGES and
                        col.split('_')[1] != 'Общий']  # Исключаем общий зачет
        user_data = df.groupby('Участник')[language_columns].first()
        user_language_counts = (user_data > 0).sum(axis=1)
        language_distribution = user_language_counts.value_counts().sort_index()
        
        if language_distribution.empty:
            raise ValueError("Нет данных для построения диаграммы - ни один участник не имеет положительных баллов")
        
        total_participants = len(user_data)
        num_languages = language_distribution.index.tolist()
        user_counts = language_distribution.values.tolist()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax = sns.barplot(x=list(num_languages), 
                        y=list(user_counts), 
                        hue=list(num_languages),
                        palette='viridis',
                        legend=False,
                        ax=ax)
        
        ax.annotate(f'Всего участников: {total_participants}',
                xy=(0.95, 0.95),
                xycoords='axes fraction',
                ha='right',
                va='top',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
                fontsize=12)
        
        for p in ax.patches:
            ax.annotate(
                f'{int(p.get_height())}',
                (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='center',
                xytext=(0, 5),
                textcoords='offset points',
                fontsize=10
            )
        
        ax.set_title('Распределение участников по количеству используемых языков', 
                    pad=20, fontsize=14, fontweight='bold')
        ax.set_xlabel('Количество языков программирования', fontsize=12)
        ax.set_ylabel('Количество участников', fontsize=12)
        ax.grid(axis='y', linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        return fig

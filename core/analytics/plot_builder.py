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
        
        sorted_languages, sorted_counts = zip(*sorted(language_counts.items(), key=lambda x: x[1], reverse=True))
        fig, ax = plt.subplots(figsize=(10, 8))
        colors = sns.color_palette('viridis', len(sorted_languages))
        
        # Визуальные улучшения:
        explode = [0.03] * len(sorted_languages)  # небольшое отделение секторов
        startangle = 90  # начальный угол для лучшего отображения
        
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
        sorted_languages, sorted_counts = zip(*sorted(zip(languages, counts), key=lambda x: x[1], reverse=True))

        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Используем seaborn barplot
        ax = sns.barplot(x=list(sorted_languages), 
                        y=list(sorted_counts), 
                        hue=list(sorted_languages),
                        palette='viridis',
                        legend=False,
                        ax=ax)
        
        # Добавляем подписи значений
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
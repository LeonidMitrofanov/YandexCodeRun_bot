import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
from typing import Optional, List, Dict, Any
from parser.config import ParserConfig

class CodeRunRatingScraper:
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        """
        Инициализация парсера рейтинга CodeRun.
        
        Args:
            languages: Список языков программирования для парсинга
            delay: Задержка между запросами (в секундах)
            max_retries: Максимальное количество попыток повторного запроса
        """
        self.languages = languages or ParserConfig.get_languages()
        self.delay = delay or ParserConfig.DELAY_BETWEEN_REQUESTS
        self.max_retries = max_retries or ParserConfig.MAX_RETRIES
        self.df = pd.DataFrame()
        self._last_update: Optional[datetime] = None

    @property
    def last_update(self) -> Optional[datetime]:
        """Возвращает время последнего успешного обновления данных."""
        return self._last_update

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """Определяет общее количество страниц с рейтингом."""
        pagination = soup.find('div', class_='Pagination-Pages')
        if pagination:
            page_links = pagination.find_all('a', class_='Pagination-PagesItem')
            if page_links:
                return max(int(link.text) for link in page_links if link.text.isdigit())
        return 1

    def _parse_table(self, soup: BeautifulSoup, language: str) -> List[Dict[str, Any]]:
        """Парсит таблицу рейтинга для конкретного языка."""
        table = soup.find('table', class_='RatingTable_rating-table__ixEUi')
        if not table:
            return []

        rows = table.select('tbody tr[role="row"]')
        data = []
        for row in rows:
            cells = row.find_all(['td', 'th'], class_='Cell')
            if len(cells) < 5:
                continue

            rank = cells[0].get_text(strip=True)
            user = cells[1].get_text(strip=True)
            tasks = cells[2].get_text(strip=True)
            points = cells[3].get_text(strip=True)

            time_tag = cells[4].find('time')
            date = time_tag['datetime'] if time_tag else cells[4].get_text(strip=True)

            data.append({
                'Участник': user,
                'Задачи': tasks,
                f'Место_{language}': rank,
                f'Баллы_{language}': float(points.replace(',', '.')),
                'Дата': date
            })
        return data

    def _collect_language_stats(self, language: str) -> List[Dict[str, Any]]:
        """Собирает статистику по всем страницам для указанного языка."""
        all_data = []
        params = {"language": language, "currentPage": 1}

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    ParserConfig.BASE_URL,
                    params=params,
                    headers=ParserConfig.get_headers(),
                    timeout=ParserConfig.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                total_pages = self._get_total_pages(soup)
                break
            except Exception as e:
                if attempt == self.max_retries - 1:
                    print(f"[{language}] ❌ Ошибка при загрузке первой страницы: {e}")
                    return []
                time.sleep(self.delay * 2)

        print(f"[{language}] Обнаружено страниц: {total_pages}")
        all_data.extend(self._parse_table(soup, language))

        for page in range(2, total_pages + 1):
            print(f"[{language}] Загружается страница {page}...")
            params = {"language": language, "currentPage": page}
            
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(
                        ParserConfig.BASE_URL,
                        params=params,
                        headers=ParserConfig.get_headers(),
                        timeout=ParserConfig.REQUEST_TIMEOUT
                    )
                    response.raise_for_status()
                    soup = BeautifulSoup(response.text, 'html.parser')
                    all_data.extend(self._parse_table(soup, language))
                    break
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        print(f"[{language}] ❌ Ошибка на странице {page}: {e}")
                        return all_data
                    time.sleep(self.delay * 2)

            time.sleep(self.delay)

        return all_data

    def get_data(self) -> pd.DataFrame:
        """Возвращает текущий DataFrame с рейтингом."""
        return self.df.copy()

    def update(self) -> None:
        """Обновляет данные рейтинга по всем языкам."""
        all_results = []
        for lang in self.languages:
            print(f"⏳ Обработка языка: {lang}")
            lang_data = self._collect_language_stats(lang)
            all_results.extend(lang_data)

        if not all_results:
            print("⚠️ Нет данных для построения DataFrame.")
            self.df = pd.DataFrame()
            self._last_update = None
            return

        self.df = pd.DataFrame(all_results)
        self._last_update = datetime.now()
        print(f"✅ Данные обновлены ({self._last_update.isoformat()}), всего записей: {len(self.df)}")

    def save(
        self,
        filename: str = None,
        file_format: str = None,
        encoding: str = 'utf-8-sig'
    ) -> None:
        """
        Сохраняет данные в файл.
        
        Args:
            filename: Имя файла (без расширения)
            file_format: Формат файла ('csv' или 'excel')
            encoding: Кодировка для CSV файлов
        """
        if self.df.empty:
            raise ValueError("DataFrame пуст, нечего сохранять.")

        filename = filename or ParserConfig.DEFAULT_FILENAME
        file_format = file_format or ParserConfig.DEFAULT_SAVE_FORMAT

        if file_format.lower() == 'csv':
            full_filename = f"{filename}.csv"
            self.df.to_csv(full_filename, index=False, encoding=encoding)
            print(f"✅ Данные сохранены в CSV: {full_filename}")
        elif file_format.lower() in ('excel', 'xlsx'):
            full_filename = f"{filename}.xlsx"
            self.df.to_excel(full_filename, index=False)
            print(f"✅ Данные сохранены в Excel: {full_filename}")
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_format}")
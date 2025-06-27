import asyncio
import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List, Dict, Any
from .config import ParserConfig


class CodeRunRatingScraper:
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        """
        Асинхронный парсер рейтинга CodeRun.
        
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
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()  # Для защиты от параллельных обновлений

    @property
    def last_update(self) -> Optional[datetime]:
        """Возвращает время последнего успешного обновления данных."""
        return self._last_update

    async def _get_session(self) -> aiohttp.ClientSession:
        """Создает или возвращает существующую сессию."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=ParserConfig.get_headers(),
                timeout=aiohttp.ClientTimeout(total=ParserConfig.REQUEST_TIMEOUT)
            )
        return self._session

    async def close(self) -> None:
        """Закрывает HTTP-сессию."""
        if self._session and not self._session.closed:
            await self._session.close()

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

    async def _fetch_page(self, language: str, page: int) -> str:
        """Асинхронно загружает страницу."""
        session = await self._get_session()
        params = {"language": language, "currentPage": page}
        
        for attempt in range(self.max_retries):
            try:
                async with session.get(
                    ParserConfig.BASE_URL,
                    params=params,
                    ssl=False
                ) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.delay * 2)

    async def _collect_language_stats(self, language: str) -> List[Dict[str, Any]]:
        """Асинхронно собирает статистику по всем страницам для указанного языка."""
        all_data = []
        
        try:
            html = await self._fetch_page(language, 1)
            soup = BeautifulSoup(html, 'html.parser')
            total_pages = self._get_total_pages(soup)
            
            print(f"[{language}] Обнаружено страниц: {total_pages}")
            all_data.extend(self._parse_table(soup, language))

            tasks = []
            for page in range(2, total_pages + 1):
                tasks.append(self._process_page(language, page))
                
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    print(f"[{language}] Ошибка при обработке страницы: {result}")
                else:
                    all_data.extend(result)
                
        except Exception as e:
            print(f"[{language}] ❌ Ошибка при сборе статистики: {e}")
            return []
            
        return all_data

    async def _process_page(self, language: str, page: int) -> List[Dict[str, Any]]:
        """Обрабатывает одну страницу."""
        print(f"[{language}] Загружается страница {page}...")
        await asyncio.sleep(self.delay)  # Задержка между запросами
        
        html = await self._fetch_page(language, page)
        soup = BeautifulSoup(html, 'html.parser')
        return self._parse_table(soup, language)

    def get_data(self) -> pd.DataFrame:
        """Возвращает текущий DataFrame с рейтингом."""
        return self.df.copy()

    async def update(self) -> None:
        """Асинхронно обновляет данные рейтинга по всем языкам."""
        async with self._lock:  # Защита от параллельных вызовов
            all_results = []
            
            for lang in self.languages:
                print(f"⏳ Обработка языка: {lang}")
                lang_data = await self._collect_language_stats(lang)
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
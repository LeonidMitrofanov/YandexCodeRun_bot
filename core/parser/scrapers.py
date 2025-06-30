import asyncio
import aiohttp
import pytz
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List, Dict, Any
from .exceptions import *
from .config import ParserConfig


class CodeRunRatingScraper:
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None,
        include_general: bool = True
    ):
        """
        Асинхронный парсер рейтинга CodeRun.
        
        Args:
            languages: Список языков программирования для парсинга
            delay: Задержка между запросами (в секундах)
            max_retries: Максимальное количество попыток повторного запроса
            include_general: Включать ли общий зачет в парсинг
        """
        self.languages = languages or ParserConfig.DEFAULT_LANGUAGES
        self.delay = delay or ParserConfig.DELAY_BETWEEN_REQUESTS
        self.max_retries = max_retries or ParserConfig.MAX_RETRIES
        self.include_general = include_general
        self.df = pd.DataFrame()
        self._last_update: Optional[datetime] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()
        self._is_updating = False

    @property
    def last_update(self) -> Optional[datetime]:
        """Возвращает время последнего успешного обновления данных."""
        return self._last_update

    async def _get_session(self) -> aiohttp.ClientSession:
        """Создает или возвращает существующую сессию."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=ParserConfig.HEADERS,
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

    def _parse_table(self, soup: BeautifulSoup, rating_type: str) -> List[Dict[str, Any]]:
        """Парсит таблицу рейтинга для конкретного языка или общего зачета.
        
        Args:
            soup: Объект BeautifulSoup с HTML страницы
            rating_type: Тип рейтинга ('Общий' или язык программирования)
        """
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
            if time_tag:
                dt = datetime.fromisoformat(time_tag['datetime'])
                dt = dt.astimezone(pytz.timezone(ParserConfig.TIME_ZONE))
                date = dt  # оставляем как datetime
            else:
                date_str = cells[4].get_text(strip=True)
                date = pd.to_datetime(date_str, errors='coerce')

            data.append({
                'Участник': user,
                'Задачи': tasks,
                f'Место_{rating_type}': rank,
                f'Баллы_{rating_type}': float(points.replace(',', '.')),
                'Дата': date
            })
        return data

    async def _fetch_page(self, rating_type: str, page: int) -> str:
        """Асинхронно загружает страницу.
        
        Args:
            rating_type: Тип рейтинга ('Общий' или язык программирования)
            page: Номер страницы
        """
        session = await self._get_session()
        params = {"currentPage": page}
        
        # Добавляем параметр language только если это не общий зачет
        if rating_type != 'Общий':
            params["language"] = rating_type
        
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
                    raise NetworkError(f"Не удалось загрузить страницу {page} для {rating_type} после {self.max_retries} попыток: {str(e)}")
                await asyncio.sleep(self.delay * 2)

    async def _collect_stats(self, rating_type: str) -> List[Dict[str, Any]]:
        """Асинхронно собирает статистику по всем страницам для указанного типа рейтинга."""
        all_data = []

        try:
            # Загружаем первую страницу
            html = await self._fetch_page(rating_type, 1)
            soup = BeautifulSoup(html, 'html.parser')
            total_pages = self._get_total_pages(soup)

            if total_pages <= 0:
                raise DataCollectionError(rating_type, "Не удалось определить количество страниц")

            page_data = self._parse_table(soup, rating_type)
            if not page_data:
                raise EmptyDataError(f"Нет данных на первой странице для {rating_type}")
            all_data.extend(page_data)

            for page in range(2, total_pages + 1):
                try:
                    print(f"[{rating_type}] Загружается страница {page}...")
                    result = await self._process_page(rating_type, page)
                    if not result:
                        raise EmptyDataError(f"Нет данных на странице {page} для {rating_type}")
                    all_data.extend(result)
                    await asyncio.sleep(self.delay)  # Задержка между запросами
                except Exception as e:
                    raise PageProcessingError(rating_type, message=str(e))

        except Exception as e:
            if not isinstance(e, ScraperError):
                raise DataCollectionError(rating_type, str(e))
            raise

        if not all_data:
            raise EmptyDataError(f"Не удалось собрать данные для {rating_type}")

        return all_data


    async def _process_page(self, rating_type: str, page: int) -> List[Dict[str, Any]]:
        """Обрабатывает одну страницу."""
        print(f"[{rating_type}] Загружается страница {page}...")
        await asyncio.sleep(self.delay)  # Задержка между запросами
        
        html = await self._fetch_page(rating_type, page)
        soup = BeautifulSoup(html, 'html.parser')
        return self._parse_table(soup, rating_type)

    def get_data(self) -> pd.DataFrame:
        """Возвращает текущий DataFrame с рейтингом."""
        return self.df.copy()

    async def update(self) -> None:
        """Асинхронно обновляет данные рейтинга по всем языкам и общему зачету."""
        if self._is_updating:
            raise UpdateInProgressError()
            
        self._is_updating = True
        try:
            async with self._lock:
                all_results = []
                
                # Собираем данные по общему зачету, если требуется
                if self.include_general:
                    try:
                        general_data = await self._collect_stats('Общий')
                        all_results.extend(general_data)
                    except DataCollectionError as e:
                        raise DataCollectionError(f"Не удалось обработать общий зачет: {str(e)}")
                
                # Собираем данные по языкам программирования
                for lang in self.languages:
                    try:
                        lang_data = await self._collect_stats(lang)
                        all_results.extend(lang_data)
                    except DataCollectionError as e:
                        raise DataCollectionError(f"Не удалось обработать язык {lang}: {str(e)}")

                if not all_results:
                    raise EmptyDataError("Нет данных для построения DataFrame")
                    
                self.df = pd.DataFrame(all_results)
                self._last_update = datetime.now()
        finally:
            self._is_updating = False

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
        file_format = file_format or ParserConfig.DEFAULT_FILE_FORMAT

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

    def load(
        self,
        filename: str = None,
        file_format: str = None,
        encoding: str = 'utf-8-sig'
    ) -> None:
        """
        Загружает данные из файла и восстанавливает состояние объекта.
        
        Args:
            filename: Имя файла (без расширения)
            file_format: Формат файла ('csv' или 'excel')
            encoding: Кодировка для CSV файлов
            
        Raises:
            ValueError: Если файл не найден или данные не могут быть загружены
            FileNotFoundError: Если указанный файл не существует
        """
        filename = filename or ParserConfig.DEFAULT_FILENAME
        file_format = file_format or ParserConfig.DEFAULT_FILE_FORMAT
        if file_format.lower() == 'csv':
            full_filename = f"{filename}.csv"
            try:
                self.df = pd.read_csv(full_filename, encoding=encoding)
            except UnicodeDecodeError:
                self.df = pd.read_csv(full_filename, encoding='utf-8')
        elif file_format.lower() in ('excel', 'xlsx'):
            full_filename = f"{filename}.xlsx"
            self.df = pd.read_excel(full_filename)
        else:
            raise ValueError(f"Неподдерживаемый формат файла: {file_format}")
        
        if self.df.empty:
            raise ValueError("Загруженный DataFrame пуст. Возможно, файл поврежден.")
        
        self._last_update = datetime.now()
        print(f"✅ Данные успешно загружены из {full_filename}")
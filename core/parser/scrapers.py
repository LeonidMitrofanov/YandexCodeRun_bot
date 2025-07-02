import pytz
import asyncio
import aiohttp
import logging
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List, Dict, Any
from .exceptions import *
from .config import ParserConfig

logger = logging.getLogger(__name__)

class CodeRunRatingScraper:
    def __init__(
        self,
        languages: Optional[List[str]] = None,
        delay: Optional[float] = None,
        max_retries: Optional[int] = None,
        include_general: bool = None
    ):
        """
        Парсер рейтинга CodeRun.
        
        Args:
            languages: Список языков программирования для парсинга
            delay: Задержка между запросами (в секундах)
            max_retries: Максимальное количество попыток повторного запроса
            include_general: Включать ли общий зачет в парсинг
        """
        self.languages = languages or ParserConfig.DEFAULT_LANGUAGES
        self.delay = delay or ParserConfig.DELAY_BETWEEN_REQUESTS
        self.max_retries = max_retries or ParserConfig.MAX_RETRIES
        self.include_general = include_general if include_general is not None \
                                else ParserConfig.INCLUDE_GENERAL
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
            logger.debug("Создание новой HTTP-сессии")
            self._session = aiohttp.ClientSession(
                headers=ParserConfig.HEADERS,
                timeout=aiohttp.ClientTimeout(total=ParserConfig.REQUEST_TIMEOUT)
            )
        return self._session

    async def close(self) -> None:
        """Закрывает HTTP-сессию."""
        if self._session and not self._session.closed:
            logger.debug("Закрытие HTTP-сессии")
            await self._session.close()

    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """Определяет общее количество страниц с рейтингом."""
        pagination = soup.find('div', class_='Pagination-Pages')
        if pagination:
            page_links = pagination.find_all('a', class_='Pagination-PagesItem')
            if page_links:
                return max(int(link.text) for link in page_links if link.text.isdigit())
        return 1

    def _parse_table(self, soup: BeautifulSoup, rating_type: str) -> tuple:
        """Парсит таблицу рейтинга и возвращает данные + флаг обнаружения 0 баллов.
        Применяется одинаково как к языкам, так и к общему зачету."""
        table = soup.find('table', class_='RatingTable_rating-table__ixEUi')
        if not table:
            logger.warning(f"Не найдена таблица рейтинга для {rating_type}")
            return [], False

        rows = table.select('tbody tr[role="row"]')
        data = []
        found_zero = False
        
        for row in rows:
            cells = row.find_all(['td', 'th'], class_='Cell')
            if len(cells) < 5:
                continue

            rank = cells[0].get_text(strip=True)
            user = cells[1].get_text(strip=True)
            tasks = cells[2].get_text(strip=True)
            points_text = cells[3].get_text(strip=True)

            try:
                points_value = float(points_text.replace(',', '.'))
                if points_value == 0:
                    found_zero = True
                    logger.debug(f"Найден участник с 0 баллов: {user}")
            except ValueError:
                points_value = 0.0

            time_tag = cells[4].find('time')
            if time_tag:
                dt = datetime.fromisoformat(time_tag['datetime'])
                dt = dt.astimezone(pytz.timezone(ParserConfig.TIME_ZONE))
                date = dt
            else:
                date_str = cells[4].get_text(strip=True)
                date = pd.to_datetime(date_str, errors='coerce') or pd.NaT

            data.append({
                'Участник': user,
                'Задачи': int(tasks) if tasks.isdigit() else 0,
                f'Место_{rating_type}': rank,
                f'Баллы_{rating_type}': points_value,
                'Дата': date
            })
            if found_zero:
                break
        logger.debug(f"Обработано {len(data)} строк для {rating_type}")
        return data, found_zero

    async def _fetch_page(self, rating_type: str, page: int) -> str:
        """Загружает страницу.
        
        Args:
            rating_type: Тип рейтинга ('Общий' или язык программирования)
            page: Номер страницы
        """
        session = await self._get_session()
        params = {"currentPage": page}
        
        if rating_type != 'Общий':
            params["language"] = rating_type
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Запрос страницы {page} для {rating_type} (попытка {attempt + 1})")
                async with session.get(
                    ParserConfig.BASE_URL,
                    params=params,
                    ssl=False
                ) as response:
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Ошибка загрузки страницы {page} для {rating_type}: {str(e)}")
                    raise NetworkError(f"Не удалось загрузить страницу {page} для {rating_type} после {self.max_retries} попыток: {str(e)}")
                await asyncio.sleep(self.delay * 2)
                logger.debug(f"Повторная попытка ({attempt + 2}/{self.max_retries})")

    async def _collect_stats(self, rating_type: str) -> List[Dict[str, Any]]:
        """Cобирает статистику по всем страницам для указанного типа рейтинга.
        Прекращает парсинг при обнаружении первого участника с 0 баллов."""
        all_data = []
        found_zero = False
        page = 1

        try:
            while not found_zero:
                logger.debug(f"[{rating_type}] Загрузка страницы {page}")

                html = await self._fetch_page(rating_type, page)
                soup = BeautifulSoup(html, 'html.parser')
                
                if page == 1:
                    total_pages = self._get_total_pages(soup)
                    if total_pages <= 0:
                        logger.error(f"Неверное количество страниц: {total_pages}")
                        raise DataCollectionError(rating_type, "Не удалось определить количество страниц")
                    logger.info(f"Всего страниц для {rating_type}: {total_pages}")

                page_data, zero_detected = self._parse_table(soup, rating_type)
                found_zero = zero_detected
                
                if not page_data:
                    if page == 1:
                        logger.error(f"Нет данных на первой странице для {rating_type}")
                        raise EmptyDataError(f"Нет данных на первой странице для {rating_type}")
                    break
                
                all_data.extend(page_data)
                
                if not found_zero and page < total_pages:
                    page += 1
                    await asyncio.sleep(self.delay)
                else:
                    logger.debug(f"Завершение сбора для {rating_type} на странице {page}")
                    break

        except Exception as e:
            logger.error(f"Ошибка сбора данных для {rating_type}: {str(e)}", exc_info=True)
            if not isinstance(e, ScraperError):
                raise DataCollectionError(rating_type, str(e))
            raise

        if not all_data:
            logger.error(f"Нет данных для {rating_type}")
            raise EmptyDataError(f"Не удалось собрать данные для {rating_type}")

        logger.info(f"Собрано {len(all_data)} записей для {rating_type}")
        return all_data

    async def update(self) -> None:
        """Асинхронно обновляет данные рейтинга."""
        if self._is_updating:
            logger.warning("Попытка обновления во время уже выполняющегося обновления")
            raise UpdateInProgressError()
            
        self._is_updating = True
        logger.info("Начало обновления данных")
        
        try:
            async with self._lock:
                all_results = []
                if self.include_general:
                    try:
                        logger.debug("Начало обработки общего зачета")
                        general_data = await self._collect_stats('Общий')
                        all_results.extend(general_data)
                        logger.info("Общий зачет успешно обработан")
                    except DataCollectionError as e:
                        logger.error(f"Ошибка обработки общего зачета: {str(e)}")
                        raise DataCollectionError(f"Не удалось обработать общий зачет: {str(e)}")
                
                for lang in self.languages:
                    try:
                        logger.debug(f"Начало обработки языка {lang}")
                        lang_data = await self._collect_stats(lang)
                        all_results.extend(lang_data)
                        logger.info(f"Язык {lang} успешно обработан")
                    except DataCollectionError as e:
                        logger.error(f"Ошибка обработки языка {lang}: {str(e)}")
                        raise DataCollectionError(f"Не удалось обработать язык {lang}: {str(e)}")

                if not all_results:
                    logger.error("Нет данных для построения DataFrame")
                    raise EmptyDataError("Нет данных для построения DataFrame")
                    
                self.df = pd.DataFrame(all_results)
                self._last_update = datetime.now()
                logger.info(f"Данные успешно обновлены. Всего записей: {len(self.df)}")
        except Exception as e:
            logger.error(f"Критическая ошибка при обновлении: {str(e)}", exc_info=True)
            raise
        finally:
            self._is_updating = False
            logger.debug("Флаг обновления сброшен")

    def get_data(self) -> pd.DataFrame:
        """Возвращает текущий DataFrame с рейтингом."""
        return self.df.copy()
    
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
            logger.error("Попытка сохранения пустого DataFrame")
            raise ValueError("DataFrame пуст, нечего сохранять.")

        filename = filename or ParserConfig.DEFAULT_FILENAME
        file_format = file_format or ParserConfig.DEFAULT_FILE_FORMAT

        try:
            if file_format.lower() == 'csv':
                full_filename = f"{filename}.csv"
                self.df.to_csv(full_filename, index=False, encoding=encoding)
                logger.info(f"Данные сохранены в CSV: {full_filename}")
            elif file_format.lower() in ('excel', 'xlsx'):
                full_filename = f"{filename}.xlsx"
                self.df.to_excel(full_filename, index=False)
                logger.info(f"Данные сохранены в Excel: {full_filename}")
            else:
                logger.error(f"Неподдерживаемый формат файла: {file_format}")
                raise ValueError(f"Неподдерживаемый формат файла: {file_format}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {str(e)}")
            raise

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
        
        try:
            if file_format.lower() == 'csv':
                full_filename = f"{filename}.csv"
                logger.debug(f"Загрузка данных из CSV: {full_filename}")
                self.df = pd.read_csv(full_filename, encoding=encoding)
            elif file_format.lower() in ('excel', 'xlsx'):
                full_filename = f"{filename}.xlsx"
                logger.debug(f"Загрузка данных из Excel: {full_filename}")
                self.df = pd.read_excel(full_filename)
            else:
                logger.error(f"Неподдерживаемый формат файла: {file_format}")
                raise ValueError(f"Неподдерживаемый формат файла: {file_format}")
            
            if self.df.empty:
                logger.error("Загруженный DataFrame пуст")
                raise ValueError("Загруженный DataFrame пуст.")
            
            self._last_update = datetime.now()
            logger.info(f"Данные успешно загружены из {full_filename}. Записей: {len(self.df)}")
        except FileNotFoundError:
            logger.error(f"Файл не найден: {full_filename}")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки данных: {str(e)}")
            raise

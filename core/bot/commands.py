import logging
import pandas as pd
from io import BytesIO
from aiogram.filters import Command
from aiogram import Dispatcher, Router, types
from matplotlib import pyplot as plt
from core.analytics import StatsCalculator, PlotBuilder
from core.parser import CodeRunRatingScraper
from core.parser.exceptions import *
from .texts.commands import CommandTexts
from .keyboards import help_keyboard
from .texts.info import InfoText
from .utils import format_date
from .config import BotConfig

logger = logging.getLogger(__name__)

scraper = CodeRunRatingScraper()
router = Router()

def get_user_info(message: types.Message) -> str:
    """Формирует строку с информацией о пользователе"""
    user = message.from_user
    return f"(@{user.username}) [id:{user.id}]"


async def on_startup(dispatcher: Dispatcher):
    try:
        logger.info("Попытка загрузки данных при старте бота")
        scraper.load(BotConfig.PATH_TO_DATA)
    except FileNotFoundError:
        logger.warning("Файл с данными не найден, будет создан при первом обновлении")
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}", exc_info=True)
        raise


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /start от пользователя {user_info}")
        await message.answer(
            CommandTexts.START,
            reply_markup=help_keyboard
        )
        logger.debug(f"Команда /start успешно обработана для {user_info}")
    except Exception as e:
        logger.error(f"Ошибка в обработке /start: {e}", exc_info=True)
        raise


@router.message(Command("help"))
async def cmd_help(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /help от пользователя {user_info}")
        await message.answer(
            CommandTexts.HELP,
            reply_markup=help_keyboard
        )
        logger.debug(f"Команда /help успешно обработана для {user_info}")
    except Exception as e:
        logger.error(f"Ошибка в обработке /help: {e}", exc_info=True)
        raise


@router.message(Command("update"))
async def cmd_update(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /update от пользователя {user_info}")
        if scraper._is_updating:
            logger.warning(f"Попытка обновления во время уже выполняющегося обновления ({user_info})")
            await message.answer("🔄 Парсинг уже в процессе, пожалуйста подождите...")
            return
            
        progress_msg = await message.answer("⏳ Парсим данные...")
        logger.debug(f"Начато обновление данных по запросу {user_info}")
        
        await scraper.update()
        scraper.save(BotConfig.PATH_TO_DATA)
        
        formatted_date = format_date(scraper.last_update)
        logger.info(f"Данные успешно обновлены ({formatted_date}) по запросу {user_info}")
        
        await message.answer(f"✅ Данные обновлены ({formatted_date})")
        await progress_msg.delete()
        
    except DataCollectionError as e:
        logger.error(f"Ошибка сбора данных: {str(e)}", exc_info=True)
        await message.answer(f"❌ Ошибка при обновлении данных: {str(e)}")
    except Exception as e:
        logger.critical(f"Неизвестная ошибка при обновлении: {str(e)}", exc_info=True)
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")
    finally:
        logger.debug(f"Завершение обработки команды /update для {get_user_info(message)}")


@router.message(Command("contact"))
async def cmd_contact(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /contact от пользователя {user_info}")
        await message.answer(InfoText.contact)
        logger.debug(f"Команда /contact успешно обработана для {user_info}")
    except Exception as e:
        logger.error(f"Ошибка в обработке /contact: {e}", exc_info=True)
        raise


@router.message(Command("user_by_lang"))
async def cmd_lang_distr(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /user_by_lang от пользователя {user_info}")
        df = scraper.get_data()
        
        if df.empty:
            logger.warning(f"Нет данных для построения графиков (запрос от {user_info})")
            await message.answer("Нет данных для построения графиков\nВыполните /update")
            return

        progress_msg = await message.answer("⏳ Строим графики...")
        logger.debug(f"Начато построение графиков распределения по языкам для {user_info}")
        
        fig_bar = PlotBuilder.plot_users_by_language_bar(df)
        fig_pie = PlotBuilder.plot_users_by_language_pie(df)
        logger.debug(f"Графики успешно построены для {user_info}")

        def fig_to_bytes(fig: plt.Figure) -> bytes:
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.getvalue()

        bar_bytes = fig_to_bytes(fig_bar)
        pie_bytes = fig_to_bytes(fig_pie)        
        bar_photo = types.BufferedInputFile(bar_bytes, filename="lang_bar.png")
        pie_photo = types.BufferedInputFile(pie_bytes, filename="lang_pie.png")

        await message.answer_photo(
            photo=bar_photo,
            caption="📊 Распределение участников по языкам (столбчатая диаграмма)"
        )        
        await message.answer_photo(
            photo=pie_photo,
            caption="🍰 Распределение участников по языкам (круговая диаграмма)"
        )
        
        await progress_msg.delete()
        logger.info(f"Графики успешно отправлены пользователю {user_info}")

    except ValueError as e:
        logger.error(f"Ошибка значения при построении графиков: {str(e)}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при построении графиков: {str(e)}", exc_info=True)
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")



@router.message(Command("langcnt_by_user"))
async def cmd_user_langs_distr(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /langcnt_by_user от пользователя {user_info}")
        df = scraper.get_data()
        
        if df.empty:
            logger.warning(f"Нет данных для построения графиков (запрос от {user_info})")
            await message.answer("Нет данных для построения графиков\nВыполните /update")
            return

        progress_msg = await message.answer("⏳ Строим диаграмму...")
        logger.debug(f"Начато построение диаграммы распределения языков для {user_info}")
        
        fig = PlotBuilder.plot_languages_per_user_distribution(df)
        logger.debug(f"Диаграмма успешно построена для {user_info}")

        def fig_to_bytes(fig: plt.Figure) -> bytes:
            buf = BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)
            plt.close(fig)
            return buf.getvalue()
        
        image_bytes = fig_to_bytes(fig)
        photo = types.BufferedInputFile(image_bytes, filename="user_langs_distr.png")
        
        await message.answer_photo(
            photo=photo,
            caption="📊 Распределение участников по количеству используемых языков"
        )
        
        await progress_msg.delete()
        logger.info(f"Диаграмма успешно отправлена пользователю {user_info}")
    
    except ValueError as e:
        logger.error(f"Ошибка значения при построении диаграммы: {str(e)}", exc_info=True)
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        logger.error(f"Неизвестная ошибка при построении диаграммы: {str(e)}", exc_info=True)
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")


@router.message(Command("user_stats"))
async def cmd_user_stats(message: types.Message):
    try:
        user_info = get_user_info(message)
        logger.info(f"Обработка команды /user_stats от пользователя {user_info}")
        username = message.text.split(maxsplit=1)[1].strip()
        logger.debug(f"Запрошена статистика для пользователя: {username} (запрос от {user_info})")
        
        df = scraper.get_data()
        
        if df.empty:
            logger.warning(f"Нет данных для анализа (запрос от {user_info})")
            await message.answer("Нет данных для анализа\nВыполните /update")
            return

        user_stats = StatsCalculator.group_by_user(df)
        user_data = user_stats[user_stats['Участник'] == username]

        if user_data.empty:
            logger.warning(f"Пользователь {username} не найден (запрос от {user_info})")
            await message.answer(f"Пользователь {username} не найден")
            return

        # Основные данные
        tasks = user_data['Задачи'].values[0]
        last_update = format_date(user_data['Дата'].iloc[0])
        total_points = user_data['Баллы_Общий'].values[0]
        total_place = user_data['Место_Общий'].values[0]
        logger.debug(f"Получены основные данные для {username} (запрос от {user_info})")

        # Собираем информацию по языкам
        languages = []
        for col in user_data.columns:
            if col.startswith('Баллы_'):
                lang = col.split('_')[1]
                points = user_data[col].values[0]
                place_str = user_data[f'Место_{lang}'].values[0]
                
                if pd.notna(points) and place_str.isdigit():
                    place = int(place_str)
                    languages.append({
                        'lang': lang,
                        'points': points,
                        'place': place
                    })
        logger.debug(f"Получены данные по языкам для {username} (запрос от {user_info})")

        # Сортируем языки по баллам (по убыванию)
        languages.sort(key=lambda x: x['points'], reverse=True)

        # Разделяем языки на группы
        top_languages = []
        good_languages = []
        other_languages = []
        
        for lang in languages:
            if lang['lang'] != 'Общий':
                if lang['place'] <= 10:
                    top_languages.append(lang)
                elif lang['place'] <= 20:
                    good_languages.append(lang)
                else:
                    other_languages.append(lang)
        logger.debug(f"Языки классифицированы для {username} (запрос от {user_info})")

        # Формируем сообщение
        response = [
            f"👤 *{username}*",
            f"✅ Решено задач: {tasks}",
            f"🕒 Последнее решение: {last_update}",
            "\n---\n",
            "🔹 *Общий зачёт:*"
        ]

        # Добавляем общую статистику
        try:
            total_place_int = int(total_place)
            top100_row = user_stats[user_stats['Место_Общий'] == '100']
            top100_points = top100_row['Баллы_Общий'].values[0] if not top100_row.empty else 0
            points_diff = abs(total_points - top100_points)
            
            if total_points >= top100_points:
                response.append(f"📍 {total_place} место ({total_points} баллов)")
                response.append(f"📊 +{points_diff} баллов над топ-100")
            else:
                response.append(f"📍 {total_place} место ({total_points} баллов)")
                response.append(f"📊 -{points_diff} баллов до топ-100")
        except (ValueError, IndexError):
            response.append(f"📍 {total_place} место ({total_points} баллов)")
        logger.debug(f"Сформирована общая статистика для {username} (запрос от {user_info})")

        # Добавляем языки программирования
        if languages:
            response.append("\n🔹 *Языки программирования:*")
            
            for lang in top_languages:
                response.append(f"🏆 {lang['lang']} – {lang['place']} место ({lang['points']})")
            
            for lang in good_languages:
                response.append(f"📜 {lang['lang']} – {lang['place']} место ({lang['points']})")
                
            for lang in other_languages[:5]:
                response.append(f"🔸 {lang['lang']} – {lang['place']} место ({lang['points']})")
        else:
            response.append("\n🔹 Нет данных по языкам программирования")
        logger.debug(f"Сформирована статистика по языкам для {username} (запрос от {user_info})")

        # Добавляем информацию о привилегиях
        has_fast_track = total_place_int <= 100 if 'total_place_int' in locals() else False
        has_merch = total_place_int <= 100 if 'total_place_int' in locals() else False
        has_certificate = total_place_int <= 300 if 'total_place_int' in locals() else False
        
        if not has_fast_track:
            has_fast_track = any(lang['place'] <= 10 for lang in languages)
        if not has_merch:
            has_merch = any(lang['place'] <= 10 for lang in languages)
        if not has_certificate:
            has_certificate = any(lang['place'] <= 20 for lang in languages)

        response.extend([
            "\n---\n",
            "🎁 *Текущие привилегии:*",
            "✅ Фаст-трек" if has_fast_track else "❌ Фаст-трек",
            "✅ Мерч CodeRun" if has_merch else "❌ Мерч CodeRun",
            "✅ Сертификат" if has_certificate else "❌ Сертификат",
            "\n---\n",
            InfoText.about_reward
        ])
        logger.debug(f"Сформирована информация о привилегиях для {username} (запрос от {user_info})")

        await message.answer("\n".join(response), parse_mode="Markdown")
        logger.info(f"Статистика для {username} успешно отправлена пользователю {user_info}")

    except IndexError:
        logger.warning(f"Не указан ник пользователя для команды /user_stats (запрос от {get_user_info(message)})")
        await message.answer("Укажите ник пользователя:\n/user_stats <ник>")
    except Exception as e:
        logger.error(f"Ошибка при обработке /user_stats: {str(e)}", exc_info=True)
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")


def register_commands(dp):
    try:
        logger.info("Регистрация команд бота")
        dp.startup.register(on_startup)
        dp.include_router(router)
        logger.debug("Команды успешно зарегистрированы")
    except Exception as e:
        logger.critical(f"Ошибка при регистрации команд: {e}", exc_info=True)
        raise
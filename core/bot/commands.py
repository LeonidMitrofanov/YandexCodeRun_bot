import pandas as pd
from aiogram import Dispatcher, Router, types
from aiogram.filters import Command
from io import BytesIO
from matplotlib import pyplot as plt
from core.parser import CodeRunRatingScraper
from core.parser.exceptions import *
from core.analytics import StatsCalculator, PlotBuilder
from .utils import format_date
from .texts.commands import CommandTexts
from .texts.info import InfoText
from .keyboards import help_keyboard
from .config import BotConfig

scraper = CodeRunRatingScraper()
router = Router()

async def on_startup(dispatcher: Dispatcher):
    try:
        scraper.load(BotConfig.PATH_TO_DATA)
        print(f"✅ Данные успешно загружены из файла ({scraper.last_update})")
    except FileNotFoundError:
        print("ℹ️ Файл с данными не найден, будет создан при первом обновлении")
    except Exception as e:
        print(f"⚠️ Ошибка при загрузке данных: {e}")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        CommandTexts.START,
        reply_markup=help_keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        CommandTexts.HELP,
        reply_markup=help_keyboard
    )

@router.message(Command("update"))
async def cmd_update(message: types.Message):
    if scraper._is_updating:
        await message.answer("🔄 Парсинг уже в процессе, пожалуйста подождите...")
        return
    try:
        progress_msg = await message.answer("⏳ Парсим данные...")
        await scraper.update()
        scraper.save(BotConfig.PATH_TO_DATA)
        formatted_date = format_date(scraper.last_update)
        await message.answer(f"✅ Данные обновлены ({formatted_date})")
        await progress_msg.delete()
    except DataCollectionError as e:
        await message.answer(f"❌ Ошибка при обновлении данных: {str(e)}")
    except Exception as e:
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")

@router.message(Command("contact"))
async def cmd_contact(message: types.Message):
    await message.answer(InfoText.contact)

@router.message(Command("user_by_lang"))
async def cmd_lang_distr(message: types.Message):
    try:
        df = scraper.get_data()
        if df.empty:
            await message.answer("Нет данных для построения графиков\n"
                                 "Выполните /update")
            return

        progress_msg = await message.answer("⏳ Строим графики...")
        fig_bar = PlotBuilder.plot_users_by_language_bar(df)
        fig_pie = PlotBuilder.plot_users_by_language_pie(df)

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

    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")
    
@router.message(Command("langcnt_by_user"))
async def cmd_user_langs_distr(message: types.Message):
    """
    Отправляет диаграмму распределения участников по количеству используемых языков
    """
    try:
        df = scraper.get_data()
        if df.empty:
            await message.answer("Нет данных для построения графиков\n"
                            "Выполните /update")
            return

        progress_msg = await message.answer("⏳ Строим диаграмму...")
        fig = PlotBuilder.plot_languages_per_user_distribution(df)
        
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
    
    except ValueError as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
    except Exception as e:
        await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")
    
@router.message(Command("user_stats"))
async def cmd_user_stats(message: types.Message):
    """
    Показывает статистику по конкретному пользователю
    Использование: /user_stats <ник>
    """
    try:
        username = message.text.split(maxsplit=1)[1].strip()
        df = scraper.get_data()
        
        if df.empty:
            await message.answer("Нет данных для анализа\nВыполните /update")
            return

        user_stats = StatsCalculator.group_by_user(df)
        user_data = user_stats[user_stats['Участник'] == username]

        if user_data.empty:
            await message.answer(f"Пользователь {username} не найден")
            return

        # Основные данные
        tasks = user_data['Задачи'].values[0]
        last_update = format_date(user_data['Дата'].iloc[0])
        total_points = user_data['Баллы_Общий'].values[0]
        total_place = user_data['Место_Общий'].values[0]

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

        # Добавляем языки программирования
        if languages:
            response.append("\n🔹 *Языки программирования:*")
            
            for lang in top_languages:
                response.append(f"🏆 {lang['lang']} – {lang['place']} место ({lang['points']})")
            
            for lang in good_languages:
                response.append(f"📜 {lang['lang']} – {lang['place']} место ({lang['points']})")
                
            for lang in other_languages[:5]:  # Ограничиваем количество других языков
                response.append(f"🔸 {lang['lang']} – {lang['place']} место ({lang['points']})")
        else:
            response.append("\n🔹 Нет данных по языкам программирования")

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

        await message.answer("\n".join(response), parse_mode="Markdown")

    except IndexError:
        await message.answer("Укажите ник пользователя:\n/user_stats <ник>")
    except Exception as e:
        raise e
        # await message.answer(f"⚠️ Неизвестная ошибка: {str(e)}")

def register_commands(dp):
    dp.startup.register(on_startup)
    dp.include_router(router)
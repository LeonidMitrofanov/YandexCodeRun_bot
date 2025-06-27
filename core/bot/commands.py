from aiogram import Dispatcher, Router, types
from aiogram.filters import Command
from io import BytesIO
from matplotlib import pyplot as plt
from core.parser import CodeRunRatingScraper
from core.parser.exceptions import *
from core.analytics import StatsCalculator, PlotBuilder
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
        await message.answer(f"✅ Данные обновлены ({scraper.last_update})")
        await progress_msg.delete()
    except DataCollectionError as e:
        await message.answer(f"❌ Ошибка при обновлении данных: {str(e)}")
    except Exception as e:
        await message.answer(f"❌ Неизвестная ошибка: {str(e)}")

@router.message(Command("contact"))
async def cmd_contact(message: types.Message):
    await message.answer(InfoText.contact_text)

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
        await message.answer(f"⚠️ Произошла непредвиденная ошибка: {str(e)}")
    
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
        await message.answer(f"⚠️ Произошла непредвиденная ошибка: {str(e)}")

def register_commands(dp):
    dp.startup.register(on_startup)
    dp.include_router(router)
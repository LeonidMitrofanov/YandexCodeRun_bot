from aiogram import Router, types
from aiogram.filters import Command
from core.parser import CodeRunRatingScraper
from core.parser.exceptions import *
from core.analytics import StatsCalculator, PlotBuilder
from .texts.commands import CommandTexts
from .keyboards import help_keyboard

scraper = CodeRunRatingScraper()
router = Router()

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
        await message.answer("⏳ Начинаем парсинг данных...")
        await scraper.update()
        await message.answer(f"✅ Данные обновлены ({scraper.last_update})")
    except DataCollectionError as e:
        await message.answer(f"❌ Ошибка при обновлении данных: {str(e)}")
    except Exception as e:
        await message.answer(f"❌ Неизвестная ошибка: {str(e)}")

@router.message(Command("lang_distr"))
async def cmd_lang_distr(message: types.Message):
    await message.answer(f"Распределение участников по языкам: ")

def register_commands(dp):
    dp.include_router(router)
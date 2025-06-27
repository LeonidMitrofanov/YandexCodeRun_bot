from aiogram import Router, types, F
from aiogram.filters import Command
from .keyboards import help_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для анализа данных. Вот что я умею:\n"
        "/user <ник> - информация о пользователе\n"
        "/top - топ участников\n"
        "/recent - последние решения\n"
        "/task <номер> - статистика по задаче\n"
        "/help - справка по командам",
        reply_markup=help_keyboard
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "Список доступных команд:\n"
        "/user <ник> - информация о пользователе\n"
        "/top - топ участников\n"
        "/recent - последние решения\n"
        "/task <номер> - статистика по задаче\n"
        "/help - справка по командам",
        reply_markup=help_keyboard
    )

@router.message(Command("user"))
async def cmd_user(message: types.Message):
    args = message.text.split(maxsplit=1)
    username = args[1] if len(args) > 1 else None
    if not username:
        await message.answer("Пожалуйста, укажите ник пользователя: /user <ник>")
        return
    await message.answer(f"Информация о пользователе {username}")

@router.message(Command("top"))
async def cmd_top(message: types.Message):
    await message.answer("Топ участников")

@router.message(Command("recent"))
async def cmd_recent(message: types.Message):
    await message.answer("Последние решения")

@router.message(Command("task"))
async def cmd_task(message: types.Message):
    args = message.text.split(maxsplit=1)
    task_id = args[1] if len(args) > 1 else None
    if not task_id:
        await message.answer("Пожалуйста, укажите номер задачи: /task <номер>")
        return
    await message.answer(f"Статистика по задаче {task_id}")

def register_commands(dp):
    dp.include_router(router)
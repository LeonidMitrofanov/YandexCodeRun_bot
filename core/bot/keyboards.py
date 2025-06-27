from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_help_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="/help")
    builder.button(text="/start")
    builder.button(text="/update")
    return builder.as_markup(resize_keyboard=True)

help_keyboard = get_help_keyboard()
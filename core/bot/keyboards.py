from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_help_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="/help")
    builder.button(text="/start")
    builder.button(text="/update")
    builder.button(text="/lang_distr")
    builder.adjust(2, 2)  # 2 кнопки в первом ряду, 2 во втором
    return builder.as_markup(resize_keyboard=True)

help_keyboard = get_help_keyboard()
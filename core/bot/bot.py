from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from .config import BotConfig

bot = Bot(
    token=BotConfig.BOT_TOKEN,
)
dp = Dispatcher()
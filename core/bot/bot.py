from aiogram import Bot, Dispatcher
from .config import BotConfig

bot = Bot(
    token=BotConfig.BOT_TOKEN,
)
dp = Dispatcher()
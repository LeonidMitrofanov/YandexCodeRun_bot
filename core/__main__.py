from core.bot import dp, bot, register_commands
import asyncio

async def main():
    register_commands(dp)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
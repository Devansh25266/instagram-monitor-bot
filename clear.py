from telegram import Bot
import asyncio

TOKEN = "8585255621:AAFSprY9LRhfmrXzp3kUbcufycsNQPJUXWk"

async def main():

    bot = Bot(TOKEN)

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    print("Webhook cleared!")

asyncio.run(main())
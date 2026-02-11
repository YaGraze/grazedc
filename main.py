import discord
import os # Библиотека для работы с системой
from discord.ext import commands
from dotenv import load_dotenv # Библиотека для загрузки .env файла
load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Бот вошел в систему как {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

if TOKEN is None:
    print("Ошибка: Токен не найден! Проверь файл .env")
else:
    bot.run(TOKEN)

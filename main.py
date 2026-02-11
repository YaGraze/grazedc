import discord
from discord.ext import commands

# Настройка намерений (Intents)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Событие запуска
@bot.event
async def on_ready():
    print(f'Бот вошел в систему как {bot.user}')

# Простая команда !ping
@bot.command()
async def ping(ctx):
    await ctx.send('Pong!')

# Команда !hello
@bot.command()
async def hello(ctx):
    await ctx.send(f'Привет, {ctx.author.mention}!')

# ЗАПУСК БОТА
# Замени 'ТВОЙ_ТОКЕН' на токен, который ты скопировал на Шаге 1
bot.run('MTEwMzM1MTEwMTkyOTAzMzg1OA.GyOPbu.otkMQIKX4NxbjTaCLSCkVvyGuYnXOMsNoMDX0k')

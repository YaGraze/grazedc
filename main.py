# ------------------------------------------------------------------------------
# ИМПОРТ БИБЛИОТЕК
# ------------------------------------------------------------------------------
import discord
import os
import datetime
import re 
import random 
import asyncio # Нужен для асинхронных задач
import yt_dlp # Библиотека для YouTube
from collections import defaultdict
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# КОНФИГУРАЦИЯ И ЗАПУСК
# ------------------------------------------------------------------------------

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

SPAM_LIMIT = 5       
SPAM_TIME = 5        
MUTE_MINUTES = 5 
LOFI_STREAM_URL = "http://stream.zeno.fm/0r0xa854rp8uv"

# Настройки для YouTube (yt-dlp)
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # Использовать IPv4
}

# Настройки FFmpeg
FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)

# Основной класс бота
class MyBot(commands.Bot):
    def __init__(self):
        # Настраиваем интенты (права на события)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True # Нужно для работы с участниками (бан, кик)

        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # ВАЖНО: Добавляем View с тем же классом, что используется в коде.
        # Это позволяет меню работать после перезагрузки.
        self.add_view(NavigationView())
        await self.tree.sync()

    async def on_ready(self):
        print(f'✅ Бот успешно запущен: {self.user} (ID: {self.user.id})')
        print('------')

# Инициализация бота
bot = MyBot()

# Вспомогательная функция для получения ссылки на аудио
class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        # Запускаем в отдельном потоке, чтобы бот не завис
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # Если это плейлист или поиск, берем первый результат
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, executable='./ffmpeg', **FFMPEG_OPTIONS), data=data)

# ------------------------------------------------------------------------------
# РАЗДЕЛ 1: СИСТЕМА НАВИГАЦИИ (Меню и Кнопки)
# ------------------------------------------------------------------------------

class NavigationSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Правила сервера", description="Краткий свод правил", emoji="📜", value="rules"),
            discord.SelectOption(label="Роли сервера", description="Информация о ролях", emoji="🎭", value="roles"),
            discord.SelectOption(label="Текстовые каналы", description="Описание чатов", emoji="💬", value="text_channels"),
            discord.SelectOption(label="Голосовые каналы", description="Описание войсов", emoji="🔊", value="voice_channels"),
            discord.SelectOption(label="Музыка", description="Музыкальный бот и Lofi", emoji="🎵", value="music"),
            discord.SelectOption(label="Команды", description="Список команд", emoji="💻", value="commands"),
        ]
        super().__init__(
            placeholder="Выберите нужное", 
            min_values=1, 
            max_values=1, 
            options=options, 
            custom_id="navigation_menu"
        )

    async def callback(self, interaction: discord.Interaction):
        choice = self.values[0]
        view = discord.ui.View() # Контейнер для кнопок-ссылок
        content = "" 

        if choice == "rules":
            content = (
                "**📜 Краткие правила сервера Mates:**\n\n"
                "1. **🤝 Уважение:** Без оскорблений, провокаций, агрессии и дискриминации.\n"
                "2. **💬 Общение:** Без спама, флуда, оффтопа и лишних пингов (@).\n"
                "3. **🔞 Контент:** Строгий запрет на NSFW (18+), шок-контент и насилие.\n"
                "4. **📢 Реклама:** Запрещен любой пиар и рассылки в ЛС без разрешения.\n"
                "5. **🔊 Войс:** Не мешайте другим играть и общаться, уважайте тишину.\n"
                "6. **⚖️ Discord:** Соблюдаем официальные правила платформы.\n\n"
                "🔨 *Незнание правил не освобождает от ответственности. Наказание — Бан.*"
            )
            view.add_item(discord.ui.Button(label="📖 Полные правила", url="https://ptb.discord.com/channels/618407303699496982/1103654934852931625"))

        elif choice == "text_channels":
            content = (
                "**💬 Текстовые каналы**\n"
                "Это основные чаты для общения. Здесь мы обсуждаем игры, делимся мемами, "
                "читаем новости и просто болтаем на любые темы. Выбирай подходящий чат и присоединяйся!"
            )
            view.add_item(discord.ui.Button(label="💬 Перейти к чатам", url="https://discord.com/channels/618407303699496982/1099461741651447838"))

        elif choice == "voice_channels":
            content = (
                "**🔊 Голосовые каналы**\n"
                "Здесь расположены комнаты для живого общения. Залетай в любой свободный канал "
                "для совместных игр или просто ламповых посиделок."
            )
            view.add_item(discord.ui.Button(label="🔊 Перейти к голосовым", url="https://discord.com/channels/618407303699496982/768437875854934016"))

        elif choice == "music":
            content = (
                "**🎵 Музыкальный раздел**\n"
                "В этом чате ты можешь управлять музыкой. Используй команды, чтобы запустить "
                "бота, или включи **Lofi радио** для создания приятной атмосферы во время игры или отдыха."
            )
            view.add_item(discord.ui.Button(label="🎵 Перейти в Music", url="https://ptb.discord.com/channels/618407303699496982/1092366005432496182"))

        elif choice == "roles":
            content = (
                "**🎭 Описание ролей сервера Mates:**\n\n"
                "**👑 Администрация:**\n"
                "• **Owner** — Создатель сервера.\n"
                "• **Helpmate** — Модераторы, следящие за порядком.\n\n"
                
                "**👥 Участники:**\n"
                "• **Mates** — Основная роль активных игроков (выдается по умолчанию).\n"
                "• **Dudes** — Роль для тех, кто зашел просто пообщаться и не играет.\n\n"
                
                "**🏆 Киберспортивные команды:**\n"
                "• **Mortelles-v.1** — Команда сервера по CS2.\n"
                "• **Mortelles-v.2** — Команда сервера по Valorant.\n\n"
                
                "**🎮 Игровые роли:**\n"
                "Выбираются при входе. Показывают, во что ты играешь:\n"
                "CS2, Dota 2, Valorant, Apex, Fortnite, OW2, The Finals, PUBG, RL, Destiny 2 и другие."
            )
            
        elif choice == "commands":
            content = "**💻 Команды навигации:**\n`/navigation` - Вызвать это меню."
            
        else:
            content = "Информация не найдена."

        await interaction.response.send_message(content=content, view=view, ephemeral=True)

class NavigationView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(NavigationSelect())

@bot.tree.command(name="navigation", description="Показать меню навигации (Только для админов)")
@app_commands.checks.has_permissions(administrator=True)
async def navigation(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Раздел навигации.",
        description=(
            "Привет, рады видеть тебя с нами! Наш сервер создан для "
            "совместных игр и поиска тиммейтов в различных играх. "
            "Перед тем, как начать общение, ты можешь быстренько изучить "
            "сервер с помощью меню навигации. Тут можно ознакомиться с "
            "ролями, и где их получить, а также узнать об основных каналах.\n\n"
            "Для ознакомления с сервером нажми **\"Выберите нужное\"**"
        ),
        color=0xDEA266
    )
    
    # ⚠️ СЮДА ВСТАВИТЬ ССЫЛКУ НА КАРТИНКУ
    image_url = "https://media.discordapp.net/attachments/1103698978811412600/1471055017254453279/Frame_24.jpg?ex=698d8a3e&is=698c38be&hm=882bf70b7fb343e5e3925daa4e9a1a7f2ae6c6630bb4e5e983db73aa66858d76&=&format=webp&width=1264&height=351" 
    embed.set_image(url=image_url) # <--- РАСКОММЕНТИРОВАТЬ ЭТУ СТРОКУ, КОГДА БУДЕТ ССЫЛКА

    await interaction.response.send_message(embed=embed, view=NavigationView())

# ------------------------------------------------------------------------------
# РАЗДЕЛ 2: МОДЕРАЦИЯ (Kick, Ban, Mute, Clear)
# ------------------------------------------------------------------------------

# 1. ОЧИСТКА ЧАТА (CLEAR)
@bot.tree.command(name="clear", description="Очистить чат от сообщений")
@app_commands.describe(amount="Количество сообщений для удаления")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True) # Бот "думает", сообщение видят только админы
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🗑️ Удалено {len(deleted)} сообщений.", ephemeral=True)

# 2. КИК ПОЛЬЗОВАТЕЛЯ (KICK)
@bot.tree.command(name="kick", description="Выгнать пользователя с сервера")
@app_commands.describe(member="Кого выгнать", reason="Причина")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
    if member.id == interaction.user.id:
        await interaction.response.send_message("Вы не можете выгнать самого себя!", ephemeral=True)
        return
    
    try:
        await member.kick(reason=reason)
        # Красивый ответ
        embed = discord.Embed(title="🔨 Пользователь выгнан", color=0xDEA266)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Причина", value=f"{reason}", inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ У меня нет прав выгнать этого пользователя (возможно, его роль выше моей).", ephemeral=True)

# 3. БАН ПОЛЬЗОВАТЕЛЯ (BAN)
@bot.tree.command(name="ban", description="Забанить пользователя")
@app_commands.describe(member="Кого забанить", reason="Причина")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "Не указана"):
    if member.id == interaction.user.id:
        await interaction.response.send_message("Себя банить нельзя!", ephemeral=True)
        return

    try:
        await member.ban(reason=reason)
        embed = discord.Embed(title="⛔ Пользователь забанен", color=0xDEA266)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Модератор", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Причина", value=f"{reason}", inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Недостаточно прав для бана этого пользователя.", ephemeral=True)

# 4. РАЗБАН (UNBAN)
@bot.tree.command(name="unban", description="Разбанить пользователя по ID")
@app_commands.describe(user_id="ID пользователя")
@app_commands.checks.has_permissions(ban_members=True)
async def unban(interaction: discord.Interaction, user_id: str):
    try:
        user_obj = discord.Object(id=int(user_id))
        await interaction.guild.unban(user_obj)
        await interaction.response.send_message(f"✅ Пользователь с ID {user_id} был разбанен.")
    except discord.NotFound:
        await interaction.response.send_message("❌ Пользователь не найден в списке банов.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Введите корректный ID (только цифры).", ephemeral=True)

# 5. МУТ / ТАЙМАУТ (TIMEOUT)
@bot.tree.command(name="mute", description="Временно запретить писать и говорить (Timeout)")
@app_commands.describe(member="Кого замутить", minutes="На сколько минут", reason="Причина")
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "Не указана"):
    if member.id == interaction.user.id:
        await interaction.response.send_message("Нельзя замутить себя!", ephemeral=True)
        return

    duration = datetime.timedelta(minutes=minutes)
    try:
        await member.timeout(duration, reason=reason)
        embed = discord.Embed(title="🔇 Пользователь отправлен в тайм-аут", color=0xDEA266)
        embed.add_field(name="Пользователь", value=f"{member.mention}", inline=True)
        embed.add_field(name="Время", value=f"{minutes} мин.", inline=True)
        embed.add_field(name="Причина", value=f"{reason}", inline=False)
        await interaction.response.send_message(embed=embed)
    except discord.Forbidden:
        await interaction.response.send_message("❌ Не удалось замутить (возможно, это админ или роль выше моей).", ephemeral=True)

# 6. СНЯТЬ МУТ (UNMUTE)
@bot.tree.command(name="unmute", description="Снять тайм-аут раньше времени")
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(interaction: discord.Interaction, member: discord.Member):
    try:
        await member.timeout(None) # None убирает таймаут
        await interaction.response.send_message(f"🔊 С {member.mention} снято ограничение.")
    except discord.Forbidden:
        await interaction.response.send_message("❌ Ошибка доступа.", ephemeral=True)

# Обработка ошибок прав доступа
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ У вас недостаточно прав для использования этой команды.", ephemeral=True)
    else:
        # Для отладки можно выводить ошибку в консоль
        print(f"Ошибка команды: {error}")
        await interaction.response.send_message("Произошла ошибка при выполнении команды.", ephemeral=True)

# ------------------------------------------------------------------------------
# РАЗДЕЛ 3: РАЗВЛЕЧЕНИЯ (FUN)
# ------------------------------------------------------------------------------

# КОМАНДА GAYRATE
@bot.tree.command(name="gayrate", description="Узнать процент гейства")
@app_commands.describe(member="Чей процент проверить? (Пусто = твой)")
async def gayrate(interaction: discord.Interaction, member: discord.Member = None):
    # Если member не указан, берем того, кто вызвал команду
    target = member or interaction.user
    
    # Генерируем случайное число от 0 до 100
    percent = random.randint(0, 100)
    
    # Красивый Embed
    embed = discord.Embed(title="🏳️‍🌈 Gay Rate Machine", color=0xDEA266)
    embed.description = f"{target.mention} гей на **{percent}%**"
    
    # Если процент высокий, добавляем забавную картинку (опционально)
    if percent > 90:
        embed.set_footer(text="Ого, мощно! 💅")
    elif percent < 10:
        embed.set_footer(text="Подозрительно мало... 🤔")

    await interaction.response.send_message(embed=embed)

# КОМАНДА FLIP (МОНЕТКА)
@bot.tree.command(name="flip", description="Подбросить монетку")
async def flip(interaction: discord.Interaction):
    result = random.choice(["🦅 Орёл", "🪙 Решка"])
    
    embed = discord.Embed(title="Подбрасываем монетку...", color=0xDEA266)
    embed.add_field(name="Результат", value=f"**{result}**")
    
    await interaction.response.send_message(embed=embed)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ У вас недостаточно прав.", ephemeral=True)

# ------------------------------------------------------------------------------
# РАЗДЕЛ 4: АВТО-МОДЕРАЦИЯ (AutoMod)
# ------------------------------------------------------------------------------

# Переменная для хранения истории сообщений (для анти-спама)
spam_tracking = defaultdict(list)

@bot.event
async def on_message(message):
    # Не проверяем сообщения от самого бота
    if message.author.bot:
        return

    # Не проверяем сообщения от Администраторов (им можно все)
    if message.author.guild_permissions.administrator:
        return # Просто выходим из функции, если это админ

    msg_content = message.content.lower()

    # --- 2. АНТИ-ССЫЛКИ (Discord Invites) ---
    # Ищем ссылки вида discord.gg/ или discord.com/invite/
    if re.search(r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li)|discord(?:app)?\.com/invite)/.+", msg_content):
        try:
            await message.delete()
            await message.channel.send(f"{message.author.mention}, реклама сторонних серверов запрещена! 🚫", delete_after=5)
        except discord.Forbidden:
            pass
        return

    # --- 3. АНТИ-СПАМ ---
    user_id = message.author.id
    now = datetime.datetime.now()
    
    # Добавляем время текущего сообщения в список пользователя
    spam_tracking[user_id].append(now)
    
    # Очищаем старые записи (удаляем те, что были раньше чем SPAM_TIME секунд назад)
    spam_tracking[user_id] = [t for t in spam_tracking[user_id] if (now - t).total_seconds() < SPAM_TIME]
    
    # Если количество сообщений за последние секунды превысило лимит
    if len(spam_tracking[user_id]) > SPAM_LIMIT:
        # Очищаем историю спама, чтобы не замутить повторно мгновенно
        spam_tracking[user_id] = []
        
        try:
            # Даем мут
            duration = datetime.timedelta(minutes=MUTE_MINUTES)
            await message.author.timeout(duration, reason="AutoMod: Спам")
            
            # Удаляем спам-сообщения (необязательно, но полезно)
            # (Это удалит последние сообщения от пользователя в этом канале)
            await message.channel.purge(limit=SPAM_LIMIT, check=lambda m: m.author.id == user_id)
            
            embed = discord.Embed(title="🛡️ AutoMod", description=f"{message.author.mention} получил мут на {MUTE_MINUTES} мин. за спам.", color=0xDEA266)
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            print(f"Не удалось замутить спамера {message.author}")

#МУЗЫКА

@bot.tree.command(name="play", description="Играть с YouTube")
@app_commands.describe(query="Название или ссылка")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Зайди в канал!", ephemeral=True)

    await interaction.response.defer()

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if voice and voice.is_connected(): await voice.move_to(channel)
    else: voice = await channel.connect()

    def after_playing(error):
        coro = voice.disconnect()
        fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
        try: fut.result()
        except: pass

    try:
        player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
        if voice.is_playing(): voice.stop()
        
        # Запускаем воспроизведение через загруженный локально ffmpeg
        voice.play(player, after=after_playing)
        
        embed = discord.Embed(title="🎶 Играет", description=f"[{player.title}]({player.url})", color=0xDEA266)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")

@bot.tree.command(name="lofi", description="Lofi радио")
async def lofi(interaction: discord.Interaction):
    if not interaction.user.voice:
        return await interaction.response.send_message("❌ Зайди в канал!", ephemeral=True)

    await interaction.response.defer()
    
    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if voice and voice.is_connected(): await voice.move_to(channel)
    else: voice = await channel.connect()

    if voice.is_playing(): voice.stop()

    try:
        # Используем загруженный ffmpeg и здесь
        voice.play(discord.FFmpegPCMAudio("http://stream.zeno.fm/0r0xa854rp8uv", executable='./ffmpeg', **FFMPEG_OPTIONS))
        embed = discord.Embed(title="☕ Lofi Radio", description="Эфир запущен.", color=0xDEA266)
        await interaction.followup.send(embed=embed)
    except Exception as e:
        await interaction.followup.send(f"Ошибка: {e}")

@bot.tree.command(name="stop", description="Стоп")
async def stop(interaction: discord.Interaction):
    voice = interaction.guild.voice_client
    if voice and voice.is_connected():
        voice.stop()
        await voice.disconnect()
        await interaction.response.send_message("👋 Стоп.")
    else:
        await interaction.response.send_message("❌ Бот не в канале.", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Нет прав.", ephemeral=True)

# ------------------------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------------------------
if TOKEN:
    bot.run(TOKEN)
else:
    print("⛔ Ошибка: Токен не найден в .env файле!")

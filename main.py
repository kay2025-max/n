import discord
from discord.ext import commands
import asyncio
import random
import os
import json
import datetime
from typing import Dict, Any
from collections import defaultdict, deque

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True
bot = commands.Bot(command_prefix='g', intents=intents)

activity = discord.Streaming(
        name="Welcome GameHub VN",
        url="https://www.youtube.com/watch?si=k8w_-I5jc-L-mwxs&v=bJ_N6o6WRM4&feature=youtu.be" 
# Data storage
DATA_FILE = 'bot_data.json'
LEVEL_ANNOUNCE_CHANNEL = 1407953599085936691
LOG_CHANNEL =1407631967658180670 # Set this to your log channel ID
WELCOME_CHANNEL = 1407878136737173524  # Welcome channel ID
WELCOME_ROLE = 1407879478075461753     # Role to assign to new members

# Anti-spam tracking
user_join_times = defaultdict(deque)
SPAM_THRESHOLD = 5  # Max joins in time window
SPAM_WINDOW = 60  # Time window in seconds

# Load data
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            'users': {},
            'daily_checkins': {},
            'user_stats': {}
        }

# Save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Get user data
def get_user_data(user_id):
    data = load_data()
    if str(user_id) not in data['users']:
        data['users'][str(user_id)] = {
            'coins': 0,
            'level': 1,
            'xp': 0,
            'messages': 0,
            'games_won': 0,
            'games_played': 0
        }
        save_data(data)
    return data['users'][str(user_id)]

# Add XP and check level up
async def add_xp(user_id, xp_amount):
    data = load_data()
    user_data = get_user_data(user_id)
    user_data['xp'] += xp_amount

    # Level calculation (100 XP per level)
    new_level = user_data['xp'] // 100 + 1
    if new_level > user_data['level']:
        user_data['level'] = new_level
        data['users'][str(user_id)] = user_data
        save_data(data)

        # Announce level up
        channel = bot.get_channel(LEVEL_ANNOUNCE_CHANNEL)
        if channel:
            user = bot.get_user(user_id)
            embed = discord.Embed(
                title="🎉 Level Up!",
                description=f"{user.mention} đã lên level {new_level}!",
                color=0x00ff00
            )
            await channel.send(embed=embed)
    else:
        data['users'][str(user_id)] = user_data
        save_data(data)

@bot.event
async def on_ready():
    print(f'{bot.user} đã sẵn sàng!')

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Add XP for messages
    await add_xp(message.author.id, 5)

    # Update message count
    data = load_data()
    user_data = get_user_data(message.author.id)
    user_data['messages'] += 1
    data['users'][str(message.author.id)] = user_data
    save_data(data)

    await bot.process_commands(message)

# Daily check-in
@bot.command(name='daily')
async def daily_checkin(ctx):
    user_id = str(ctx.author.id)
    today = datetime.date.today().isoformat()

    data = load_data()

    if user_id in data['daily_checkins'] and data['daily_checkins'][user_id] == today:
        embed = discord.Embed(
            title="🚫 ĐÃ NHẬN THƯỞNG HÔM NAY",
            description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                       "⏰ **Bạn đã check-in hôm nay rồi!**\n"
                       "🌅 **Quay lại vào ngày mai để nhận thưởng**\n"
                       "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0xFF6B6B
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/692028638932959302.png")
        embed.add_field(name="⏳ Thời gian còn lại", value="Đếm ngược đến 00:00 ngày mai", inline=False)
        embed.set_footer(text="💎 Hãy chơi game để kiếm thêm vàng!", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)
        return

    # Give daily coins (50-150 random)
    coins_earned = random.randint(50, 150)
    user_data = get_user_data(ctx.author.id)
    user_data['coins'] += coins_earned

    data['users'][user_id] = user_data
    data['daily_checkins'][user_id] = today
    save_data(data)

    # Determine reward tier
    if coins_earned >= 130:
        tier = "🌟 SIÊU PHẨM"
        tier_color = 0xFFD700
    elif coins_earned >= 100:
        tier = "💎 HIẾM"
        tier_color = 0x9B59B6
    else:
        tier = "✨ THƯỜNG"
        tier_color = 0x3498DB

    embed = discord.Embed(
        title="🎁 CHECK-IN THÀNH CÔNG!",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎉 **Chúc mừng {ctx.author.display_name}!**\n"
                   f"💰 **+{coins_earned} vàng** {tier}\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=tier_color
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/812499369077137428.gif")

    embed.add_field(
        name="💎 Tổng vàng hiện tại",
        value=f"```yaml\n{user_data['coins']:,} vàng```",
        inline=True
    )

    embed.add_field(
        name="📊 Streak Daily",
        value="```yaml\n🔥 Duy trì hàng ngày```",
        inline=True
    )

    embed.add_field(
        name="🎮 Gợi ý",
        value="Chơi **!guess**, **!rps**, **!trivia** để kiếm thêm vàng!",
        inline=False
    )

    embed.set_footer(text="🎪 Game Hub - Quay lại vào ngày mai nhé!", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# Number guessing game
@bot.command(name='guess')
async def guess_number(ctx):
    number = random.randint(1, 100)
    embed = discord.Embed(
        title="🎯 ĐOÁN SỐ THẦN TỐC",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎪 **Chào mừng {ctx.author.display_name}!**\n"
                   "🎲 **Tôi đang nghĩ về một số từ 1 → 100**\n"
                   "⚡ **Bạn có 5 lần đoán trong 30 giây!**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0xFF6B35
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/853929877616525312.gif")
    embed.add_field(name="🏆 Phần thưởng", value="```yaml\n💰 50 vàng + 25 XP```", inline=True)
    embed.add_field(name="⏱️ Thời gian", value="```yaml\n⏰ 30 giây```", inline=True)
    embed.set_footer(text="🎮 Gõ số để bắt đầu!", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

    start_message = await ctx.send(embed=embed)

    attempts = 0
    max_attempts = 5
    start_time = datetime.datetime.utcnow()

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    while attempts < max_attempts:
        try:
            # Calculate remaining time
            elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
            remaining_time = max(0, 30 - elapsed)

            if remaining_time <= 0:
                break

            msg = await bot.wait_for('message', check=check, timeout=remaining_time)
            guess = int(msg.content)
            attempts += 1

            # Calculate time for display
            elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()
            remaining_time = max(0, 30 - elapsed)

            if guess == number:
                # Win
                coins_won = 50
                user_data = get_user_data(ctx.author.id)
                user_data['coins'] += coins_won
                user_data['games_won'] += 1
                user_data['games_played'] += 1

                data = load_data()
                data['users'][str(ctx.author.id)] = user_data
                save_data(data)

                await add_xp(ctx.author.id, 25)

                embed = discord.Embed(
                    title="🎉 CHIẾN THẮNG HOÀN HẢO!",
                    description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                               f"🔥 **{ctx.author.display_name} đã đoán đúng!**\n"
                               f"🎯 **Số bí mật: {number}**\n"
                               f"⚡ **Lần đoán thứ: {attempts}/5**\n"
                               f"⏱️ **Thời gian: {elapsed:.1f}s**\n"
                               "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                    color=0x00FF7F
                )
                embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/819142087696769044.gif")
                embed.add_field(name="💰 Phần thưởng", value=f"```yaml\n+{coins_won} vàng\n+25 XP```", inline=True)
                embed.add_field(name="📊 Thống kê", value=f"```yaml\nTỷ lệ thành công: {(user_data['games_won']/user_data['games_played']*100):.1f}%```", inline=True)
                embed.set_footer(text="🎪 Chơi tiếp để leo bảng xếp hạng!", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
                await ctx.send(embed=embed)
                return
            elif guess < number:
                hint_embed = discord.Embed(
                    title="📈 SỐ NHỎ HƠN!",
                    description=f"🔼 **Số {guess} nhỏ hơn số bí mật**\n"
                               f"🎯 **Còn {max_attempts - attempts} lần đoán**\n"
                               f"⏱️ **Còn {remaining_time:.0f} giây**",
                    color=0xFFA500
                )
                await ctx.send(embed=hint_embed)
            else:
                hint_embed = discord.Embed(
                    title="📉 SỐ LỚN HƠN!",
                    description=f"🔽 **Số {guess} lớn hơn số bí mật**\n"
                               f"🎯 **Còn {max_attempts - attempts} lần đoán**\n"
                               f"⏱️ **Còn {remaining_time:.0f} giây**",
                    color=0xFFA500
                )
                await ctx.send(embed=hint_embed)

        except ValueError:
            error_embed = discord.Embed(
                title="❌ LỖI NHẬP LIỆU",
                description="🔢 **Vui lòng nhập một số hợp lệ từ 1-100!**",
                color=0xFF4444
            )
            await ctx.send(embed=error_embed)
        except asyncio.TimeoutError:
            break

    # Game over
    user_data = get_user_data(ctx.author.id)
    user_data['games_played'] += 1
    data = load_data()
    data['users'][str(ctx.author.id)] = user_data
    save_data(data)

    embed = discord.Embed(
        title="💀 GAME OVER",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"⏰ **Hết thời gian hoặc hết lượt đoán!**\n"
                   f"🎯 **Số bí mật là: {number}**\n"
                   f"🎮 **Lần đoán đã dùng: {attempts}/5**\n"
                   "🔥 **Chúc bạn may mắn lần sau!**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0xFF6B6B
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/765298986428850206.png")
    embed.set_footer(text="🎪 Thử lại với !guess", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# Rock Paper Scissors
@bot.command(name='rps')
async def rock_paper_scissors(ctx, choice=None):
    if not choice:
        embed = discord.Embed(
            title="✂️ OẲN TÙ TÌ - HƯỚNG DẪN",
            description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                       "🎮 **Cách chơi:**\n"
                       "```yaml\n"
                       "!rps búa     - Búa đập kéo\n"
                       "!rps bao     - Bao gói búa\n"
                       "!rps kéo     - Kéo cắt bao\n"
                       "```\n"
                       "🏆 **Phần thưởng:** +30 vàng nếu thắng\n"
                       "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0x3498DB
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/788120095034671104.gif")
        await ctx.send(embed=embed)
        return

    choices = {
        'rock': 'búa', 'búa': '🔨', 'bua': '🔨',
        'paper': 'bao', 'bao': '📜', 'giay': '📜',
        'scissors': 'kéo', 'kéo': '✂️', 'keo': '✂️'
    }

    choice_names = {
        'rock': 'búa', 'búa': 'búa', 'bua': 'búa',
        'paper': 'bao', 'bao': 'bao', 'giay': 'bao',
        'scissors': 'kéo', 'kéo': 'kéo', 'keo': 'kéo'
    }

    if choice.lower() not in choices:
        embed = discord.Embed(
            title="❌ LỰA CHỌN KHÔNG HỢP LỆ",
            description="🎯 **Sử dụng:** `!rps [búa/bao/kéo]`",
            color=0xFF6B6B
        )
        await ctx.send(embed=embed)
        return

    user_choice = choice_names[choice.lower()]
    user_emoji = choices[choice.lower()]
    bot_choice = random.choice(['búa', 'bao', 'kéo'])
    bot_emoji = {'búa': '🔨', 'bao': '📜', 'kéo': '✂️'}[bot_choice]

    # Determine winner
    if user_choice == bot_choice:
        result = "🤝 HÒA!"
        coins_change = 0
        color = 0xFFD700
        result_desc = "Cả hai cùng chọn giống nhau!"
    elif (user_choice == 'búa' and bot_choice == 'kéo') or \
         (user_choice == 'bao' and bot_choice == 'búa') or \
         (user_choice == 'kéo' and bot_choice == 'bao'):
        result = "🎉 BẠN THẮNG!"
        coins_change = 30
        color = 0x00FF7F
        result_desc = f"{user_choice.title()} đánh bại {bot_choice}!"

        user_data = get_user_data(ctx.author.id)
        user_data['games_won'] += 1
    else:
        result = "💀 BẠN THUA!"
        coins_change = -10
        color = 0xFF6B6B
        result_desc = f"{bot_choice.title()} đánh bại {user_choice}!"

    # Update user data
    user_data = get_user_data(ctx.author.id)
    user_data['coins'] += coins_change
    user_data['games_played'] += 1

    data = load_data()
    data['users'][str(ctx.author.id)] = user_data
    save_data(data)

    if coins_change > 0:
        await add_xp(ctx.author.id, 15)

    embed = discord.Embed(
        title="✂️ KẾT QUẢ OẲN TÙ TÌ",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎪 **{ctx.author.display_name} vs Game Hub Bot**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=color
    )

    embed.add_field(
        name="👤 Bạn chọn",
        value=f"```yaml\n{user_emoji} {user_choice.upper()}```",
        inline=True
    )

    embed.add_field(
        name="🤖 Bot chọn", 
        value=f"```yaml\n{bot_emoji} {bot_choice.upper()}```",
        inline=True
    )

    embed.add_field(
        name="🏆 Kết quả",
        value=f"```yaml\n{result}```",
        inline=False
    )

    embed.add_field(
        name="📖 Diễn biến",
        value=result_desc,
        inline=False
    )

    if coins_change != 0:
        sign = '+' if coins_change > 0 else ''
        embed.add_field(
            name="💰 Thay đổi vàng",
            value=f"```yaml\n{sign}{coins_change} vàng```",
            inline=True
        )

    embed.add_field(
        name="💎 Tổng vàng",
        value=f"```yaml\n{user_data['coins']:,} vàng```",
        inline=True
    )

    embed.set_footer(text="🎮 Chơi lại với !rps [búa/bao/kéo]", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    await ctx.send(embed=embed)

# Trivia Quiz
trivia_questions = [
    {"question": "Thủ đô của Việt Nam là gì?", "answer": "hà nội"},
    {"question": "Ai là người phát minh ra bóng đèn?", "answer": "thomas edison"},
    {"question": "Hành tinh nào gần Mặt Trời nhất?", "answer": "sao thủy"},
    {"question": "1 + 1 = ?", "answer": "2"},
    {"question": "Con vật nào được gọi là vua của rừng?", "answer": "sư tử"},
    {"question": "Nước nào có hình dáng giống chiếc ủng?", "answer": "ý"},
    {"question": "Ngôn ngữ lập trình nào có logo là con rắn?", "answer": "python"},
]

@bot.command(name='trivia')
async def trivia_quiz(ctx):
    question_data = random.choice(trivia_questions)

    embed = discord.Embed(
        title="🧠 TRIVIA QUIZ - THÁCH THỨC TRÍ TUỆ",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎪 **Chào mừng {ctx.author.display_name}!**\n"
                   f"❓ **{question_data['question']}**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0x9932CC
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/853626873862701067.gif")
    embed.add_field(name="🏆 Phần thưởng", value="```yaml\n💰 40 vàng + 20 XP```", inline=True)
    embed.add_field(name="⏱️ Thời gian", value="```yaml\n⏰ 15 giây```", inline=True)
    embed.set_footer(text="🎮 Gõ đáp án để trả lời!", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

    start_message = await ctx.send(embed=embed)
    start_time = datetime.datetime.utcnow()

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        # Create countdown task
        countdown_task = asyncio.create_task(countdown_timer(ctx, 15))

        msg = await bot.wait_for('message', check=check, timeout=15.0)
        countdown_task.cancel()  # Stop countdown when answer received

        # Calculate response time
        elapsed = (datetime.datetime.utcnow() - start_time).total_seconds()

        if msg.content.lower().strip() == question_data['answer']:
            coins_won = 40
            # Bonus for fast answer
            if elapsed < 5:
                coins_won += 10
                speed_bonus = "⚡ Tốc độ siêu nhanh +10 vàng!"
            elif elapsed < 10:
                coins_won += 5
                speed_bonus = "🔥 Phản xạ nhanh +5 vàng!"
            else:
                speed_bonus = ""

            user_data = get_user_data(ctx.author.id)
            user_data['coins'] += coins_won
            user_data['games_won'] += 1
            user_data['games_played'] += 1

            data = load_data()
            data['users'][str(ctx.author.id)] = user_data
            save_data(data)

            await add_xp(ctx.author.id, 20)

            embed = discord.Embed(
                title="🎉 CHÍNH XÁC TUYỆT ĐỐI!",
                description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                           f"🧠 **{ctx.author.display_name} thông minh quá!**\n"
                           f"✅ **Đáp án đúng: {question_data['answer']}**\n"
                           f"⏱️ **Thời gian phản xử: {elapsed:.1f}s**\n"
                           f"{speed_bonus}\n"
                           "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=0x00FF7F
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/819142087696769044.gif")
            embed.add_field(name="💰 Phần thưởng", value=f"```yaml\n+{coins_won} vàng\n+20 XP```", inline=True)
            embed.add_field(name="📊 Thống kê", value=f"```yaml\nTỷ lệ thành công: {(user_data['games_won']/user_data['games_played']*100):.1f}%```", inline=True)
        else:
            user_data = get_user_data(ctx.author.id)
            user_data['games_played'] += 1

            data = load_data()
            data['users'][str(ctx.author.id)] = user_data
            save_data(data)

            embed = discord.Embed(
                title="❌ SAI RỒI!",
                description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                           f"💭 **Đáp án của bạn: {msg.content}**\n"
                           f"✅ **Đáp án đúng: {question_data['answer']}**\n"
                           f"⏱️ **Thời gian: {elapsed:.1f}s**\n"
                           "🔥 **Chúc bạn may mắn lần sau!**\n"
                           "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                color=0xFF6B6B
            )
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/765298986428850206.png")

        embed.set_footer(text="🎪 Chơi tiếp với !trivia", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

    except asyncio.TimeoutError:
        user_data = get_user_data(ctx.author.id)
        user_data['games_played'] += 1
        data = load_data()
        data['users'][str(ctx.author.id)] = user_data
        save_data(data)

        embed = discord.Embed(
            title="⏰ HẾT THỜI GIAN!",
            description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                       f"💭 **Câu hỏi: {question_data['question']}**\n"
                       f"✅ **Đáp án đúng: {question_data['answer']}**\n"
                       "⚡ **Hãy nhanh tay hơn lần sau!**\n"
                       "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            color=0xFF6B6B
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/765298986428850206.png")
        embed.set_footer(text="🎪 Thử lại với !trivia", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
        await ctx.send(embed=embed)

async def countdown_timer(ctx, seconds):
    """Display countdown timer for trivia"""
    try:
        for i in range(seconds, 0, -5):
            if i <= 10:
                await asyncio.sleep(1)
                if i <= 5:
                    countdown_embed = discord.Embed(
                        title=f"⏰ {i} GIÂY!",
                        description="🔥 **Nhanh lên!**",
                        color=0xFF4444
                    )
                    await ctx.send(embed=countdown_embed, delete_after=1)
            else:
                await asyncio.sleep(5)
    except asyncio.CancelledError:
        pass

# Leaderboards
@bot.command(name='leaderboard', aliases=['lb', 'top'])
async def leaderboard(ctx, category='coins'):
    data = load_data()
    users = data['users']

    if category.lower() in ['coins', 'xu', 'vang', 'gold']:
        sorted_users = sorted(users.items(), key=lambda x: x[1]['coins'], reverse=True)
        title = "💰 BẢNG XẾP HẠNG VÀNG"
        value_key = 'coins'
        suffix = " vàng"
        emoji = "💰"
        color = 0xFFD700
    elif category.lower() in ['level', 'lv']:
        sorted_users = sorted(users.items(), key=lambda x: x[1]['level'], reverse=True)
        title = "📊 BẢNG XẾP HẠNG LEVEL"
        value_key = 'level'
        suffix = ""
        emoji = "⭐"
        color = 0x9B59B6
    elif category.lower() in ['messages', 'chat', 'msg']:
        sorted_users = sorted(users.items(), key=lambda x: x[1]['messages'], reverse=True)
        title = "💬 BẢNG XẾP HẠNG CHAT"
        value_key = 'messages'
        suffix = " tin nhắn"
        emoji = "💬"
        color = 0x3498DB
    else:
        error_embed = discord.Embed(
            title="❌ DANH MỤC KHÔNG HỢP LỆ",
            description="🎯 **Sử dụng:** `!leaderboard [vang/level/chat]`\n"
                       "💰 `vang` - Xếp hạng theo vàng\n"
                       "📊 `level` - Xếp hạng theo cấp độ\n"
                       "💬 `chat` - Xếp hạng theo tin nhắn",
            color=0xFF6B6B
        )
        await ctx.send(embed=error_embed)
        return

    embed = discord.Embed(
        title=title,
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   "🎪 **TOP 10 THÀNH VIÊN XUẤT SẮC NHẤT**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=color
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/812499369077137428.gif")

    if not sorted_users:
        embed.add_field(
            name="📭 Trống",
            value="Chưa có dữ liệu để hiển thị",
            inline=False
        )
    else:
        leaderboard_text = ""
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, user_data) in enumerate(sorted_users[:10]):
            try:
                user = bot.get_user(int(user_id))
                name = user.display_name if user else f"User {user_id}"

                # Truncate long names
                if len(name) > 15:
                    name = name[:12] + "..."

                # Medal or ranking
                if i < 3:
                    rank_emoji = medals[i]
                else:
                    rank_emoji = f"`{i+1:2d}.`"

                # Format value with commas for large numbers
                value = f"{user_data[value_key]:,}{suffix}"

                leaderboard_text += f"{rank_emoji} **{name}** - {emoji} {value}\n"

            except Exception as e:
                continue

        if leaderboard_text:
            embed.add_field(
                name="🏆 BẢNG XẾP HẠNG",
                value=leaderboard_text,
                inline=False
            )

    # Add statistics
    total_users = len(users)
    if category.lower() in ['coins', 'xu', 'vang', 'gold']:
        total_coins = sum(user_data.get('coins', 0) for user_data in users.values())
        avg_coins = total_coins / total_users if total_users > 0 else 0
        embed.add_field(
            name="📈 Thống kê",
            value=f"👥 **Tổng thành viên:** {total_users}\n"
                  f"💰 **Tổng vàng:** {total_coins:,}\n"
                  f"📊 **Trung bình:** {avg_coins:.0f} vàng",
            inline=True
        )

    # Show user's position
    user_position = None
    for i, (user_id, user_data) in enumerate(sorted_users):
        if int(user_id) == ctx.author.id:
            user_position = i + 1
            user_value = user_data[value_key]
            break

    if user_position:
        embed.add_field(
            name="🎯 Vị trí của bạn",
            value=f"**#{user_position}** - {emoji} {user_value:,}{suffix}",
            inline=True
        )

    embed.set_footer(
        text="🎪 Chơi game để leo rank! | !daily để nhận vàng",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )

    await ctx.send(embed=embed)

# Profile command
@bot.command(name='profile', aliases=['p'])
async def profile(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    user_data = get_user_data(member.id)

    # Calculate additional stats
    next_level_xp = (user_data['level']) * 100
    current_level_xp = user_data['xp'] - ((user_data['level'] - 1) * 100)
    xp_progress = current_level_xp / 100 * 100 if user_data['level'] > 1 else user_data['xp']

    # Determine profile color based on level
    if user_data['level'] >= 10:
        color = 0xFF6B35  # Orange for high level
    elif user_data['level'] >= 5:
        color = 0x9B59B6  # Purple for mid level
    else:
        color = 0x3498DB  # Blue for low level

    embed = discord.Embed(
        title=f"👑 PROFILE - {member.display_name}",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"🎪 **Thông tin chi tiết của {member.mention}**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=color
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    # Main stats - Row 1
    embed.add_field(
        name="💰 Vàng",
        value=f"```yaml\n{user_data['coins']:,} 💰```",
        inline=True
    )
    embed.add_field(
        name="⭐ Level",
        value=f"```yaml\n{user_data['level']} ⭐```",
        inline=True
    )
    embed.add_field(
        name="✨ Kinh nghiệm",
        value=f"```yaml\n{user_data['xp']:,} XP```",
        inline=True
    )

    # Progress bar for XP
    progress_bar_length = 10
    filled = int(xp_progress / 100 * progress_bar_length)
    empty = progress_bar_length - filled
    progress_bar = "█" * filled + "░" * empty

    embed.add_field(
        name="📊 Tiến độ Level",
        value=f"```yaml\n{progress_bar} {xp_progress:.0f}%\n{current_level_xp}/100 XP đến level {user_data['level'] + 1}```",
        inline=False
    )

    # Activity stats - Row 2
    embed.add_field(
        name="💬 Hoạt động",
        value=f"```yaml\n{user_data['messages']:,} tin nhắn```",
        inline=True
    )
    embed.add_field(
        name="🎮 Game thắng",
        value=f"```yaml\n{user_data['games_won']:,} trận```",
        inline=True
    )
    embed.add_field(
        name="🎯 Tổng game",
        value=f"```yaml\n{user_data['games_played']:,} trận```",
        inline=True
    )

    # Win rate and achievements
    if user_data['games_played'] > 0:
        win_rate = (user_data['games_won'] / user_data['games_played']) * 100
        if win_rate >= 70:
            skill_level = "🏆 Cao thủ"
        elif win_rate >= 50:
            skill_level = "⚔️ Thiện chiến"
        elif win_rate >= 30:
            skill_level = "🎯 Khá ổn"
        else:
            skill_level = "🌱 Tập luyện"

        embed.add_field(
            name="📈 Tỷ lệ thắng",
            value=f"```yaml\n{win_rate:.1f}% - {skill_level}```",
            inline=True
        )
    else:
        embed.add_field(
            name="📈 Tỷ lệ thắng",
            value="```yaml\nChưa chơi game nào```",
            inline=True
        )

    # Achievements/Badges
    badges = []
    if user_data['level'] >= 10:
        badges.append("🌟 Level Master")
    if user_data['coins'] >= 1000:
        badges.append("💎 Tỷ phú")
    if user_data['games_won'] >= 50:
        badges.append("🏆 Game Pro")
    if user_data['messages'] >= 100:
        badges.append("💬 Talkative")
    if not badges:
        badges.append("🌱 Newbie")

    embed.add_field(
        name="🏅 Thành tích",
        value=" ".join(badges),
        inline=True
    )

    # Ranking info
    data = load_data()
    users = data['users']

    # Get coin ranking
    sorted_by_coins = sorted(users.items(), key=lambda x: x[1]['coins'], reverse=True)
    coin_rank = next((i+1 for i, (uid, _) in enumerate(sorted_by_coins) if int(uid) == member.id), "N/A")

    # Get level ranking  
    sorted_by_level = sorted(users.items(), key=lambda x: x[1]['level'], reverse=True)
    level_rank = next((i+1 for i, (uid, _) in enumerate(sorted_by_level) if int(uid) == member.id), "N/A")

    embed.add_field(
        name="🏆 Xếp hạng",
        value=f"💰 Vàng: **#{coin_rank}**\n⭐ Level: **#{level_rank}**",
        inline=True
    )

    # Member info
    days_since_join = (datetime.datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days if member.joined_at else 0
    embed.add_field(
        name="📅 Thông tin thành viên",
        value=f"📥 Tham gia: {days_since_join} ngày trước\n"
              f"🆔 ID: {member.id}",
        inline=False
    )

    embed.set_footer(
        text="🎪 Game Hub - Chơi game để tăng stats! | !daily để nhận vàng",
        icon_url=member.avatar.url if member.avatar else member.default_avatar.url
    )

    await ctx.send(embed=embed)

# User info command
@bot.command(name='userinfo', aliases=['ui'])
async def user_info(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    # Use member's color if they have one, otherwise use a nice default
    embed_color = member.color if member.color != discord.Color.default() else 0x3498DB

    embed = discord.Embed(
        title=f"🔍 THÔNG TIN CHI TIẾT",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"👤 **Hồ sơ của {member.display_name}**\n"
                   "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=embed_color
    )
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

    # Basic info section
    embed.add_field(
        name="👤 Thông tin cơ bản",
        value=f"```yaml\n"
              f"Tên: {member.name}#{member.discriminator}\n"
              f"Biệt danh: {member.display_name}\n"
              f"ID: {member.id}\n"
              f"Bot: {'Có' if member.bot else 'Không'}\n"
              f"```",
        inline=False
    )

    # Account dates
    account_age = (datetime.datetime.utcnow() - member.created_at.replace(tzinfo=None)).days
    embed.add_field(
        name="📅 Thời gian",
        value=f"```yaml\n"
              f"Tạo tài khoản: {member.created_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
              f"Tuổi tài khoản: {account_age} ngày\n"
              f"```",
        inline=True
    )

    # Server info
    if member.joined_at:
        days_in_server = (datetime.datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days
        embed.add_field(
            name="🏠 Trong server",
            value=f"```yaml\n"
                  f"Tham gia: {member.joined_at.strftime('%d/%m/%Y %H:%M:%S')}\n"
                  f"Đã ở đây: {days_in_server} ngày\n"
                  f"```",
            inline=True
        )

    # Status and activity
    status_emoji = {
        discord.Status.online: "🟢 Trực tuyến",
        discord.Status.idle: "🟡 Rảnh rỗi", 
        discord.Status.dnd: "🔴 Đừng làm phiền",
        discord.Status.offline: "⚫ Ngoại tuyến"
    }

    status_text = status_emoji.get(member.status, "❓ Không rõ")

    embed.add_field(
        name="📶 Trạng thái",
        value=f"```yaml\n{status_text}```",
        inline=True
    )

    # Permissions
    permission_level = "👤 Thành viên"
    if member.guild_permissions.administrator:
        permission_level = "👑 Administrator"
    elif member.guild_permissions.manage_guild:
        permission_level = "⚔️ Quản lý Server"
    elif member.guild_permissions.manage_messages:
        permission_level = "🛡️ Moderator"
    elif member.guild_permissions.kick_members or member.guild_permissions.ban_members:
        permission_level = "🔨 Staff"

    embed.add_field(
        name="🔑 Quyền hạn",
        value=f"```yaml\n{permission_level}```",
        inline=True
    )

    # Server stats
    member_count = len(member.guild.members)
    join_position = sorted(member.guild.members, key=lambda m: m.joined_at or datetime.datetime.min).index(member) + 1 if member.joined_at else "N/A"

    embed.add_field(
        name="📊 Thống kê server",
        value=f"```yaml\n"
              f"Thành viên thứ: #{join_position}\n"
              f"Tổng thành viên: {member_count}\n"
              f"```",
        inline=True
    )

    # Roles
    if len(member.roles) > 1:  # Exclude @everyone
        roles = [role.mention for role in reversed(member.roles[1:])]

        # Group roles for better display
        if len(roles) <= 15:
            role_text = " ".join(roles)
        else:
            role_text = " ".join(roles[:15]) + f"\n**+{len(roles) - 15} role khác...**"

        embed.add_field(
            name=f"🎭 Roles ({len(member.roles) - 1})",
            value=role_text,
            inline=False
        )
    else:
        embed.add_field(
            name="🎭 Roles",
            value="```yaml\nChỉ có @everyone```",
            inline=False
        )

    # Avatar info
    embed.add_field(
        name="🖼️ Avatar",
        value=f"[Xem avatar]({member.avatar.url if member.avatar else member.default_avatar.url})",
        inline=True
    )

    # Additional info for bots
    if member.bot:
        embed.add_field(
            name="🤖 Thông tin Bot",
            value="```yaml\nĐây là một Discord Bot```",
            inline=True
        )

    embed.set_footer(
        text=f"🎪 Game Hub - Thông tin được yêu cầu bởi {ctx.author.display_name}",
        icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url
    )

    await ctx.send(embed=embed)

# Help command
@bot.command(name='help_bot', aliases=['commands'])
async def help_command(ctx):
    embed = discord.Embed(
        title="🌟 GAME HUB - HƯỚNG DẪN SỬ DỤNG 🌟",
        description="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n✨ **Khám phá thế giới giải trí tuyệt vời!** ✨\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=0xFFD700
    )
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/894912734729777182.gif")

    embed.add_field(
        name="🎮 **MINI GAMES**",
        value="```yaml\n"
              "🎯 !guess    : Đoán số từ 1-100 (30s)\n"
              "✂️ !rps      : Oẳn tù tì với bot\n"
              "🧠 !trivia   : Trả lời câu hỏi kiến thức\n"
              "```",
        inline=False
    )

    embed.add_field(
        name="💎 **HỆ THỐNG THƯỞNG**",
        value="```yaml\n"
              "🎁 !daily    : Nhận vàng miễn phí hàng ngày\n"
              "👤 !profile  : Xem thông tin cá nhân\n"
              "🏆 !leaderboard: Bảng xếp hạng server\n"
              "ℹ️ !userinfo : Chi tiết thành viên\n"
              "```",
        inline=False
    )

    embed.add_field(
        name="🎯 **CÁCH CHƠI**",
        value="• 💬 **Chat** để nhận XP và tăng level\n"
              "• 🎮 **Chơi game** để kiếm vàng và XP\n"
              "• 📈 **Level up** mỗi 100 XP\n"
              "• 🏅 **Cạnh tranh** trên bảng xếp hạng",
        inline=False
    )

    embed.add_field(
        name="💰 **PHẦN THƯỞNG**",
        value="🥇 **Daily**: 50-150 vàng\n🎯 **Guess**: 50 vàng\n✂️ **RPS**: 30 vàng\n🧠 **Trivia**: 40 vàng",
        inline=True
    )

    embed.add_field(
        name="⚡ **XP THƯỞNG**",
        value="💬 **Chat**: 5 XP\n🎮 **Game Win**: 15-25 XP\n📊 **Level Up**: Thông báo công khai",
        inline=True
    )

    embed.set_footer(text="🎪 Game Hub - Nơi giải trí không giới hạn! 🎪", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)

    await ctx.send(embed=embed)

# Anti-spam detection and logging events
async def log_activity(embed):
    """Send log to designated channel"""
    if LOG_CHANNEL:
        channel = bot.get_channel(LOG_CHANNEL)
        if channel:
            await channel.send(embed=embed)

@bot.event
async def on_member_join(member):
    """Anti-spam detection and log member joins"""
    guild_id = member.guild.id
    current_time = datetime.datetime.utcnow()

    # Add join time to tracking
    user_join_times[guild_id].append(current_time)

    # Remove old entries outside the spam window
    cutoff_time = current_time - datetime.timedelta(seconds=SPAM_WINDOW)
    while user_join_times[guild_id] and user_join_times[guild_id][0] < cutoff_time:
        user_join_times[guild_id].popleft()

    # Check for spam
    if len(user_join_times[guild_id]) >= SPAM_THRESHOLD:
        # Potential bot spam detected
        if member.bot:
            try:
                await member.kick(reason="Bot spam detected")
                embed = discord.Embed(
                    title="🚫 Bot Spam Detected",
                    description=f"Kicked bot {member.mention} ({member.id}) for potential spam",
                    color=0xff0000
                )
                await log_activity(embed)
                return
            except discord.Forbidden:
                pass

    # Log member join
    embed = discord.Embed(
        title="📥 Member Joined",
        description=f"{member.mention} ({member.name}#{member.discriminator})",
        color=0x00ff00
    )
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Account Created", value=member.created_at.strftime("%d/%m/%Y %H:%M:%S"), inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await log_activity(embed)

    # Send welcome message
    welcome_channel = bot.get_channel(WELCOME_CHANNEL)
    if welcome_channel:
        # Give new member starter cash
        user_data = get_user_data(member.id)
        starter_cash = 100
        user_data['coins'] += starter_cash
        data = load_data()
        data['users'][str(member.id)] = user_data
        save_data(data)

        # Create welcome embed
        welcome_embed = discord.Embed(
            title="🎊 Welcome GameHub VN",
            description=f"🌟 **Chào mừng {member.mention} gia nhập GameHub!**\n"
                       f"💰 **Quà tặng:** +{starter_cash} vàng khởi đầu\n"
                       f"🎮 **Khám phá:** `!daily` `!guess` `!rps` `!trivia`",
            color=0xFF6B35
        )
        welcome_embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        welcome_embed.add_field(
            name="🎯 Thành viên", 
            value=f"#{len(member.guild.members)}", 
            inline=True
        )
        welcome_embed.add_field(
            name="💎 Vàng hiện tại", 
            value=f"{user_data['coins']} 🪙", 
            inline=True
        )

        if welcome_role:
            welcome_embed.add_field(
                name="🎭 Role", 
                value=welcome_role.mention, 
                inline=True
            )

        welcome_embed.set_footer(text="GameHub VN - Nơi giải trí số 1! 🎪")

        try:
            # Send welcome message with role tag
            message_content = f"{welcome_role.mention}" if welcome_role else ""
            await welcome_channel.send(content=message_content, embed=welcome_embed)
        except discord.Forbidden:
            print(f"Không thể gửi tin nhắn chào mừng tới kênh {welcome_channel.name}")

@bot.event
async def on_member_remove(member):
    """Log member leaves"""
    embed = discord.Embed(
        title="📤 Member Left",
        description=f"{member.name}#{member.discriminator}",
        color=0xff9900
    )
    embed.add_field(name="ID", value=member.id, inline=True)
    if member.joined_at:
        days_in_server = (datetime.datetime.utcnow() - member.joined_at.replace(tzinfo=None)).days
        embed.add_field(name="Days in Server", value=days_in_server, inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await log_activity(embed)

@bot.event
async def on_voice_state_update(member, before, after):
    """Log voice channel activity"""
    if before.channel != after.channel:
        if after.channel:  # Joined voice
            embed = discord.Embed(
                title="🔊 Voice Channel Joined",
                description=f"{member.mention} joined {after.channel.name}",
                color=0x00ff00
            )
        elif before.channel:  # Left voice
            embed = discord.Embed(
                title="🔇 Voice Channel Left",
                description=f"{member.mention} left {before.channel.name}",
                color=0xff9900
            )
        else:
            return

        embed.add_field(name="User", value=f"{member.name}#{member.discriminator}", inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        await log_activity(embed)

@bot.event
async def on_guild_channel_create(channel):
    """Log channel creation"""
    embed = discord.Embed(
        title="➕ Channel Created",
        description=f"Channel {channel.mention} was created",
        color=0x00ff00
    )
    embed.add_field(name="Name", value=channel.name, inline=True)
    embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
    embed.add_field(name="ID", value=channel.id, inline=True)
    await log_activity(embed)

@bot.event
async def on_guild_channel_delete(channel):
    """Log channel deletion"""
    embed = discord.Embed(
        title="➖ Channel Deleted",
        description=f"Channel #{channel.name} was deleted",
        color=0xff0000
    )
    embed.add_field(name="Type", value=str(channel.type).title(), inline=True)
    embed.add_field(name="ID", value=channel.id, inline=True)
    await log_activity(embed)

@bot.event
async def on_guild_channel_update(before, after):
    """Log channel name changes"""
    if before.name != after.name:
        embed = discord.Embed(
            title="✏️ Channel Renamed",
            description=f"Channel renamed from #{before.name} to {after.mention}",
            color=0x0099ff
        )
        embed.add_field(name="ID", value=after.id, inline=True)
        await log_activity(embed)

@bot.event
async def on_member_update(before, after):
    """Log username changes"""
    if before.name != after.name or before.discriminator != after.discriminator:
        embed = discord.Embed(
            title="👤 Username Changed",
            description=f"{before.name}#{before.discriminator} → {after.name}#{after.discriminator}",
            color=0x0099ff
        )
        embed.add_field(name="User", value=after.mention, inline=True)
        embed.add_field(name="ID", value=after.id, inline=True)
        embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)
        await log_activity(embed)

@bot.event
async def on_message_delete(message):
    """Log message deletions"""
    if message.author.bot:
        return

    embed = discord.Embed(
        title="🗑️ Message Deleted",
        description=f"Message by {message.author.mention} deleted in {message.channel.mention}",
        color=0xff0000
    )

    if message.content:
        content = message.content[:1000] + "..." if len(message.content) > 1000 else message.content
        embed.add_field(name="Content", value=f"```{content}```", inline=False)

    embed.add_field(name="Author", value=f"{message.author.name}#{message.author.discriminator}", inline=True)
    embed.add_field(name="Channel", value=message.channel.name, inline=True)
    embed.add_field(name="ID", value=message.id, inline=True)
    embed.set_thumbnail(url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url)
    await log_activity(embed)

import os
 bot.run(os.getenv("DISCORD_TOKEN"))

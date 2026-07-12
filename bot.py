import discord
from discord import app_commands
import os
import random
import json
import asyncio
import math
from aiohttp import web

# ===== KEEP ALIVE =====
async def keep_alive():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Lekklir Bot is alive!"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

# ===== CONFIG =====
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
BALANCE_FILE = "balance.json"
FIGHTERS_FILE = "fighters.json"
DECKS_FILE = "decks.json"
LEVELS_FILE = "levels.json"

CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]

SHOP_ROLES = [
    (500, "Нищеброд", "🥉"),
    (1000, "Малой с карманными", "🥈"),
    (5000, "Уже не так плохо", "🥇"),
    (10000, "Начинающий донатер", "💎"),
    (15000, "Казик мой дом", "🎰"),
    (20000, "Рофлан", "🃏"),
    (30000, "Сынок папы", "👑"),
    (40000, "Богатенький Буратино", "💰"),
    (50000, "Топ 1 сервера (нет)", "🏆"),
    (75000, "Читер или нет?", "⚡"),
    (100000, "Мама я в топе", "🌟"),
    (250000, "Это вообще реально?", "💫"),
    (500000, "Продал почку", "🔥"),
    (750000, "Без комментариев", "⚜️"),
    (1000000, "Бог Казика", "👾"),
]

LEVEL_ROLES = {
    1: "😀 Новичок",
    5: "😎 Привыкший",
    10: "😊 Знакомый",
    20: "🕹️ Активный",
    30: "⚔️ Ветеран",
    50: "👑 Легенда",
}

FIGHTERS = {
    "Редкий": [
        {"name": "Нищеброд Петя", "emoji": "🥉", "income": 5, "atk": 10, "def": 5, "power": 15},
        {"name": "Сонный Ваня", "emoji": "😴", "income": 6, "atk": 8, "def": 8, "power": 16},
        {"name": "Пиццаед 3000", "emoji": "🍕", "income": 7, "atk": 12, "def": 4, "power": 16},
        {"name": "Лягух из подвала", "emoji": "🐸", "income": 8, "atk": 9, "def": 9, "power": 18},
        {"name": "Камень с IQ 0", "emoji": "🗿", "income": 9, "atk": 7, "def": 13, "power": 20},
        {"name": "67", "emoji": "🎤", "income": 10, "atk": 15, "def": 5, "power": 20},
    ],
    "Сверхредкий": [
        {"name": "Клоун который всё проиграл", "emoji": "🤡", "income": 11, "atk": 20, "def": 10, "power": 30},
        {"name": "Парень который не проигрывает", "emoji": "😤", "income": 13, "atk": 18, "def": 15, "power": 33},
        {"name": "Утка которая думает что она человек", "emoji": "🦆", "income": 15, "atk": 22, "def": 12, "power": 34},
        {"name": "Кот который смотрит в стену", "emoji": "🐱", "income": 17, "atk": 16, "def": 20, "power": 36},
        {"name": "Дед который не понимает мемы", "emoji": "👴", "income": 19, "atk": 14, "def": 25, "power": 39},
        {"name": "Убежище", "emoji": "🏚️", "income": 20, "atk": 25, "def": 15, "power": 40},
    ],
    "Эпический": [
        {"name": "Тот кто поставил всё на рулетку", "emoji": "💀", "income": 22, "atk": 35, "def": 20, "power": 55},
        {"name": "Чел который выиграл один раз", "emoji": "🔥", "income": 28, "atk": 40, "def": 18, "power": 58},
        {"name": "Гений казино (банкрот)", "emoji": "🧠", "income": 35, "atk": 30, "def": 35, "power": 65},
        {"name": "Призрак чужих ликкеров", "emoji": "👻", "income": 42, "atk": 45, "def": 25, "power": 70},
        {"name": "Чекушка", "emoji": "🍶", "income": 50, "atk": 38, "def": 40, "power": 78},
    ],
    "Мифический": [
        {"name": "Сынок папы на максималках", "emoji": "👑", "income": 55, "atk": 60, "def": 40, "power": 100},
        {"name": "Ночной охотник за ликкерами", "emoji": "🌚", "income": 65, "atk": 70, "def": 45, "power": 115},
        {"name": "Тот кто не спит ради казика", "emoji": "⚡", "income": 80, "atk": 80, "def": 50, "power": 130},
        {"name": "Казик это моя жизнь", "emoji": "🎰", "income": 100, "atk": 90, "def": 60, "power": 150},
    ],
    "Легендарный": [
        {"name": "Топ 1 который реально топ 1", "emoji": "🏆", "income": 120, "atk": 120, "def": 80, "power": 200},
        {"name": "Продал почку выиграл две", "emoji": "💸", "income": 175, "atk": 150, "def": 100, "power": 250},
        {"name": "Мама я в топе", "emoji": "🌟", "income": 250, "atk": 180, "def": 120, "power": 300},
    ],
    "Ультра легендарный": [
        {"name": "Без комментариев", "emoji": "💎", "income": 400, "atk": 250, "def": 200, "power": 450},
        {"name": "Бог казика в человеческом теле", "emoji": "👾", "income": 800, "atk": 400, "def": 300, "power": 700},
    ],
    "Секретный": [
        {"name": "Тот самый", "emoji": "👁️", "income": 850, "atk": 500, "def": 400, "power": 900},
        {"name": "Ошибка системы", "emoji": "🌀", "income": 1000, "atk": 600, "def": 500, "power": 1100},
        {"name": "Бог Ликкеров", "emoji": "💰", "income": 1250, "atk": 800, "def": 700, "power": 1500},
    ],
}

RARITY_CHANCES = [
    ("Редкий", 50.0), ("Сверхредкий", 25.0), ("Эпический", 15.0),
    ("Мифический", 6.0), ("Легендарный", 2.5), ("Ультра легендарный", 1.4), ("Секретный", 0.1),
]

RARITY_COLORS = {
    "Редкий": "⬜", "Сверхредкий": "🟦", "Эпический": "🟪",
    "Мифический": "🟥", "Легендарный": "🟨", "Ультра легендарный": "🟧", "Секретный": "⬛",
}

LUCK_PRICES = {10: 50, 20: 120, 30: 220, 40: 350, 50: 500, 60: 700, 70: 1000, 80: 1400, 90: 2000}

user_last_message = {}

# ===== FILE FUNCTIONS =====
def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_balance(uid):
    data = load_file(BALANCE_FILE)
    return data.get(str(uid), 0)

def set_balance(uid, amount):
    data = load_file(BALANCE_FILE)
    data[str(uid)] = max(0, amount)
    save_file(BALANCE_FILE, data)

def get_fighters(uid):
    data = load_file(FIGHTERS_FILE)
    return data.get(str(uid), [])

def add_fighter(uid, fighter):
    data = load_file(FIGHTERS_FILE)
    if str(uid) not in data:
        data[str(uid)] = []
    data[str(uid)].append(fighter)
    save_file(FIGHTERS_FILE, data)

def get_decks(uid):
    data = load_file(DECKS_FILE)
    return data.get(str(uid), {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []})

def save_deck(uid, deck_name, fighters):
    data = load_file(DECKS_FILE)
    if str(uid) not in data:
        data[str(uid)] = {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []}
    data[str(uid)][deck_name] = fighters
    save_file(DECKS_FILE, data)

def get_level_data(uid):
    data = load_file(LEVELS_FILE)
    return data.get(str(uid), {"xp": 0, "level": 0})

def save_level_data(uid, level_data):
    data = load_file(LEVELS_FILE)
    data[str(uid)] = level_data
    save_file(LEVELS_FILE, data)

def xp_for_level(level):
    return 250 + level * 50

def reward_for_level(level):
    return 1000 + (level - 1) * 500

def get_level_role_name(level):
    achieved = [lvl for lvl in LEVEL_ROLES if level >= lvl]
    if not achieved:
        return None
    return LEVEL_ROLES[max(achieved)]

def roll_fighter(luck_bonus=0):
    total = sum(c + (luck_bonus / 100) * c if r != "Секретный" else c for r, c in RARITY_CHANCES)
    r = random.uniform(0, total)
    cur = 0
    for rarity, chance in RARITY_CHANCES:
        adj = chance if rarity == "Секретный" else chance + (luck_bonus / 100) * chance
        cur += adj
        if r <= cur:
            fighter = random.choice(FIGHTERS[rarity])
            return rarity, fighter
    return "Редкий", random.choice(FIGHTERS["Редкий"])

# ===== BOT SETUP =====
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    uid = message.author.id
    now = asyncio.get_event_loop().time()
    last = user_last_message.get(uid, 0)
    if now - last < 60:
        return
    user_last_message[uid] = now
    ld = get_level_data(uid)
    ld["xp"] += 1
    leveled_up = False
    while ld["xp"] >= xp_for_level(ld["level"] + 1):
        ld["xp"] -= xp_for_level(ld["level"] + 1)
        ld["level"] += 1
        leveled_up = True
        reward = reward_for_level(ld["level"])
        bal = get_balance(uid)
        set_balance(uid, bal + reward)
        role_name = get_level_role_name(ld["level"])
        if role_name and message.guild:
            role = discord.utils.get(message.guild.roles, name=role_name)
            if not role:
                role = await message.guild.create_role(name=role_name)
            await message.author.add_roles(role)
        await message.channel.send(
            f"🎉 {message.author.mention} достиг **{ld['level']} уровня**! +**{reward}** ликкеров!" +
            (f" Роль: **{role_name}**" if role_name else "")
        )
    save_level_data(uid, ld)

# ===== COMMANDS =====

@tree.command(name="баланс", description="Баланс ликкеров")
@app_commands.describe(участник="Участник")
async def balance(interaction: discord.Interaction, участник: discord.Member = None):
    target = участник or interaction.user
    bal = get_balance(target.id)
    fighters = get_fighters(target.id)
    income = sum(f.get("income", 0) for f in fighters)
    await interaction.response.send_message(
        f"**Баланс {target.display_name}**\n\nЛикеры: **{bal}**\nДоход: **{income}**/час\nБойцов: **{len(fighters)}**",
        ephemeral=True
    )

@tree.command(name="мойранг", description="Мой уровень и XP")
@app_commands.describe(участник="Участник")
async def my_rank(interaction: discord.Interaction, участник: discord.Member = None):
    target = участник or interaction.user
    ld = get_level_data(target.id)
    need = xp_for_level(ld["level"] + 1)
    bar = int((ld["xp"] / need) * 10)
    bar_str = "█" * bar + "░" * (10 - bar)
    role_name = get_level_role_name(ld["level"])
    text = f"**Ранг {target.display_name}**\n\nУровень: **{ld['level']}**\nXP: **{ld['xp']}** / **{need}**\n[{bar_str}]"
    if role_name:
        text += f"\nРоль: **{role_name}**"
    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="лидеры", description="Топ по уровням")
async def leaders(interaction: discord.Interaction):
    data = load_file(LEVELS_FILE)
    sorted_users = sorted(data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)[:10]
    if not sorted_users:
        await interaction.response.send_message("Пока нет данных!", ephemeral=True)
        return
    medals = ["🥇", "🥈", "🥉"]
    text = "**Топ по уровням:**\n\n"
    for i, (uid, ld) in enumerate(sorted_users):
        prefix = medals[i] if i < 3 else f"{i+1}."
        try:
            user = await client.fetch_user(int(uid))
            name = user.display_name
        except:
            name = f"ID:{uid}"
        text += f"{prefix} **{name}** — Уровень **{ld['level']}** | XP: **{ld['xp']}**\n"
    await interaction.response.send_message(text)

@tree.command(name="рулетка", description="Рулетка")
@app_commands.describe(ставка="Ставка", выбор="red/black/even/odd/0")
async def roulette(interaction: discord.Interaction, ставка: int, выбор: str):
    if not any(c in interaction.channel.name for c in CASINO_CHANNELS):
        await interaction.response.send_message("Только в казино-каналах!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if bal < ставка:
        await interaction.response.send_message(f"Мало ликкеров! Есть: **{bal}**", ephemeral=True)
        return
    roll = random.randint(0, 36)
    red = [1,3,5,7,9,12,14,16,18,19,21,23,25,27,30,32,34,36]
    is_red = roll in red
    is_black = roll > 0 and not is_red
    color = "🟢" if roll == 0 else "🔴" if is_red else "⚫"
    win = 0
    if выбор == "0" and roll == 0: win = ставка * 35
    elif выбор == "red" and is_red: win = ставка
    elif выбор == "black" and is_black: win = ставка
    elif выбор == "even" and roll > 0 and roll % 2 == 0: win = ставка
    elif выбор == "odd" and roll % 2 == 1: win = ставка
    new_bal = bal - ставка + (ставка + win if win > 0 else 0)
    set_balance(interaction.user.id, new_bal)
    result = f"Победа! +**{win}**" if win > 0 else f"Проигрыш -**{ставка}**"
    await interaction.response.send_message(f"Рулетка: {color} **{roll}**\n{result}\nБаланс: **{new_bal}**")

@tree.command(name="монета", description="Монетка")
@app_commands.describe(ставка="Ставка", выбор="орел или решка")
async def coin(interaction: discord.Interaction, ставка: int, выбор: str):
    if not any(c in interaction.channel.name for c in CASINO_CHANNELS):
        await interaction.response.send_message("Только в казино-каналах!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if bal < ставка:
        await interaction.response.send_message("Мало ликкеров!", ephemeral=True)
        return
    flip = random.choice(["орел", "решка"])
    won = flip == выбор
    new_bal = bal + ставка if won else bal - ставка
    set_balance(interaction.user.id, new_bal)
    await interaction.response.send_message(
        f"{'🪙' if won else '💀'} Выпало **{flip}**! {'Победа +' if won else 'Проигрыш -'}**{ставка}**\nБаланс: **{new_bal}**"
    )

@tree.command(name="слоты", description="Слоты")
@app_commands.describe(ставка="Ставка")
async def slots(interaction: discord.Interaction, ставка: int):
    if not any(c in interaction.channel.name for c in CASINO_CHANNELS):
        await interaction.response.send_message("Только в казино-каналах!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if bal < ставка:
        await interaction.response.send_message("Мало ликкеров!", ephemeral=True)
        return
    symbols = ["🍒", "🍋", "🍊", "⭐", "💎", "7️⃣"]
    s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
    mult = 0
    if s1 == s2 == s3:
        if s3 == "7️⃣": mult = 10
        elif s3 == "💎": mult = 7
        else: mult = 4
    elif s1 == s2 or s2 == s3 or s1 == s3:
        mult = 1
    win = ставка * mult
    new_bal = bal - ставка + win
    set_balance(interaction.user.id, new_bal)
    if mult == 0: res = f"Проигрыш -**{ставка}**"
    elif mult == 1: res = "Пара! Возврат ставки"
    else: res = f"ДЖЕКПОТ x{mult}! +**{win - ставка}**"
    await interaction.response.send_message(f"🎰 | {s1} {s2} {s3} |\n{res}\nБаланс: **{new_bal}**")

@tree.command(name="бокс", description="Купить боксы с бойцами")
@app_commands.describe(количество="Количество боксов", удача="Удача % (0,10,20...90)")
async def box(interaction: discord.Interaction, количество: int = 1, удача: int = 0):
    base_price = количество * 100
    extra = LUCK_PRICES.get(удача, 0) * количество
    total = base_price + extra
    bal = get_balance(interaction.user.id)
    if bal < total:
        await interaction.response.send_message(f"Нужно **{total}** ликкеров, есть **{bal}**!", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - total)
    text = f"📦 **{количество} боксов** за **{total}** ликкеров!\n\n"
    for _ in range(количество):
        rarity, fighter = roll_fighter(удача)
        f = {**fighter, "rarity": rarity}
        add_fighter(interaction.user.id, f)
        color = RARITY_COLORS.get(rarity, "⬜")
        text += f"{color} **[{rarity}]** {fighter['emoji']} **{fighter['name']}** +{fighter['income']}/час\n"
    fighters = get_fighters(interaction.user.id)
    income = sum(f.get("income", 0) for f in fighters)
    new_bal = get_balance(interaction.user.id)
    text += f"\nДоход: **{income}**/час | Остаток: **{new_bal}**"
    if len(text) > 2000: text = text[:1990] + "..."
    await interaction.response.send_message(text)

@tree.command(name="бойцы", description="Список бойцов")
async def fighters_cmd(interaction: discord.Interaction):
    fighters = get_fighters(interaction.user.id)
    if not fighters:
        await interaction.response.send_message("Нет бойцов! Купи /бокс", ephemeral=True)
        return
    sorted_f = sorted(fighters, key=lambda x: x.get("power", 0), reverse=True)
    text = f"**Бойцы {interaction.user.display_name}** ({len(fighters)}):\n\n"
    for f in sorted_f[:15]:
        color = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
        text += f"{color} {f['emoji']} **{f['name']}** | ATK:{f['atk']} DEF:{f['def']} PWR:{f['power']} +{f['income']}/час\n"
    if len(fighters) > 15:
        text += f"\n...и ещё {len(fighters) - 15} бойцов"
    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="колода", description="Управление колодой")
@app_commands.describe(название="К1-К5", действие="show/auto/clear")
async def deck_cmd(interaction: discord.Interaction, название: str = "К1", действие: str = "show"):
    uid = interaction.user.id
    decks = get_decks(uid)
    deck = decks.get(название, [])
    if действие == "show":
        if not deck:
            await interaction.response.send_message(f"Колода **{название}** пуста!", ephemeral=True)
            return
        text = f"**Колода {название}** ({len(deck)}/5):\n\n"
        power = 0
        for f in deck:
            color = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            text += f"{color} {f['emoji']} **{f['name']}** | PWR:{f['power']}\n"
            power += f.get("power", 0)
        text += f"\nСила: **{power}**"
        await interaction.response.send_message(text, ephemeral=True)
    elif действие == "auto":
        all_fighters = get_fighters(uid)
        used = [f["name"] for dk, df in decks.items() if dk != название for f in df]
        available = [f for f in all_fighters if f["name"] not in used]
        best = sorted(available, key=lambda x: x.get("power", 0), reverse=True)[:5]
        save_deck(uid, название, best)
        text = f"**Колода {название}** заполнена!\n\n"
        for f in best:
            color = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            text += f"{color} {f['emoji']} **{f['name']}** | PWR:{f['power']}\n"
        await interaction.response.send_message(text, ephemeral=True)
    elif действие == "clear":
        save_deck(uid, название, [])
        await interaction.response.send_message(f"Колода **{название}** очищена!", ephemeral=True)

@tree.command(name="бой", description="Вызвать на бой")
@app_commands.describe(оппонент="Оппонент", ставка="Ставка", колода="Колода (К1-К5)")
async def battle(interaction: discord.Interaction, оппонент: discord.Member, ставка: int = 0, колода: str = "К1"):
    uid = interaction.user.id
    op_id = оппонент.id
    if op_id == uid:
        await interaction.response.send_message("Нельзя биться с собой!", ephemeral=True)
        return
    my_bal = get_balance(uid)
    if ставка > 0 and my_bal < ставка:
        await interaction.response.send_message("Мало ликкеров!", ephemeral=True)
        return
    my_decks = get_decks(uid)
    my_deck = my_decks.get(колода, [])
    if not my_deck:
        await interaction.response.send_message(f"Колода **{колода}** пуста! /колода {колода} auto", ephemeral=True)
        return
    op_decks = get_decks(op_id)
    op_deck_name = next((k for k, v in op_decks.items() if v), None)
    if not op_deck_name:
        await interaction.response.send_message("У оппонента нет колод!", ephemeral=True)
        return
    op_deck = op_decks[op_deck_name]
    op_bal = get_balance(op_id)
    if ставка > 0 and op_bal < ставка:
        await interaction.response.send_message("У оппонента мало ликкеров!", ephemeral=True)
        return
    if ставка > 0:
        set_balance(uid, my_bal - ставка)
        set_balance(op_id, op_bal - ставка)
    my_hp = sum(f["def"] * 5 + f["power"] * 2 for f in my_deck)
    op_hp = sum(f["def"] * 5 + f["power"] * 2 for f in op_deck)
    my_atk = sum(f["atk"] for f in my_deck)
    op_atk = sum(f["atk"] for f in op_deck)
    rounds = 0
    while my_hp > 0 and op_hp > 0 and rounds < 50:
        my_hp -= op_atk * random.uniform(0.8, 1.2)
        op_hp -= my_atk * random.uniform(0.8, 1.2)
        rounds += 1
    i_won = my_hp > op_hp
    if ставка > 0:
        winner_id = uid if i_won else op_id
        winner_bal = get_balance(winner_id)
        set_balance(winner_id, winner_bal + ставка * 2)
    my_final = get_balance(uid)
    result = "🏆 **Победа!**" if i_won else "💀 **Поражение!**"
    winner_name = interaction.user.display_name if i_won else оппонент.display_name
    text = f"{result}\n\n{winner_name} победил за {rounds} раундов!"
    if ставка > 0:
        text += f"\nБаланс: **{my_final}**"
    await interaction.response.send_message(text)

@tree.command(name="перевод", description="Перевод ликкеров")
@app_commands.describe(получатель="Получатель", сумма="Сумма")
async def transfer(interaction: discord.Interaction, получатель: discord.Member, сумма: int):
    uid = interaction.user.id
    if получатель.id == uid:
        await interaction.response.send_message("Нельзя переводить себе!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.response.send_message("Сумма > 0!", ephemeral=True)
        return
    bal = get_balance(uid)
    if bal < сумма:
        await interaction.response.send_message("Мало ликкеров!", ephemeral=True)
        return
    set_balance(uid, bal - сумма)
    set_balance(получатель.id, get_balance(получатель.id) + сумма)
    await interaction.response.send_message(f"Перевод **{сумма}** ликкеров {получатель.mention}!\nОстаток: **{bal - сумма}**")

@tree.command(name="дать", description="Выдать ликкеры")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def give(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    bal = get_balance(участник.id)
    set_balance(участник.id, bal + сумма)
    await interaction.response.send_message(f"Выдано **{сумма}** ликкеров {участник.mention}!\nТеперь: **{bal + сумма}**")

@tree.command(name="магазин", description="Магазин ролей")
async def shop(interaction: discord.Interaction):
    bal = get_balance(interaction.user.id)
    text = f"**Магазин ролей**\n\nЛикеры: **{bal}**\n\n"
    for price, name, emoji in SHOP_ROLES:
        text += f"{emoji} **{name}** — {price} ликкеров\n"
    text += "\nКупить: /купить <название>"
    await interaction.response.send_message(text, ephemeral=True)

@tree.command(name="купить", description="Купить роль")
@app_commands.describe(роль="Название роли")
async def buy(interaction: discord.Interaction, роль: str):
    role_data = next((r for r in SHOP_ROLES if r[1].lower() == роль.lower()), None)
    if not role_data:
        await interaction.response.send_message("Роль не найдена!", ephemeral=True)
        return
    price, name, emoji = role_data
    bal = get_balance(interaction.user.id)
    if bal < price:
        await interaction.response.send_message(f"Нужно **{price}**, есть **{bal}**!", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - price)
    role = discord.utils.get(interaction.guild.roles, name=name)
    if not role:
        role = await interaction.guild.create_role(name=name)
    await interaction.user.add_roles(role)
    await interaction.response.send_message(f"{emoji} Роль **{name}** куплена!\nОстаток: **{bal - price}**")

@tree.command(name="накруткауровня", description="[Владелец] Добавить уровни")
@app_commands.describe(участник="Участник", количество="Количество уровней")
async def boost_level(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message("Только для владельца!", ephemeral=True)
        return
    ld = get_level_data(участник.id)
    ld["level"] += количество
    reward = sum(reward_for_level(ld["level"] - i) for i in range(количество))
    bal = get_balance(участник.id)
    set_balance(участник.id, bal + reward)
    save_level_data(участник.id, ld)
    await interaction.response.send_message(f"{участник.mention} получил **{количество}** уровней! Теперь: **{ld['level']}** ур. +**{reward}** ликкеров")

@tree.command(name="накруткаопыта", description="[Владелец] Добавить XP")
@app_commands.describe(участник="Участник", количество="Количество XP")
async def boost_xp(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message("Только для владельца!", ephemeral=True)
        return
    ld = get_level_data(участник.id)
    ld["xp"] += количество
    while ld["xp"] >= xp_for_level(ld["level"] + 1):
        ld["xp"] -= xp_for_level(ld["level"] + 1)
        ld["level"] += 1
    save_level_data(участник.id, ld)
    await interaction.response.send_message(f"{участник.mention} получил **{количество}** XP! Уровень: **{ld['level']}** | XP: **{ld['xp']}**")

@tree.command(name="отобратьопыт", description="[Владелец] Отнять XP")
@app_commands.describe(участник="Участник", количество="Количество XP")
async def remove_xp(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message("Только для владельца!", ephemeral=True)
        return
    ld = get_level_data(участник.id)
    ld["xp"] = max(0, ld["xp"] - количество)
    save_level_data(участник.id, ld)
    await interaction.response.send_message(f"У {участник.mention} отнято **{количество}** XP! XP: **{ld['xp']}**")

@tree.command(name="отобратьранг", description="[Владелец] Отнять уровни")
@app_commands.describe(участник="Участник", количество="Количество уровней")
async def remove_rank(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message("Только для владельца!", ephemeral=True)
        return
    ld = get_level_data(участник.id)
    ld["level"] = max(0, ld["level"] - количество)
    ld["xp"] = 0
    save_level_data(участник.id, ld)
    await interaction.response.send_message(f"У {участник.mention} отнято **{количество}** уровней! Теперь: **{ld['level']}** ур.")

@tree.command(name="написать", description="[Владелец] Написать от лица бота")
@app_commands.describe(текст="Текст сообщения", канал="Канал (опционально)")
async def write_as_bot(interaction: discord.Interaction, текст: str, канал: discord.TextChannel = None):
    if interaction.guild.owner_id != interaction.user.id:
        await interaction.response.send_message("Только для владельца!", ephemeral=True)
        return
    target = канал or interaction.channel
    await target.send(текст)
    await interaction.response.send_message("Отправлено!", ephemeral=True)

@tree.command(name="помощь", description="Список команд")
async def help_cmd(interaction: discord.Interaction):
    text = (
        "**Команды бота:**\n\n"
        "**Профиль**\n"
        "/баланс — баланс ликкеров\n"
        "/мойранг — уровень и XP\n"
        "/лидеры — топ по уровням\n\n"
        "**Казино**\n"
        "/рулетка <ставка> <red/black/even/odd/0>\n"
        "/монета <ставка> <орел/решка>\n"
        "/слоты <ставка>\n\n"
        "**Бойцы**\n"
        "/бокс <кол-во> <удача%>\n"
        "/бойцы — список бойцов\n"
        "/колода <К1-К5> <show/auto/clear>\n"
        "/бой <@оппонент> <ставка> <колода>\n\n"
        "**Прочее**\n"
        "/перевод <@пользователь> <сумма>\n"
        "/магазин — магазин ролей\n"
        "/купить <роль>\n"
        "/дать <@пользователь> <сумма>"
    )
    await interaction.response.send_message(text, ephemeral=True)

async def main():
    await keep_alive()
    await client.start(DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

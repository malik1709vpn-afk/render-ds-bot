import os
import random
import json
import asyncio
import time
import threading
from datetime import timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler

import discord
from discord import app_commands

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

BALANCE_FILE = "balance.json"

CASINO_CHANNELS = ["казик", "казино", "лучшие-по-казику", "чемпионат-по-казику"]
BAN_ROLES = ["Модератор", "Главный Модератор", "Создатель Сервера"]
SEND_ROLES = ["Главный Модератор", "Владелец Сервера"]

СТРАНЫ = [
    ("Россия", ["Москва", "Санкт-Петербург", "Казань", "Новосибирск"]),
    ("Украина", ["Киев", "Харьков", "Одесса"]),
    ("Беларусь", ["Минск", "Гомель"]),
    ("Казахстан", ["Алматы", "Астана"]),
    ("Узбекистан", ["Ташкент"]),
    ("Азербайджан", ["Баку"]),
    ("Армения", ["Ереван"]),
    ("Грузия", ["Тбилиси"]),
    ("Молдова", ["Кишинёв"]),
    ("Кыргызстан", ["Бишкек"]),
    ("Таджикистан", ["Душанбе"]),
    ("Туркменистан", ["Ашхабад"]),
    ("Израиль", ["Тель-Авив", "Иерусалим"]),
    ("Палестина", ["Газа"]),
    ("Афганистан", ["Кабул"]),
    ("КНДР", ["Пхеньян"]),
    ("Иран", ["Тегеран"]),
    ("США", ["Нью-Йорк", "Лос-Анджелес"]),
    ("Сирия", ["Дамаск"]),
    ("Ирак", ["Багдад"]),
    ("Остров Эпштейна", ["Остров Эпштейна"]),
]
СПИСОК_СТРАН = [с[0] for с in СТРАНЫ]
УЛИЦЫ = ["ул. Ленина", "пр. Мира", "ул. Пушкина", "ул. Гагарина", "пр. Победы",
          "ул. Советская", "ул. Садовая", "пр. Независимости"]

FIGHTERS_FILE = "fighters.json"
PAYOUT_FILE = "payout.json"
BOX_PRICE = 100
PAYOUT_INTERVAL = 24 * 60 * 60  # доход раз в 24 часа

# Доход бойца: от 0.5 до 15 ликкеров раз в 24 часа
FIGHTERS = {
    "Редкий": [
        {"name": "Нищеброд Петя", "emoji": "🥉", "income": 0.5},
        {"name": "Сонный Ваня", "emoji": "😴", "income": 0.5},
        {"name": "Пиццаед 3000", "emoji": "🍕", "income": 0.5},
        {"name": "Лягух из подвала", "emoji": "🐸", "income": 1},
        {"name": "Камень с IQ 0", "emoji": "🗿", "income": 1},
        {"name": "67", "emoji": "🎤", "income": 1},
    ],
    "Сверхредкий": [
        {"name": "Клоун который всё проиграл", "emoji": "🤡", "income": 1.5},
        {"name": "Парень который не проигрывает", "emoji": "😤", "income": 1.5},
        {"name": "Утка которая думает что она человек", "emoji": "🦆", "income": 2},
        {"name": "Кот который смотрит в стену", "emoji": "🐱", "income": 2},
        {"name": "Дед который не понимает мемы", "emoji": "👴", "income": 2.5},
        {"name": "Убежище", "emoji": "🏚️", "income": 3},
    ],
    "Эпический": [
        {"name": "Тот кто поставил всё на рулетку", "emoji": "💀", "income": 4},
        {"name": "Чел который выиграл один раз", "emoji": "🔥", "income": 4.5},
        {"name": "Гений казино (банкрот)", "emoji": "🧠", "income": 5},
        {"name": "Призрак чужих ликкеров", "emoji": "👻", "income": 5.5},
        {"name": "Чекушка", "emoji": "🍶", "income": 6},
    ],
    "Мифический": [
        {"name": "Сынок папы на максималках", "emoji": "👑", "income": 7},
        {"name": "Ночной охотник за ликкерами", "emoji": "🌚", "income": 7.5},
        {"name": "Тот кто не спит ради казика", "emoji": "⚡", "income": 8},
        {"name": "Казик это моя жизнь", "emoji": "🎰", "income": 9},
    ],
    "Легендарный": [
        {"name": "Топ 1 который реально топ 1", "emoji": "🏆", "income": 10},
        {"name": "Продал почку выиграл две", "emoji": "💸", "income": 11},
        {"name": "Мама я в топе", "emoji": "🌟", "income": 12},
    ],
    "Ультра легендарный": [
        {"name": "Без комментариев", "emoji": "💎", "income": 13},
        {"name": "Бог казика в человеческом теле", "emoji": "👾", "income": 14},
    ],
    "Секретный": [
        {"name": "Тот самый", "emoji": "👁️", "income": 15},
        {"name": "Ошибка системы", "emoji": "🌀", "income": 15},
        {"name": "Бог Ликкеров", "emoji": "💰", "income": 15},
    ],
}

# Шансы в процентах (сумма = 100). "Ничего" — макс. 35%, Секретный — 0.01%
RARITY_CHANCES = [
    ("Ничего", 35.0),
    ("Редкий", 30.0),
    ("Сверхредкий", 20.0),
    ("Эпический", 10.0),
    ("Мифический", 3.5),
    ("Легендарный", 1.2),
    ("Ультра легендарный", 0.29),
    ("Секретный", 0.01),
]

RARITY_COLORS = {
    "Редкий": "⬜", "Сверхредкий": "🟦", "Эпический": "🟪",
    "Мифический": "🟥", "Легендарный": "🟨", "Ультра легендарный": "🟧", "Секретный": "⬛",
}
RARITY_ORDER = ["Редкий", "Сверхредкий", "Эпический", "Мифический",
                "Легендарный", "Ультра легендарный", "Секретный"]


# ===== ФАЙЛОВЫЕ ФУНКЦИИ =====
def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_balance(user_id):
    data = load_file(BALANCE_FILE)
    return data.get(str(user_id), 0)

def clean_num(x):
    """Округляет до 0.1 и убирает .0 у целых чисел."""
    x = round(x, 1)
    return int(x) if x == int(x) else x

def set_balance(user_id, amount):
    data = load_file(BALANCE_FILE)
    data[str(user_id)] = clean_num(max(0, amount))
    save_file(BALANCE_FILE, data)

def get_fighters_list(user_id):
    return load_file(FIGHTERS_FILE).get(str(user_id), [])

def add_fighters(user_id, new_fighters):
    data = load_file(FIGHTERS_FILE)
    data.setdefault(str(user_id), []).extend(new_fighters)
    save_file(FIGHTERS_FILE, data)

def get_daily_income(user_id):
    return clean_num(sum(f["income"] for f in get_fighters_list(user_id)))

def roll_fighter():
    """Возвращает (редкость, боец) или ("Ничего", None)."""
    r = random.uniform(0, sum(c for _, c in RARITY_CHANCES))
    current = 0
    for rarity, chance in RARITY_CHANCES:
        current += chance
        if r <= current:
            if rarity == "Ничего":
                return "Ничего", None
            return rarity, random.choice(FIGHTERS[rarity])
    return "Ничего", None

async def income_loop():
    """Раз в 24 часа начисляет доход от бойцов. Время последней выплаты хранится в файле."""
    await client.wait_until_ready()
    while True:
        last = load_file(PAYOUT_FILE).get("last", 0)
        now = time.time()
        if now - last >= PAYOUT_INTERVAL:
            fighters_data = load_file(FIGHTERS_FILE)
            bal_data = load_file(BALANCE_FILE)
            for uid, f_list in fighters_data.items():
                income = sum(f["income"] for f in f_list)
                if income > 0:
                    bal_data[uid] = clean_num(bal_data.get(uid, 0) + income)
            save_file(BALANCE_FILE, bal_data)
            save_file(PAYOUT_FILE, {"last": now})
            last = now
        wait = PAYOUT_INTERVAL - (time.time() - last)
        await asyncio.sleep(max(60, min(wait, 3600)))


# ===== ВЕБ-СЕРВЕР ДЛЯ RENDER =====
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")
    def log_message(self, format, *args):
        pass

def run_web():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


income_started = False

@client.event
async def on_ready():
    global income_started
    await tree.sync()
    print(f"Бот запущен: {client.user}")
    if not income_started:
        income_started = True
        client.loop.create_task(income_loop())


# ===== КОМАНДЫ =====

@tree.command(name="баланс", description="Посмотреть баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    await interaction.followup.send(
        f"┌─────────────────────┐\n"
        f"        💰 **{цель.name}**\n"
        f"└─────────────────────┘\n"
        f"💵 **{bal}** ликкеров\n"
        f"📈 Доход: **{get_daily_income(цель.id)}**/сутки\n"
        f"⚔️ Бойцов: **{len(get_fighters_list(цель.id))}**")

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    await interaction.response.send_message("🏪 **Магаз**\n\nНичего не продаётся.", ephemeral=True)

@tree.command(name="сброс", description="Сбросить все балансы до 0")
async def сброс(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    save_file(BALANCE_FILE, {})
    await interaction.followup.send("✅ Все балансы сброшены до **0**!")

@tree.command(name="датьвсем", description="Дать всем участникам ликкеры")
@app_commands.describe(сумма="Сумма для каждого")
async def датьвсем(interaction: discord.Interaction, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    count = 0
    for member in interaction.guild.members:
        if not member.bot:
            set_balance(member.id, get_balance(member.id) + сумма)
            count += 1
    await interaction.followup.send(f"✅ **{count}** участникам выдано по **{сумма} ликкеров**!")

СТОРОНА_ВЫБОР = [
    app_commands.Choice(name="Орёл", value="орёл"),
    app_commands.Choice(name="Решка", value="решка"),
]

@tree.command(name="оир", description="Орёл или решка")
@app_commands.describe(сторона="Выбери сторону", ставка="Сумма ставки")
@app_commands.choices(сторона=СТОРОНА_ВЫБОР)
async def оир(interaction: discord.Interaction, сторона: app_commands.Choice[str], ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    результат = random.choice(["орёл", "решка"])
    if сторона.value == результат:
        set_balance(interaction.user.id, bal + ставка)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🪙 Выпало **{результат}**!\n🎉 Выиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")
    else:
        set_balance(interaction.user.id, bal - ставка)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🪙 Выпало **{результат}**!\n😢 Проиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")

@tree.command(name="рул", description="Рулетка")
@app_commands.describe(ставка="Сумма ставки")
async def рул(interaction: discord.Interaction, ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    победа = random.choice([True, False])
    if победа:
        set_balance(interaction.user.id, bal + ставка)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🎰 ДЖЕКПОТ!\n✅ Выиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")
    else:
        set_balance(interaction.user.id, bal - ставка)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🎰 Не повезло...\n❌ Проиграл **{ставка}** ликкеров!\n💰 Баланс: **{new_bal}**")

@tree.command(name="мн", description="Множитель — ставка с умножением")
@app_commands.describe(ставка="Сумма ставки")
async def мн(interaction: discord.Interaction, ставка: int):
    if interaction.channel.name not in CASINO_CHANNELS:
        await interaction.response.send_message("❌ Только в **#казик**!", ephemeral=True)
        return
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if ставка > bal:
        await interaction.response.send_message(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    победа = random.choice([True, False])
    множитель = round(random.uniform(1.1, 1.9), 2)
    # Ставка сразу списывается с баланса
    остаток = bal - ставка
    set_balance(interaction.user.id, остаток)
    if победа:
        выигрыш = int(ставка * множитель)
        итог = остаток + выигрыш
        set_balance(interaction.user.id, итог)
        await interaction.response.send_message(
            f"🎲 **Ставка:** {ставка} | **Осталось:** {остаток}\n\n"
            f"🎉 ВЫИГРЫШ! **Множитель:** x{множитель}\n"
            f"✅ {ставка} × {множитель} = **{выигрыш}**\n"
            f"➕ {остаток} + {выигрыш} = **{итог}**\n"
            f"💰 Баланс: **{get_balance(interaction.user.id)}**")
    else:
        await interaction.response.send_message(
            f"🎲 **Ставка:** {ставка} | **Осталось:** {остаток}\n\n"
            f"💀 ПРОИГРЫШ! Ставка **{ставка}** потеряна.\n"
            f"💰 Баланс: **{get_balance(interaction.user.id)}**")

@tree.command(name="нак", description="Накрутить баланс участнику")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def нак(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    set_balance(участник.id, bal + сумма)
    new_bal = get_balance(участник.id)
    await interaction.followup.send(f"✅ {участник.mention} получил **{сумма}** ликкеров\n💰 Баланс: **{new_bal}**")

@tree.command(name="пер", description="Перевести ликкеры")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def пер(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    if участник.id == interaction.user.id:
        await interaction.followup.send("❌ Себе нельзя!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    bal = get_balance(interaction.user.id)
    if сумма > bal:
        await interaction.followup.send(f"❌ Мало ликкеров! Баланс: **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - сумма)
    set_balance(участник.id, get_balance(участник.id) + сумма)
    new_bal = get_balance(interaction.user.id)
    await interaction.followup.send(f"💸 **{interaction.user.name}** → {участник.mention}\n**{сумма}** ликкеров\n💰 Твой баланс: **{new_bal}**")

@tree.command(name="отобрать", description="Отобрать ликкеры")
@app_commands.describe(участник="Участник", сумма="Сумма")
async def отобрать(interaction: discord.Interaction, участник: discord.Member, сумма: int):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if сумма <= 0:
        await interaction.followup.send("❌ Сумма > 0!", ephemeral=True)
        return
    bal = get_balance(участник.id)
    реально = min(сумма, bal)
    set_balance(участник.id, bal - реально)
    set_balance(interaction.user.id, get_balance(interaction.user.id) + реально)
    new_bal_target = get_balance(участник.id)
    new_bal_self = get_balance(interaction.user.id)
    await interaction.followup.send(
        f"💀 У {участник.mention} отобрано **{реально}** ликкеров!\n"
        f"💰 Баланс {участник.name}: **{new_bal_target}**\n"
        f"💰 Твой баланс: **{new_bal_self}**")

@tree.command(name="топ", description="Топ 10 по ликкерам")
async def топ(interaction: discord.Interaction):
    await interaction.response.defer()
    data = load_file(BALANCE_FILE)
    if not data:
        await interaction.followup.send("❌ Нет данных!")
        return
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
    текст = "🏆 **Топ 10 по ликкерам:**\n\n"
    for i, (uid, bal) in enumerate(sorted_data):
        try:
            user = await client.fetch_user(int(uid))
            имя = user.name
        except:
            имя = f"Игрок {uid}"
        текст += f"{medals[i]} **{имя}** — {bal} ликкеров\n"
    await interaction.followup.send(текст)

@tree.command(name="ip", description="Узнать IP участника")
@app_commands.describe(участник="Участник (необязательно)")
async def ip(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    страна, города = random.choice(СТРАНЫ)
    город = random.choice(города)
    айпи = f"{random.randint(1,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"
    улица = random.choice(УЛИЦЫ)
    дом = f"{random.randint(1,99)}{random.choice(['', 'а', 'б', 'в'])}"
    подъезд = random.randint(1, 10)
    квартира = random.randint(1, 99)
    await interaction.followup.send(
        f"🔍 **Пробив {цель.name}**\n\n"
        f"🌐 **IP:** `{айпи}`\n"
        f"🌍 **Страна:** {страна}\n"
        f"🏙️ **Город:** {город}\n"
        f"📍 **Адрес:** {улица}, д. {дом}\n"
        f"🚪 **Подъезд:** {подъезд}\n"
        f"🏠 **Квартира:** {квартира}")

@tree.command(name="fake_ban", description="Бан на 67 секунд")
@app_commands.describe(участник="Участник")
async def fake_ban(interaction: discord.Interaction, участник: discord.Member):
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in BAN_ROLES):
        await interaction.response.send_message("❌ Нет прав!", ephemeral=True)
        return
    await interaction.response.send_message(f"🔨 {участник.mention} **забанен на 67 секунд!**")
    try:
        await участник.timeout(discord.utils.utcnow() + timedelta(seconds=67))
    except:
        pass
    await asyncio.sleep(67)
    await interaction.channel.send(f"✅ {участник.mention} бан снят!")

async def страна_autocomplete(interaction: discord.Interaction, current: str):
    return [app_commands.Choice(name=с, value=с) for с in СПИСОК_СТРАН if current.lower() in с.lower()][:25]

@tree.command(name="отправить", description="Отправить участника в страну")
@app_commands.describe(участник="Участник", страна="Страна")
@app_commands.autocomplete(страна=страна_autocomplete)
async def отправить(interaction: discord.Interaction, участник: discord.Member, страна: str):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if not any(r in роли for r in SEND_ROLES):
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if страна not in СПИСОК_СТРАН:
        await interaction.followup.send("❌ Страна не найдена!", ephemeral=True)
        return
    await interaction.followup.send(f"✈️ {участник.mention} **отправлен в {страна}!**\n🧳 Счастливого пути!")


@tree.command(name="боксы", description="Открыть боксы (1 бокс = 100 ликкеров)")
@app_commands.describe(количество="Количество боксов (от 1 до 100)")
async def боксы(interaction: discord.Interaction, количество: int):
    await interaction.response.defer()
    if количество <= 0 or количество > 100:
        await interaction.followup.send("❌ От 1 до 100!", ephemeral=True)
        return
    price = количество * BOX_PRICE
    bal = get_balance(interaction.user.id)
    if bal < price:
        await interaction.followup.send(f"❌ Нужно **{price}**, есть **{bal}**", ephemeral=True)
        return
    set_balance(interaction.user.id, bal - price)

    выпало = {}   # (редкость, имя) -> [боец, количество]
    ничего = 0
    новые = []
    for _ in range(количество):
        rarity, fighter = roll_fighter()
        if fighter is None:
            ничего += 1
            continue
        новые.append({**fighter, "rarity": rarity})
        key = (rarity, fighter["name"])
        if key in выпало:
            выпало[key][1] += 1
        else:
            выпало[key] = [fighter, 1]
    if новые:
        add_fighters(interaction.user.id, новые)

    текст = f"📦 **{количество} боксов** за **{price}** ликкеров!\n\n"
    for (rarity, _), (fighter, count) in sorted(
            выпало.items(), key=lambda x: RARITY_ORDER.index(x[0][0]), reverse=True):
        цвет = RARITY_COLORS.get(rarity, "⬜")
        x = f" ×{count}" if count > 1 else ""
        if rarity == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {fighter['emoji']} **{fighter['name']}**{x} +{fighter['income']}/сутки 🤫\n"
        else:
            текст += f"{цвет} **[{rarity}]** {fighter['emoji']} **{fighter['name']}**{x} +{fighter['income']}/сутки\n"
    if ничего:
        текст += f"📭 Пустых боксов: **{ничего}**\n"
    текст += (f"\n📈 Доход: **{get_daily_income(interaction.user.id)}**/сутки\n"
              f"💰 Остаток: **{get_balance(interaction.user.id)}**")
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст)

@tree.command(name="бойцы", description="Мои бойцы")
async def бойцы(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    f_list = get_fighters_list(interaction.user.id)
    if not f_list:
        await interaction.followup.send("❌ Нет бойцов! Открой `/боксы`", ephemeral=True)
        return
    группы = {}
    for f in f_list:
        key = (f.get("rarity", "Редкий"), f["name"])
        if key in группы:
            группы[key][1] += 1
        else:
            группы[key] = [f, 1]
    текст = f"⚔️ **Бойцы {interaction.user.name}** ({len(f_list)}):\n\n"
    for (rarity, _), (f, count) in sorted(
            группы.items(), key=lambda x: RARITY_ORDER.index(x[0][0]) if x[0][0] in RARITY_ORDER else 0,
            reverse=True):
        цвет = RARITY_COLORS.get(rarity, "⬜")
        x = f" ×{count}" if count > 1 else ""
        метка = "СЕКРЕТНЫЙ" if rarity == "Секретный" else rarity
        текст += f"{цвет} **[{метка}]** {f['emoji']} **{f['name']}**{x} +{f['income']}/сутки\n"
    текст += f"\n📈 Доход: **{get_daily_income(interaction.user.id)}**/сутки"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст, ephemeral=True)

@tree.command(name="всебойцы", description="Все возможные бойцы")
async def всебойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    текст = "⚔️ **Все бойцы:**\n\n"
    for rarity in RARITY_ORDER:
        if rarity == "Секретный":
            continue
        цвет = RARITY_COLORS.get(rarity, "⬜")
        текст += f"{цвет} **{rarity}:**\n"
        for f in FIGHTERS[rarity]:
            текст += f"  {f['emoji']} {f['name']} | +{f['income']}/сутки\n"
        текст += "\n"
    текст += "⬛ **Секретный:** ???"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст)


# ===== ЗАПУСК БОТА =====
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("❌ Переменная окружения DISCORD_TOKEN не задана! Добавь её в Environment на Render.")
    threading.Thread(target=run_web, daemon=True).start()
    client.run(DISCORD_TOKEN)

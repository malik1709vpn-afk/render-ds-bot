import os
import random
import json
import asyncio
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

def set_balance(user_id, amount):
    data = load_file(BALANCE_FILE)
    data[str(user_id)] = max(0, amount)
    save_file(BALANCE_FILE, data)


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


@client.event
async def on_ready():
    await tree.sync()
    print(f"Бот запущен: {client.user}")


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
        f"💵 **{bal}** ликкеров")

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
    if победа:
        выигрыш = int(ставка * множитель)
        set_balance(interaction.user.id, bal + выигрыш)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🎲 **Множитель:** x{множитель}\n\n"
            f"🎉 ВЫИГРЫШ!\n"
            f"✅ **{ставка}** × {множитель} = **{выигрыш}** ликкеров!\n"
            f"💰 Баланс: **{new_bal}**")
    else:
        потеря = int(ставка * множитель)
        set_balance(interaction.user.id, max(0, bal - потеря))
        new_bal = get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"🎲 **Множитель:** x{множитель}\n\n"
            f"💀 ПРОИГРЫШ!\n"
            f"❌ **{ставка}** × {множитель} = **{потеря}** ликкеров потеряно!\n"
            f"💰 Баланс: **{new_bal}**")

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


# ===== ЗАПУСК БОТА =====
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("❌ Переменная окружения DISCORD_TOKEN не задана! Добавь её в Environment на Render.")
    threading.Thread(target=run_web, daemon=True).start()
    client.run(DISCORD_TOKEN)

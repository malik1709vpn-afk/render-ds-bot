import math
import time
import discord
from discord import app_commands
import os
import random
import json
from datetime import datetime, timedelta
import asyncio
import pytz
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

BALANCE_FILE = "balance.json"

LEVELS_FILE = "levels.json"
user_last_message = {}

LEVEL_ROLES = {
    1: "😀Новичок(1 лвл)",
    5: "😎Привыкший(5 лвл)",
    10: "😊Знакомый(10 лвл)",
    20: "🕹️Активный(20 лвл)",
}

def get_level_reward(level):
    if level <= 5: return 1000
    elif level <= 15: return 5000
    elif level <= 30: return 10000
    elif level <= 60: return 20000
    elif level <= 100: return 25000
    return 0

def get_level_data():
    return load_file(LEVELS_FILE)

def save_level_data(data):
    save_file(LEVELS_FILE, data)

def get_target_level_role_name(level):
    """Самая высокая роль-уровня, которая уже открыта при данном level."""
    achieved = [lvl for lvl in LEVEL_ROLES if level >= lvl]
    if not achieved:
        return None
    return LEVEL_ROLES[max(achieved)]

async def apply_level_role(member: discord.Member, level: int):
    """Выдаёт нужную роль за уровень и снимает более младшие роли-уровня.
    Используется и при левел-апе, и при возвращении участника на сервер."""
    target_name = get_target_level_role_name(level)
    if not target_name or not member.guild:
        return
    for lvl, role_name in LEVEL_ROLES.items():
        role_obj = discord.utils.get(member.guild.roles, name=role_name)
        if not role_obj:
            continue
        try:
            if role_name == target_name:
                if role_obj not in member.roles:
                    await member.add_roles(role_obj)
            else:
                if role_obj in member.roles:
                    await member.remove_roles(role_obj)
        except:
            pass

FIGHTERS_FILE = "fighters.json"
DECKS_FILE = "decks.json"

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

# Цены на удачу (процент -> цена за бокс доп.)
LUCK_PRICES = {
    10: 50, 20: 120, 30: 220, 40: 350, 50: 500,
    60: 700, 70: 1000, 80: 1400, 90: 2000,
}

# ===== ЗАДАЧКИ ДЛЯ БОЯ =====
QUIZ_QUESTIONS = [
    # === МАТЕМАТИКА ===
    {"question": "🧮 Сколько будет 17 × 13?", "options": ["201", "221", "231", "211"], "answer": 1},
    {"question": "🧮 Сколько будет 256 ÷ 8?", "options": ["28", "30", "32", "34"], "answer": 2},
    {"question": "🧮 Сколько будет 19 × 19?", "options": ["341", "351", "361", "371"], "answer": 2},
    {"question": "🧮 Сколько будет 1000 − 387?", "options": ["603", "613", "623", "633"], "answer": 1},
    {"question": "🧮 Сколько будет 48 × 25?", "options": ["1100", "1150", "1200", "1250"], "answer": 2},
    {"question": "🧮 Сколько будет 144 ÷ 12?", "options": ["10", "11", "12", "13"], "answer": 2},
    {"question": "🧮 Сколько будет 23 × 4?", "options": ["82", "88", "92", "96"], "answer": 2},
    {"question": "🧮 Сколько будет 15 × 15?", "options": ["205", "215", "225", "235"], "answer": 2},
    {"question": "🧮 Сколько будет 360 ÷ 9?", "options": ["36", "38", "40", "42"], "answer": 2},
    {"question": "🧮 Сколько будет 7 × 8 × 3?", "options": ["156", "162", "168", "174"], "answer": 2},
    {"question": "🧮 Сколько будет 450 − 178?", "options": ["262", "272", "282", "292"], "answer": 1},
    {"question": "🧮 Сколько будет 36 × 5?", "options": ["160", "170", "180", "190"], "answer": 2},
    {"question": "🧮 Сколько будет 84 ÷ 7?", "options": ["10", "11", "12", "13"], "answer": 2},
    {"question": "🧮 Сколько будет 13 × 11?", "options": ["133", "143", "153", "163"], "answer": 1},
    {"question": "🧮 Сколько будет 500 − 263?", "options": ["227", "237", "247", "257"], "answer": 1},
    {"question": "🧮 Сколько будет 25 × 12?", "options": ["280", "290", "300", "310"], "answer": 2},
    {"question": "🧮 Сколько будет 63 ÷ 9 × 7?", "options": ["43", "47", "49", "53"], "answer": 2},
    {"question": "🧮 Сколько будет 18 × 6?", "options": ["98", "108", "118", "128"], "answer": 1},
    {"question": "🧮 Сколько будет 720 ÷ 8?", "options": ["80", "85", "90", "95"], "answer": 2},
    {"question": "🧮 Сколько будет 34 × 3?", "options": ["92", "96", "100", "102"], "answer": 3},
    {"question": "🧮 Сколько будет 11 × 11 × 2?", "options": ["222", "232", "242", "252"], "answer": 2},
    {"question": "🧮 Сколько будет 96 ÷ 6?", "options": ["14", "15", "16", "17"], "answer": 2},
    {"question": "🧮 Сколько будет 45 × 8?", "options": ["340", "350", "360", "370"], "answer": 2},
    {"question": "🧮 Сколько будет 1000 ÷ 25?", "options": ["30", "35", "40", "45"], "answer": 2},
    {"question": "🧮 Сколько будет 56 + 78?", "options": ["124", "130", "134", "136"], "answer": 2},
    {"question": "🧮 Сколько будет 9 × 9 − 1?", "options": ["78", "80", "82", "84"], "answer": 1},
    {"question": "🧮 Сколько будет 125 × 8?", "options": ["900", "950", "1000", "1050"], "answer": 2},
    {"question": "🧮 Сколько будет 14 × 14?", "options": ["176", "186", "196", "206"], "answer": 2},
    {"question": "🧮 Сколько будет 300 − 144?", "options": ["146", "154", "156", "166"], "answer": 2},
    {"question": "🧮 Сколько будет 72 ÷ 8 + 15?", "options": ["22", "24", "26", "28"], "answer": 1},

    # === ДРОБИ И ПРОЦЕНТЫ ===
    {"question": "🧮 Сколько будет 1/2 от 80?", "options": ["30", "35", "40", "45"], "answer": 2},
    {"question": "🧮 Сколько будет 1/4 от 120?", "options": ["25", "30", "35", "40"], "answer": 1},
    {"question": "🧮 Сколько будет 3/4 от 100?", "options": ["65", "70", "75", "80"], "answer": 2},
    {"question": "🧮 10% от 250 — это сколько?", "options": ["20", "25", "30", "35"], "answer": 1},
    {"question": "🧮 20% от 60 — это сколько?", "options": ["10", "12", "14", "16"], "answer": 1},
    {"question": "🧮 50% от 84 — это сколько?", "options": ["38", "40", "42", "44"], "answer": 2},
    {"question": "🧮 25% от 200 — это сколько?", "options": ["40", "45", "50", "55"], "answer": 2},
    {"question": "🧮 Сколько будет 2/5 от 50?", "options": ["15", "18", "20", "22"], "answer": 2},
    {"question": "🧮 Сколько будет 3/5 от 60?", "options": ["30", "34", "36", "38"], "answer": 2},
    {"question": "🧮 30% от 90 — это сколько?", "options": ["21", "24", "27", "30"], "answer": 2},

    # === СТЕПЕНИ И КВАДРАТЫ ===
    {"question": "🧮 Сколько будет 2⁸?", "options": ["128", "256", "512", "64"], "answer": 1},
    {"question": "🧮 Сколько будет 3⁴?", "options": ["71", "79", "81", "83"], "answer": 2},
    {"question": "🧮 Сколько будет 5³?", "options": ["105", "115", "125", "135"], "answer": 2},
    {"question": "🧮 Квадратный корень из 144?", "options": ["10", "11", "12", "13"], "answer": 2},
    {"question": "🧮 Квадратный корень из 225?", "options": ["13", "14", "15", "16"], "answer": 2},
    {"question": "🧮 Сколько будет 4³?", "options": ["54", "60", "64", "68"], "answer": 2},
    {"question": "🧮 Квадратный корень из 196?", "options": ["12", "13", "14", "15"], "answer": 2},
    {"question": "🧮 Сколько будет 6²?", "options": ["32", "34", "36", "38"], "answer": 2},
    {"question": "🧮 Сколько будет 12²?", "options": ["134", "140", "144", "148"], "answer": 2},
    {"question": "🧮 Сколько будет 2⁶?", "options": ["54", "60", "64", "68"], "answer": 2},

    # === ГЕОМЕТРИЯ ===
    {"question": "📐 Периметр квадрата со стороной 7 см?", "options": ["21", "24", "28", "32"], "answer": 2},
    {"question": "📐 Площадь прямоугольника 6×9?", "options": ["48", "50", "54", "56"], "answer": 2},
    {"question": "📐 Сколько градусов в прямом угле?", "options": ["45", "60", "90", "180"], "answer": 2},
    {"question": "📐 Сумма углов треугольника?", "options": ["90°", "120°", "180°", "360°"], "answer": 2},
    {"question": "📐 Площадь квадрата со стороной 8?", "options": ["56", "60", "64", "68"], "answer": 2},
    {"question": "📐 Периметр прямоугольника 5×10?", "options": ["25", "28", "30", "32"], "answer": 2},
    {"question": "📐 Сколько сторон у шестиугольника?", "options": ["4", "5", "6", "7"], "answer": 2},
    {"question": "📐 Диагональ делит прямоугольник на сколько треугольников?", "options": ["1", "2", "3", "4"], "answer": 1},
    {"question": "📐 Площадь треугольника с основанием 10 и высотой 6?", "options": ["25", "28", "30", "32"], "answer": 2},
    {"question": "📐 Сколько градусов в развёрнутом угле?", "options": ["90", "120", "180", "270"], "answer": 2},

    # === ЗАДАЧИ НА ЛОГИКУ И СКОРОСТЬ ===
    {"question": "🚂 Поезд едет 60 км/ч. За 3 часа проедет сколько км?", "options": ["150", "170", "180", "200"], "answer": 2},
    {"question": "🚶 Пешеход идёт 5 км/ч. За 4 часа пройдёт сколько км?", "options": ["15", "18", "20", "25"], "answer": 2},
    {"question": "🚗 Машина едет 90 км/ч. 270 км проедет за сколько часов?", "options": ["2", "3", "4", "5"], "answer": 1},
    {"question": "⏱️ В 1 часе минут — сколько в 3.5 часах?", "options": ["180", "200", "210", "220"], "answer": 2},
    {"question": "📦 Коробка вмещает 12 яблок. 9 коробок — сколько яблок?", "options": ["96", "104", "108", "112"], "answer": 2},
    {"question": "🍕 Пиццу делят на 8 кусков. Съели 3/8 — сколько кусков осталось?", "options": ["3", "4", "5", "6"], "answer": 2},
    {"question": "💰 Купил за 350 р, дал 500 р. Сдача?", "options": ["130", "140", "150", "160"], "answer": 2},
    {"question": "📚 В классе 30 учеников, 2/5 — мальчики. Сколько мальчиков?", "options": ["10", "12", "14", "16"], "answer": 1},
    {"question": "🍎 Купили 5 кг яблок по 40 р/кг. Итого?", "options": ["160", "180", "200", "220"], "answer": 2},
    {"question": "🐄 На ферме 7 коров, каждая даёт 12 л молока. Итого литров?", "options": ["74", "80", "84", "90"], "answer": 2},

    # === ЧИСЛА И ДЕЛИТЕЛИ ===
    {"question": "🔢 Наименьшее общее кратное 4 и 6?", "options": ["8", "10", "12", "14"], "answer": 2},
    {"question": "🔢 НОД числа 12 и 18?", "options": ["3", "4", "6", "9"], "answer": 2},
    {"question": "🔢 Какое число делится и на 3, и на 4?", "options": ["8", "9", "12", "14"], "answer": 2},
    {"question": "🔢 Простое число из списка?", "options": ["21", "27", "29", "33"], "answer": 2},
    {"question": "🔢 Сколько делителей у числа 12?", "options": ["4", "5", "6", "7"], "answer": 2},
    {"question": "🔢 На что делится число 1125?", "options": ["Только на 3", "На 3 и 5", "На 3, 5 и 9", "На 5 и 7"], "answer": 2},
    {"question": "🔢 Следующее простое число после 13?", "options": ["14", "15", "16", "17"], "answer": 3},
    {"question": "🔢 Сколько чётных чисел от 1 до 20?", "options": ["8", "9", "10", "11"], "answer": 2},
    {"question": "🔢 Чему равно НОК(5, 7)?", "options": ["12", "25", "35", "70"], "answer": 2},
    {"question": "🔢 Какое из чисел делится на 9?", "options": ["124", "135", "146", "157"], "answer": 1},

    # === УРАВНЕНИЯ ===
    {"question": "✏️ x + 17 = 50. Чему равен x?", "options": ["23", "28", "33", "37"], "answer": 2},
    {"question": "✏️ 3x = 72. Чему равен x?", "options": ["20", "22", "24", "26"], "answer": 2},
    {"question": "✏️ x − 14 = 29. Чему равен x?", "options": ["39", "41", "43", "45"], "answer": 2},
    {"question": "✏️ 5x + 3 = 28. Чему равен x?", "options": ["3", "4", "5", "6"], "answer": 2},
    {"question": "✏️ 2x − 6 = 18. Чему равен x?", "options": ["10", "11", "12", "13"], "answer": 2},
    {"question": "✏️ x ÷ 4 = 13. Чему равен x?", "options": ["48", "50", "52", "54"], "answer": 2},
    {"question": "✏️ 7x = 63. Чему равен x?", "options": ["7", "8", "9", "10"], "answer": 2},
    {"question": "✏️ 4x − 8 = 20. Чему равен x?", "options": ["5", "6", "7", "8"], "answer": 2},
    {"question": "✏️ x/3 + 5 = 14. Чему равен x?", "options": ["21", "24", "27", "30"], "answer": 2},
    {"question": "✏️ 6x + 6 = 42. Чему равен x?", "options": ["4", "5", "6", "7"], "answer": 2},
]

# Активные бои: {(user1_id, user2_id): данные}
active_battles = {}

# ===== ФАЙЛОВЫЕ ФУНКЦИИ =====
def load_file(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def process_xp(member):
    now = time.time()
    if now - user_last_message.get(member.id, 0) < 5: return
    user_last_message[member.id] = now
    
    data = get_level_data()
    u_id = str(member.id)
    u = data.get(u_id, {"xp": 0, "level": 1})
    
    xp_gain = random.randint(5, 15)
    if member.voice and member.voice.channel and not member.voice.self_mute:
        xp_gain += 5
    
    u["xp"] += xp_gain
    new_level = int(math.sqrt(u["xp"]) / 10) + 1
    
    if new_level > u["level"]:
        reward = get_level_reward(new_level)
        set_balance(member.id, get_balance(member.id) + reward)
        u["level"] = new_level
        await apply_level_role(member, new_level)
        try:
            await member.send(f"🎉 Вы апнули {new_level} уровень! Получили {reward} ликкеров.")
        except:
            pass
    
    data[u_id] = u
    save_level_data(data)

def get_balance(user_id):
    data = load_file(BALANCE_FILE)
    return data.get(str(user_id), 0)

def set_balance(user_id, amount):
    data = load_file(BALANCE_FILE)
    data[str(user_id)] = max(0, amount)
    save_file(BALANCE_FILE, data)

def get_fighters_list(user_id):
    data = load_file(FIGHTERS_FILE)
    return data.get(str(user_id), [])

def add_fighter(user_id, fighter):
    data = load_file(FIGHTERS_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = []
    data[str(user_id)].append(fighter)
    save_file(FIGHTERS_FILE, data)

def get_hourly_income(user_id):
    return sum(f["income"] for f in get_fighters_list(user_id))

def get_decks(user_id):
    data = load_file(DECKS_FILE)
    return data.get(str(user_id), {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []})

def save_deck(user_id, deck_name, fighters):
    data = load_file(DECKS_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = {"К1": [], "К2": [], "К3": [], "К4": [], "К5": []}
    data[str(user_id)][deck_name] = fighters
    save_file(DECKS_FILE, data)

def get_best_deck(user_id):
    decks = get_decks(user_id)
    best = None
    best_power = -1
    best_name = None
    for name, deck in decks.items():
        if deck:
            power = sum(f.get("power", 0) for f in deck)
            if power > best_power:
                best_power = power
                best = deck
                best_name = name
    return best_name, best

def get_used_fighters_in_decks(user_id):
    """Возвращает список имён бойцов, уже занятых в колодах"""
    decks = get_decks(user_id)
    used = []
    for deck in decks.values():
        for f in deck:
            used.append(f["name"])
    return used

def roll_fighter(luck_bonus=0):
    chances = []
    total = 0
    for rarity, chance in RARITY_CHANCES:
        adj = chance if rarity == "Секретный" else chance + (luck_bonus / 100) * chance
        chances.append((rarity, adj))
        total += adj
    r = random.uniform(0, total)
    current = 0
    for rarity, chance in chances:
        current += chance
        if r <= current:
            fighter = random.choice(FIGHTERS[rarity])
            return rarity, fighter
    return "Редкий", random.choice(FIGHTERS["Редкий"])

def has_role(member, role_name):
    return any(r.name == role_name for r in member.roles)

def get_role_index(member):
    for i in range(len(SHOP_ROLES) - 1, -1, -1):
        if has_role(member, SHOP_ROLES[i][1]):
            return i
    return -1

async def bonus_loop():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_bonus = -1
    while True:
        now = datetime.now(msk)
        slot = now.hour // 6
        if slot != last_bonus:
            data = load_file(BALANCE_FILE)
            for uid in data:
                data[uid] = max(0, data[uid] + 100)
            save_file(BALANCE_FILE, data)
            last_bonus = slot
        await asyncio.sleep(60)

async def income_loop():
    await client.wait_until_ready()
    msk = pytz.timezone("Europe/Moscow")
    last_hour = -1
    while True:
        now = datetime.now(msk)
        if now.hour != last_hour:
            fighters_data = load_file(FIGHTERS_FILE)
            bal_data = load_file(BALANCE_FILE)
            for uid, f_list in fighters_data.items():
                income = sum(f["income"] for f in f_list)
                if income > 0:
                    bal_data[uid] = bal_data.get(uid, 0) + income
            save_file(BALANCE_FILE, bal_data)
            last_hour = now.hour
        await asyncio.sleep(60)

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
    client.loop.create_task(bonus_loop())
    client.loop.create_task(income_loop())

@client.event
async def on_message(message):
    if message.author.bot or not message.guild:
        return
    await process_xp(message.author)

@client.event
async def on_member_join(member):
    if member.bot:
        return
    # Стартовая валюта — только тем, кого мы видим первый раз
    bal_data = load_file(BALANCE_FILE)
    uid = str(member.id)
    if uid not in bal_data:
        bal_data[uid] = 1000
        save_file(BALANCE_FILE, bal_data)
    # Возвращаем роль за уровень, если участник уже играл раньше (уровень/опыт не теряются при выходе)
    level_data = get_level_data()
    u = level_data.get(uid)
    if u:
        await apply_level_role(member, u.get("level", 1))

# ===== МАГАЗИН =====
class ShopMainView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="🎭 Роли", style=discord.ButtonStyle.primary, row=0)
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🔓 Команды", style=discord.ButtonStyle.secondary, row=0)
    async def commands_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🔓 **Магазин команд**\nСкоро откроется! 🔜", view=BackExitView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=0)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class BackExitView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary)
    async def back(self, interaction: discord.Interaction, button: discord.ui.Button):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
            view=ShopMainView())

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger)
    async def exit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class ShopRolesView(discord.ui.View):
    def __init__(self, page, member):
        super().__init__(timeout=60)
        current_index = get_role_index(member)
        start = page * 4
        end = min(start + 4, len(SHOP_ROLES))
        for i in range(start, end):
            price, name, emoji = SHOP_ROLES[i]
            owned = has_role(member, name)
            locked = i > current_index + 1
            self.add_item(RoleButton(price, name, emoji, owned, locked))
        if end < len(SHOP_ROLES):
            self.add_item(NextPageButton(page + 1, member))
        if page > 0:
            self.add_item(PrevPageButton(page - 1, member))
        self.add_item(BackMainButton())
        self.add_item(ExitShopButton())

class RoleButton(discord.ui.Button):
    def __init__(self, price, name, emoji, owned, locked):
        if owned:
            label, style, disabled = f"✅ {name}", discord.ButtonStyle.success, True
        elif locked:
            label, style, disabled = f"🔒 {name}", discord.ButtonStyle.secondary, True
        else:
            label, style, disabled = f"{emoji} {price} — {name}", discord.ButtonStyle.primary, False
        super().__init__(label=label[:80], style=style, disabled=disabled)
        self.price = price
        self.name = name
        self.emoji_icon = emoji

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        await interaction.response.edit_message(
            content=f"❓ **Покупка**\n{self.emoji_icon} **{self.name}**\nЦена: **{self.price}** | Баланс: **{bal}**\n\nУверены?",
            view=ConfirmBuyView(self.price, self.name, self.emoji_icon))

class ConfirmBuyView(discord.ui.View):
    def __init__(self, price, name, emoji):
        super().__init__(timeout=30)
        self.price = price
        self.name = name
        self.emoji = emoji

    @discord.ui.button(label="✅ Купить", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if has_role(interaction.user, self.name):
            await interaction.response.edit_message(content="❌ Уже есть!", view=BackExitView())
            return
        bal = get_balance(interaction.user.id)
        if bal < self.price:
            await interaction.response.edit_message(content=f"❌ Мало ликкеров! Нужно **{self.price}**, есть **{bal}**", view=BackExitView())
            return
        role = discord.utils.get(interaction.guild.roles, name=self.name)
        if not role:
            try:
                role = await interaction.guild.create_role(name=self.name)
            except:
                await interaction.response.edit_message(content="❌ Ошибка создания роли!", view=BackExitView())
                return
        try:
            await interaction.user.add_roles(role)
        except:
            await interaction.response.edit_message(content="❌ Ошибка выдачи роли! Проверь иерархию.", view=BackExitView())
            return
        set_balance(interaction.user.id, bal - self.price)
        new_bal = get_balance(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎉 Роль **{self.emoji} {self.name}** получена!\n💰 Остаток: **{new_bal}**",
            view=BackExitView())

    @discord.ui.button(label="❌ Отмена", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="🚫 Отменено!", view=ShopRolesView(0, interaction.user))

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.secondary)
    async def exit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class NextPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="▶️ Далее", style=discord.ButtonStyle.primary, row=2)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(self.page, interaction.user))

class PrevPageButton(discord.ui.Button):
    def __init__(self, page, member):
        super().__init__(label="◀️ Назад", style=discord.ButtonStyle.secondary, row=2)
        self.page = page
        self.member = member

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🎭 **Магазин ролей**\n💰 **{bal}** | 📈 **{income}**/час\n\nВыбери роль:",
            view=ShopRolesView(self.page, interaction.user))

class BackMainButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🏪 В меню", style=discord.ButtonStyle.secondary, row=2)

    async def callback(self, interaction: discord.Interaction):
        bal = get_balance(interaction.user.id)
        income = get_hourly_income(interaction.user.id)
        await interaction.response.edit_message(
            content=f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
            view=ShopMainView())

class ExitShopButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=2)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ===== КОЛОДА =====
class DeckMainView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        decks = get_decks(user_id)
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            deck = decks.get(name, [])
            power = sum(f.get("power", 0) for f in deck)
            label = f"{name} {'⚔️' if deck else '🆕'} [{power}]" if deck else f"{name} 🆕"
            self.add_item(DeckSelectButton(name, label, user_id))
        self.add_item(ExitDeckButton())

class DeckSelectButton(discord.ui.Button):
    def __init__(self, deck_name, label, user_id):
        super().__init__(label=label, style=discord.ButtonStyle.primary if deck_name else discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        decks = get_decks(self.user_id)
        deck = decks.get(self.deck_name, [])
        f_list = get_fighters_list(self.user_id)
        await interaction.response.edit_message(
            content=f"⚔️ **Колода {self.deck_name}**\nБойцов в колоде: **{len(deck)}/5**\n\nВыбери действие:",
            view=DeckEditView(self.deck_name, self.user_id, deck, f_list))

class DeckEditView(discord.ui.View):
    def __init__(self, deck_name, user_id, deck, f_list):
        super().__init__(timeout=120)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    @discord.ui.button(label="➕ Добавить бойца", style=discord.ButtonStyle.success, row=0)
    async def add_fighter_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if len(self.deck) >= 5:
            await interaction.response.send_message("❌ В колоде уже 5 бойцов!", ephemeral=True)
            return
        if not self.f_list:
            await interaction.response.send_message("❌ У тебя нет бойцов! Открой `/боксы`", ephemeral=True)
            return
        # Фильтруем бойцов занятых в других колодах
        used = get_used_fighters_in_decks(self.user_id)
        current_deck_names = [f["name"] for f in self.deck]
        available = [f for f in self.f_list if f["name"] not in used or f["name"] in current_deck_names]
        if not available:
            await interaction.response.send_message("❌ Все бойцы уже в других колодах!", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"➕ **Выбери бойца для колоды {self.deck_name}:**",
            view=AddFighterView(self.deck_name, self.user_id, self.deck, available, 0))

    @discord.ui.button(label="🏆 Сильнейшая", style=discord.ButtonStyle.primary, row=0)
    async def best_deck_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        f_list = get_fighters_list(self.user_id)
        if not f_list:
            await interaction.response.send_message("❌ Нет бойцов!", ephemeral=True)
            return
        # Берём бойцов, не занятых в других колодах (кроме текущей)
        decks = get_decks(self.user_id)
        other_used = []
        for dk_name, dk in decks.items():
            if dk_name != self.deck_name:
                for f in dk:
                    other_used.append(f["name"])
        available = [f for f in f_list if f["name"] not in other_used]
        sorted_f = sorted(available, key=lambda x: x.get("power", 0), reverse=True)
        best = sorted_f[:5]
        save_deck(self.user_id, self.deck_name, best)
        текст = f"🏆 **Колода {self.deck_name}** — сильнейшие бойцы:\n\n"
        for f in best:
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            текст += f"{цвет} {f['emoji']} **{f['name']}** | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        await interaction.response.edit_message(content=текст, view=DeckEditView(self.deck_name, self.user_id, best, f_list))

    @discord.ui.button(label="🗑️ Очистить", style=discord.ButtonStyle.danger, row=0)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        save_deck(self.user_id, self.deck_name, [])
        await interaction.response.edit_message(
            content=f"✅ Колода **{self.deck_name}** очищена!",
            view=DeckEditView(self.deck_name, self.user_id, [], self.f_list))

    @discord.ui.button(label="📋 Показать", style=discord.ButtonStyle.secondary, row=1)
    async def show_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.deck:
            await interaction.response.edit_message(content=f"❌ Колода **{self.deck_name}** пуста!", view=self)
            return
        текст = f"⚔️ **Колода {self.deck_name}:**\n\n"
        total_power = 0
        for f in self.deck:
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            текст += f"{цвет} {f['emoji']} **{f['name']}** | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
            total_power += f.get("power", 0)
        текст += f"\n💪 Общая сила: **{total_power}**"
        await interaction.response.edit_message(content=текст, view=self)

    @discord.ui.button(label="◀️ Назад", style=discord.ButtonStyle.secondary, row=1)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        decks = get_decks(self.user_id)
        текст = "⚔️ **Мои колоды:**\n\n"
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            deck = decks.get(name, [])
            power = sum(f.get("power", 0) for f in deck)
            текст += f"{'⚔️' if deck else '🆕'} **{name}** — {len(deck)}/5 бойцов | Сила: {power}\n"
        await interaction.response.edit_message(content=текст, view=DeckMainView(self.user_id))

    @discord.ui.button(label="🚪 Выйти", style=discord.ButtonStyle.danger, row=1)
    async def exit_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

class AddFighterView(discord.ui.View):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(timeout=120)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page
        start = page * 5
        end = min(start + 5, len(f_list))
        for i in range(start, end):
            f = f_list[i]
            цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
            label = f"{цвет} {f['emoji']} {f['name'][:20]} 💪{f['power']}"
            self.add_item(FighterPickButton(f, label, deck_name, user_id, deck, f_list))
        if end < len(f_list):
            self.add_item(NextFighterPage(deck_name, user_id, deck, f_list, page + 1))
        if page > 0:
            self.add_item(PrevFighterPage(deck_name, user_id, deck, f_list, page - 1))
        self.add_item(BackToDeckButton(deck_name, user_id, deck, f_list))

class FighterPickButton(discord.ui.Button):
    def __init__(self, fighter, label, deck_name, user_id, deck, f_list):
        super().__init__(label=label[:80], style=discord.ButtonStyle.success)
        self.fighter = fighter
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    async def callback(self, interaction: discord.Interaction):
        if len(self.deck) >= 5:
            await interaction.response.send_message("❌ Колода полна!", ephemeral=True)
            return
        new_deck = self.deck + [self.fighter]
        save_deck(self.user_id, self.deck_name, new_deck)
        await interaction.response.edit_message(
            content=f"✅ **{self.fighter['emoji']} {self.fighter['name']}** добавлен в колоду **{self.deck_name}**!\nБойцов: **{len(new_deck)}/5**",
            view=DeckEditView(self.deck_name, self.user_id, new_deck, self.f_list))

class NextFighterPage(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(label="▶️", style=discord.ButtonStyle.primary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=AddFighterView(self.deck_name, self.user_id, self.deck, self.f_list, self.page))

class PrevFighterPage(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list, page):
        super().__init__(label="◀️", style=discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list
        self.page = page

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=AddFighterView(self.deck_name, self.user_id, self.deck, self.f_list, self.page))

class BackToDeckButton(discord.ui.Button):
    def __init__(self, deck_name, user_id, deck, f_list):
        super().__init__(label="◀️ Назад", style=discord.ButtonStyle.secondary)
        self.deck_name = deck_name
        self.user_id = user_id
        self.deck = deck
        self.f_list = f_list

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            content=f"⚔️ **Колода {self.deck_name}** — {len(self.deck)}/5 бойцов",
            view=DeckEditView(self.deck_name, self.user_id, self.deck, self.f_list))

class ExitDeckButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="🚪 Выйти", style=discord.ButtonStyle.danger)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="👋 Закрыто!", view=None)
        await asyncio.sleep(3)
        try:
            await interaction.delete_original_response()
        except:
            pass

# ===== НОВАЯ СИСТЕМА БОЯ =====

class BattleInviteView(discord.ui.View):
    """Приглашение на бой — показывается оппоненту"""
    def __init__(self, challenger: discord.Member, opponent: discord.Member, bet: int, channel):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.channel = channel

    @discord.ui.button(label="✅ Принять", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("❌ Это не твой вызов!", ephemeral=True)
            return
        # Проверяем балансы (только если ставка > 0)
        ch_bal = get_balance(self.challenger.id)
        op_bal = get_balance(self.opponent.id)
        if self.bet > 0:
            if ch_bal < self.bet:
                await interaction.response.edit_message(
                    content=f"❌ У **{self.challenger.name}** не хватает ликкеров для ставки!", view=None)
                return
            if op_bal < self.bet:
                await interaction.response.edit_message(
                    content=f"❌ У тебя не хватает ликкеров! Нужно **{self.bet}**", view=None)
                return
            set_balance(self.challenger.id, ch_bal - self.bet)
            set_balance(self.opponent.id, op_bal - self.bet)
        await interaction.response.edit_message(
            content=f"⚔️ **{self.challenger.name}** vs **{self.opponent.name}**\n💰 Ставка: **{self.bet}** ликкеров каждый\n\n{self.challenger.mention}, выбери колоду для боя:",
            view=BattleDeckSelectView(self.challenger, self.opponent, self.bet, self.channel, phase="challenger"))

    @discord.ui.button(label="❌ Отклонить", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("❌ Это не твой вызов!", ephemeral=True)
            return
        await interaction.response.edit_message(
            content=f"❌ **{self.opponent.name}** отклонил вызов!", view=None)


class BattleDeckSelectView(discord.ui.View):
    """Выбор колоды для боя"""
    def __init__(self, challenger: discord.Member, opponent: discord.Member, bet: int, channel,
                 phase: str, challenger_deck=None, challenger_deck_name=None):
        super().__init__(timeout=60)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.channel = channel
        self.phase = phase  # "challenger" или "opponent"
        self.challenger_deck = challenger_deck
        self.challenger_deck_name = challenger_deck_name

        # Определяем чьи колоды показываем
        current_user = challenger if phase == "challenger" else opponent
        decks = get_decks(current_user.id)
        for name in ["К1", "К2", "К3", "К4", "К5"]:
            deck = decks.get(name, [])
            if deck:
                power = sum(f.get("power", 0) for f in deck)
                self.add_item(BattleDeckChoiceButton(
                    name, power, deck,
                    challenger, opponent, bet, channel,
                    phase, challenger_deck, challenger_deck_name))

        self.add_item(BattleCancelRefundButton(challenger, opponent, bet))


class BattleDeckChoiceButton(discord.ui.Button):
    def __init__(self, deck_name, power, deck, challenger, opponent, bet, channel,
                 phase, challenger_deck, challenger_deck_name):
        super().__init__(label=f"{deck_name} 💪{power}", style=discord.ButtonStyle.primary)
        self.deck_name = deck_name
        self.deck = deck
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet
        self.channel = channel
        self.phase = phase
        self.challenger_deck = challenger_deck
        self.challenger_deck_name = challenger_deck_name

    async def callback(self, interaction: discord.Interaction):
        expected_id = self.challenger.id if self.phase == "challenger" else self.opponent.id
        if interaction.user.id != expected_id:
            await interaction.response.send_message("❌ Сейчас не твой ход!", ephemeral=True)
            return

        if self.phase == "challenger":
            # Challenger выбрал — теперь opponent выбирает
            await interaction.response.edit_message(
                content=f"⚔️ **{self.challenger.name}** выбрал колоду **{self.deck_name}**!\n\n{self.opponent.mention}, теперь твоя очередь — выбери колоду:",
                view=BattleDeckSelectView(
                    self.challenger, self.opponent, self.bet, self.channel,
                    phase="opponent",
                    challenger_deck=self.deck,
                    challenger_deck_name=self.deck_name))
        else:
            # Оба выбрали — запускаем бой
            await interaction.response.edit_message(
                content=f"⚔️ **Бой начинается!**\n\n**{self.challenger.name}** ({self.challenger_deck_name}) vs **{self.opponent.name}** ({self.deck_name})\n\n⏳ Идёт подготовка...",
                view=None)
            await asyncio.sleep(2)
            msg = await interaction.original_response()
            await run_battle(
                msg, self.channel,
                self.challenger, self.opponent, self.bet,
                self.challenger_deck, self.challenger_deck_name,
                self.deck, self.deck_name)


class BattleCancelRefundButton(discord.ui.Button):
    def __init__(self, challenger, opponent, bet):
        super().__init__(label="❌ Отмена (возврат ставок)", style=discord.ButtonStyle.danger)
        self.challenger = challenger
        self.opponent = opponent
        self.bet = bet

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in [self.challenger.id, self.opponent.id]:
            await interaction.response.send_message("❌ Не твой бой!", ephemeral=True)
            return
        # Возвращаем ставки
        set_balance(self.challenger.id, get_balance(self.challenger.id) + self.bet)
        set_balance(self.opponent.id, get_balance(self.opponent.id) + self.bet)
        await interaction.response.edit_message(
            content=f"❌ Бой отменён! Ставки возвращены:\n{self.challenger.mention}: +{self.bet}\n{self.opponent.mention}: +{self.bet}",
            view=None)


class QuizView(discord.ui.View):
    """Задачка во время раунда"""
    def __init__(self, question_data, challenger_id, opponent_id):
        super().__init__(timeout=15)
        self.question_data = question_data
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.answered = {}  # user_id -> bool (правильно/нет)
        labels = ["🅐", "🅑", "🅒", "🅓"]
        for i, opt in enumerate(question_data["options"]):
            self.add_item(QuizAnswerButton(i, f"{labels[i]} {opt}", question_data["answer"], self))

    def get_boost(self, user_id):
        return self.answered.get(user_id, False)


class QuizAnswerButton(discord.ui.Button):
    def __init__(self, index, label, correct_index, quiz_view):
        super().__init__(label=label[:80], style=discord.ButtonStyle.secondary)
        self.index = index
        self.correct_index = correct_index
        self.quiz_view = quiz_view

    async def callback(self, interaction: discord.Interaction):
        uid = interaction.user.id
        if uid not in [self.quiz_view.challenger_id, self.quiz_view.opponent_id]:
            await interaction.response.send_message("❌ Ты не участник этого боя!", ephemeral=True)
            return
        if uid in self.quiz_view.answered:
            await interaction.response.send_message("✋ Ты уже ответил!", ephemeral=True)
            return
        correct = self.index == self.correct_index
        self.quiz_view.answered[uid] = correct
        if correct:
            await interaction.response.send_message("✅ Правильно! Твои бойцы получат буст в этом раунде!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Неправильно! Буста не будет.", ephemeral=True)


async def run_battle(message, channel, challenger: discord.Member, opponent: discord.Member,
                     bet: int, ch_deck: list, ch_deck_name: str, op_deck: list, op_deck_name: str):
    """Бой с пошаговой анимацией — каждая атака редактирует сообщение каждые 2 сек"""

    def make_hp(deck):
        fighters = []
        for f in deck:
            hp = f["def"] * 5 + f["power"] * 2
            fighters.append({**f, "hp": hp, "max_hp": hp})
        return fighters

    def hp_bar(hp, max_hp):
        pct = hp / max_hp
        filled = int(pct * 8)
        bar = "█" * filled + "░" * (8 - filled)
        return f"[{bar}] {hp}/{max_hp}"

    def side_status(fighters, name):
        if not fighters:
            return f"**{name}:** 💀 все выбыли"
        lines = []
        for f in fighters:
            lines.append(f"  {f['emoji']} **{f['name']}** {hp_bar(f['hp'], f['max_hp'])}")
        return f"**{name}:**\n" + "\n".join(lines)

    ch_fighters = make_hp(ch_deck)
    op_fighters = make_hp(op_deck)
    round_num = 0

    while ch_fighters and op_fighters:
        round_num += 1

        # === ЗАДАЧКА ===
        q = random.choice(QUIZ_QUESTIONS)
        quiz_view = QuizView(q, challenger.id, opponent.id)
        quiz_text = (
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚔️ **РАУНД {round_num}** начинается!\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🧮 **ЗАДАЧА (15 сек):**\n{q['question']}\n\n"
            f"✅ Правильный ответ = буст **x1.5–2.0** твоим бойцам!\n\n"
            f"{side_status(ch_fighters, challenger.name)}\n\n"
            f"{side_status(op_fighters, opponent.name)}"
        )
        try:
            await message.edit(content=quiz_text[:1900], view=quiz_view)
        except:
            pass
        await asyncio.sleep(15)
        quiz_view.stop()

        ch_boost = round(random.uniform(1.5, 2.0), 2) if quiz_view.get_boost(challenger.id) else 1.0
        op_boost = round(random.uniform(1.5, 2.0), 2) if quiz_view.get_boost(opponent.id) else 1.0

        # === АНИМАЦИЯ БОЯ ===
        # Формируем очередь атак: перемешиваем бойцов обеих сторон
        # Каждый боец атакует случайного живого врага — показываем по одной атаке

        # Собираем все атаки раунда заранее (чтобы не было проблем с мёртвыми)
        attacks = []
        ch_alive = list(ch_fighters)
        op_alive = list(op_fighters)

        # Перемешиваем порядок атак (случайный боец любой стороны)
        all_attackers = [(f, "ch") for f in ch_alive] + [(f, "op") for f in op_alive]
        random.shuffle(all_attackers)

        temp_ch = {f["name"]: f for f in ch_fighters}
        temp_op = {f["name"]: f for f in op_fighters}

        for attacker_orig, side in all_attackers:
            if side == "ch":
                # Атакует боец challenger
                a = temp_ch.get(attacker_orig["name"])
                if not a:
                    continue
                alive_enemies = [f for f in temp_op.values() if f["hp"] > 0]
                if not alive_enemies:
                    break
                target = random.choice(alive_enemies)
                raw_dmg = max(1, int(a["atk"] * ch_boost) - target["def"] // 3)
                dmg = max(1, raw_dmg + random.randint(-3, 5))
                died = (target["hp"] - dmg) <= 0
                attacks.append({
                    "side": "ch",
                    "atk_emoji": a["emoji"], "atk_name": a["name"],
                    "def_emoji": target["emoji"], "def_name": target["name"],
                    "dmg": dmg, "died": died,
                    "boost": ch_boost,
                    "target_name": target["name"],
                    "hp_before": target["hp"],
                    "hp_after": max(0, target["hp"] - dmg),
                    "hp_max": target["max_hp"],
                })
                target["hp"] = max(0, target["hp"] - dmg)
                if target["hp"] <= 0:
                    del temp_op[target["name"]]
            else:
                # Атакует боец opponent
                a = temp_op.get(attacker_orig["name"])
                if not a:
                    continue
                alive_enemies = [f for f in temp_ch.values() if f["hp"] > 0]
                if not alive_enemies:
                    break
                target = random.choice(alive_enemies)
                raw_dmg = max(1, int(a["atk"] * op_boost) - target["def"] // 3)
                dmg = max(1, raw_dmg + random.randint(-3, 5))
                died = (target["hp"] - dmg) <= 0
                attacks.append({
                    "side": "op",
                    "atk_emoji": a["emoji"], "atk_name": a["name"],
                    "def_emoji": target["emoji"], "def_name": target["name"],
                    "dmg": dmg, "died": died,
                    "target_name": target["name"],
                    "hp_before": target["hp"],
                    "hp_after": max(0, target["hp"] - dmg),
                    "hp_max": target["max_hp"],
                    "boost": op_boost,
                })
                target["hp"] = max(0, target["hp"] - dmg)
                if target["hp"] <= 0:
                    del temp_ch[target["name"]]

        # Применяем итоговые HP к реальным спискам
        for f in ch_fighters:
            if f["name"] in temp_ch:
                f["hp"] = temp_ch[f["name"]]["hp"]
            else:
                f["hp"] = 0
        for f in op_fighters:
            if f["name"] in temp_op:
                f["hp"] = temp_op[f["name"]]["hp"]
            else:
                f["hp"] = 0

        ch_fighters = [f for f in ch_fighters if f["hp"] > 0]
        op_fighters = [f for f in op_fighters if f["hp"] > 0]

        # Показываем атаки одну за одной с паузой 2 сек
        shown_lines = []
        header = f"━━━━━━━━━━━━━━━━━━━━━\n⚔️ **РАУНД {round_num}**"
        if ch_boost > 1.0:
            header += f"\n⚡ {challenger.name} буст x{ch_boost}!"
        if op_boost > 1.0:
            header += f"\n⚡ {opponent.name} буст x{op_boost}!"
        header += "\n━━━━━━━━━━━━━━━━━━━━━\n"

        for atk in attacks:
            side_arrow = "🔴" if atk["side"] == "ch" else "🔵"
            boost_tag = f" ⚡x{atk['boost']}" if atk["boost"] > 1.0 else ""
            line = (
                f"{side_arrow} {atk['atk_emoji']} **{atk['atk_name']}**{boost_tag} "
                f"⟶ {atk['def_emoji']} **{atk['def_name']}** "
                f"[-**{atk['dmg']}** HP] ({atk['hp_after']}/{atk['hp_max']})"
            )
            if atk["died"]:
                line += f"\n   💀 **{atk['def_emoji']} {atk['def_name']} выбыл!**"
            shown_lines.append(line)

            display = header + "\n".join(shown_lines[-12:])  # последние 12 строк
            try:
                await message.edit(content=display[:1900], view=None)
            except:
                pass
            await asyncio.sleep(2)

        # Итог раунда — показываем финальный статус HP
        status_text = (
            header
            + "\n".join(shown_lines[-8:])
            + f"\n\n{'─'*21}\n"
            + f"{side_status(ch_fighters, challenger.name)}\n\n"
            + f"{side_status(op_fighters, opponent.name)}"
        )
        try:
            await message.edit(content=status_text[:1900], view=None)
        except:
            pass

        if not ch_fighters or not op_fighters:
            break

        await asyncio.sleep(4)

    # === ИТОГ ===
    if ch_fighters and not op_fighters:
        winner, loser = challenger, opponent
    elif op_fighters and not ch_fighters:
        winner, loser = opponent, challenger
    else:
        # Ничья
        if bet > 0:
            set_balance(challenger.id, get_balance(challenger.id) + bet)
            set_balance(opponent.id, get_balance(opponent.id) + bet)
            draw_text = f"⚔️ **НИЧЬЯ!**\n\nОба потеряли всех бойцов одновременно!\n💰 Ставки возвращены: по **{bet}** ликкеров"
        else:
            draw_text = "⚔️ **НИЧЬЯ!**\n\nОба потеряли всех бойцов одновременно!"
        try:
            await message.edit(content=draw_text, view=None)
        except:
            pass
        return

    if bet > 0:
        prize = bet * 2
        set_balance(winner.id, get_balance(winner.id) + prize)
        prize_text = f"💰 {winner.mention} забирает **{prize}** ликкеров!\n📊 Баланс {winner.name}: **{get_balance(winner.id)}**\n📊 Баланс {loser.name}: **{get_balance(loser.id)}**"
    else:
        prize_text = "🎮 Бой был товарищеским — без ставок!"

    result_text = (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 **БОЙ ЗАВЕРШЁН!** (Раунд {round_num})\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🥇 **ПОБЕДИТЕЛЬ: {winner.name}** 🎉\n"
        f"💀 Проиграл: {loser.name}\n\n"
        f"{prize_text}"
    )
    try:
        await message.edit(content=result_text[:1900], view=None)
    except:
        pass


# ===== БОКСЫ С УДАЧЕЙ =====
class BoxLuckView(discord.ui.View):
    """Выбор % удачи при покупке боксов"""
    def __init__(self, количество: int, user_id: int):
        super().__init__(timeout=60)
        self.количество = количество
        self.user_id = user_id
        # Базовая кнопка (без удачи)
        self.add_item(LuckButton(0, количество, user_id, row=0))
        # 10-40%
        for pct in [10, 20, 30, 40]:
            self.add_item(LuckButton(pct, количество, user_id, row=1))
        # 50-80%
        for pct in [50, 60, 70, 80]:
            self.add_item(LuckButton(pct, количество, user_id, row=2))
        # 90%
        self.add_item(LuckButton(90, количество, user_id, row=3))
        self.add_item(CancelBoxButton(row=3))


class LuckButton(discord.ui.Button):
    def __init__(self, luck_pct: int, количество: int, user_id: int, row: int):
        base_price = количество * 100
        extra = LUCK_PRICES.get(luck_pct, 0) * количество
        total = base_price + extra
        if luck_pct == 0:
            label = f"🎲 Без удачи ({base_price}🪙)"
        else:
            label = f"🍀 {luck_pct}% ({total}🪙)"
        super().__init__(label=label[:80], style=discord.ButtonStyle.primary if luck_pct > 0 else discord.ButtonStyle.secondary, row=row)
        self.luck_pct = luck_pct
        self.количество = количество
        self.user_id = user_id
        self.total = total

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Это не твои боксы!", ephemeral=True)
            return
        bal = get_balance(interaction.user.id)
        if bal < self.total:
            await interaction.response.edit_message(
                content=f"❌ Нужно **{self.total}**, есть **{bal}**", view=None)
            return
        set_balance(interaction.user.id, bal - self.total)
        результаты = []
        for _ in range(self.количество):
            rarity, fighter = roll_fighter(self.luck_pct)
            f = {**fighter, "rarity": rarity}
            add_fighter(interaction.user.id, f)
            результаты.append((rarity, fighter))
        luck_str = f"🍀 Удача: **{self.luck_pct}%**\n" if self.luck_pct > 0 else ""
        текст = f"📦 **{self.количество} боксов** за **{self.total}** ликкеров!\n{luck_str}\n"
        for rarity, fighter in результаты:
            цвет = RARITY_COLORS.get(rarity, "⬜")
            if rarity == "Секретный":
                текст += f"{цвет} **[СЕКРЕТНЫЙ]** {fighter['emoji']} **{fighter['name']}** +{fighter['income']}/час 🤫\n"
            else:
                текст += f"{цвет} **[{rarity}]** {fighter['emoji']} **{fighter['name']}** +{fighter['income']}/час\n"
        new_bal = get_balance(interaction.user.id)
        текст += f"\n📈 Доход: **{get_hourly_income(interaction.user.id)}**/час\n💰 Остаток: **{new_bal}**"
        if len(текст) > 1900:
            текст = текст[:1900] + "..."
        await interaction.response.edit_message(content=текст, view=None)


class CancelBoxButton(discord.ui.Button):
    def __init__(self, row: int):
        super().__init__(label="❌ Отмена", style=discord.ButtonStyle.danger, row=row)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content="🚫 Отменено!", view=None)


# ===== КОМАНДЫ =====

@tree.command(name="баланс", description="Посмотреть баланс")
@app_commands.describe(участник="Участник (необязательно)")
async def баланс(interaction: discord.Interaction, участник: discord.Member = None):
    await interaction.response.defer()
    цель = участник if участник else interaction.user
    bal = get_balance(цель.id)
    income = get_hourly_income(цель.id)
    f_count = len(get_fighters_list(цель.id))
    await interaction.followup.send(
        f"┌─────────────────────┐\n"
        f"        💰 **{цель.name}**\n"
        f"└─────────────────────┘\n"
        f"💵 **{bal}** ликкеров\n"
        f"📈 Доход: **{income}**/час\n"
        f"⚔️ Бойцов: **{f_count}**")

@tree.command(name="сброс", description="Сбросить все балансы до 0")
async def сброс(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    save_file(BALANCE_FILE, {})
    await interaction.followup.send("✅ Все балансы сброшены до **0**!")

@tree.command(name="сбросдохода", description="Сбросить всех бойцов у всех")
async def сбросдохода(interaction: discord.Interaction):
    await interaction.response.defer()
    роли = [r.name for r in interaction.user.roles]
    if "Владелец Сервера" not in роли:
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    save_file(FIGHTERS_FILE, {})
    await interaction.followup.send("✅ Все бойцы сброшены!")

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
    множитель = round(random.uniform(1.1, 2.0), 2)
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
    if not any(r in роли for r in BAN_ROLES) and interaction.user.name != "milk17lekklir":
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
    if not any(r in роли for r in SEND_ROLES) and interaction.user.name != "milk17lekklir":
        await interaction.followup.send("❌ Нет прав!", ephemeral=True)
        return
    if страна not in СПИСОК_СТРАН:
        await interaction.followup.send("❌ Страна не найдена!", ephemeral=True)
        return
    await interaction.followup.send(f"✈️ {участник.mention} **отправлен в {страна}!**\n🧳 Счастливого пути!")

@tree.command(name="магазин", description="Открыть магазин")
async def магазин(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    bal = get_balance(interaction.user.id)
    income = get_hourly_income(interaction.user.id)
    await interaction.followup.send(
        f"🏪 **Магаз**\n💰 **{bal}** ликкеров | 📈 **{income}**/час\n\nЧто хочешь купить?",
        view=ShopMainView(), ephemeral=True)

@tree.command(name="боксы", description="Открыть боксы (выбор удачи)")
@app_commands.describe(количество="Количество (1 = 100 ликкеров)")
async def боксы(interaction: discord.Interaction, количество: int):
    await interaction.response.defer()
    if количество <= 0 or количество > 100:
        await interaction.followup.send("❌ От 1 до 100!", ephemeral=True)
        return
    base_price = количество * 100
    bal = get_balance(interaction.user.id)
    if bal < base_price:
        await interaction.followup.send(f"❌ Нужно минимум **{base_price}**, есть **{bal}**", ephemeral=True)
        return

    luck_info = "\n".join([
        f"🍀 **{pct}%** удачи — +{LUCK_PRICES[pct] * количество}🪙 (итого {base_price + LUCK_PRICES[pct] * количество})"
        for pct in [10, 20, 30, 40, 50, 60, 70, 80, 90]
    ])

    await interaction.followup.send(
        f"📦 **Покупка {количество} боксов**\n💰 Базовая цена: **{base_price}** ликкеров\n\n"
        f"**Выбери уровень удачи:**\n{luck_info}\n\nИли купи без удачи 🎲",
        view=BoxLuckView(количество, interaction.user.id))

@tree.command(name="бойцы", description="Мои бойцы")
async def бойцы(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    f_list = get_fighters_list(interaction.user.id)
    if not f_list:
        await interaction.followup.send("❌ Нет бойцов! Открой `/боксы`", ephemeral=True)
        return
    текст = f"⚔️ **Бойцы {interaction.user.name}:**\n\n"
    for f in f_list:
        цвет = RARITY_COLORS.get(f.get("rarity", "Редкий"), "⬜")
        if f.get("rarity") == "Секретный":
            текст += f"{цвет} **[СЕКРЕТНЫЙ]** {f['emoji']} **{f['name']}** +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        else:
            текст += f"{цвет} **[{f.get('rarity','?')}]** {f['emoji']} **{f['name']}** +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
    текст += f"\n📈 Доход: **{sum(f['income'] for f in f_list)}**/час"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст, ephemeral=True)

@tree.command(name="всебойцы", description="Все возможные бойцы")
async def всебойцы(interaction: discord.Interaction):
    await interaction.response.defer()
    текст = "⚔️ **Все бойцы:**\n\n"
    for rarity, fighters in FIGHTERS.items():
        if rarity == "Секретный":
            continue
        цвет = RARITY_COLORS.get(rarity, "⬜")
        текст += f"{цвет} **{rarity}:**\n"
        for f in fighters:
            текст += f"  {f['emoji']} {f['name']} | +{f['income']}/час | ⚔️{f['atk']} 🛡️{f['def']} 💪{f['power']}\n"
        текст += "\n"
    текст += "⬛ **Секретный:** ???"
    if len(текст) > 1900:
        текст = текст[:1900] + "..."
    await interaction.followup.send(текст)

@tree.command(name="колода", description="Управление колодами бойцов")
async def колода(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    decks = get_decks(interaction.user.id)
    текст = "⚔️ **Мои колоды:**\n\n"
    for name in ["К1", "К2", "К3", "К4", "К5"]:
        deck = decks.get(name, [])
        power = sum(f.get("power", 0) for f in deck)
        текст += f"{'⚔️' if deck else '🆕'} **{name}** — {len(deck)}/5 бойцов | Сила: {power}\n"
    await interaction.followup.send(текст, view=DeckMainView(interaction.user.id), ephemeral=True)

@tree.command(name="бой", description="Бой с участником на ставку")
@app_commands.describe(участник="Участник для боя", ставка="Ставка ликкеров")
async def бой(interaction: discord.Interaction, участник: discord.Member, ставка: int):
    await interaction.response.defer()

    if участник.id == interaction.user.id:
        await interaction.followup.send("❌ Нельзя сражаться с собой!", ephemeral=True)
        return
    if участник.bot:
        await interaction.followup.send("❌ Нельзя сражаться с ботом!", ephemeral=True)
        return
    if ставка < 0:
        await interaction.followup.send("❌ Ставка не может быть отрицательной!", ephemeral=True)
        return

    ch_bal = get_balance(interaction.user.id)
    if ставка > 0 and ch_bal < ставка:
        await interaction.followup.send(f"❌ Тебе не хватает ликкеров! Нужно **{ставка}**, есть **{ch_bal}**", ephemeral=True)
        return

    my_fighters = get_fighters_list(interaction.user.id)
    if not my_fighters:
        await interaction.followup.send("❌ У тебя нет бойцов! Открой `/боксы`", ephemeral=True)
        return

    my_decks = get_decks(interaction.user.id)
    has_any_ch = any(my_decks.get(n) for n in ["К1", "К2", "К3", "К4", "К5"])
    if not has_any_ch:
        await interaction.followup.send("❌ У тебя нет колод! Создай через `/колода`", ephemeral=True)
        return

    opp_decks = get_decks(участник.id)
    has_any_op = any(opp_decks.get(n) for n in ["К1", "К2", "К3", "К4", "К5"])
    if not has_any_op:
        await interaction.followup.send(f"❌ У **{участник.name}** нет колод! Бой невозможен.", ephemeral=True)
        return

    ставка_текст = f"💰 Ставка: **{ставка}** ликкеров каждый" if ставка > 0 else "🎮 Товарищеский бой (без ставки)"
    await interaction.followup.send(
        f"⚔️ **{interaction.user.name}** вызывает **{участник.mention}** на бой!\n"
        f"{ставка_текст}\n\n"
        f"{участник.mention}, принимаешь вызов?",
        view=BattleInviteView(interaction.user, участник, ставка, interaction.channel))

# =============================================
# ============= СИСТЕМА МАФИИ ================
# =============================================

MAFIA_ROLES = {
    "🔫 Дон Мафии":     {"team": "mafia",    "desc": "Убиваешь ночью. 1 раз можешь отмазать игрока от голосования."},
    "🕵️ Мафиози":       {"team": "mafia",    "desc": "Убиваешь ночью вместе с Доном."},
    "👨‍⚕️ Доктор":        {"team": "town",     "desc": "Каждую ночь лечишь одного игрока. Себя нельзя 2 ночи подряд."},
    "🔍 Шериф":         {"team": "town",     "desc": "Каждую ночь проверяешь игрока — мафия или нет."},
    "👁️ Детектив":      {"team": "town",     "desc": "Раз в 2 ночи узнаёшь точную роль игрока."},
    "💰 Коррупционер":  {"team": "town",     "desc": "1 раз за игру можешь сменить чужой голос на нужного тебе."},
    "💣 Маньяк":        {"team": "maniac",   "desc": "Победишь если останешься последним живым."},
    "🃏 Шут":           {"team": "jester",   "desc": "Победишь если тебя линчуют днём голосованием."},
    "👤 Мирный":        {"team": "town",     "desc": "Обычный житель. Найди мафию голосованием!"},
}

def get_role_team(role): return MAFIA_ROLES.get(role, {}).get("team", "town")

def assign_roles(count):
    roles = []
    if count <= 6:
        roles = ["🔫 Дон Мафии", "👨‍⚕️ Доктор", "🔍 Шериф"]
        roles += ["👤 Мирный"] * (count - 3)
    elif count <= 9:
        roles = ["🔫 Дон Мафии", "🕵️ Мафиози", "👨‍⚕️ Доктор", "🔍 Шериф", "👁️ Детектив"]
        roles += ["👤 Мирный"] * (count - 5)
    elif count <= 12:
        roles = ["🔫 Дон Мафии", "🕵️ Мафиози", "🕵️ Мафиози",
                 "👨‍⚕️ Доктор", "🔍 Шериф", "👁️ Детектив", "💣 Маньяк"]
        roles += ["👤 Мирный"] * (count - 7)
    else:
        roles = ["🔫 Дон Мафии", "🕵️ Мафиози", "🕵️ Мафиози", "🕵️ Мафиози",
                 "👨‍⚕️ Доктор", "👨‍⚕️ Доктор", "🔍 Шериф", "👁️ Детектив", "💣 Маньяк", "🃏 Шут"]
        roles += ["👤 Мирный"] * (count - 10)
    random.shuffle(roles)
    return roles

# Хранилище активных игр: guild_id -> данные игры
mafia_games = {}
MAFIA_MIN_PLAYERS = 4

class MafiaGame:
    def __init__(self, guild, channel, host):
        self.guild = guild
        self.channel = channel          # канал где запустили
        self.host = host
        self.players = []               # list of Member
        self.roles = {}                 # member.id -> role str
        self.alive = []                 # list of member.id
        self.phase = "lobby"            # lobby / night / day / vote
        self.night_num = 0
        self.night_actions = {}         # role -> target member.id
        self.votes = {}                 # voter_id -> target_id
        self.last_healed = None         # доктор не лечит себя 2 ночи
        self.detective_cooldown = 0
        self.don_shield_used = False
        self.corr_used = False
        self.corr_override = {}         # voter_id -> forced target
        self.ended = False              # защита от повторного завершения игры
        # Каналы
        self.ch_main = None
        self.ch_chat = None
        self.ch_mafia = None
        self.ch_dead = None
        # Сообщение с составом (закреплённое)
        self.pinned_msg = None
        self.lobby_msg = None

    def get_role(self, uid): return self.roles.get(uid, "👤 Мирный")
    def is_alive(self, uid): return uid in self.alive
    def mafia_ids(self): return [uid for uid, r in self.roles.items() if get_role_team(r) == "mafia"]
    def town_ids(self): return [uid for uid, r in self.roles.items() if get_role_team(r) == "town"]

    def check_win(self):
        alive_mafia = [uid for uid in self.alive if get_role_team(self.get_role(uid)) == "mafia"]
        alive_town  = [uid for uid in self.alive if get_role_team(self.get_role(uid)) != "mafia"]
        alive_maniac = [uid for uid in self.alive if get_role_team(self.get_role(uid)) == "maniac"]

        if len(self.alive) == 1 and alive_maniac:
            return "maniac"
        if not alive_mafia:
            return "town"
        if len(alive_mafia) >= len(alive_town):
            return "mafia"
        return None


async def mafia_create_channels(game: MafiaGame):
    guild = game.guild
    overwrites_hidden = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
    }
    cat = None
    for c in guild.categories:
        if c.name == "🎭 МАФИЯ":
            cat = c
            break
    if not cat:
        cat = await guild.create_category("🎭 МАФИЯ")

    game.ch_main  = await guild.create_text_channel("мафия-игра",  category=cat, overwrites=overwrites_hidden)
    game.ch_chat  = await guild.create_text_channel("мафия-чат",   category=cat, overwrites=overwrites_hidden)
    game.ch_mafia = await guild.create_text_channel("мафия-мафия", category=cat, overwrites=overwrites_hidden)
    game.ch_dead  = await guild.create_text_channel("мафия-мёртвые", category=cat, overwrites=overwrites_hidden)

    # Выдаём доступ живым игрокам к основным каналам
    for m in game.players:
        await game.ch_main.set_permissions(m, read_messages=True, send_messages=False)
        await game.ch_dead.set_permissions(m, read_messages=True, send_messages=False)

    # Мафия видит свой канал
    for uid in game.mafia_ids():
        m = game.guild.get_member(uid)
        if m:
            await game.ch_mafia.set_permissions(m, read_messages=True, send_messages=True)


async def mafia_delete_channels(game: MafiaGame):
    for ch in [game.ch_main, game.ch_chat, game.ch_mafia, game.ch_dead]:
        if ch:
            try:
                await ch.delete()
            except:
                pass
    # Удаляем категорию если пустая
    if game.ch_main:
        try:
            cat = game.ch_main.category
            if cat and len(cat.channels) == 0:
                await cat.delete()
        except:
            pass


async def mafia_update_pinned(game: MafiaGame):
    lines = ["📋 **Игроки:**\n"]
    for m in game.players:
        uid = m.id
        status = "✅" if game.is_alive(uid) else "💀"
        lines.append(f"{status} {m.display_name}")
    text = "\n".join(lines) + f"\n\n🌙 Ночь #{game.night_num}" if game.phase == "night" else "\n".join(lines)
    if game.pinned_msg:
        try:
            await game.pinned_msg.edit(content=text)
        except:
            pass
    else:
        game.pinned_msg = await game.ch_main.send(text)
        try:
            await game.pinned_msg.pin()
        except:
            pass


async def mafia_send_night_dms(game: MafiaGame):
    """Отправить ночные ЛС всем живым игрокам"""
    alive_members = [game.guild.get_member(uid) for uid in game.alive]
    alive_members = [m for m in alive_members if m]

    for m in alive_members:
        role = game.get_role(m.id)
        team = get_role_team(role)
        desc = MAFIA_ROLES.get(role, {}).get("desc", "")
        targets = [x for x in alive_members if x.id != m.id]

        if not targets:
            continue

        try:
            if role == "👨‍⚕️ Доктор":
                view = MafiaNightActionView(game, m, targets, "heal")
                await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**\n{desc}\n\nКого лечишь?", view=view)

            elif role == "🔍 Шериф":
                view = MafiaNightActionView(game, m, targets, "check")
                await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**\n{desc}\n\nКого проверяешь?", view=view)

            elif role == "👁️ Детектив":
                if game.night_num % 2 == 1:
                    view = MafiaNightActionView(game, m, targets, "detect")
                    await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**\n{desc}\n\nКого изучаешь?", view=view)
                else:
                    await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**\n📵 Сегодня способность на перезарядке.")

            elif role in ("🔫 Дон Мафии", "🕵️ Мафиози"):
                mafia_names = ", ".join([
                    game.guild.get_member(uid).display_name
                    for uid in game.mafia_ids()
                    if game.guild.get_member(uid) and uid != m.id
                ])
                mafia_str = f"\n🔴 Твои: {mafia_names}" if mafia_names else ""
                view = MafiaNightActionView(game, m, targets, "kill")
                await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**{mafia_str}\n\nКого убиваем?", view=view)

            else:
                await m.send(f"🌙 **Ночь #{game.night_num}** — ты **{role}**\n{desc}\n\n😴 Ложись спать, жди утра.")
        except discord.Forbidden:
            pass


class MafiaNightActionView(discord.ui.View):
    def __init__(self, game: MafiaGame, actor: discord.Member, targets: list, action: str):
        super().__init__(timeout=60)
        self.game = game
        self.actor = actor
        self.action = action
        for t in targets[:20]:
            self.add_item(MafiaNightTargetButton(game, actor, t, action))


class MafiaNightTargetButton(discord.ui.Button):
    def __init__(self, game: MafiaGame, actor: discord.Member, target: discord.Member, action: str):
        super().__init__(label=target.display_name[:80], style=discord.ButtonStyle.primary)
        self.game = game
        self.actor = actor
        self.target = target
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.actor.id:
            await interaction.response.send_message("❌ Не твоя кнопка!", ephemeral=True)
            return
        self.game.night_actions[self.action + str(self.actor.id)] = self.target.id
        self.view.stop()

        role = self.game.get_role(self.actor.id)
        if self.action == "heal":
            await interaction.response.edit_message(content=f"💉 Ты лечишь **{self.target.display_name}** этой ночью.", view=None)
        elif self.action == "check":
            await interaction.response.edit_message(content=f"🔍 Проверяешь **{self.target.display_name}**... результат утром.", view=None)
        elif self.action == "detect":
            await interaction.response.edit_message(content=f"👁️ Изучаешь **{self.target.display_name}**... результат утром.", view=None)
        elif self.action == "kill":
            await interaction.response.edit_message(content=f"🔫 Цель выбрана: **{self.target.display_name}**.", view=None)
            # Оповещаем остальных мафиози в канале мафии
            if self.game.ch_mafia:
                try:
                    await self.game.ch_mafia.send(f"🔫 **{self.actor.display_name}** выбрал цель: **{self.target.display_name}**")
                except:
                    pass


async def mafia_resolve_night(game: MafiaGame):
    """Подводим итоги ночи"""
    results = []

    # Кто убит (берём первый kill-action от мафии)
    killed_id = None
    for uid in game.mafia_ids():
        k = game.night_actions.get("kill" + str(uid))
        if k:
            killed_id = k
            break

    # Кого лечит доктор
    healed_id = None
    for uid, role in game.roles.items():
        if role == "👨‍⚕️ Доктор":
            h = game.night_actions.get("heal" + str(uid))
            if h:
                healed_id = h
                # Нельзя лечить себя 2 раза подряд
                if h == uid and game.last_healed == uid:
                    healed_id = None
                else:
                    game.last_healed = h

    # Применяем убийство
    if killed_id and killed_id != healed_id:
        if killed_id in game.alive:
            game.alive.remove(killed_id)
            victim = game.guild.get_member(killed_id)
            results.append(f"💀 Ночью был убит **{victim.display_name if victim else killed_id}**")
            # Переводим в мёртвые
            if victim and game.ch_dead:
                try:
                    await game.ch_dead.set_permissions(victim, read_messages=True, send_messages=True)
                    await game.ch_chat.set_permissions(victim, read_messages=False, send_messages=False)
                except:
                    pass
    elif killed_id and killed_id == healed_id:
        results.append("🏥 Доктор успел спасти жертву этой ночью! Никто не погиб.")

    # Шериф — результат в ЛС
    for uid, role in game.roles.items():
        if role == "🔍 Шериф" and uid in game.alive:
            t_id = game.night_actions.get("check" + str(uid))
            if t_id:
                t_member = game.guild.get_member(t_id)
                t_role = game.get_role(t_id)
                t_team = get_role_team(t_role)
                result_str = "🔴 МАФИЯ" if t_team == "mafia" else "🟢 Мирный"
                sheriff = game.guild.get_member(uid)
                if sheriff:
                    try:
                        await sheriff.send(f"🔍 **Результат проверки:** {t_member.display_name if t_member else t_id} — {result_str}")
                    except:
                        pass

    # Детектив — точная роль в ЛС
    for uid, role in game.roles.items():
        if role == "👁️ Детектив" and uid in game.alive:
            t_id = game.night_actions.get("detect" + str(uid))
            if t_id:
                t_member = game.guild.get_member(t_id)
                t_role = game.get_role(t_id)
                det = game.guild.get_member(uid)
                if det:
                    try:
                        await det.send(f"👁️ **Результат:** {t_member.display_name if t_member else t_id} — **{t_role}**")
                    except:
                        pass

    game.night_actions.clear()
    return results


class MafiaVoteView(discord.ui.View):
    def __init__(self, game: MafiaGame, alive_members: list):
        super().__init__(timeout=45)
        self.game = game
        self.votes = {}
        self.alive_ids = [m.id for m in alive_members]
        for m in alive_members:
            self.add_item(MafiaVoteButton(game, m, self))
        self.add_item(MafiaSkipVoteButton(self))

    def tally(self):
        counts = {}
        for voter, target in self.votes.items():
            if target == "skip":
                continue
            # Коррупционер
            real_target = self.game.corr_override.get(voter, target)
            counts[real_target] = counts.get(real_target, 0) + 1
        return counts


class MafiaVoteButton(discord.ui.Button):
    def __init__(self, game: MafiaGame, target: discord.Member, vote_view):
        super().__init__(label=target.display_name[:80], style=discord.ButtonStyle.danger)
        self.game = game
        self.target = target
        self.vote_view = vote_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.vote_view.alive_ids:
            await interaction.response.send_message("❌ Ты не участник или уже выбыл!", ephemeral=True)
            return
        self.vote_view.votes[interaction.user.id] = self.target.id
        await interaction.response.send_message(f"🗳️ Ты проголосовал за **{self.target.display_name}**", ephemeral=True)


class MafiaSkipVoteButton(discord.ui.Button):
    def __init__(self, vote_view):
        super().__init__(label="⏭️ Пропустить", style=discord.ButtonStyle.secondary)
        self.vote_view = vote_view

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id not in self.vote_view.alive_ids:
            await interaction.response.send_message("❌ Ты не участник!", ephemeral=True)
            return
        self.vote_view.votes[interaction.user.id] = "skip"
        await interaction.response.send_message("⏭️ Ты воздержался.", ephemeral=True)


class MafiaNominateView(discord.ui.View):
    """Кнопка выдвинуть на голосование — появляется в день"""
    def __init__(self, game: MafiaGame):
        super().__init__(timeout=120)
        self.game = game
        self.nominated = set()

    @discord.ui.button(label="👆 Выдвинуть на голосование", style=discord.ButtonStyle.primary)
    async def nominate(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.game.alive:
            await interaction.response.send_message("❌ Ты уже выбыл!", ephemeral=True)
            return
        self.nominated.add(interaction.user.id)
        count = len(self.nominated)
        total = len(self.game.alive)
        await interaction.response.send_message(
            f"👆 **{interaction.user.display_name}** хочет начать голосование! ({count}/{total})",
            ephemeral=False)


async def mafia_run_game(game: MafiaGame):
    """Основной цикл игры"""
    guild_id = game.guild.id

    await mafia_create_channels(game)

    # Раздаём роли
    roles_list = assign_roles(len(game.players))
    for i, m in enumerate(game.players):
        game.roles[m.id] = roles_list[i]
        game.alive.append(m.id)

    # Выдаём доступ к чату живым
    for m in game.players:
        await game.ch_chat.set_permissions(m, read_messages=True, send_messages=True)

    # Отправляем роль в ЛС
    for m in game.players:
        role = game.get_role(m.id)
        desc = MAFIA_ROLES.get(role, {}).get("desc", "")
        try:
            await m.send(
                f"🎭 **Игра началась!**\n\n"
                f"Твоя роль: **{role}**\n"
                f"📖 {desc}\n\n"
                f"Игра идёт в: {game.ch_main.mention}")
        except discord.Forbidden:
            pass

    # Сообщение мафии в их канале
    mafia_members = [game.guild.get_member(uid) for uid in game.mafia_ids()]
    mafia_str = ", ".join([m.display_name for m in mafia_members if m])
    await game.ch_mafia.send(
        f"🔴 **Добро пожаловать, Мафия!**\n\n"
        f"Ваша команда: **{mafia_str}**\n"
        f"Общайтесь здесь в любое время — этот канал только для вас!")

    await mafia_update_pinned(game)
    await game.ch_main.send(
        f"🎭 **Игра в мафию началась!** ({len(game.players)} игроков)\n\n"
        f"📋 Роли розданы — проверьте ЛС!\n"
        f"🗣️ Общий чат: {game.ch_chat.mention}\n"
        f"💀 Мёртвые: {game.ch_dead.mention}")

    await asyncio.sleep(5)

    # ===== ИГРОВОЙ ЦИКЛ =====
    while True:
        win = game.check_win()
        if win:
            await mafia_end_game(game, win)
            break

        # ===== НОЧЬ =====
        game.phase = "night"
        game.night_num += 1

        # Закрываем чат ночью
        for m in [game.guild.get_member(uid) for uid in game.alive if game.guild.get_member(uid)]:
            await game.ch_chat.set_permissions(m, read_messages=True, send_messages=False)

        await game.ch_main.send(
            f"🌙 **НОЧЬ #{game.night_num}**\n\n"
            f"Город засыпает... Проверьте ЛС для своего действия!\n"
            f"⏳ **60 секунд**")
        await mafia_update_pinned(game)
        await mafia_send_night_dms(game)
        await asyncio.sleep(60)

        # Подводим итоги ночи
        night_results = await mafia_resolve_night(game)

        # ===== ДЕНЬ =====
        game.phase = "day"

        # Открываем чат днём
        for m in [game.guild.get_member(uid) for uid in game.alive if game.guild.get_member(uid)]:
            await game.ch_chat.set_permissions(m, read_messages=True, send_messages=True)

        result_text = "\n".join(night_results) if night_results else "😴 Тихая ночь — никто не погиб."
        await game.ch_main.send(
            f"☀️ **ДЕНЬ #{game.night_num}**\n\n"
            f"{result_text}\n\n"
            f"🗣️ Обсуждайте в {game.ch_chat.mention}!\n"
            f"⏳ **2 минуты на обсуждение**")
        await mafia_update_pinned(game)

        win = game.check_win()
        if win:
            await mafia_end_game(game, win)
            break

        nominate_view = MafiaNominateView(game)
        await game.ch_chat.send("👆 Хочешь начать голосование? Жми кнопку!", view=nominate_view)
        await asyncio.sleep(120)

        # ===== ГОЛОСОВАНИЕ =====
        game.phase = "vote"
        alive_members = [game.guild.get_member(uid) for uid in game.alive if game.guild.get_member(uid)]

        vote_view = MafiaVoteView(game, alive_members)
        vote_msg = await game.ch_main.send(
            f"🗳️ **ГОЛОСОВАНИЕ!**\n\n"
            f"Кого линчуем? У вас **45 секунд!**\n"
            f"Живых игроков: {len(alive_members)}",
            view=vote_view)

        await asyncio.sleep(45)
        vote_view.stop()

        tally = vote_view.tally()
        if not tally:
            await game.ch_main.send("🤷 Никто не проголосовал. Никого не линчуют.")
        else:
            max_votes = max(tally.values())
            top = [uid for uid, v in tally.items() if v == max_votes]
            if len(top) > 1:
                await game.ch_main.send(f"⚖️ **Ничья!** Никого не линчуют.")
            else:
                lynched_id = top[0]
                lynched = game.guild.get_member(lynched_id)
                lynched_role = game.get_role(lynched_id)
                if lynched_id in game.alive:
                    game.alive.remove(lynched_id)
                # Раскрываем роль
                await game.ch_main.send(
                    f"⚖️ **{lynched.display_name if lynched else lynched_id}** линчован!\n"
                    f"Его роль была: **{lynched_role}**")
                # Шут победил?
                if lynched_role == "🃏 Шут":
                    await game.ch_main.send(f"🃏 **{lynched.display_name}** был Шутом и победил!")
                    set_balance(lynched_id, get_balance(lynched_id) + 1000)
                    await mafia_end_game(game, "jester", jester_id=lynched_id)
                    break
                # Переводим в мёртвые
                if lynched and game.ch_dead:
                    try:
                        await game.ch_dead.set_permissions(lynched, read_messages=True, send_messages=True)
                        await game.ch_chat.set_permissions(lynched, read_messages=False, send_messages=False)
                    except:
                        pass

        game.corr_override.clear()
        await mafia_update_pinned(game)

        win = game.check_win()
        if win:
            await mafia_end_game(game, win)
            break

        await asyncio.sleep(3)


async def mafia_end_game(game: MafiaGame, win: str, jester_id=None):
    """Завершает игру: объявляет победителей, начисляет ликкеры победителям, удаляет каналы мафии."""
    if game.ended:
        return
    game.ended = True
    mafia_games.pop(game.guild.id, None)

    REWARD = 500
    winners_ids = []
    if win == "town":
        text = "🏙️ **Мирные жители победили!** Мафия уничтожена."
        winners_ids = game.town_ids()
    elif win == "mafia":
        text = "🔴 **Мафия победила!** Город захвачен."
        winners_ids = game.mafia_ids()
    elif win == "maniac":
        text = "💣 **Маньяк победил!** Он остался последним выжившим."
        winners_ids = [uid for uid in game.roles if get_role_team(game.get_role(uid)) == "maniac"]
    elif win == "jester":
        text = "🃏 **Шут одержал победу!** Его линчевали — план сработал."
        winners_ids = [jester_id] if jester_id else []
    else:
        text = "🏁 Игра завершена."

    for uid in winners_ids:
        set_balance(uid, get_balance(uid) + REWARD)

    roles_text = "\n".join(
        f"{'✅' if game.is_alive(uid) else '💀'} {(game.guild.get_member(uid).display_name if game.guild.get_member(uid) else uid)} — {role}"
        for uid, role in game.roles.items()
    )
    reward_line = f"💰 Победители получили **{REWARD}** ликкеров!" if winners_ids else ""
    if game.ch_main:
        try:
            await game.ch_main.send(
                f"{text}\n\n📋 **Итоговые роли:**\n{roles_text}\n\n{reward_line}\n\n"
                f"⏳ Каналы мафии будут удалены через 30 секунд...")
        except:
            pass
    await asyncio.sleep(30)
    await mafia_delete_channels(game)


async def mafia_refresh_lobby_message(game: MafiaGame):
    if not game.lobby_msg:
        return
    names = "\n".join(f"• {m.display_name}" for m in game.players) or "_никого пока нет_"
    text = (f"🎭 **Лобби мафии открыто!**\n\n"
            f"Игроков: **{len(game.players)}** (нужно минимум {MAFIA_MIN_PLAYERS})\n{names}\n\n"
            f"Хост: **{game.host.display_name}**\n"
            f"Жми ✅, чтобы присоединиться. Хост запускает игру кнопкой 🎬.")
    try:
        await game.lobby_msg.edit(content=text)
    except:
        pass


async def mafia_handle_leave(game: MafiaGame, member: discord.Member):
    """Убирает участника из мафии — работает и в лобби, и во время игры в любой момент. Возвращает текст результата."""
    uid = member.id

    if game.phase == "lobby":
        existing = discord.utils.get(game.players, id=uid)
        if not existing:
            return "❌ Тебя нет в этом лобби."
        game.players.remove(existing)
        if not game.players:
            mafia_games.pop(game.guild.id, None)
            if game.lobby_msg:
                try:
                    await game.lobby_msg.edit(content="🎭 Лобби мафии распущено — все вышли.", view=None)
                except:
                    pass
            return "🚪 Ты вышел. Лобби пустое и закрыто."
        if game.host.id == uid:
            game.host = game.players[0]
        await mafia_refresh_lobby_message(game)
        return "🚪 Ты вышел из лобби."

    # Игра уже идёт (ночь / день / голосование) — выйти можно в любой момент
    if not discord.utils.get(game.players, id=uid):
        return "❌ Ты не участвуешь в текущей игре."
    if uid not in game.alive:
        return "❌ Ты уже выбыл из игры ранее."
    game.alive.remove(uid)
    if game.ch_dead and game.ch_chat:
        try:
            await game.ch_dead.set_permissions(member, read_messages=True, send_messages=True)
            await game.ch_chat.set_permissions(member, read_messages=False, send_messages=False)
        except:
            pass
    if game.ch_main:
        try:
            await game.ch_main.send(f"🚪 **{member.display_name}** покинул игру по собственному желанию.")
        except:
            pass
    return "🚪 Ты вышел из игры. Дальше можешь наблюдать из канала мёртвых."


class MafiaLobbyView(discord.ui.View):
    def __init__(self, game: MafiaGame):
        super().__init__(timeout=600)
        self.game = game

    @discord.ui.button(label="✅ Присоединиться", style=discord.ButtonStyle.success)
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.phase != "lobby":
            await interaction.response.send_message("❌ Игра уже началась.", ephemeral=True)
            return
        if discord.utils.get(self.game.players, id=interaction.user.id):
            await interaction.response.send_message("Ты уже в лобби!", ephemeral=True)
            return
        self.game.players.append(interaction.user)
        await interaction.response.send_message("✅ Ты присоединился к мафии!", ephemeral=True)
        await mafia_refresh_lobby_message(self.game)

    @discord.ui.button(label="🚪 Покинуть лобби", style=discord.ButtonStyle.danger)
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.game.phase != "lobby":
            await interaction.response.send_message("❌ Лобби уже закрыто, игра идёт. Используй /мафия_выйти.", ephemeral=True)
            return
        result = await mafia_handle_leave(self.game, interaction.user)
        await interaction.response.send_message(result, ephemeral=True)

    @discord.ui.button(label="🎬 Начать игру", style=discord.ButtonStyle.primary)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.game.host.id:
            await interaction.response.send_message("❌ Только хост лобби может начать игру.", ephemeral=True)
            return
        if len(self.game.players) < MAFIA_MIN_PLAYERS:
            await interaction.response.send_message(
                f"❌ Нужно минимум {MAFIA_MIN_PLAYERS} игрока(ов), сейчас {len(self.game.players)}.", ephemeral=True)
            return
        self.game.phase = "starting"
        self.stop()
        try:
            await interaction.response.edit_message(content="🎬 Игра начинается, создаю каналы...", view=None)
        except:
            pass
        client.loop.create_task(mafia_run_game(self.game))


@tree.command(name="мафия", description="Открыть лобби игры в мафию")
async def mafia_start_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Команда работает только на сервере.", ephemeral=True)
        return
    if interaction.guild.id in mafia_games:
        await interaction.response.send_message("❌ На этом сервере уже открыто лобби или идёт игра в мафию.", ephemeral=True)
        return
    game = MafiaGame(interaction.guild, interaction.channel, interaction.user)
    game.players.append(interaction.user)
    mafia_games[interaction.guild.id] = game
    view = MafiaLobbyView(game)
    await interaction.response.send_message(
        f"🎭 **Лобби мафии открыто!**\n\n"
        f"Игроков: **1** (нужно минимум {MAFIA_MIN_PLAYERS})\n• {interaction.user.display_name}\n\n"
        f"Хост: **{interaction.user.display_name}**\n"
        f"Жми ✅, чтобы присоединиться. Хост запускает игру кнопкой 🎬.",
        view=view)
    game.lobby_msg = await interaction.original_response()


@tree.command(name="мафия_выйти", description="Выйти из мафии (можно в любой момент — лобби или игра)")
async def mafia_leave_cmd(interaction: discord.Interaction):
    if not interaction.guild:
        await interaction.response.send_message("❌ Команда работает только на сервере.", ephemeral=True)
        return
    game = mafia_games.get(interaction.guild.id)
    if not game:
        await interaction.response.send_message("❌ Сейчас нет ни лобби, ни активной игры в мафию.", ephemeral=True)
        return
    result = await mafia_handle_leave(game, interaction.user)
    await interaction.response.send_message(result, ephemeral=True)



# ===== НОВЫЕ КОМАНДЫ =====

def is_superuser(interaction: discord.Interaction) -> bool:
    return (interaction.guild.owner_id == interaction.user.id or 
            interaction.user.name == "milk17lekklir")

@tree.command(name="накруткауровня", description="[Владелец] Накрутить уровень участнику")
@app_commands.describe(участник="Участник", количество="Количество уровней")
async def boost_level(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if not is_superuser(interaction):
        await interaction.response.send_message("❌ Только для владельца сервера!", ephemeral=True)
        return
    data = get_level_data()
    u = data.get(str(участник.id), {"xp": 0, "level": 1})
    u["level"] += количество
    data[str(участник.id)] = u
    save_level_data(data)
    await apply_level_role(участник, u["level"])
    await interaction.response.send_message(f"✅ Уровень {участник.mention} повышен на **{количество}**. Теперь: **{u['level']}** ур.")

@tree.command(name="накруткаопыта", description="[Владелец] Накрутить XP участнику")
@app_commands.describe(участник="Участник", количество="Количество XP")
async def boost_xp(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if not is_superuser(interaction):
        await interaction.response.send_message("❌ Только для владельца сервера!", ephemeral=True)
        return
    data = get_level_data()
    u = data.get(str(участник.id), {"xp": 0, "level": 1})
    u["xp"] = u.get("xp", 0) + количество
    data[str(участник.id)] = u
    save_level_data(data)
    await interaction.response.send_message(f"✅ {участник.mention} получил **{количество}** XP! XP: **{u['xp']}**")

@tree.command(name="отобратьопыт", description="[Владелец] Отнять XP у участника")
@app_commands.describe(участник="Участник", количество="Количество XP")
async def remove_xp(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if not is_superuser(interaction):
        await interaction.response.send_message("❌ Только для владельца сервера!", ephemeral=True)
        return
    data = get_level_data()
    u = data.get(str(участник.id), {"xp": 0, "level": 1})
    u["xp"] = max(0, u.get("xp", 0) - количество)
    data[str(участник.id)] = u
    save_level_data(data)
    await interaction.response.send_message(f"✅ У {участник.mention} отнято **{количество}** XP. Осталось: **{u['xp']}**")

@tree.command(name="отобратьранг", description="[Владелец] Отнять уровни у участника")
@app_commands.describe(участник="Участник", количество="Количество уровней")
async def remove_rank(interaction: discord.Interaction, участник: discord.Member, количество: int):
    if not is_superuser(interaction):
        await interaction.response.send_message("❌ Только для владельца сервера!", ephemeral=True)
        return
    data = get_level_data()
    u = data.get(str(участник.id), {"xp": 0, "level": 1})
    u["level"] = max(1, u["level"] - количество)
    u["xp"] = 0
    data[str(участник.id)] = u
    save_level_data(data)
    await apply_level_role(участник, u["level"])
    await interaction.response.send_message(f"✅ У {участник.mention} отнято **{количество}** уровней. Теперь: **{u['level']}** ур.")

@tree.command(name="написать", description="[Владелец] Написать от лица бота")
@app_commands.describe(текст="Текст сообщения", канал="Канал (необязательно)")
async def write_as_bot(interaction: discord.Interaction, текст: str, канал: discord.TextChannel = None):
    if not is_superuser(interaction):
        await interaction.response.send_message("❌ Только для владельца сервера!", ephemeral=True)
        return
    target = канал or interaction.channel
    await target.send(текст)
    await interaction.response.send_message("✅ Отправлено!", ephemeral=True)

@tree.command(name="мойранг", description="Посмотреть свой уровень и XP")
@app_commands.describe(участник="Участник (необязательно)")
async def my_rank(interaction: discord.Interaction, участник: discord.Member = None):
    target = участник or interaction.user
    data = get_level_data()
    u = data.get(str(target.id), {"xp": 0, "level": 1})
    level = u.get("level", 1)
    xp = u.get("xp", 0)
    role_name = get_target_level_role_name(level)
    bar = int((xp / max(1, xp + 50)) * 10)
    bar_str = "█" * bar + "░" * (10 - bar)
    text = f"**Ранг {target.display_name}**\n\nУровень: **{level}**\nXP: **{xp}**\n[{bar_str}]"
    if role_name:
        text += f"\nРоль: **{role_name}**"
    await interaction.response.send_message(text, ephemeral=True)

# ===== ЗАПУСК БОТА =====
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        raise SystemExit("❌ Переменная окружения DISCORD_TOKEN не задана! Добавь её в Environment на Render.")
    threading.Thread(target=run_web, daemon=True).start()
    client.run(DISCORD_TOKEN)

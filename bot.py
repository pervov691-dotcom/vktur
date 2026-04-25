import vk_api
import re
import sqlite3
import random
import time
import json
import hashlib
import os
from datetime import datetime, timedelta
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.utils import get_random_id
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

# ========== КОНФИГУРАЦИЯ ==========
GROUP_TOKEN = os.environ.get("VK_TOKEN", "vk1.a.qUyg4SYpR2414W6nHk3hZB4ggpljiji-rBo3P2TBcXlmuEc-jOtXEc_T5BqoKGcIExwbmn5nAyEUTh5NkMMdqVb2qumib8fjaA2JrW1MUBbTyptBks0Khp4QgzvER2gGm9U485X1rnIQ3B3S4lu_BmGFf_tsO6zY5Slr2kC6x5GcKR5C1xzl-CqoTytONqeUyw8RUYys0RQSD7DOaSZQSg")
GROUP_ID = int(os.environ.get("VK_GROUP_ID", 237951367))
ADMIN_IDS = [int(os.environ.get("ADMIN_ID", 123456789))]

# ========== ЛИМИТЫ ==========
BOSS_DAILY_LIMIT = 6
MAX_RAID_PLAYERS = 999

# ========== ТАЙМИНГИ ==========
BOSS_COOLDOWN = 30
WORK_COOLDOWN = 60
DAILY_BONUS_COOLDOWN = 21600
FREE_WEAPON_COOLDOWN = 10

# ========== ВРЕМЯ НА РЕЙД ==========
RAID_TIME_LIMITS = {1: 1, 2: 2, 3: 3, 4: 5, 5: 8, 6: 12, 7: 18, 8: 24}

# ========== БОССЫ ==========
BOSSES = {
    1: {"id": 1, "name": "🧟 Червь", "hp": 1000, "reward_money": (500, 1000), "reward_auth": (10, 20), "reward_xp": (50, 100), "min_level": 1},
    2: {"id": 2, "name": "🔪 Молодой", "hp": 2000, "reward_money": (1000, 2000), "reward_auth": (20, 40), "reward_xp": (100, 200), "min_level": 3},
    3: {"id": 3, "name": "💪 Пацан", "hp": 3500, "reward_money": (2000, 4000), "reward_auth": (40, 70), "reward_xp": (200, 350), "min_level": 6},
    4: {"id": 4, "name": "🔥 Блатной", "hp": 5500, "reward_money": (4000, 7000), "reward_auth": (70, 120), "reward_xp": (350, 600), "min_level": 10},
    5: {"id": 5, "name": "👑 Смотрящий", "hp": 8000, "reward_money": (7000, 12000), "reward_auth": (120, 200), "reward_xp": (600, 1000), "min_level": 15},
    6: {"id": 6, "name": "🐉 Пахан", "hp": 12000, "reward_money": (12000, 20000), "reward_auth": (200, 350), "reward_xp": (1000, 1800), "min_level": 20},
    7: {"id": 7, "name": "⭐ Законник", "hp": 18000, "reward_money": (20000, 35000), "reward_auth": (350, 600), "reward_xp": (1800, 3000), "min_level": 25},
    8: {"id": 8, "name": "💀 Авторитет", "hp": 25000, "reward_money": (35000, 60000), "reward_auth": (600, 1000), "reward_xp": (3000, 5000), "min_level": 30}
}

# ========== ОРУЖИЕ ==========
WEAPONS = {
    1: {"id": 1, "name": "👊 Кастет", "price": 0, "damage": 5, "min_level": 1, "emoji": "👊", "crit_chance": 25},
    2: {"id": 2, "name": "🔪 Заточка", "price": 1000, "damage": 15, "min_level": 3, "emoji": "🔪", "crit_chance": 30},
    3: {"id": 3, "name": "⚔️ Бита", "price": 5000, "damage": 35, "min_level": 8, "emoji": "⚔️", "crit_chance": 35},
    4: {"id": 4, "name": "🔫 Ствол", "price": 20000, "damage": 80, "min_level": 15, "emoji": "🔫", "crit_chance": 40},
    5: {"id": 5, "name": "⭐ Фрачная масть", "price": 50000, "damage": 160, "min_level": 25, "emoji": "⭐", "crit_chance": 50}
}

# ========== РАБОТЫ ==========
JOBS = {
    1: {"name": "🧹 Уборка камер", "earn": 200, "min_level": 1},
    2: {"name": "🍲 Раздача баланды", "earn": 400, "min_level": 3},
    3: {"name": "📦 Подсобник", "earn": 700, "min_level": 6},
    4: {"name": "⚙️ Шестёрка", "earn": 1200, "min_level": 10},
    5: {"name": "💰 Притон", "earn": 2000, "min_level": 15},
    6: {"name": "⚖️ Общак", "earn": 3500, "min_level": 20},
    7: {"name": "👑 Сходка", "earn": 6000, "min_level": 25},
    8: {"name": "💎 Блатная жизнь", "earn": 10000, "min_level": 30}
}

# ========== ТЮРЕМНЫЕ ДОЛЖНОСТИ ==========
RANKS = {
    0: {"name": "🪳 Червь", "auth_needed": 0},
    1: {"name": "🔪 Молодой", "auth_needed": 50},
    2: {"name": "💪 Пацан", "auth_needed": 150},
    3: {"name": "🔥 Блатной", "auth_needed": 300},
    4: {"name": "👑 Смотрящий", "auth_needed": 600},
    5: {"name": "🐉 Пахан", "auth_needed": 1000},
    6: {"name": "⭐ Законник", "auth_needed": 2000},
    7: {"name": "💀 Авторитет", "auth_needed": 4000}
}

# ========== ИНИЦИАЛИЗАЦИЯ ==========
vk_session = vk_api.VkApi(token=GROUP_TOKEN)
vk = vk_session.get_api()
longpoll = VkBotLongPoll(vk_session, GROUP_ID)

user_states = {}
last_free_weapon_use = {}
last_work_time = {}
active_raids = {}
user_raid_temp = {}

# ========== ФУНКЦИИ ДЛЯ ЛИМИТОВ ==========
def get_boss_kills_today(user_id, boss_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM boss_kills_daily WHERE user_id = ? AND boss_id = ? AND date = ?', 
              (user_id, boss_id, today))
    count = c.fetchone()[0]
    conn.close()
    return count

def add_boss_kill_today(user_id, boss_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''INSERT INTO boss_kills_daily (user_id, boss_id, date, count) 
                 VALUES (?, ?, ?, 1)
                 ON CONFLICT(user_id, boss_id, date) 
                 DO UPDATE SET count = count + 1''', 
              (user_id, boss_id, today))
    conn.commit()
    conn.close()

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS prisoners
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  money INTEGER DEFAULT 500,
                  authority INTEGER DEFAULT 0,
                  level INTEGER DEFAULT 1,
                  xp INTEGER DEFAULT 0,
                  weapon_inventory TEXT,
                  boss_kills TEXT,
                  is_admin_hidden INTEGER DEFAULT 0,
                  daily_bonus TEXT,
                  last_work TEXT,
                  join_date TEXT,
                  referrer_id INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS boss_hp
                 (boss_id INTEGER PRIMARY KEY,
                  current_hp INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS raid_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  raid_id TEXT,
                  user_id INTEGER,
                  damage INTEGER,
                  time TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS boss_kills_daily
                 (user_id INTEGER,
                  boss_id INTEGER,
                  date TEXT,
                  count INTEGER DEFAULT 1,
                  PRIMARY KEY (user_id, boss_id, date))''')
    
    conn.commit()
    
    for boss_id, boss in BOSSES.items():
        c.execute('INSERT OR IGNORE INTO boss_hp (boss_id, current_hp) VALUES (?, ?)', (boss_id, boss['hp']))
    
    conn.commit()
    conn.close()
    print("✅ База данных готова")

init_db()

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def send_message(user_id, message, keyboard=None):
    try:
        params = {'user_id': user_id, 'message': message[:4000], 'random_id': get_random_id()}
        if keyboard:
            params['keyboard'] = keyboard.get_keyboard()
        vk.messages.send(**params)
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def get_user_name(user_id):
    try:
        user = vk.users.get(user_ids=user_id)[0]
        return f"{user['first_name']} {user['last_name']}"
    except:
        return f"Пользователь {user_id}"

def get_user_mention(user_id):
    return f"[id{user_id}|{get_user_name(user_id)}]"

def is_admin(user_id):
    return user_id in ADMIN_IDS

def register_user(user_id, referrer_id=None):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM prisoners WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        name = get_user_name(user_id)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO prisoners (user_id, name, join_date, weapon_inventory, referrer_id) VALUES (?, ?, ?, ?, ?)',
                  (user_id, name, now, '{"1":1}', referrer_id or 0))
        conn.commit()
        print(f"✅ Новый игрок: {name}")
    conn.close()

def get_prisoner_stats(user_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT * FROM prisoners WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        if len(result) >= 13:
            return {
                'user_id': result[0], 'name': result[1], 'money': result[2],
                'authority': result[3], 'level': result[4], 'xp': result[5],
                'weapon_inventory': result[6], 'boss_kills': result[7],
                'is_admin_hidden': result[8], 'daily_bonus': result[9],
                'last_work': result[10], 'join_date': result[11], 'referrer_id': result[12]
            }
        else:
            return {
                'user_id': result[0], 'name': result[1], 'money': result[2],
                'authority': result[3], 'level': result[4], 'xp': result[5],
                'weapon_inventory': result[6], 'boss_kills': result[7],
                'is_admin_hidden': 0, 'daily_bonus': None,
                'last_work': None, 'join_date': result[8] if len(result) > 8 else None,
                'referrer_id': result[9] if len(result) > 9 else 0
            }
    return None

def add_money(user_id, amount):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('UPDATE prisoners SET money = money + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_authority(user_id, amount):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('UPDATE prisoners SET authority = authority + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_xp(user_id, amount):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT level, xp FROM prisoners WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return
    level, xp = result
    xp += amount
    level_up = False
    while xp >= level * 100:
        xp -= level * 100
        level += 1
        level_up = True
    c.execute('UPDATE prisoners SET level = ?, xp = ? WHERE user_id = ?', (level, xp, user_id))
    if level_up:
        bonus = level * 500
        c.execute('UPDATE prisoners SET money = money + ? WHERE user_id = ?', (bonus, user_id))
        conn.commit()
        conn.close()
        send_message(user_id, f"🎉 НОВЫЙ УРОВЕНЬ! {level}\n💰 +{bonus} бабла")
        return True
    conn.commit()
    conn.close()
    return False

def get_rank_name(authority):
    for level, rank in sorted(RANKS.items(), reverse=True):
        if authority >= rank['auth_needed']:
            return rank['name']
    return RANKS[0]['name']

def get_boss_hp(boss_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT current_hp FROM boss_hp WHERE boss_id = ?', (boss_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else BOSSES[boss_id]['hp']

def update_boss_hp(boss_id, new_hp):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('UPDATE boss_hp SET current_hp = ? WHERE boss_id = ?', (new_hp, boss_id))
    conn.commit()
    conn.close()

def reset_boss_hp(boss_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('UPDATE boss_hp SET current_hp = ? WHERE boss_id = ?', (BOSSES[boss_id]['hp'], boss_id))
    conn.commit()
    conn.close()

def get_user_weapons(user_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT weapon_inventory FROM prisoners WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        try:
            return json.loads(result[0])
        except:
            return {"1": 1}
    return {"1": 1}

def save_user_weapons(user_id, weapons):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('UPDATE prisoners SET weapon_inventory = ? WHERE user_id = ?', (json.dumps(weapons), user_id))
    conn.commit()
    conn.close()

def add_weapon_to_inventory(user_id, weapon_id):
    weapons = get_user_weapons(user_id)
    weapons[str(weapon_id)] = weapons.get(str(weapon_id), 0) + 1
    save_user_weapons(user_id, weapons)

def remove_weapon_from_inventory(user_id, weapon_id):
    weapons = get_user_weapons(user_id)
    key = str(weapon_id)
    if weapons.get(key, 0) > 0:
        weapons[key] -= 1
        if weapons[key] == 0:
            del weapons[key]
        save_user_weapons(user_id, weapons)
        return True
    return False

# ========== КЛАВИАТУРЫ ==========
def create_main_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("📜 Личное дело", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("⚔️ Пробив", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("💼 Работа", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🏪 Малява", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📦 Хата", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🏆 Рейтинг", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🎁 Чифир", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("👥 Стрелка", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("❓ Помощь", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_boss_keyboard():
    keyboard = VkKeyboard(one_time=False)
    for boss_id, boss in BOSSES.items():
        keyboard.add_button(f"{boss['name']}", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_fight_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("👊 Кастет", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔪 Заточка", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⚔️ Бита", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔫 Ствол", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⭐ Фрачная масть", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🏪 Перейти в маляву", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика боя", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🏳️ Сдаться", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_shop_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🔪 Заточка (1000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⚔️ Бита (5000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔫 Ствол (20000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⭐ Фрачная масть (50000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_raid_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("⚔️ Создать стрелку", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🔍 Ввести ID", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика стрелки", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_admin_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("💰 Выдать деньги", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("👑 Выдать понятия", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("⭐ Выдать оружие", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("📈 Повысить уровень", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("⚔️ Сбросить боссов", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📊 Умная статистика", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("👥 Список игроков", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("📢 Опубликовать ТОП", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🔨 Очистить БД", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("⭐ Прокачать админа", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_back_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("◀️ Вернуться в бой", color=VkKeyboardColor.SECONDARY)
    return keyboard

# ========== ОСНОВНЫЕ КОМАНДЫ ==========
def handle_start(user_id, referrer_id=None):
    register_user(user_id, referrer_id)
    send_message(user_id, 
        "🔥 ДОБРО ПОЖАЛОВАТЬ В ТЮРЯГУ! 🔥\n\n"
        "📜 Личное дело - твоё досье\n"
        "⚔️ Пробив - наезд на авторитетов\n"
        "💼 Работа - фартим бабло\n"
        "🏪 Малява - купить ствол\n"
        "📦 Хата - твои заточки\n"
        "🏆 Рейтинг - топ братвы\n"
        "🎁 Чифир - халявное бабло (раз в 6ч)\n"
        "👥 Стрелка - рейды с братвой\n\n"
        "👉 ЖМИ ПО КНОПКАМ, БРАТОК! 👈",
        create_main_keyboard())

def handle_profile(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    rank_name = get_rank_name(stats['authority'])
    try:
        kills = json.loads(stats['boss_kills']) if stats['boss_kills'] else []
    except:
        kills = []
    message = f"""📜 ЛИЧНОЕ ДЕЛО

👤 {stats['name']}
⭐ {rank_name}
📊 Уровень {stats['level']} (XP: {stats['xp']}/{stats['level']*100})

💰 Бабла: {stats['money']}
👑 Понятия: {stats['authority']}

⚔️ Авторитетов пробито: {len(kills)}/{len(BOSSES)}

📅 На зоне с: {stats['join_date'][:10] if stats['join_date'] else 'сегодня'}"""
    send_message(user_id, message, create_main_keyboard())

def handle_inventory(user_id):
    weapons_inv = get_user_weapons(user_id)
    message = "📦 ХАТА\n\n"
    for weapon_id, weapon in WEAPONS.items():
        count = weapons_inv.get(str(weapon_id), 0)
        if count > 0 or weapon_id == 1:
            message += f"{weapon['emoji']} {weapon['name']}: {count} шт.\n"
            message += f"   ⚔️ Урон +{weapon['damage']}\n"
            message += f"   💥 Шанс крита: {weapon['crit_chance']}%\n"
    if all(weapons_inv.get(str(wid), 0) == 0 for wid in range(2, 6)):
        message += "\n🔸 Стволов нет\n🔸 Зайди в Маляву"
    send_message(user_id, message, create_main_keyboard())

def handle_boss_list(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            send_message(user_id, f"❌ Ты уже на стрелке {raid_code}!\nСначала заверши её.", create_main_keyboard())
            return
    message = "⚔️ КОГО ПРОБИВАЕМ?\n\n"
    for boss_id, boss in BOSSES.items():
        current_hp = get_boss_hp(boss_id)
        req = "✅" if stats['level'] >= boss['min_level'] else f"🔒 УР.{boss['min_level']}"
        filled = int((current_hp / boss['hp']) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        kills_today = get_boss_kills_today(user_id, boss_id)
        message += f"{boss['name']} {req}\n"
        message += f"❤️ [{bar}] {current_hp}/{boss['hp']}\n"
        message += f"💰 {boss['reward_money'][0]}-{boss['reward_money'][1]} | 👑 +{boss['reward_auth'][0]}-{boss['reward_auth'][1]}\n"
        message += f"📅 Сегодня: {kills_today}/{BOSS_DAILY_LIMIT}\n\n"
    send_message(user_id, message, create_boss_keyboard())

def handle_boss_selection(user_id, boss_name):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            send_message(user_id, f"❌ Ты уже на стрелке {raid_code}!\nСначала заверши её.", create_main_keyboard())
            return
    boss_data = None
    boss_id = None
    for bid, bdata in BOSSES.items():
        if bdata['name'] in boss_name:
            boss_id = bid
            boss_data = bdata
            break
    if not boss_data:
        send_message(user_id, "❌ Такого нет!", create_main_keyboard())
        return
    if stats['level'] < boss_data['min_level']:
        send_message(user_id, f"❌ Нужен {boss_data['min_level']} уровень!", create_main_keyboard())
        return
    user_states[user_id] = {'state': 'fighting', 'boss_id': boss_id, 'boss_name': boss_data['name']}
    current_hp = get_boss_hp(boss_id)
    kills_today = get_boss_kills_today(user_id, boss_id)
    remaining = BOSS_DAILY_LIMIT - kills_today
    message = f"⚔️ ПРОБИВ {boss_data['name']} ⚔️\n\n"
    message += f"❤️ ХП: {current_hp}/{boss_data['hp']}\n"
    message += f"📅 Сегодня можно убить: {remaining}/{BOSS_DAILY_LIMIT}\n\n"
    message += "Чем валим?"
    send_message(user_id, message, create_fight_keyboard())

def handle_fight(user_id, weapon_name):
    state = user_states.get(user_id, {})
    if state.get('state') != 'fighting':
        return False
    if "Сдаться" in weapon_name:
        del user_states[user_id]
        send_message(user_id, "🏳️ Сдался, пацан!", create_main_keyboard())
        return True
    if "Назад" in weapon_name:
        del user_states[user_id]
        handle_boss_list(user_id)
        return True
    if "Статистика боя" in weapon_name:
        boss_id = state['boss_id']
        boss_name = state['boss_name']
        current_hp = get_boss_hp(boss_id)
        boss_data = BOSSES[boss_id]
        message = f"📊 СТАТИСТИКА БОЯ\n\n"
        message += f"🐉 Противник: {boss_name}\n"
        message += f"❤️ ХП: {current_hp}/{boss_data['hp']}\n"
        message += f"📊 Прогресс: {((boss_data['hp'] - current_hp) / boss_data['hp'] * 100):.1f}%\n"
        send_message(user_id, message, create_fight_keyboard())
        return True
    boss_id = state['boss_id']
    boss_name = state['boss_name']
    boss_data = BOSSES[boss_id]
    weapon_data = None
    weapon_id = None
    for wid, wdata in WEAPONS.items():
        if wdata['name'] in weapon_name:
            weapon_id = wid
            weapon_data = wdata
            break
    if not weapon_data:
        if "Кастет" in weapon_name:
            weapon_id = 1
            weapon_data = WEAPONS[1]
        elif "Заточка" in weapon_name:
            weapon_id = 2
            weapon_data = WEAPONS[2]
        elif "Бита" in weapon_name:
            weapon_id = 3
            weapon_data = WEAPONS[3]
        elif "Ствол" in weapon_name:
            weapon_id = 4
            weapon_data = WEAPONS[4]
        elif "Фрачная масть" in weapon_name:
            weapon_id = 5
            weapon_data = WEAPONS[5]
        else:
            send_message(user_id, "❌ Выбери ствол!", create_fight_keyboard())
            return True
    stats = get_prisoner_stats(user_id)
    current_hp = get_boss_hp(boss_id)
    if current_hp <= 0:
        send_message(user_id, "❌ Уже пробит!", create_main_keyboard())
        del user_states[user_id]
        return True
    will_kill = (current_hp - (weapon_data['damage'] + stats['level'] * 2)) <= 0
    if will_kill:
        kills_today = get_boss_kills_today(user_id, boss_id)
        if kills_today >= BOSS_DAILY_LIMIT:
            send_message(user_id, f"⚠️ Ты уже убил {BOSS_DAILY_LIMIT} боссов {boss_name} сегодня!\nЛимит на день исчерпан. Возвращайся завтра!", create_main_keyboard())
            del user_states[user_id]
            return True
    if weapon_data['price'] == 0:
        if user_id in last_free_weapon_use:
            last = last_free_weapon_use[user_id]
            if datetime.now() - last < timedelta(seconds=FREE_WEAPON_COOLDOWN):
                remaining = FREE_WEAPON_COOLDOWN - (datetime.now() - last).seconds
                send_message(user_id, f"⏱️ Кастет через {remaining} сек", create_fight_keyboard())
                return True
        last_free_weapon_use[user_id] = datetime.now()
    else:
        weapons_inv = get_user_weapons(user_id)
        if weapons_inv.get(str(weapon_id), 0) <= 0:
            send_message(user_id, f"❌ Нет {weapon_data['name']}!", create_fight_keyboard())
            return True
        remove_weapon_from_inventory(user_id, weapon_id)
    damage = weapon_data['damage'] + stats['level'] * 2
    crit = random.randint(1, 100) <= weapon_data['crit_chance']
    if crit:
        damage = damage * 2
    new_hp = current_hp - damage
    if new_hp <= 0:
        new_hp = 0
        update_boss_hp(boss_id, 0)
        money_reward = random.randint(boss_data['reward_money'][0], boss_data['reward_money'][1])
        auth_reward = random.randint(boss_data['reward_auth'][0], boss_data['reward_auth'][1])
        xp_reward = random.randint(boss_data['reward_xp'][0], boss_data['reward_xp'][1])
        add_money(user_id, money_reward)
        add_authority(user_id, auth_reward)
        add_xp(user_id, xp_reward)
        add_boss_kill_today(user_id, boss_id)
        kills_today = get_boss_kills_today(user_id, boss_id)
        try:
            kills = json.loads(stats['boss_kills']) if stats['boss_kills'] else []
        except:
            kills = []
        if boss_id not in kills:
            kills.append(boss_id)
            conn = sqlite3.connect('tyaryzhka.db')
            c = conn.cursor()
            c.execute('UPDATE prisoners SET boss_kills = ? WHERE user_id = ?', (json.dumps(kills), user_id))
            conn.commit()
            conn.close()
        reset_boss_hp(boss_id)
        del user_states[user_id]
        crit_text = " 💥КРИТ💥" if crit else ""
        message = f"⚔️ ПРОБИЛ {boss_name}! ⚔️\n\n"
        message += f"💥 Урон: {damage}{crit_text}\n"
        message += f"💰 +{money_reward} бабла\n"
        message += f"👑 +{auth_reward} понятий\n"
        message += f"📊 +{xp_reward} XP\n"
        message += f"🏆 Всего пробито: {len(kills)}/{len(BOSSES)}\n"
        message += f"📅 Сегодня убито {boss_name}: {kills_today}/{BOSS_DAILY_LIMIT}"
        send_message(user_id, message, create_main_keyboard())
    else:
        update_boss_hp(boss_id, new_hp)
        crit_text = " 💥КРИТ💥" if crit else ""
        kills_today = get_boss_kills_today(user_id, boss_id)
        remaining = BOSS_DAILY_LIMIT - kills_today
        message = f"⚔️ БЬЁМ!\n\n"
        message += f"🔫 {weapon_data['emoji']} {weapon_data['name']}\n"
        message += f"💥 Урон: {damage}{crit_text}\n"
        message += f"❤️ ХП: {current_hp} → {new_hp}\n"
        message += f"📅 Сегодня можно убить {boss_name}: {remaining}/{BOSS_DAILY_LIMIT}"
        send_message(user_id, message, create_fight_keyboard())
    return True

def handle_work(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    if user_id in last_work_time:
        last = last_work_time[user_id]
        if datetime.now() - last < timedelta(seconds=WORK_COOLDOWN):
            remaining = WORK_COOLDOWN - (datetime.now() - last).seconds
            send_message(user_id, f"⏱️ Работа через {remaining} сек", create_main_keyboard())
            return
    available_jobs = []
    for job_id, job in JOBS.items():
        if stats['level'] >= job['min_level']:
            available_jobs.append(job)
    if not available_jobs:
        send_message(user_id, "❌ Низкий уровень!", create_main_keyboard())
        return
    best_job = max(available_jobs, key=lambda x: x['earn'])
    earnings = best_job['earn'] + random.randint(-50, 50)
    earnings = max(50, earnings)
    add_money(user_id, earnings)
    last_work_time[user_id] = datetime.now()
    send_message(user_id, f"💼 {best_job['name']}\n💰 +{earnings} бабла!", create_main_keyboard())

def handle_shop(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = f"🏪 МАЛЯВА\n💰 Бабла: {stats['money']}\n\n"
    for weapon_id, weapon in WEAPONS.items():
        if weapon['price'] > 0:
            message += f"{weapon['emoji']} {weapon['name']}\n"
            message += f"   💰 {weapon['price']} | ⚔️ +{weapon['damage']} | УР.{weapon['min_level']}\n"
            message += f"   💥 Шанс крита: {weapon['crit_chance']}%\n\n"
    message += "👉 Напиши номер оружия:\n2 - Заточка, 3 - Бита, 4 - Ствол, 5 - Фрачная масть"
    send_message(user_id, message, create_shop_keyboard())
    user_states[user_id] = {'state': 'buying'}

def handle_buy_weapon(user_id, weapon_choice):
    try:
        weapon_id = int(weapon_choice)
        if weapon_id not in [2, 3, 4, 5]:
            send_message(user_id, "❌ Доступные номера: 2, 3, 4, 5", create_main_keyboard())
            if user_id in user_states:
                del user_states[user_id]
            return
    except:
        send_message(user_id, "❌ Напиши номер оружия: 2, 3, 4 или 5", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return
    weapon_data = WEAPONS[weapon_id]
    stats = get_prisoner_stats(user_id)
    if stats['level'] < weapon_data['min_level']:
        send_message(user_id, f"❌ Нужен {weapon_data['min_level']} уровень!", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return
    if stats['money'] < weapon_data['price']:
        send_message(user_id, f"❌ Не хватает! Нужно {weapon_data['price']}💰", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return
    add_weapon_to_inventory(user_id, weapon_id)
    add_money(user_id, -weapon_data['price'])
    weapons_inv = get_user_weapons(user_id)
    current_count = weapons_inv.get(str(weapon_id), 0)
    send_message(user_id, f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет\n📦 Теперь у тебя: {current_count} шт.", create_main_keyboard())
    if user_id in user_states:
        del user_states[user_id]

def handle_ranking(user_id):
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    message = "🏆 РЕЙТИНГ 🏆\n\n"
    c.execute('SELECT user_id, name, level, authority FROM prisoners WHERE is_admin_hidden = 0 ORDER BY authority DESC, level DESC LIMIT 15')
    top = c.fetchall()
    for i, (uid, name, level, auth) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        mention = get_user_mention(uid)
        message += f"{medal} {i}. {mention}\n   УР.{level} | 👑{auth}\n\n"
    if not top:
        message += "🔸 Пока никого нет\n🔸 Будь первым!"
    conn.close()
    send_message(user_id, message, create_main_keyboard())

def handle_daily_bonus(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT daily_bonus FROM prisoners WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result and result[0]:
        try:
            last = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last < timedelta(seconds=DAILY_BONUS_COOLDOWN):
                remaining = DAILY_BONUS_COOLDOWN - (datetime.now() - last).seconds
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                send_message(user_id, f"🎁 Чифир через {hours}ч {minutes}мин", create_main_keyboard())
                conn.close()
                return
        except:
            pass
    bonus = 500 + stats['level'] * 50
    add_money(user_id, bonus)
    c.execute('UPDATE prisoners SET daily_bonus = ? WHERE user_id = ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()
    send_message(user_id, f"🎁 ЧИФИР!\n💰 +{bonus} бабла!", create_main_keyboard())

# ========== ФУНКЦИИ СТРЕЛКИ ==========
def handle_raid(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            elapsed = datetime.now() - raid['start_time']
            remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
            remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
            message = f"⚔️ ТЫ УЖЕ В СТРЕЛКЕ {raid_code}! ⚔️\n\n"
            message += f"🐉 Цель: {raid['boss_name']}\n"
            message += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n\n"
            message += "👉 Вали цель!"
            user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_code}
            send_message(user_id, message, create_fight_keyboard())
            return
    if user_id in user_raid_temp:
        raid_id = user_raid_temp[user_id]
        if raid_id in active_raids:
            raid = active_raids[raid_id]
            elapsed = datetime.now() - raid['start_time']
            remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
            remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
            message = f"⚔️ У ТЕБЯ ЕСТЬ НЕЗАВЕРШЁННАЯ СТРЕЛКА! ⚔️\n\n"
            message += f"🐉 Цель: {raid['boss_name']}\n"
            message += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n\n"
            message += "👉 Нажми 'Ввести ID' и введи: " + raid_id
            send_message(user_id, message, create_raid_keyboard())
            user_states[user_id] = {'state': 'raid_menu'}
            return
    message = "👥 СТРЕЛКА 👥\n\n"
    message += "⚔️ Создать стрелку - выбрать босса\n"
    message += "🔍 Ввести ID - подключиться или вернуться\n"
    message += "📊 Статистика стрелки - посмотреть активные стрелки\n\n"
    message += "👉 Выбери действие"
    send_message(user_id, message, create_raid_keyboard())
    user_states[user_id] = {'state': 'raid_menu'}

def handle_raid_create(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = "⚔️ ВЫБЕРИ ЦЕЛЬ ДЛЯ СТРЕЛКИ ⚔️\n\n"
    for boss_id, boss in BOSSES.items():
        if stats['level'] >= boss['min_level']:
            message += f"{boss_id}. {boss['name']}\n"
    message += "\n👉 Напиши номер"
    send_message(user_id, message)
    user_states[user_id] = {'state': 'raid_creating'}

def handle_raid_create_boss(user_id, text):
    try:
        boss_id = int(text)
        if boss_id not in BOSSES:
            send_message(user_id, "❌ Неверно!", create_main_keyboard())
            del user_states[user_id]
            return
    except:
        send_message(user_id, "❌ Напиши номер!", create_main_keyboard())
        del user_states[user_id]
        return
    stats = get_prisoner_stats(user_id)
    if stats['level'] < BOSSES[boss_id]['min_level']:
        send_message(user_id, f"❌ Нужен {BOSSES[boss_id]['min_level']} уровень!", create_main_keyboard())
        del user_states[user_id]
        return
    raid_id = str(random.randint(100000, 999999))
    active_raids[raid_id] = {
        'boss_id': boss_id,
        'boss_name': BOSSES[boss_id]['name'],
        'boss_max_hp': BOSSES[boss_id]['hp'],
        'boss_current_hp': BOSSES[boss_id]['hp'],
        'creator': user_id,
        'players': {user_id: 0},
        'start_time': datetime.now(),
        'time_limit_hours': RAID_TIME_LIMITS.get(boss_id, 3)
    }
    time_limit = RAID_TIME_LIMITS.get(boss_id, 3)
    message = f"⚔️ СТРЕЛКА СОЗДАНА! ⚔️\n\n"
    message += f"🐉 Цель: {BOSSES[boss_id]['name']}\n"
    message += f"🔢 ID: {raid_id}\n\n"
    message += f"📝 Братва подключается: !рейд {raid_id}\n\n"
    message += f"👥 Участников: 1\n"
    message += f"❤️ ХП: {BOSSES[boss_id]['hp']}\n"
    message += f"⏰ Время на стрелку: {time_limit} часов\n\n"
    message += "💡 Если выйдешь из боя - вернуться можно по кнопке 'Ввести ID'"
    user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
    send_message(user_id, message, create_fight_keyboard())

def handle_raid_join(user_id, raid_id):
    raid_id = str(raid_id).strip()
    print(f"🔗 ПОДКЛЮЧЕНИЕ К СТРЕЛКЕ: user={user_id}, raid_id={raid_id}")
    
    if raid_id not in active_raids:
        send_message(user_id, "❌ Стрелка не найдена!\nПроверь ID.", create_main_keyboard())
        return
    
    raid = active_raids[raid_id]
    print(f"🎯 РЕЙД: {raid['boss_name']}, ХП={raid['boss_current_hp']}")
    
    elapsed = datetime.now() - raid['start_time']
    if elapsed > timedelta(hours=raid['time_limit_hours']):
        send_message(user_id, "❌ Время стрелки истекло!", create_main_keyboard())
        del active_raids[raid_id]
        return
    
    stats = get_prisoner_stats(user_id)
    boss_data = BOSSES[raid['boss_id']]
    
    if stats['level'] < boss_data['min_level']:
        send_message(user_id, f"❌ Нужен {boss_data['min_level']} уровень!", create_main_keyboard())
        return
    
    if len(raid['players']) >= MAX_RAID_PLAYERS:
        send_message(user_id, f"❌ Стрелка переполнена!", create_main_keyboard())
        return
    
    for rcode, r in active_raids.items():
        if user_id in r.get('players', {}):
            send_message(user_id, f"❌ Ты уже на стрелке {rcode}!", create_main_keyboard())
            return
    
    remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
    remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
    
    if user_id in raid['players']:
        message = f"⚔️ ВОЗВРАЩЕНИЕ НА СТРЕЛКУ! ⚔️\n\n"
        message += f"🐉 Цель: {raid['boss_name']}\n"
        message += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
        message += f"👥 Участников: {len(raid['players'])}\n"
        message += f"⏰ Осталось: {remaining_text}\n\n"
        message += "👉 Вали цель!"
        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
        if user_id in user_raid_temp:
            del user_raid_temp[user_id]
        send_message(user_id, message, create_fight_keyboard())
        return
    
    raid['players'][user_id] = 0
    print(f"✅ НОВЫЙ УЧАСТНИК {get_user_name(user_id)} добавлен в стрелку {raid_id}")
    print(f"👥 ТЕКУЩИЕ УЧАСТНИКИ: {list(raid['players'].keys())}")
    
    user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
    print(f"📌 Установлено состояние для {user_id}: {user_states[user_id]}")
    
    message = f"⚔️ ТЫ НА СТРЕЛКЕ! ⚔️\n\n"
    message += f"🐉 Цель: {raid['boss_name']}\n"
    message += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
    message += f"👥 Участников: {len(raid['players'])}\n"
    message += f"⏰ Осталось: {remaining_text}\n\n"
    message += "👉 НАЖМИ НА ОРУЖИЕ, ЧТОБЫ НАНЕСТИ УДАР!\n"
    message += "👊 Кастет - бесплатно\n"
    message += "🔪 Заточка, ⚔️ Бита, 🔫 Ствол, ⭐ Фрачная масть - купить в Маляве\n\n"
    message += "💡 Если удары не проходят - напиши !проверить"
    send_message(user_id, message, create_fight_keyboard())

def handle_raid_stats(user_id):
    if not active_raids:
        send_message(user_id, "❌ Нет активных стрелок!", create_main_keyboard())
        return
    user_raid = None
    for raid_id, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            user_raid = raid
            break
    if user_raid:
        elapsed = datetime.now() - user_raid['start_time']
        remaining_hours = user_raid['time_limit_hours'] - elapsed.total_seconds() / 3600
        remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
        sorted_players = sorted(user_raid['players'].items(), key=lambda x: x[1], reverse=True)
        message = f"📊 ТВОЯ СТРЕЛКА 📊\n\n"
        message += f"🐉 Цель: {user_raid['boss_name']}\n"
        message += f"❤️ ХП: {user_raid['boss_current_hp']}/{user_raid['boss_max_hp']}\n"
        message += f"📊 Прогресс: {((user_raid['boss_max_hp'] - user_raid['boss_current_hp']) / user_raid['boss_max_hp'] * 100):.1f}%\n"
        message += f"👥 Участников: {len(user_raid['players'])}\n"
        message += f"⏰ Осталось: {remaining_text}\n\n"
        message += f"👥 БРАТВА (по урону):\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, dmg) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else "📌"
            mention = get_user_mention(uid)
            message += f"{medal} {mention}: {dmg} урона\n"
        send_message(user_id, message, create_main_keyboard())
    else:
        message = "📊 АКТИВНЫЕ СТРЕЛКИ 📊\n\n"
        for raid_id, raid in active_raids.items():
            elapsed = datetime.now() - raid['start_time']
            remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
            remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
            message += f"🔢 ID: {raid_id}\n"
            message += f"🐉 Босс: {raid['boss_name']}\n"
            message += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n"
            message += f"👑 Создатель: {get_user_name(raid['creator'])}\n\n"
        send_message(user_id, message, create_main_keyboard())

def handle_shop_in_raid(user_id):
    stats = get_prisoner_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = f"🏪 МАЛЯВА (Прямо во время стрелки!)\n💰 Бабла: {stats['money']}\n\n"
    message += "2. 🔪 Заточка - 1000💰 (урон +15, УР.3, крит 30%)\n"
    message += "3. ⚔️ Бита - 5000💰 (урон +35, УР.8, крит 35%)\n"
    message += "4. 🔫 Ствол - 20000💰 (урон +80, УР.15, крит 40%)\n"
    message += "5. ⭐ Фрачная масть - 50000💰 (урон +160, УР.25, крит 50%)\n\n"
    message += "👉 Напиши номер оружия для покупки:\n"
    message += "2 - Заточка\n"
    message += "3 - Бита\n"
    message += "4 - Ствол\n"
    message += "5 - Фрачная масть\n\n"
    message += "💡 После покупки продолжишь бой!"
    send_message(user_id, message, create_back_keyboard())
    user_states[user_id] = {'state': 'buying_in_raid'}

def handle_buy_weapon_in_raid(user_id, weapon_choice):
    try:
        weapon_id = int(weapon_choice)
        if weapon_id not in [2, 3, 4, 5]:
            send_message(user_id, "❌ Доступные номера: 2, 3, 4, 5", create_fight_keyboard())
            del user_states[user_id]
            return
    except:
        send_message(user_id, "❌ Напиши номер оружия: 2, 3, 4 или 5", create_fight_keyboard())
        del user_states[user_id]
        return
    weapon_data = WEAPONS[weapon_id]
    stats = get_prisoner_stats(user_id)
    raid_code = user_states[user_id].get('raid_code')
    if stats['level'] < weapon_data['min_level']:
        send_message(user_id, f"❌ Нужен {weapon_data['min_level']} уровень!", create_fight_keyboard())
        del user_states[user_id]
        return
    if stats['money'] < weapon_data['price']:
        send_message(user_id, f"❌ Не хватает! Нужно {weapon_data['price']}💰\n💰 У тебя: {stats['money']}", create_fight_keyboard())
        del user_states[user_id]
        return
    add_weapon_to_inventory(user_id, weapon_id)
    add_money(user_id, -weapon_data['price'])
    if raid_code and raid_code in active_raids:
        raid = active_raids[raid_code]
        remaining = raid['time_limit_hours'] - (datetime.now() - raid['start_time']).total_seconds() / 3600
        remaining_text = f"{int(remaining)}ч {int((remaining % 1) * 60)}мин" if remaining > 0 else "Время истекло"
        weapons_inv = get_user_weapons(user_id)
        current_count = weapons_inv.get(str(weapon_id), 0)
        msg = f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет\n📦 Теперь в хате: {current_count} шт.\n\n"
        msg += f"⚔️ ВОЗВРАЩЕНИЕ В БОЙ!\n🐉 Цель: {raid['boss_name']}\n❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n⏰ Осталось: {remaining_text}\n\n👉 ПРОДОЛЖАЙ ВАЛИТЬ!"
        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_code}
        send_message(user_id, msg, create_fight_keyboard())
    else:
        send_message(user_id, f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет", create_main_keyboard())
        del user_states[user_id]

def handle_raid_attack(user_id, weapon_text):
    print(f"🔫 АТАКА В СТРЕЛКЕ: user={user_id}, weapon='{weapon_text}'")
    
    if user_id not in user_states:
        print(f"⚠️ НЕТ СОСТОЯНИЯ, ищем рейд для {user_id}...")
        for rcode, raid in active_raids.items():
            if user_id in raid.get('players', {}):
                print(f"✅ НАЙДЕН РЕЙД {rcode} ДЛЯ {user_id}")
                user_states[user_id] = {'state': 'raid_attacking', 'raid_code': rcode}
                break
    
    if user_id not in user_states:
        print(f"❌ НЕТ СОСТОЯНИЯ И РЕЙДА ДЛЯ {user_id}")
        send_message(user_id, "❌ Ты не в бою! Напиши !рейд с ID стрелки", create_main_keyboard())
        return False
    
    state = user_states[user_id]
    raid_code = state.get('raid_code')
    
    if not raid_code:
        print(f"🔍 ИЩЕМ РЕЙД ПО УЧАСТНИКУ {user_id}...")
        for rcode, raid in active_raids.items():
            if user_id in raid.get('players', {}):
                raid_code = rcode
                state['raid_code'] = raid_code
                print(f"✅ НАЙДЕН РЕЙД {raid_code}, ОБНОВЛЯЕМ СОСТОЯНИЕ")
                break
    
    if not raid_code or raid_code not in active_raids:
        send_message(user_id, "❌ Стрелка не найдена! Подключись заново: !рейд [ID]", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return False
    
    raid = active_raids[raid_code]
    print(f"🎯 РЕЙД: {raid['boss_name']}, ХП={raid['boss_current_hp']}, УЧАСТНИКИ={list(raid['players'].keys())}")
    
    total_damage_dealt = sum(raid['players'].values())
    if total_damage_dealt == 0 and user_id != raid['creator']:
        print(f"⚠️ ПЕРВЫЙ УДАР МОЖЕТ НАНЕСТИ ТОЛЬКО СОЗДАТЕЛЬ! Создатель: {raid['creator']}, пытается: {user_id}")
        send_message(user_id, f"⚠️ Первый удар по {raid['boss_name']} должен нанести создатель стрелки!\n👑 Создатель: {get_user_name(raid['creator'])}\n\nДождись, пока он начнёт битву, потом подключайся!", create_fight_keyboard())
        return True
    
    if user_id not in raid['players']:
        print(f"⚠️ ИГРОК {user_id} НЕ В СПИСКЕ УЧАСТНИКОВ! Добавляем...")
        raid['players'][user_id] = 0
    
    if "Перейти в маляву" in weapon_text:
        user_states[user_id] = {'state': 'buying_in_raid', 'raid_code': raid_code}
        handle_shop_in_raid(user_id)
        return True
    
    if "Сдаться" in weapon_text:
        user_raid_temp[user_id] = raid_code
        send_message(user_id, f"🏳️ Вышел из стрелки!\nВернись: !рейд {raid_code}", create_main_keyboard())
        del user_states[user_id]
        return True
    
    if "Статистика" in weapon_text:
        sorted_players = sorted(raid['players'].items(), key=lambda x: x[1], reverse=True)
        msg = f"📊 СТАТИСТИКА БОЯ\n\n"
        msg += f"🐉 {raid['boss_name']}\n"
        msg += f"❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
        msg += f"📊 Прогресс: {((raid['boss_max_hp'] - raid['boss_current_hp']) / raid['boss_max_hp'] * 100):.1f}%\n\n"
        msg += f"👥 УЧАСТНИКИ ({len(raid['players'])}):\n"
        for i, (uid, dmg) in enumerate(sorted_players[:5]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📌"
            msg += f"{medal} {get_user_name(uid)}: {dmg} урона\n"
        send_message(user_id, msg, create_fight_keyboard())
        return True
    
    weapon_id = None
    if "Кастет" in weapon_text:
        weapon_id = 1
    elif "Заточка" in weapon_text:
        weapon_id = 2
    elif "Бита" in weapon_text:
        weapon_id = 3
    elif "Ствол" in weapon_text:
        weapon_id = 4
    elif "Фрачная масть" in weapon_text:
        weapon_id = 5
    else:
        send_message(user_id, "❌ Выбери ствол: 👊 Кастет, 🔪 Заточка, ⚔️ Бита, 🔫 Ствол, ⭐ Фрачная масть", create_fight_keyboard())
        return True
    
    weapon_data = WEAPONS[weapon_id]
    stats = get_prisoner_stats(user_id)
    
    if not stats:
        send_message(user_id, "❌ Ошибка загрузки профиля!", create_main_keyboard())
        return True
    
    if raid['boss_current_hp'] <= 0:
        send_message(user_id, "❌ Цель УЖЕ ПРОБИТА!", create_main_keyboard())
        del active_raids[raid_code]
        del user_states[user_id]
        return True
    
    if weapon_data['price'] > 0:
        weapons_inv = get_user_weapons(user_id)
        available = weapons_inv.get(str(weapon_id), 0)
        if available <= 0:
            send_message(user_id, f"❌ Нет {weapon_data['name']}! Купи в Маляве\n\nНажми '🏪 Перейти в маляву'", create_fight_keyboard())
            return True
        remove_weapon_from_inventory(user_id, weapon_id)
    else:
        if user_id in last_free_weapon_use:
            last = last_free_weapon_use[user_id]
            if datetime.now() - last < timedelta(seconds=FREE_WEAPON_COOLDOWN):
                remaining = FREE_WEAPON_COOLDOWN - (datetime.now() - last).seconds
                send_message(user_id, f"⏱️ Кастет через {remaining} сек", create_fight_keyboard())
                return True
        last_free_weapon_use[user_id] = datetime.now()
    
    damage = weapon_data['damage'] + stats['level'] * 2
    crit = random.randint(1, 100) <= weapon_data['crit_chance']
    if crit:
        damage = damage * 2
    
    old_hp = raid['boss_current_hp']
    raid['boss_current_hp'] -= damage
    raid['players'][user_id] = raid['players'].get(user_id, 0) + damage
    
    crit_text = " 💥КРИТ💥" if crit else ""
    
    if raid['boss_current_hp'] <= 0:
        raid['boss_current_hp'] = 0
        
        boss_data = BOSSES[raid['boss_id']]
        base_money = random.randint(boss_data['reward_money'][0], boss_data['reward_money'][1])
        base_auth = random.randint(boss_data['reward_auth'][0], boss_data['reward_auth'][1])
        base_xp = random.randint(boss_data['reward_xp'][0], boss_data['reward_xp'][1])
        
        sorted_players = sorted(raid['players'].items(), key=lambda x: x[1], reverse=True)
        
        for i, (uid, dmg) in enumerate(sorted_players):
            bonus_money = base_money // 2 if i == 0 else base_money // 3 if i == 1 else base_money // 4 if i == 2 else 0
            bonus_auth = base_auth // 2 if i == 0 else base_auth // 3 if i == 1 else base_auth // 4 if i == 2 else 0
            if uid == raid['creator']:
                bonus_money += base_money // 3
                bonus_auth += base_auth // 3
            
            add_money(uid, base_money + bonus_money)
            add_authority(uid, base_auth + bonus_auth)
            add_xp(uid, base_xp)
            add_boss_kill_today(uid, raid['boss_id'])
            kills_today = get_boss_kills_today(uid, raid['boss_id'])
            
            st = get_prisoner_stats(uid)
            kills = json.loads(st['boss_kills']) if st['boss_kills'] else []
            if raid['boss_id'] not in kills:
                kills.append(raid['boss_id'])
                conn = sqlite3.connect('tyaryzhka.db')
                c = conn.cursor()
                c.execute('UPDATE prisoners SET boss_kills = ? WHERE user_id = ?', (json.dumps(kills), uid))
                conn.commit()
                conn.close()
            
            bonus_text = "🏆 ТОП УРОНА! " if i == 0 else ""
            send_message(uid, f"🎉 ПОБЕДА В СТРЕЛКЕ НАД {raid['boss_name']}!\n💰 +{base_money + bonus_money} бабла\n👑 +{base_auth + bonus_auth} понятий\n📊 +{base_xp} XP\n{bonus_text}\n📅 Сегодня убито {raid['boss_name']}: {kills_today}/{BOSS_DAILY_LIMIT}")
        
        reset_boss_hp(raid['boss_id'])
        send_message(user_id, f"🎉 СТРЕЛКА ЗАВЕРШЕНА ПОБЕДОЙ!\n💥 Твой урон: {damage}{crit_text}", create_main_keyboard())
        del active_raids[raid_code]
        del user_states[user_id]
        if user_id in user_raid_temp:
            del user_raid_temp[user_id]
        return True
    
    hp_left = raid['boss_current_hp']
    hp_total = raid['boss_max_hp']
    percent = ((hp_total - hp_left) / hp_total * 100)
    
    message = f"⚔️ УДАР ПО {raid['boss_name']}!\n"
    message += f"🔫 {weapon_data['emoji']} {weapon_data['name']}\n"
    message += f"💥 Урон: {damage}{crit_text}\n"
    message += f"❤️ ХП: {hp_left}/{hp_total} ({percent:.1f}%)\n"
    
    send_message(user_id, message, create_fight_keyboard())
    return True

def handle_help(user_id):
    message = """🔥 ТЮРЯГА - ПОМОЩЬ 🔥

📜 Личное дело - твоё досье
⚔️ Пробив - соло наезд на босса
💼 Работа - фартим бабло
🏪 Малява - купить ствол
📦 Хата - твои заточки
🏆 Рейтинг - топ братвы
🎁 Чифир - халявное бабло (раз в 6ч)
👥 Стрелка - рейд с братвой

🔢 КАК СОБРАТЬ СТРЕЛКУ:
1. Нажми "👥 Стрелка" → "Создать стрелку"
2. Выбери цель → получи ID
3. Братва подключается: !рейд ID
4. Если вышел - вернись по кнопке 'Ввести ID'

💡 В стрелке:
- Урон всех суммируется
- ТОП урона получает бонус
- Создатель получает бонус
- Кнопка 'Статистика боя' показывает прогресс
- Кнопка 'Перейти в маляву' - купить стволы не выходя из боя

📅 ЛИМИТЫ:
- Каждого босса можно убить 6 раз в день
- Лимиты сбрасываются в 00:00
- Команда !лимиты показывает прогресс

👥 УЧАСТНИКОВ В СТРЕЛКЕ:
- Безлимит!

👉 ВСЁ УПРАВЛЕНИЕ ПО КНОПКАМ!"""
    send_message(user_id, message, create_main_keyboard())

# ========== АДМИН-ПАНЕЛЬ ==========
def handle_admin_panel(user_id):
    if not is_admin(user_id):
        send_message(user_id, "⛔ Доступ запрещён", create_main_keyboard())
        return
    send_message(user_id, "🔐 АДМИН-ПАНЕЛЬ", create_admin_keyboard())
    user_states[user_id] = {'state': 'admin'}

def handle_admin_max(user_id):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(prisoners)")
    columns = [col[1] for col in c.fetchall()]
    if 'is_admin_hidden' not in columns:
        c.execute('ALTER TABLE prisoners ADD COLUMN is_admin_hidden INTEGER DEFAULT 0')
    c.execute('UPDATE prisoners SET money = 1000000, authority = 5000, level = 50, xp = 0 WHERE user_id = ?', (user_id,))
    weapons_inv = {"1": 1, "2": 99, "3": 99, "4": 99, "5": 99}
    c.execute('UPDATE prisoners SET weapon_inventory = ? WHERE user_id = ?', (json.dumps(weapons_inv), user_id))
    c.execute('UPDATE prisoners SET is_admin_hidden = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    send_message(user_id, "✅ АДМИН ПРОКАЧАН!\n💰 Бабло: 1,000,000\n👑 Понятия: 5000\n📊 Уровень: 50\n📦 Всё оружие в хате\n⭐ Скрыт из рейтинга!", create_admin_keyboard())

def handle_admin_give_money(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "💰 Введи ID и сумму:\nПример: 123456789 5000")
    user_states[user_id] = {'state': 'admin_give_money'}

def handle_admin_give_auth(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "👑 Введи ID и количество понятий:\nПример: 123456789 100")
    user_states[user_id] = {'state': 'admin_give_auth'}

def handle_admin_give_weapon(user_id):
    if not is_admin(user_id):
        return
    message = "⭐ Введи ID и номер оружия:\n\n"
    for wid, w in WEAPONS.items():
        if wid > 1:
            message += f"{w['emoji']} {w['name']} - {wid}\n"
    message += "\nПример: 123456789 2"
    send_message(user_id, message)
    user_states[user_id] = {'state': 'admin_give_weapon'}

def handle_admin_upgrade_level(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "📈 Введи ID и количество уровней:\nПример: 123456789 5")
    user_states[user_id] = {'state': 'admin_upgrade_level'}

def handle_admin_smart_stats(user_id):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM prisoners')
    total_players = c.fetchone()[0]
    c.execute('SELECT SUM(money) FROM prisoners')
    total_money = c.fetchone()[0] or 0
    c.execute('SELECT AVG(level) FROM prisoners')
    avg_level = c.fetchone()[0] or 0
    c.execute('SELECT SUM(authority) FROM prisoners')
    total_auth = c.fetchone()[0] or 0
    c.execute('SELECT name, money FROM prisoners ORDER BY money DESC LIMIT 5')
    top_money = c.fetchall()
    c.execute('SELECT name, level FROM prisoners ORDER BY level DESC LIMIT 5')
    top_level = c.fetchall()
    c.execute('SELECT name, authority FROM prisoners ORDER BY authority DESC LIMIT 5')
    top_auth = c.fetchall()
    active_raids_count = len(active_raids)
    c.execute("SELECT boss_kills FROM prisoners WHERE boss_kills IS NOT NULL AND boss_kills != '[]'")
    all_kills = c.fetchall()
    total_boss_kills = 0
    for row in all_kills:
        try:
            kills = json.loads(row[0])
            total_boss_kills += len(kills)
        except:
            pass
    conn.close()
    message = f"📊 УМНАЯ СТАТИСТИКА 📊\n\n"
    message += f"👥 Всего игроков: {total_players}\n"
    message += f"💰 Всего бабла: {total_money:,}\n"
    message += f"👑 Всего понятий: {total_auth:,}\n"
    message += f"📊 Средний уровень: {avg_level:.1f}\n"
    message += f"⚔️ Убито боссов: {total_boss_kills}\n"
    message += f"👥 Активных стрелок: {active_raids_count}\n\n"
    message += f"💰 БОГАТЕЙШИЕ:\n"
    for i, (name, money) in enumerate(top_money, 1):
        message += f"{i}. {name}: {money:,}💰\n"
    message += f"\n👑 АВТОРИТЕТНЫЕ:\n"
    for i, (name, auth) in enumerate(top_auth, 1):
        message += f"{i}. {name}: {auth}👑\n"
    message += f"\n📊 МОЩНЫЕ ПО УРОВНЮ:\n"
    for i, (name, level) in enumerate(top_level, 1):
        message += f"{i}. {name}: УР.{level}\n"
    send_message(user_id, message, create_admin_keyboard())

def handle_admin_players_list(user_id, page=0):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    c.execute('SELECT user_id, name, money, authority, level FROM prisoners ORDER BY level DESC, authority DESC')
    players = c.fetchall()
    conn.close()
    items_per_page = 15
    start = page * items_per_page
    end = start + items_per_page
    page_players = players[start:end]
    if not page_players:
        send_message(user_id, "❌ Нет игроков на этой странице", create_admin_keyboard())
        return
    total_pages = (len(players) + items_per_page - 1) // items_per_page
    message = f"👥 СПИСОК ИГРОКОВ (стр.{page+1}/{total_pages})\n\n"
    for uid, name, money, auth, level in page_players:
        message += f"📌 {name}\n   💰{money:,} | 👑{auth} | УР.{level}\n   🆔 {uid}\n\n"
    keyboard = VkKeyboard(one_time=False)
    if page > 0:
        keyboard.add_button("◀️ Предыдущая", color=VkKeyboardColor.PRIMARY)
    if end < len(players):
        keyboard.add_button("Следующая ▶️", color=VkKeyboardColor.PRIMARY)
    if page > 0 or end < len(players):
        keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    send_message(user_id, message, keyboard)
    user_states[user_id] = {'state': 'admin_players_list', 'page': page}

def handle_reset_all_bosses(user_id):
    if not is_admin(user_id):
        return
    for boss_id in BOSSES:
        reset_boss_hp(boss_id)
    send_message(user_id, "✅ ВСЕ БОССЫ ВОСКРЕСЛИ!", create_admin_keyboard())

def handle_post_top(user_id):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('tyaryzhka.db')
    c = conn.cursor()
    message = "🏆 ТОП-15 ИГРОКОВ ТЮРЯГИ 🏆\n\n"
    c.execute('SELECT user_id, name, level, authority FROM prisoners WHERE is_admin_hidden = 0 ORDER BY authority DESC, level DESC LIMIT 15')
    top = c.fetchall()
    for i, (uid, name, level, auth) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        mention = get_user_mention(uid)
        message += f"{medal} {i}. {mention}\n   УР.{level} | 👑{auth}\n\n"
    conn.close()
    try:
        vk.wall.post(owner_id=-GROUP_ID, message=message, from_group=1)
        send_message(user_id, "✅ ТОП-15 опубликован в сообществе!", create_admin_keyboard())
    except Exception as e:
        send_message(user_id, f"❌ Ошибка публикации: {e}", create_admin_keyboard())

def handle_clear_db(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "⚠️ ТОЧНО ОЧИСТИТЬ ВСЮ БАЗУ?\nНапиши ДА", create_admin_keyboard())
    user_states[user_id] = {'state': 'admin_clear_confirm'}

def handle_clear_db_confirm(user_id, text):
    if not is_admin(user_id):
        return False
    if text.upper() == "ДА":
        conn = sqlite3.connect('tyaryzhka.db')
        c = conn.cursor()
        c.execute('DELETE FROM prisoners')
        c.execute('DELETE FROM boss_hp')
        c.execute('DELETE FROM raid_logs')
        c.execute('DELETE FROM boss_kills_daily')
        conn.commit()
        conn.close()
        for boss_id, boss in BOSSES.items():
            reset_boss_hp(boss_id)
        send_message(user_id, "✅ ВСЯ СТАТИСТИКА ОЧИЩЕНА!", create_admin_keyboard())
    else:
        send_message(user_id, "❌ ОТМЕНЕНО!", create_admin_keyboard())
    if user_id in user_states:
        del user_states[user_id]
    return True

def execute_admin_action(user_id, text):
    if not is_admin(user_id):
        return False
    state = user_states.get(user_id, {}).get('state')
    if state == 'admin_give_money':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                amount = int(parts[1])
                add_money(target_id, amount)
                send_message(user_id, f"✅ Выдано {amount}💰 игроку {get_user_name(target_id)}", create_admin_keyboard())
            except:
                send_message(user_id, "❌ Ошибка! Формат: ID сумма", create_admin_keyboard())
        else:
            send_message(user_id, "❌ Формат: ID сумма", create_admin_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return True
    elif state == 'admin_give_auth':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                amount = int(parts[1])
                add_authority(target_id, amount)
                send_message(user_id, f"✅ Выдано {amount} понятий игроку {get_user_name(target_id)}", create_admin_keyboard())
            except:
                send_message(user_id, "❌ Ошибка! Формат: ID сумма", create_admin_keyboard())
        else:
            send_message(user_id, "❌ Формат: ID сумма", create_admin_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return True
    elif state == 'admin_give_weapon':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                weapon_id = int(parts[1])
                if weapon_id in WEAPONS and weapon_id > 1:
                    add_weapon_to_inventory(target_id, weapon_id)
                    send_message(user_id, f"✅ Выдано {WEAPONS[weapon_id]['emoji']} {WEAPONS[weapon_id]['name']} игроку {get_user_name(target_id)}", create_admin_keyboard())
                else:
                    send_message(user_id, "❌ Неверный ID оружия!", create_admin_keyboard())
            except:
                send_message(user_id, "❌ Ошибка! Формат: ID_игрока ID_оружия", create_admin_keyboard())
        else:
            send_message(user_id, "❌ Формат: ID_игрока ID_оружия", create_admin_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return True
    elif state == 'admin_upgrade_level':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                levels = int(parts[1])
                if levels > 0:
                    conn = sqlite3.connect('tyaryzhka.db')
                    c = conn.cursor()
                    c.execute('UPDATE prisoners SET level = level + ?, xp = 0 WHERE user_id = ?', (levels, target_id))
                    conn.commit()
                    conn.close()
                    send_message(user_id, f"✅ Игроку {get_user_name(target_id)} повышен уровень на {levels}!", create_admin_keyboard())
                    send_message(target_id, f"🎉 АДМИН ПОВЫСИЛ ТЕБЕ УРОВЕНЬ НА {levels}!")
                else:
                    send_message(user_id, "❌ Количество уровней должно быть положительным!", create_admin_keyboard())
            except:
                send_message(user_id, "❌ Ошибка! Формат: ID количество", create_admin_keyboard())
        else:
            send_message(user_id, "❌ Формат: ID количество", create_admin_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return True
    elif state == 'admin_clear_confirm':
        return handle_clear_db_confirm(user_id, text)
    return False

# ========== ОСНОВНОЙ ЦИКЛ ==========
print("=" * 50)
print("🔥 ТЮРЯГА - СТРЕЛКИ НА БОССОВ 🔥")
print("=" * 50)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.obj.message
        user_id = msg['from_id']
        text = msg['text'] if msg['text'] else ""
        
        if user_id < 0:
            continue
        
        print(f"🔍 ВХОДЯЩЕЕ СООБЩЕНИЕ: '{text}' от {user_id}")
        
        if text in ["👊 Кастет", "🔪 Заточка", "⚔️ Бита", "🔫 Ствол", "⭐ Фрачная масть"]:
            print(f"🎯 ОРУЖИЕ РАСПОЗНАНО: {text}")
            if user_id in user_states:
                state = user_states[user_id]
                if state.get('state') == 'raid_attacking':
                    handle_raid_attack(user_id, text)
                elif state.get('state') == 'fighting':
                    handle_fight(user_id, text)
                else:
                    send_message(user_id, "❌ Ты не в бою! Начни битву с боссом или подключись к стрелке!", create_main_keyboard())
            else:
                send_message(user_id, "❌ Ты не в бою! Напиши !старт или !рейд [ID]", create_main_keyboard())
            continue
        
        if text.lower().startswith('!рейд'):
            parts = text.split()
            if len(parts) == 2:
                handle_raid_join(user_id, parts[1])
            else:
                send_message(user_id, "❌ Пример: !рейд 123456", create_main_keyboard())
            continue
        
        if text.lower().startswith('!админка'):
            handle_admin_panel(user_id)
            continue
        
        if text.lower().startswith('!старт'):
            handle_start(user_id)
            continue
        
        if text.lower().startswith('!помощь'):
            handle_help(user_id)
            continue
        
        if text.lower().startswith('!лимиты'):
            stats = get_prisoner_stats(user_id)
            if not stats:
                handle_start(user_id)
                continue
            message = "📊 ТВОИ ЛИМИТЫ НА СЕГОДНЯ 📊\n\n"
            for boss_id, boss in BOSSES.items():
                kills = get_boss_kills_today(user_id, boss_id)
                remaining = BOSS_DAILY_LIMIT - kills
                message += f"{boss['name']}: {kills}/{BOSS_DAILY_LIMIT} (осталось {remaining})\n"
            send_message(user_id, message, create_main_keyboard())
            continue
        
        if text.lower().startswith('!проверить'):
            state = user_states.get(user_id, {})
            raid_code = state.get('raid_code')
            msg = f"📊 ДИАГНОСТИКА:\n"
            msg += f"Состояние: {state.get('state')}\n"
            msg += f"Код рейда: {raid_code}\n"
            if raid_code and raid_code in active_raids:
                raid = active_raids[raid_code]
                msg += f"Босс: {raid['boss_name']}\n"
                msg += f"ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n"
                msg += f"Ты в участниках: {user_id in raid['players']}\n"
                msg += f"Всего участников: {len(raid['players'])}\n"
            else:
                msg += f"Рейд не найден в active_raids\n"
                msg += f"Активные рейды: {list(active_raids.keys())}"
            send_message(user_id, msg)
            continue
        
        if user_id in user_states:
            state = user_states[user_id].get('state')
            
            if state == 'buying':
                handle_buy_weapon(user_id, text)
                continue
            elif state == 'fighting':
                if handle_fight(user_id, text):
                    continue
            elif state == 'raid_attacking':
                if handle_raid_attack(user_id, text):
                    continue
            elif state == 'raid_menu':
                if text == "⚔️ Создать стрелку":
                    handle_raid_create(user_id)
                elif text == "🔍 Ввести ID":
                    send_message(user_id, "🔢 Введи ID стрелки (6 цифр):")
                    user_states[user_id] = {'state': 'raid_join_waiting'}
                elif text == "📊 Статистика стрелки":
                    handle_raid_stats(user_id)
                elif text == "◀️ Назад":
                    handle_start(user_id)
                continue
            elif state == 'raid_join_waiting':
                if text.isdigit() and len(text) == 6:
                    handle_raid_join(user_id, text)
                else:
                    send_message(user_id, "❌ ID состоит из 6 цифр!", create_main_keyboard())
                del user_states[user_id]
                continue
            elif state == 'raid_creating':
                handle_raid_create_boss(user_id, text)
                continue
            elif state == 'buying_in_raid':
                if text == "◀️ Вернуться в бой" or text == "◀️ Назад":
                    raid_code = user_states[user_id].get('raid_code')
                    if raid_code and raid_code in active_raids:
                        raid = active_raids[raid_code]
                        remaining = raid['time_limit_hours'] - (datetime.now() - raid['start_time']).total_seconds() / 3600
                        remaining_text = f"{int(remaining)}ч {int((remaining % 1) * 60)}мин" if remaining > 0 else "Время истекло"
                        msg = f"⚔️ ВОЗВРАЩЕНИЕ В БОЙ!\n🐉 Цель: {raid['boss_name']}\n❤️ ХП: {raid['boss_current_hp']}/{raid['boss_max_hp']}\n⏰ Осталось: {remaining_text}\n\n👉 ВАЛИ ЦЕЛЬ!"
                        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_code}
                        send_message(user_id, msg, create_fight_keyboard())
                    else:
                        send_message(user_id, "❌ Стрелка завершена!", create_main_keyboard())
                        del user_states[user_id]
                else:
                    handle_buy_weapon_in_raid(user_id, text)
                continue
            elif state == 'admin':
                if text == "💰 Выдать деньги":
                    handle_admin_give_money(user_id)
                elif text == "👑 Выдать понятия":
                    handle_admin_give_auth(user_id)
                elif text == "⭐ Выдать оружие":
                    handle_admin_give_weapon(user_id)
                elif text == "📈 Повысить уровень":
                    handle_admin_upgrade_level(user_id)
                elif text == "⚔️ Сбросить боссов":
                    handle_reset_all_bosses(user_id)
                elif text == "📊 Умная статистика":
                    handle_admin_smart_stats(user_id)
                elif text == "👥 Список игроков":
                    handle_admin_players_list(user_id)
                elif text == "📢 Опубликовать ТОП":
                    handle_post_top(user_id)
                elif text == "🔨 Очистить БД":
                    handle_clear_db(user_id)
                elif text == "⭐ Прокачать админа":
                    handle_admin_max(user_id)
                elif text == "◀️ Назад":
                    handle_start(user_id)
                continue
            elif state == 'admin_players_list':
                if text == "◀️ Предыдущая":
                    page = user_states[user_id].get('page', 0) - 1
                    if page >= 0:
                        handle_admin_players_list(user_id, page)
                elif text == "Следующая ▶️":
                    page = user_states[user_id].get('page', 0) + 1
                    handle_admin_players_list(user_id, page)
                elif text == "◀️ Назад":
                    handle_admin_panel(user_id)
                continue
            elif state in ['admin_give_money', 'admin_give_auth', 'admin_give_weapon', 'admin_upgrade_level']:
                if execute_admin_action(user_id, text):
                    continue
            elif state == 'admin_clear_confirm':
                if execute_admin_action(user_id, text):
                    continue
        
        if text == "📜 Личное дело":
            handle_profile(user_id)
        elif text == "⚔️ Пробив":
            handle_boss_list(user_id)
        elif text == "💼 Работа":
            handle_work(user_id)
        elif text == "🏪 Малява":
            handle_shop(user_id)
        elif text == "📦 Хата":
            handle_inventory(user_id)
        elif text == "🏆 Рейтинг":
            handle_ranking(user_id)
        elif text == "🎁 Чифир":
            handle_daily_bonus(user_id)
        elif text == "👥 Стрелка":
            handle_raid(user_id)
        elif text == "❓ Помощь":
            handle_help(user_id)
        elif text == "◀️ Назад":
            handle_start(user_id)
        elif any(boss['name'] in text for boss in BOSSES.values()):
            handle_boss_selection(user_id, text)
        else:
            conn = sqlite3.connect('tyaryzhka.db')
            c = conn.cursor()
            c.execute('SELECT user_id FROM prisoners WHERE user_id = ?', (user_id,))
            exists = c.fetchone()
            conn.close()
            if not exists:
                handle_start(user_id)

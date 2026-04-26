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
ADMIN_IDS = [int(os.environ.get("ADMIN_ID", 1024252142))]

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

# ========== МОНСТРЫ (БОССЫ) ==========
MONSTERS = {
    1: {"id": 1, "name": "🐗 Дикий вепрь", "hp": 1000, "reward_gold": (500, 1000), "reward_honor": (10, 20), "reward_xp": (50, 100), "min_level": 1},
    2: {"id": 2, "name": "🌿 Леший", "hp": 2000, "reward_gold": (1000, 2000), "reward_honor": (20, 40), "reward_xp": (100, 200), "min_level": 3},
    3: {"id": 3, "name": "🗿 Каменный голем", "hp": 3500, "reward_gold": (2000, 4000), "reward_honor": (40, 70), "reward_xp": (200, 350), "min_level": 6},
    4: {"id": 4, "name": "🐉 Огненный дракон", "hp": 5500, "reward_gold": (4000, 7000), "reward_honor": (70, 120), "reward_xp": (350, 600), "min_level": 10},
    5: {"id": 5, "name": "👑 Король-лич", "hp": 8000, "reward_gold": (7000, 12000), "reward_honor": (120, 200), "reward_xp": (600, 1000), "min_level": 15},
    6: {"id": 6, "name": "🦇 Повелитель тьмы", "hp": 12000, "reward_gold": (12000, 20000), "reward_honor": (200, 350), "reward_xp": (1000, 1800), "min_level": 20},
    7: {"id": 7, "name": "⚔️ Древний воин", "hp": 18000, "reward_gold": (20000, 35000), "reward_honor": (350, 600), "reward_xp": (1800, 3000), "min_level": 25},
    8: {"id": 8, "name": "💀 Властелин зла", "hp": 25000, "reward_gold": (35000, 60000), "reward_honor": (600, 1000), "reward_xp": (3000, 5000), "min_level": 30}
}

# ========== ОРУЖИЕ ==========
WEAPONS = {
    1: {"id": 1, "name": "👊 Кулак", "price": 0, "damage": 5, "min_level": 1, "emoji": "👊", "crit_chance": 25},
    2: {"id": 2, "name": "🗡️ Кинжал", "price": 1000, "damage": 15, "min_level": 3, "emoji": "🗡️", "crit_chance": 30},
    3: {"id": 3, "name": "⚔️ Длинный меч", "price": 5000, "damage": 35, "min_level": 8, "emoji": "⚔️", "crit_chance": 35},
    4: {"id": 4, "name": "🏹 Арбалет", "price": 20000, "damage": 80, "min_level": 15, "emoji": "🏹", "crit_chance": 40},
    5: {"id": 5, "name": "👑 Королевский меч", "price": 50000, "damage": 160, "min_level": 25, "emoji": "👑", "crit_chance": 50}
}

# ========== РАБОТЫ ==========
JOBS = {
    1: {"name": "🌾 Сбор урожая", "earn": 200, "min_level": 1},
    2: {"name": "🍞 Пекарь", "earn": 400, "min_level": 3},
    3: {"name": "⚒️ Кузнец", "earn": 700, "min_level": 6},
    4: {"name": "🛡️ Стражник", "earn": 1200, "min_level": 10},
    5: {"name": "🏰 Рыцарь", "earn": 2000, "min_level": 15},
    6: {"name": "👑 Лорд", "earn": 3500, "min_level": 20},
    7: {"name": "⚔️ Полководец", "earn": 6000, "min_level": 25},
    8: {"name": "💎 Королевский советник", "earn": 10000, "min_level": 30}
}

# ========== РАНГИ (ЗВАНИЯ) ==========
RANKS = {
    0: {"name": "🪶 Сквайр", "honor_needed": 0},
    1: {"name": "🗡️ Оруженосец", "honor_needed": 50},
    2: {"name": "🛡️ Стражник", "honor_needed": 150},
    3: {"name": "⚔️ Рыцарь", "honor_needed": 300},
    4: {"name": "🏰 Барон", "honor_needed": 600},
    5: {"name": "👑 Граф", "honor_needed": 1000},
    6: {"name": "⭐ Герцог", "honor_needed": 2000},
    7: {"name": "💀 Король", "honor_needed": 4000}
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
def get_monster_kills_today(user_id, monster_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT COUNT(*) FROM monster_kills_daily WHERE user_id = ? AND monster_id = ? AND date = ?', 
              (user_id, monster_id, today))
    count = c.fetchone()[0]
    conn.close()
    return count

def add_monster_kill_today(user_id, monster_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('''INSERT INTO monster_kills_daily (user_id, monster_id, date, count) 
                 VALUES (?, ?, ?, 1)
                 ON CONFLICT(user_id, monster_id, date) 
                 DO UPDATE SET count = count + 1''', 
              (user_id, monster_id, today))
    conn.commit()
    conn.close()

# ========== БАЗА ДАННЫХ ==========
def init_db():
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS heroes
                 (user_id INTEGER PRIMARY KEY,
                  name TEXT,
                  gold INTEGER DEFAULT 500,
                  honor INTEGER DEFAULT 0,
                  level INTEGER DEFAULT 1,
                  xp INTEGER DEFAULT 0,
                  weapon_inventory TEXT,
                  monster_kills TEXT,
                  is_admin_hidden INTEGER DEFAULT 0,
                  daily_bonus TEXT,
                  last_work TEXT,
                  join_date TEXT,
                  referrer_id INTEGER DEFAULT 0)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS monster_hp
                 (monster_id INTEGER PRIMARY KEY,
                  current_hp INTEGER)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS raid_logs
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  raid_id TEXT,
                  user_id INTEGER,
                  damage INTEGER,
                  time TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS monster_kills_daily
                 (user_id INTEGER,
                  monster_id INTEGER,
                  date TEXT,
                  count INTEGER DEFAULT 1,
                  PRIMARY KEY (user_id, monster_id, date))''')
    
    conn.commit()
    
    for monster_id, monster in MONSTERS.items():
        c.execute('INSERT OR IGNORE INTO monster_hp (monster_id, current_hp) VALUES (?, ?)', (monster_id, monster['hp']))
    
    conn.commit()
    conn.close()
    print("✅ База данных королевства готова")

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
        return f"Путник {user_id}"

def get_user_mention(user_id):
    return f"[id{user_id}|{get_user_name(user_id)}]"

def is_admin(user_id):
    return user_id in ADMIN_IDS

def register_user(user_id, referrer_id=None):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT user_id FROM heroes WHERE user_id = ?', (user_id,))
    if not c.fetchone():
        name = get_user_name(user_id)
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO heroes (user_id, name, join_date, weapon_inventory, referrer_id) VALUES (?, ?, ?, ?, ?)',
                  (user_id, name, now, '{"1":1}', referrer_id or 0))
        conn.commit()
        print(f"✅ Новый герой: {name}")
    conn.close()

def get_hero_stats(user_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT * FROM heroes WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    
    if result:
        if len(result) >= 13:
            return {
                'user_id': result[0], 'name': result[1], 'gold': result[2],
                'honor': result[3], 'level': result[4], 'xp': result[5],
                'weapon_inventory': result[6], 'monster_kills': result[7],
                'is_admin_hidden': result[8], 'daily_bonus': result[9],
                'last_work': result[10], 'join_date': result[11], 'referrer_id': result[12]
            }
        else:
            return {
                'user_id': result[0], 'name': result[1], 'gold': result[2],
                'honor': result[3], 'level': result[4], 'xp': result[5],
                'weapon_inventory': result[6], 'monster_kills': result[7],
                'is_admin_hidden': 0, 'daily_bonus': None,
                'last_work': None, 'join_date': result[8] if len(result) > 8 else None,
                'referrer_id': result[9] if len(result) > 9 else 0
            }
    return None

def add_gold(user_id, amount):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('UPDATE heroes SET gold = gold + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_honor(user_id, amount):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('UPDATE heroes SET honor = honor + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def add_xp(user_id, amount):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT level, xp FROM heroes WHERE user_id = ?', (user_id,))
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
    c.execute('UPDATE heroes SET level = ?, xp = ? WHERE user_id = ?', (level, xp, user_id))
    if level_up:
        bonus = level * 500
        c.execute('UPDATE heroes SET gold = gold + ? WHERE user_id = ?', (bonus, user_id))
        conn.commit()
        conn.close()
        send_message(user_id, f"🎉 НОВЫЙ УРОВЕНЬ! {level}\n💰 +{bonus} золота")
        return True
    conn.commit()
    conn.close()
    return False

def get_rank_name(honor):
    for level, rank in sorted(RANKS.items(), reverse=True):
        if honor >= rank['honor_needed']:
            return rank['name']
    return RANKS[0]['name']

def get_monster_hp(monster_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT current_hp FROM monster_hp WHERE monster_id = ?', (monster_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else MONSTERS[monster_id]['hp']

def update_monster_hp(monster_id, new_hp):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('UPDATE monster_hp SET current_hp = ? WHERE monster_id = ?', (new_hp, monster_id))
    conn.commit()
    conn.close()

def reset_monster_hp(monster_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('UPDATE monster_hp SET current_hp = ? WHERE monster_id = ?', (MONSTERS[monster_id]['hp'], monster_id))
    conn.commit()
    conn.close()

def get_user_weapons(user_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT weapon_inventory FROM heroes WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    if result and result[0]:
        try:
            return json.loads(result[0])
        except:
            return {"1": 1}
    return {"1": 1}

def save_user_weapons(user_id, weapons):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('UPDATE heroes SET weapon_inventory = ? WHERE user_id = ?', (json.dumps(weapons), user_id))
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
    keyboard.add_button("⚔️ Охота", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_line()
    keyboard.add_button("💼 Работа", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🏪 Торговец", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📦 Сундук", color=VkKeyboardColor.PRIMARY)
    keyboard.add_button("🏆 Рейтинг", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🍺 Трактир", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("👥 Поход", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("❓ Помощь", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_monster_keyboard():
    keyboard = VkKeyboard(one_time=False)
    for monster_id, monster in MONSTERS.items():
        keyboard.add_button(f"{monster['name']}", color=VkKeyboardColor.SECONDARY)
        keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_fight_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("👊 Кулак", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🗡️ Кинжал", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⚔️ Длинный меч", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🏹 Арбалет", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("👑 Королевский меч", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🏪 К торговцу", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика боя", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("🏳️ Отступить", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_shop_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("🗡️ Кинжал (1000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("⚔️ Длинный меч (5000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("🏹 Арбалет (20000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("👑 Королевский меч (50000💰)", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_raid_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("⚔️ Создать поход", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("🔍 Ввести ID", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("📊 Статистика похода", color=VkKeyboardColor.SECONDARY)
    keyboard.add_line()
    keyboard.add_button("◀️ Назад", color=VkKeyboardColor.SECONDARY)
    return keyboard

def create_admin_keyboard():
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button("💰 Выдать золото", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("👑 Выдать честь", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("⭐ Выдать оружие", color=VkKeyboardColor.POSITIVE)
    keyboard.add_button("📈 Повысить уровень", color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button("⚔️ Сбросить монстров", color=VkKeyboardColor.NEGATIVE)
    keyboard.add_button("📊 Умная статистика", color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button("👥 Список героев", color=VkKeyboardColor.PRIMARY)
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
        "⚔️ ДОБРО ПОЖАЛОВАТЬ В КОРОЛЕВСТВО! ⚔️\n\n"
        "📜 Личное дело - твоё досье\n"
        "⚔️ Охота - битва с монстрами\n"
        "💼 Работа - зарабатывай золото\n"
        "🏪 Торговец - купи оружие\n"
        "📦 Сундук - твоё снаряжение\n"
        "🏆 Рейтинг - топ воинов\n"
        "🍺 Трактир - халявное золото (раз в 6ч)\n"
        "👥 Поход - рейды с братвой\n\n"
        "👉 ЖМИ ПО КНОПКАМ, ВОИН! 👈",
        create_main_keyboard())

def handle_profile(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    rank_name = get_rank_name(stats['honor'])
    try:
        kills = json.loads(stats['monster_kills']) if stats['monster_kills'] else []
    except:
        kills = []
    message = f"""📜 ЛИЧНОЕ ДЕЛО

👤 {stats['name']}
⭐ {rank_name}
📊 Уровень {stats['level']} (XP: {stats['xp']}/{stats['level']*100})

💰 Золота: {stats['gold']}
👑 Честь: {stats['honor']}

⚔️ Монстров побеждено: {len(kills)}/{len(MONSTERS)}

📅 В королевстве с: {stats['join_date'][:10] if stats['join_date'] else 'сегодня'}"""
    send_message(user_id, message, create_main_keyboard())

def handle_inventory(user_id):
    weapons_inv = get_user_weapons(user_id)
    message = "📦 СУНДУК\n\n"
    for weapon_id, weapon in WEAPONS.items():
        count = weapons_inv.get(str(weapon_id), 0)
        if count > 0 or weapon_id == 1:
            message += f"{weapon['emoji']} {weapon['name']}: {count} шт.\n"
            message += f"   ⚔️ Урон +{weapon['damage']}\n"
            message += f"   💥 Шанс крита: {weapon['crit_chance']}%\n"
    if all(weapons_inv.get(str(wid), 0) == 0 for wid in range(2, 6)):
        message += "\n🔸 Оружия нет\n🔸 Зайди к Торговцу"
    send_message(user_id, message, create_main_keyboard())

def handle_monster_list(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            send_message(user_id, f"❌ Ты уже в походе {raid_code}!\nСначала заверши его.", create_main_keyboard())
            return
    message = "⚔️ НА КОГО ОХОТИМСЯ?\n\n"
    for monster_id, monster in MONSTERS.items():
        current_hp = get_monster_hp(monster_id)
        req = "✅" if stats['level'] >= monster['min_level'] else f"🔒 УР.{monster['min_level']}"
        filled = int((current_hp / monster['hp']) * 10)
        bar = "█" * filled + "░" * (10 - filled)
        kills_today = get_monster_kills_today(user_id, monster_id)
        message += f"{monster['name']} {req}\n"
        message += f"❤️ [{bar}] {current_hp}/{monster['hp']}\n"
        message += f"💰 {monster['reward_gold'][0]}-{monster['reward_gold'][1]} | 👑 +{monster['reward_honor'][0]}-{monster['reward_honor'][1]}\n"
        message += f"📅 Сегодня: {kills_today}/{BOSS_DAILY_LIMIT}\n\n"
    send_message(user_id, message, create_monster_keyboard())

def handle_monster_selection(user_id, monster_name):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            send_message(user_id, f"❌ Ты уже в походе {raid_code}!\nСначала заверши его.", create_main_keyboard())
            return
    monster_data = None
    monster_id = None
    for mid, mdata in MONSTERS.items():
        if mdata['name'] in monster_name:
            monster_id = mid
            monster_data = mdata
            break
    if not monster_data:
        send_message(user_id, "❌ Такого монстра нет!", create_main_keyboard())
        return
    if stats['level'] < monster_data['min_level']:
        send_message(user_id, f"❌ Нужен {monster_data['min_level']} уровень!", create_main_keyboard())
        return
    user_states[user_id] = {'state': 'fighting', 'monster_id': monster_id, 'monster_name': monster_data['name']}
    current_hp = get_monster_hp(monster_id)
    kills_today = get_monster_kills_today(user_id, monster_id)
    remaining = BOSS_DAILY_LIMIT - kills_today
    message = f"⚔️ БИТВА С {monster_data['name']} ⚔️\n\n"
    message += f"❤️ ХП: {current_hp}/{monster_data['hp']}\n"
    message += f"📅 Сегодня можно победить: {remaining}/{BOSS_DAILY_LIMIT}\n\n"
    message += "Чем атакуем?"
    send_message(user_id, message, create_fight_keyboard())

def handle_fight(user_id, weapon_name):
    state = user_states.get(user_id, {})
    if state.get('state') != 'fighting':
        return False
    if "Отступить" in weapon_name:
        del user_states[user_id]
        send_message(user_id, "🏳️ Ты отступил с поля боя!", create_main_keyboard())
        return True
    if "Назад" in weapon_name:
        del user_states[user_id]
        handle_monster_list(user_id)
        return True
    if "Статистика боя" in weapon_name:
        monster_id = state['monster_id']
        monster_name = state['monster_name']
        current_hp = get_monster_hp(monster_id)
        monster_data = MONSTERS[monster_id]
        message = f"📊 СТАТИСТИКА БОЯ\n\n"
        message += f"🐉 Противник: {monster_name}\n"
        message += f"❤️ ХП: {current_hp}/{monster_data['hp']}\n"
        message += f"📊 Прогресс: {((monster_data['hp'] - current_hp) / monster_data['hp'] * 100):.1f}%\n"
        send_message(user_id, message, create_fight_keyboard())
        return True
    monster_id = state['monster_id']
    monster_name = state['monster_name']
    monster_data = MONSTERS[monster_id]
    weapon_data = None
    weapon_id = None
    for wid, wdata in WEAPONS.items():
        if wdata['name'] in weapon_name:
            weapon_id = wid
            weapon_data = wdata
            break
    if not weapon_data:
        if "Кулак" in weapon_name:
            weapon_id = 1
            weapon_data = WEAPONS[1]
        elif "Кинжал" in weapon_name:
            weapon_id = 2
            weapon_data = WEAPONS[2]
        elif "Длинный меч" in weapon_name:
            weapon_id = 3
            weapon_data = WEAPONS[3]
        elif "Арбалет" in weapon_name:
            weapon_id = 4
            weapon_data = WEAPONS[4]
        elif "Королевский меч" in weapon_name:
            weapon_id = 5
            weapon_data = WEAPONS[5]
        else:
            send_message(user_id, "❌ Выбери оружие!", create_fight_keyboard())
            return True
    stats = get_hero_stats(user_id)
    current_hp = get_monster_hp(monster_id)
    if current_hp <= 0:
        send_message(user_id, "❌ Монстр уже повержен!", create_main_keyboard())
        del user_states[user_id]
        return True
    will_kill = (current_hp - (weapon_data['damage'] + stats['level'] * 2)) <= 0
    if will_kill:
        kills_today = get_monster_kills_today(user_id, monster_id)
        if kills_today >= BOSS_DAILY_LIMIT:
            send_message(user_id, f"⚠️ Ты уже победил {BOSS_DAILY_LIMIT} раз {monster_name} сегодня!\nЛимит на день исчерпан. Возвращайся завтра!", create_main_keyboard())
            del user_states[user_id]
            return True
    if weapon_data['price'] == 0:
        if user_id in last_free_weapon_use:
            last = last_free_weapon_use[user_id]
            if datetime.now() - last < timedelta(seconds=FREE_WEAPON_COOLDOWN):
                remaining = FREE_WEAPON_COOLDOWN - (datetime.now() - last).seconds
                send_message(user_id, f"⏱️ Кулак через {remaining} сек", create_fight_keyboard())
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
        update_monster_hp(monster_id, 0)
        gold_reward = random.randint(monster_data['reward_gold'][0], monster_data['reward_gold'][1])
        honor_reward = random.randint(monster_data['reward_honor'][0], monster_data['reward_honor'][1])
        xp_reward = random.randint(monster_data['reward_xp'][0], monster_data['reward_xp'][1])
        add_gold(user_id, gold_reward)
        add_honor(user_id, honor_reward)
        add_xp(user_id, xp_reward)
        add_monster_kill_today(user_id, monster_id)
        kills_today = get_monster_kills_today(user_id, monster_id)
        try:
            kills = json.loads(stats['monster_kills']) if stats['monster_kills'] else []
        except:
            kills = []
        if monster_id not in kills:
            kills.append(monster_id)
            conn = sqlite3.connect('kingdom.db')
            c = conn.cursor()
            c.execute('UPDATE heroes SET monster_kills = ? WHERE user_id = ?', (json.dumps(kills), user_id))
            conn.commit()
            conn.close()
        reset_monster_hp(monster_id)
        del user_states[user_id]
        crit_text = " 💥КРИТ💥" if crit else ""
        message = f"⚔️ ПОБЕДА НАД {monster_name}! ⚔️\n\n"
        message += f"💥 Урон: {damage}{crit_text}\n"
        message += f"💰 +{gold_reward} золота\n"
        message += f"👑 +{honor_reward} чести\n"
        message += f"📊 +{xp_reward} XP\n"
        message += f"🏆 Всего побед: {len(kills)}/{len(MONSTERS)}\n"
        message += f"📅 Сегодня побеждено {monster_name}: {kills_today}/{BOSS_DAILY_LIMIT}"
        send_message(user_id, message, create_main_keyboard())
    else:
        update_monster_hp(monster_id, new_hp)
        crit_text = " 💥КРИТ💥" if crit else ""
        kills_today = get_monster_kills_today(user_id, monster_id)
        remaining = BOSS_DAILY_LIMIT - kills_today
        message = f"⚔️ АТАКУЕМ!\n\n"
        message += f"🔫 {weapon_data['emoji']} {weapon_data['name']}\n"
        message += f"💥 Урон: {damage}{crit_text}\n"
        message += f"❤️ ХП: {current_hp} → {new_hp}\n"
        message += f"📅 Сегодня можно победить {monster_name}: {remaining}/{BOSS_DAILY_LIMIT}"
        send_message(user_id, message, create_fight_keyboard())
    return True

def handle_work(user_id):
    stats = get_hero_stats(user_id)
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
    add_gold(user_id, earnings)
    last_work_time[user_id] = datetime.now()
    send_message(user_id, f"💼 {best_job['name']}\n💰 +{earnings} золота!", create_main_keyboard())

def handle_shop(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = f"🏪 ТОРГОВЕЦ\n💰 Золота: {stats['gold']}\n\n"
    for weapon_id, weapon in WEAPONS.items():
        if weapon['price'] > 0:
            message += f"{weapon['emoji']} {weapon['name']}\n"
            message += f"   💰 {weapon['price']} | ⚔️ +{weapon['damage']} | УР.{weapon['min_level']}\n"
            message += f"   💥 Шанс крита: {weapon['crit_chance']}%\n\n"
    message += "👉 Напиши номер оружия:\n2 - Кинжал, 3 - Длинный меч, 4 - Арбалет, 5 - Королевский меч"
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
    stats = get_hero_stats(user_id)
    if stats['level'] < weapon_data['min_level']:
        send_message(user_id, f"❌ Нужен {weapon_data['min_level']} уровень!", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return
    if stats['gold'] < weapon_data['price']:
        send_message(user_id, f"❌ Не хватает! Нужно {weapon_data['price']}💰", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return
    add_weapon_to_inventory(user_id, weapon_id)
    add_gold(user_id, -weapon_data['price'])
    weapons_inv = get_user_weapons(user_id)
    current_count = weapons_inv.get(str(weapon_id), 0)
    send_message(user_id, f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет\n📦 Теперь у тебя: {current_count} шт.", create_main_keyboard())
    if user_id in user_states:
        del user_states[user_id]

def handle_ranking(user_id):
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    message = "🏆 РЕЙТИНГ ВОИНОВ 🏆\n\n"
    c.execute('SELECT user_id, name, level, honor FROM heroes WHERE is_admin_hidden = 0 ORDER BY honor DESC, level DESC LIMIT 15')
    top = c.fetchall()
    for i, (uid, name, level, honor) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        mention = get_user_mention(uid)
        message += f"{medal} {i}. {mention}\n   УР.{level} | 👑{honor}\n\n"
    if not top:
        message += "🔸 Пока никого нет\n🔸 Будь первым!"
    conn.close()
    send_message(user_id, message, create_main_keyboard())

def handle_daily_bonus(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT daily_bonus FROM heroes WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    if result and result[0]:
        try:
            last = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last < timedelta(seconds=DAILY_BONUS_COOLDOWN):
                remaining = DAILY_BONUS_COOLDOWN - (datetime.now() - last).seconds
                hours = remaining // 3600
                minutes = (remaining % 3600) // 60
                send_message(user_id, f"🍺 Трактир через {hours}ч {minutes}мин", create_main_keyboard())
                conn.close()
                return
        except:
            pass
    bonus = 500 + stats['level'] * 50
    add_gold(user_id, bonus)
    c.execute('UPDATE heroes SET daily_bonus = ? WHERE user_id = ?', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()
    send_message(user_id, f"🍺 ТРАКТИР!\n💰 +{bonus} золота!", create_main_keyboard())

# ========== ФУНКЦИИ РЕЙДОВ (ПОХОДОВ) ==========
def handle_raid(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    for raid_code, raid in active_raids.items():
        if user_id in raid.get('players', {}):
            elapsed = datetime.now() - raid['start_time']
            remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
            remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
            message = f"⚔️ ТЫ УЖЕ В ПОХОДЕ {raid_code}! ⚔️\n\n"
            message += f"🐉 Цель: {raid['monster_name']}\n"
            message += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n\n"
            message += "👉 Атакуй!"
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
            message = f"⚔️ У ТЕБЯ ЕСТЬ НЕЗАВЕРШЁННЫЙ ПОХОД! ⚔️\n\n"
            message += f"🐉 Цель: {raid['monster_name']}\n"
            message += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n\n"
            message += "👉 Нажми 'Ввести ID' и введи: " + raid_id
            send_message(user_id, message, create_raid_keyboard())
            user_states[user_id] = {'state': 'raid_menu'}
            return
    message = "👥 ПОХОД 👥\n\n"
    message += "⚔️ Создать поход - выбрать монстра\n"
    message += "🔍 Ввести ID - подключиться или вернуться\n"
    message += "📊 Статистика похода - посмотреть активные походы\n\n"
    message += "👉 Выбери действие"
    send_message(user_id, message, create_raid_keyboard())
    user_states[user_id] = {'state': 'raid_menu'}

def handle_raid_create(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = "⚔️ ВЫБЕРИ ЦЕЛЬ ДЛЯ ПОХОДА ⚔️\n\n"
    for monster_id, monster in MONSTERS.items():
        if stats['level'] >= monster['min_level']:
            message += f"{monster_id}. {monster['name']}\n"
    message += "\n👉 Напиши номер"
    send_message(user_id, message)
    user_states[user_id] = {'state': 'raid_creating'}

def handle_raid_create_monster(user_id, text):
    try:
        monster_id = int(text)
        if monster_id not in MONSTERS:
            send_message(user_id, "❌ Неверно!", create_main_keyboard())
            del user_states[user_id]
            return
    except:
        send_message(user_id, "❌ Напиши номер!", create_main_keyboard())
        del user_states[user_id]
        return
    stats = get_hero_stats(user_id)
    if stats['level'] < MONSTERS[monster_id]['min_level']:
        send_message(user_id, f"❌ Нужен {MONSTERS[monster_id]['min_level']} уровень!", create_main_keyboard())
        del user_states[user_id]
        return
    raid_id = str(random.randint(100000, 999999))
    active_raids[raid_id] = {
        'monster_id': monster_id,
        'monster_name': MONSTERS[monster_id]['name'],
        'monster_max_hp': MONSTERS[monster_id]['hp'],
        'monster_current_hp': MONSTERS[monster_id]['hp'],
        'creator': user_id,
        'players': {user_id: 0},
        'start_time': datetime.now(),
        'time_limit_hours': RAID_TIME_LIMITS.get(monster_id, 3)
    }
    time_limit = RAID_TIME_LIMITS.get(monster_id, 3)
    message = f"⚔️ ПОХОД СОЗДАН! ⚔️\n\n"
    message += f"🐉 Цель: {MONSTERS[monster_id]['name']}\n"
    message += f"🔢 ID: {raid_id}\n\n"
    message += f"📝 Братва подключается: !поход {raid_id}\n\n"
    message += f"👥 Участников: 1\n"
    message += f"❤️ ХП: {MONSTERS[monster_id]['hp']}\n"
    message += f"⏰ Время на поход: {time_limit} часов\n\n"
    message += "💡 Если выйдешь из боя - вернуться можно по кнопке 'Ввести ID'"
    user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
    send_message(user_id, message, create_fight_keyboard())

def handle_raid_join(user_id, raid_id):
    raid_id = str(raid_id).strip()
    print(f"🔗 ПОДКЛЮЧЕНИЕ К ПОХОДУ: user={user_id}, raid_id={raid_id}")
    
    if raid_id not in active_raids:
        send_message(user_id, "❌ Поход не найден!\nПроверь ID.", create_main_keyboard())
        return
    
    raid = active_raids[raid_id]
    
    elapsed = datetime.now() - raid['start_time']
    if elapsed > timedelta(hours=raid['time_limit_hours']):
        send_message(user_id, "❌ Время похода истекло!", create_main_keyboard())
        del active_raids[raid_id]
        return
    
    stats = get_hero_stats(user_id)
    monster_data = MONSTERS[raid['monster_id']]
    
    if stats['level'] < monster_data['min_level']:
        send_message(user_id, f"❌ Нужен {monster_data['min_level']} уровень!", create_main_keyboard())
        return
    
    if len(raid['players']) >= MAX_RAID_PLAYERS:
        send_message(user_id, f"❌ Поход переполнен!", create_main_keyboard())
        return
    
    for rcode, r in active_raids.items():
        if user_id in r.get('players', {}):
            send_message(user_id, f"❌ Ты уже в походе {rcode}!", create_main_keyboard())
            return
    
    remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
    remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
    
    if user_id in raid['players']:
        message = f"⚔️ ВОЗВРАЩЕНИЕ В ПОХОД! ⚔️\n\n"
        message += f"🐉 Цель: {raid['monster_name']}\n"
        message += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
        message += f"👥 Участников: {len(raid['players'])}\n"
        message += f"⏰ Осталось: {remaining_text}\n\n"
        message += "👉 Атакуй!"
        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
        if user_id in user_raid_temp:
            del user_raid_temp[user_id]
        send_message(user_id, message, create_fight_keyboard())
        return
    
    raid['players'][user_id] = 0
    
    user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_id}
    
    message = f"⚔️ ТЫ В ПОХОДЕ! ⚔️\n\n"
    message += f"🐉 Цель: {raid['monster_name']}\n"
    message += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
    message += f"👥 Участников: {len(raid['players'])}\n"
    message += f"⏰ Осталось: {remaining_text}\n\n"
    message += "👉 ВЫБЕРИ ОРУЖИЕ ДЛЯ АТАКИ!\n"
    message += "👊 Кулак - бесплатно\n"
    message += "🗡️ Кинжал, ⚔️ Длинный меч, 🏹 Арбалет, 👑 Королевский меч - купить у Торговца\n\n"
    message += "💡 Если удары не проходят - напиши !проверить"
    send_message(user_id, message, create_fight_keyboard())

def handle_raid_stats(user_id):
    if not active_raids:
        send_message(user_id, "❌ Нет активных походов!", create_main_keyboard())
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
        message = f"📊 ТВОЙ ПОХОД 📊\n\n"
        message += f"🐉 Цель: {user_raid['monster_name']}\n"
        message += f"❤️ ХП: {user_raid['monster_current_hp']}/{user_raid['monster_max_hp']}\n"
        message += f"📊 Прогресс: {((user_raid['monster_max_hp'] - user_raid['monster_current_hp']) / user_raid['monster_max_hp'] * 100):.1f}%\n"
        message += f"👥 Участников: {len(user_raid['players'])}\n"
        message += f"⏰ Осталось: {remaining_text}\n\n"
        message += f"👥 ОТРЯД (по урону):\n"
        medals = ["🥇", "🥈", "🥉"]
        for i, (uid, dmg) in enumerate(sorted_players):
            medal = medals[i] if i < 3 else "📌"
            mention = get_user_mention(uid)
            message += f"{medal} {mention}: {dmg} урона\n"
        send_message(user_id, message, create_main_keyboard())
    else:
        message = "📊 АКТИВНЫЕ ПОХОДЫ 📊\n\n"
        for raid_id, raid in active_raids.items():
            elapsed = datetime.now() - raid['start_time']
            remaining_hours = raid['time_limit_hours'] - elapsed.total_seconds() / 3600
            remaining_text = f"{int(remaining_hours)}ч {int((remaining_hours % 1) * 60)}мин" if remaining_hours > 0 else "Время истекло"
            message += f"🔢 ID: {raid_id}\n"
            message += f"🐉 Монстр: {raid['monster_name']}\n"
            message += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
            message += f"👥 Участников: {len(raid['players'])}\n"
            message += f"⏰ Осталось: {remaining_text}\n"
            message += f"👑 Создатель: {get_user_name(raid['creator'])}\n\n"
        send_message(user_id, message, create_main_keyboard())

def handle_raid_attack(user_id, weapon_text):
    if user_id not in user_states:
        for rcode, raid in active_raids.items():
            if user_id in raid.get('players', {}):
                user_states[user_id] = {'state': 'raid_attacking', 'raid_code': rcode}
                break
    
    if user_id not in user_states:
        send_message(user_id, "❌ Ты не в бою! Напиши !поход с ID", create_main_keyboard())
        return False
    
    state = user_states[user_id]
    raid_code = state.get('raid_code')
    
    if not raid_code:
        for rcode, raid in active_raids.items():
            if user_id in raid.get('players', {}):
                raid_code = rcode
                state['raid_code'] = raid_code
                break
    
    if not raid_code or raid_code not in active_raids:
        send_message(user_id, "❌ Поход не найден! Подключись заново: !поход [ID]", create_main_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return False
    
    raid = active_raids[raid_code]
    
    total_damage_dealt = sum(raid['players'].values())
    if total_damage_dealt == 0 and user_id != raid['creator']:
        send_message(user_id, f"⚠️ Первый удар по {raid['monster_name']} должен нанести создатель похода!\n👑 Создатель: {get_user_name(raid['creator'])}\n\nДождись, пока он начнёт битву, потом подключайся!", create_fight_keyboard())
        return True
    
    if user_id not in raid['players']:
        raid['players'][user_id] = 0
    
    if "К торговцу" in weapon_text:
        user_states[user_id] = {'state': 'buying_in_raid', 'raid_code': raid_code}
        handle_shop_in_raid(user_id)
        return True
    
    if "Отступить" in weapon_text:
        user_raid_temp[user_id] = raid_code
        send_message(user_id, f"🏳️ Ты покинул поход!\nВернуться: !поход {raid_code}", create_main_keyboard())
        del user_states[user_id]
        return True
    
    if "Статистика" in weapon_text:
        sorted_players = sorted(raid['players'].items(), key=lambda x: x[1], reverse=True)
        msg = f"📊 СТАТИСТИКА БОЯ\n\n"
        msg += f"🐉 {raid['monster_name']}\n"
        msg += f"❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
        msg += f"📊 Прогресс: {((raid['monster_max_hp'] - raid['monster_current_hp']) / raid['monster_max_hp'] * 100):.1f}%\n\n"
        msg += f"👥 УЧАСТНИКИ ({len(raid['players'])}):\n"
        for i, (uid, dmg) in enumerate(sorted_players[:5]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📌"
            msg += f"{medal} {get_user_name(uid)}: {dmg} урона\n"
        send_message(user_id, msg, create_fight_keyboard())
        return True
    
    weapon_id = None
    if "Кулак" in weapon_text:
        weapon_id = 1
    elif "Кинжал" in weapon_text:
        weapon_id = 2
    elif "Длинный меч" in weapon_text:
        weapon_id = 3
    elif "Арбалет" in weapon_text:
        weapon_id = 4
    elif "Королевский меч" in weapon_text:
        weapon_id = 5
    else:
        send_message(user_id, "❌ Выбери оружие: 👊 Кулак, 🗡️ Кинжал, ⚔️ Длинный меч, 🏹 Арбалет, 👑 Королевский меч", create_fight_keyboard())
        return True
    
    weapon_data = WEAPONS[weapon_id]
    stats = get_hero_stats(user_id)
    
    if not stats:
        send_message(user_id, "❌ Ошибка загрузки профиля!", create_main_keyboard())
        return True
    
    if raid['monster_current_hp'] <= 0:
        send_message(user_id, "❌ Монстр УЖЕ ПОВЕРЖЕН!", create_main_keyboard())
        del active_raids[raid_code]
        del user_states[user_id]
        return True
    
    if weapon_data['price'] > 0:
        weapons_inv = get_user_weapons(user_id)
        available = weapons_inv.get(str(weapon_id), 0)
        if available <= 0:
            send_message(user_id, f"❌ Нет {weapon_data['name']}! Купи у Торговца\n\nНажми '🏪 К торговцу'", create_fight_keyboard())
            return True
        remove_weapon_from_inventory(user_id, weapon_id)
    else:
        if user_id in last_free_weapon_use:
            last = last_free_weapon_use[user_id]
            if datetime.now() - last < timedelta(seconds=FREE_WEAPON_COOLDOWN):
                remaining = FREE_WEAPON_COOLDOWN - (datetime.now() - last).seconds
                send_message(user_id, f"⏱️ Кулак через {remaining} сек", create_fight_keyboard())
                return True
        last_free_weapon_use[user_id] = datetime.now()
    
    damage = weapon_data['damage'] + stats['level'] * 2
    crit = random.randint(1, 100) <= weapon_data['crit_chance']
    if crit:
        damage = damage * 2
    
    old_hp = raid['monster_current_hp']
    raid['monster_current_hp'] -= damage
    raid['players'][user_id] = raid['players'].get(user_id, 0) + damage
    
    crit_text = " 💥КРИТ💥" if crit else ""
    
    if raid['monster_current_hp'] <= 0:
        raid['monster_current_hp'] = 0
        
        monster_data = MONSTERS[raid['monster_id']]
        base_gold = random.randint(monster_data['reward_gold'][0], monster_data['reward_gold'][1])
        base_honor = random.randint(monster_data['reward_honor'][0], monster_data['reward_honor'][1])
        base_xp = random.randint(monster_data['reward_xp'][0], monster_data['reward_xp'][1])
        
        sorted_players = sorted(raid['players'].items(), key=lambda x: x[1], reverse=True)
        
        for i, (uid, dmg) in enumerate(sorted_players):
            bonus_gold = base_gold // 2 if i == 0 else base_gold // 3 if i == 1 else base_gold // 4 if i == 2 else 0
            bonus_honor = base_honor // 2 if i == 0 else base_honor // 3 if i == 1 else base_honor // 4 if i == 2 else 0
            if uid == raid['creator']:
                bonus_gold += base_gold // 3
                bonus_honor += base_honor // 3
            
            add_gold(uid, base_gold + bonus_gold)
            add_honor(uid, base_honor + bonus_honor)
            add_xp(uid, base_xp)
            add_monster_kill_today(uid, raid['monster_id'])
            kills_today = get_monster_kills_today(uid, raid['monster_id'])
            
            st = get_hero_stats(uid)
            kills = json.loads(st['monster_kills']) if st['monster_kills'] else []
            if raid['monster_id'] not in kills:
                kills.append(raid['monster_id'])
                conn = sqlite3.connect('kingdom.db')
                c = conn.cursor()
                c.execute('UPDATE heroes SET monster_kills = ? WHERE user_id = ?', (json.dumps(kills), uid))
                conn.commit()
                conn.close()
            
            bonus_text = "🏆 ТОП УРОНА! " if i == 0 else ""
            send_message(uid, f"🎉 ПОБЕДА В ПОХОДЕ НАД {raid['monster_name']}!\n💰 +{base_gold + bonus_gold} золота\n👑 +{base_honor + bonus_honor} чести\n📊 +{base_xp} XP\n{bonus_text}\n📅 Сегодня побеждено {raid['monster_name']}: {kills_today}/{BOSS_DAILY_LIMIT}")
        
        reset_monster_hp(raid['monster_id'])
        send_message(user_id, f"🎉 ПОХОД ЗАВЕРШЁН ПОБЕДОЙ!\n💥 Твой урон: {damage}{crit_text}", create_main_keyboard())
        del active_raids[raid_code]
        del user_states[user_id]
        if user_id in user_raid_temp:
            del user_raid_temp[user_id]
        return True
    
    hp_left = raid['monster_current_hp']
    hp_total = raid['monster_max_hp']
    percent = ((hp_total - hp_left) / hp_total * 100)
    
    message = f"⚔️ УДАР ПО {raid['monster_name']}!\n"
    message += f"🔫 {weapon_data['emoji']} {weapon_data['name']}\n"
    message += f"💥 Урон: {damage}{crit_text}\n"
    message += f"❤️ ХП: {hp_left}/{hp_total} ({percent:.1f}%)\n"
    
    send_message(user_id, message, create_fight_keyboard())
    return True

def handle_shop_in_raid(user_id):
    stats = get_hero_stats(user_id)
    if not stats:
        handle_start(user_id)
        return
    message = f"🏪 ТОРГОВЕЦ (Прямо во время боя!)\n💰 Золота: {stats['gold']}\n\n"
    message += "2. 🗡️ Кинжал - 1000💰 (урон +15, УР.3, крит 30%)\n"
    message += "3. ⚔️ Длинный меч - 5000💰 (урон +35, УР.8, крит 35%)\n"
    message += "4. 🏹 Арбалет - 20000💰 (урон +80, УР.15, крит 40%)\n"
    message += "5. 👑 Королевский меч - 50000💰 (урон +160, УР.25, крит 50%)\n\n"
    message += "👉 Напиши номер оружия для покупки:\n"
    message += "2 - Кинжал\n"
    message += "3 - Длинный меч\n"
    message += "4 - Арбалет\n"
    message += "5 - Королевский меч\n\n"
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
    stats = get_hero_stats(user_id)
    raid_code = user_states[user_id].get('raid_code')
    if stats['level'] < weapon_data['min_level']:
        send_message(user_id, f"❌ Нужен {weapon_data['min_level']} уровень!", create_fight_keyboard())
        del user_states[user_id]
        return
    if stats['gold'] < weapon_data['price']:
        send_message(user_id, f"❌ Не хватает! Нужно {weapon_data['price']}💰\n💰 У тебя: {stats['gold']}", create_fight_keyboard())
        del user_states[user_id]
        return
    add_weapon_to_inventory(user_id, weapon_id)
    add_gold(user_id, -weapon_data['price'])
    if raid_code and raid_code in active_raids:
        raid = active_raids[raid_code]
        remaining = raid['time_limit_hours'] - (datetime.now() - raid['start_time']).total_seconds() / 3600
        remaining_text = f"{int(remaining)}ч {int((remaining % 1) * 60)}мин" if remaining > 0 else "Время истекло"
        weapons_inv = get_user_weapons(user_id)
        current_count = weapons_inv.get(str(weapon_id), 0)
        msg = f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет\n📦 Теперь в сундуке: {current_count} шт.\n\n"
        msg += f"⚔️ ВОЗВРАЩЕНИЕ В БОЙ!\n🐉 Цель: {raid['monster_name']}\n❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n⏰ Осталось: {remaining_text}\n\n👉 ПРОДОЛЖАЙ АТАКУ!"
        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_code}
        send_message(user_id, msg, create_fight_keyboard())
    else:
        send_message(user_id, f"✅ Куплено {weapon_data['emoji']} {weapon_data['name']}!\n💰 Потрачено: {weapon_data['price']} монет", create_main_keyboard())
        del user_states[user_id]

def handle_help(user_id):
    message = """⚔️ КОРОЛЕВСТВО - ПОМОЩЬ ⚔️

📜 Личное дело - твоё досье
⚔️ Охота - соло битва с монстром
💼 Работа - фармим золото
🏪 Торговец - купить оружие
📦 Сундук - твоё снаряжение
🏆 Рейтинг - топ воинов
🍺 Трактир - халявное золото (раз в 6ч)
👥 Поход - рейд с братвой

🔢 КАК СОБРАТЬ ПОХОД:
1. Нажми "👥 Поход" → "Создать поход"
2. Выбери цель → получи ID
3. Братва подключается: !поход ID
4. Если вышел - вернись по кнопке 'Ввести ID'

💡 В походе:
- Урон всех суммируется
- ТОП урона получает бонус
- Создатель получает бонус
- Кнопка 'К торговцу' - купить оружие не выходя из боя

📅 ЛИМИТЫ:
- Каждого монстра можно победить 6 раз в день
- Лимиты сбрасываются в 00:00
- Команда !лимиты показывает прогресс

👥 УЧАСТНИКОВ В ПОХОДЕ:
- Безлимит!

👉 ВСЁ УПРАВЛЕНИЕ ПО КНОПКАМ!"""
    send_message(user_id, message, create_main_keyboard())

# ========== АДМИН-ПАНЕЛЬ ==========
def handle_admin_panel(user_id):
    if not is_admin(user_id):
        send_message(user_id, "⛔ Доступ запрещён", create_main_keyboard())
        return
    send_message(user_id, "🔐 АДМИН-ПАНЕЛЬ КОРОЛЕВСТВА", create_admin_keyboard())
    user_states[user_id] = {'state': 'admin'}

def handle_admin_max(user_id):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute("PRAGMA table_info(heroes)")
    columns = [col[1] for col in c.fetchall()]
    if 'is_admin_hidden' not in columns:
        c.execute('ALTER TABLE heroes ADD COLUMN is_admin_hidden INTEGER DEFAULT 0')
    c.execute('UPDATE heroes SET gold = 1000000, honor = 5000, level = 50, xp = 0 WHERE user_id = ?', (user_id,))
    weapons_inv = {"1": 1, "2": 99, "3": 99, "4": 99, "5": 99}
    c.execute('UPDATE heroes SET weapon_inventory = ? WHERE user_id = ?', (json.dumps(weapons_inv), user_id))
    c.execute('UPDATE heroes SET is_admin_hidden = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    send_message(user_id, "✅ АДМИН ПРОКАЧАН!\n💰 Золото: 1,000,000\n👑 Честь: 5000\n📊 Уровень: 50\n📦 Всё оружие в сундуке\n⭐ Скрыт из рейтинга!", create_admin_keyboard())

def handle_admin_give_gold(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "💰 Введи ID и сумму:\nПример: 123456789 5000")
    user_states[user_id] = {'state': 'admin_give_gold'}

def handle_admin_give_honor(user_id):
    if not is_admin(user_id):
        return
    send_message(user_id, "👑 Введи ID и количество чести:\nПример: 123456789 100")
    user_states[user_id] = {'state': 'admin_give_honor'}

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
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM heroes')
    total_players = c.fetchone()[0]
    c.execute('SELECT SUM(gold) FROM heroes')
    total_gold = c.fetchone()[0] or 0
    c.execute('SELECT AVG(level) FROM heroes')
    avg_level = c.fetchone()[0] or 0
    c.execute('SELECT SUM(honor) FROM heroes')
    total_honor = c.fetchone()[0] or 0
    c.execute('SELECT name, gold FROM heroes ORDER BY gold DESC LIMIT 5')
    top_gold = c.fetchall()
    c.execute('SELECT name, level FROM heroes ORDER BY level DESC LIMIT 5')
    top_level = c.fetchall()
    c.execute('SELECT name, honor FROM heroes ORDER BY honor DESC LIMIT 5')
    top_honor = c.fetchall()
    active_raids_count = len(active_raids)
    c.execute("SELECT monster_kills FROM heroes WHERE monster_kills IS NOT NULL AND monster_kills != '[]'")
    all_kills = c.fetchall()
    total_monster_kills = 0
    for row in all_kills:
        try:
            kills = json.loads(row[0])
            total_monster_kills += len(kills)
        except:
            pass
    conn.close()
    message = f"📊 УМНАЯ СТАТИСТИКА КОРОЛЕВСТВА 📊\n\n"
    message += f"👥 Всего игроков: {total_players}\n"
    message += f"💰 Всего золота: {total_gold:,}\n"
    message += f"👑 Всего чести: {total_honor:,}\n"
    message += f"📊 Средний уровень: {avg_level:.1f}\n"
    message += f"⚔️ Побеждено монстров: {total_monster_kills}\n"
    message += f"👥 Активных походов: {active_raids_count}\n\n"
    message += f"💰 БОГАТЕЙШИЕ:\n"
    for i, (name, gold) in enumerate(top_gold, 1):
        message += f"{i}. {name}: {gold:,}💰\n"
    message += f"\n👑 ПОЧЁТНЫЕ:\n"
    for i, (name, honor) in enumerate(top_honor, 1):
        message += f"{i}. {name}: {honor}👑\n"
    message += f"\n📊 МОЩНЫЕ ПО УРОВНЮ:\n"
    for i, (name, level) in enumerate(top_level, 1):
        message += f"{i}. {name}: УР.{level}\n"
    send_message(user_id, message, create_admin_keyboard())

def handle_admin_players_list(user_id, page=0):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    c.execute('SELECT user_id, name, gold, honor, level FROM heroes ORDER BY level DESC, honor DESC')
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
    message = f"👥 СПИСОК ГЕРОЕВ (стр.{page+1}/{total_pages})\n\n"
    for uid, name, gold, honor, level in page_players:
        message += f"📌 {name}\n   💰{gold:,} | 👑{honor} | УР.{level}\n   🆔 {uid}\n\n"
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

def handle_reset_all_monsters(user_id):
    if not is_admin(user_id):
        return
    for monster_id in MONSTERS:
        reset_monster_hp(monster_id)
    send_message(user_id, "✅ ВСЕ МОНСТРЫ ВОСКРЕСЛИ!", create_admin_keyboard())

def handle_post_top(user_id):
    if not is_admin(user_id):
        return
    conn = sqlite3.connect('kingdom.db')
    c = conn.cursor()
    message = "🏆 ТОП-15 ВОИНОВ КОРОЛЕВСТВА 🏆\n\n"
    c.execute('SELECT user_id, name, level, honor FROM heroes WHERE is_admin_hidden = 0 ORDER BY honor DESC, level DESC LIMIT 15')
    top = c.fetchall()
    for i, (uid, name, level, honor) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📌"
        mention = get_user_mention(uid)
        message += f"{medal} {i}. {mention}\n   УР.{level} | 👑{honor}\n\n"
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
        conn = sqlite3.connect('kingdom.db')
        c = conn.cursor()
        c.execute('DELETE FROM heroes')
        c.execute('DELETE FROM monster_hp')
        c.execute('DELETE FROM raid_logs')
        c.execute('DELETE FROM monster_kills_daily')
        conn.commit()
        conn.close()
        for monster_id, monster in MONSTERS.items():
            reset_monster_hp(monster_id)
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
    if state == 'admin_give_gold':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                amount = int(parts[1])
                add_gold(target_id, amount)
                send_message(user_id, f"✅ Выдано {amount}💰 герою {get_user_name(target_id)}", create_admin_keyboard())
            except:
                send_message(user_id, "❌ Ошибка! Формат: ID сумма", create_admin_keyboard())
        else:
            send_message(user_id, "❌ Формат: ID сумма", create_admin_keyboard())
        if user_id in user_states:
            del user_states[user_id]
        return True
    elif state == 'admin_give_honor':
        parts = text.split()
        if len(parts) >= 2:
            try:
                target_id = int(parts[0])
                amount = int(parts[1])
                add_honor(target_id, amount)
                send_message(user_id, f"✅ Выдано {amount} чести герою {get_user_name(target_id)}", create_admin_keyboard())
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
                    send_message(user_id, f"✅ Выдано {WEAPONS[weapon_id]['emoji']} {WEAPONS[weapon_id]['name']} герою {get_user_name(target_id)}", create_admin_keyboard())
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
                    conn = sqlite3.connect('kingdom.db')
                    c = conn.cursor()
                    c.execute('UPDATE heroes SET level = level + ?, xp = 0 WHERE user_id = ?', (levels, target_id))
                    conn.commit()
                    conn.close()
                    send_message(user_id, f"✅ Герою {get_user_name(target_id)} повышен уровень на {levels}!", create_admin_keyboard())
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
print("⚔️ КОРОЛЕВСТВО - ПОХОДЫ НА МОНСТРОВ ⚔️")
print("=" * 50)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        msg = event.obj.message
        user_id = msg['from_id']
        text = msg['text'] if msg['text'] else ""
        
        if user_id < 0:
            continue
        
        print(f"🔍 ВХОДЯЩЕЕ СООБЩЕНИЕ: '{text}' от {user_id}")
        
        if text in ["👊 Кулак", "🗡️ Кинжал", "⚔️ Длинный меч", "🏹 Арбалет", "👑 Королевский меч"]:
            if user_id in user_states:
                state = user_states[user_id]
                if state.get('state') == 'raid_attacking':
                    handle_raid_attack(user_id, text)
                elif state.get('state') == 'fighting':
                    handle_fight(user_id, text)
                else:
                    send_message(user_id, "❌ Ты не в бою! Начни охоту на монстра или подключись к походу!", create_main_keyboard())
            else:
                send_message(user_id, "❌ Ты не в бою! Напиши !старт", create_main_keyboard())
            continue
        
        if text.lower().startswith('!поход'):
            parts = text.split()
            if len(parts) == 2:
                handle_raid_join(user_id, parts[1])
            else:
                send_message(user_id, "❌ Пример: !поход 123456", create_main_keyboard())
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
            stats = get_hero_stats(user_id)
            if not stats:
                handle_start(user_id)
                continue
            message = "📊 ТВОИ ЛИМИТЫ НА СЕГОДНЯ 📊\n\n"
            for monster_id, monster in MONSTERS.items():
                kills = get_monster_kills_today(user_id, monster_id)
                remaining = BOSS_DAILY_LIMIT - kills
                message += f"{monster['name']}: {kills}/{BOSS_DAILY_LIMIT} (осталось {remaining})\n"
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
                msg += f"Монстр: {raid['monster_name']}\n"
                msg += f"ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n"
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
                if text == "⚔️ Создать поход":
                    handle_raid_create(user_id)
                elif text == "🔍 Ввести ID":
                    send_message(user_id, "🔢 Введи ID похода (6 цифр):")
                    user_states[user_id] = {'state': 'raid_join_waiting'}
                elif text == "📊 Статистика похода":
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
                handle_raid_create_monster(user_id, text)
                continue
            elif state == 'buying_in_raid':
                if text == "◀️ Вернуться в бой" or text == "◀️ Назад":
                    raid_code = user_states[user_id].get('raid_code')
                    if raid_code and raid_code in active_raids:
                        raid = active_raids[raid_code]
                        remaining = raid['time_limit_hours'] - (datetime.now() - raid['start_time']).total_seconds() / 3600
                        remaining_text = f"{int(remaining)}ч {int((remaining % 1) * 60)}мин" if remaining > 0 else "Время истекло"
                        msg = f"⚔️ ВОЗВРАЩЕНИЕ В БОЙ!\n🐉 Цель: {raid['monster_name']}\n❤️ ХП: {raid['monster_current_hp']}/{raid['monster_max_hp']}\n⏰ Осталось: {remaining_text}\n\n👉 АТАКУЙ!"
                        user_states[user_id] = {'state': 'raid_attacking', 'raid_code': raid_code}
                        send_message(user_id, msg, create_fight_keyboard())
                    else:
                        send_message(user_id, "❌ Поход завершён!", create_main_keyboard())
                        del user_states[user_id]
                else:
                    handle_buy_weapon_in_raid(user_id, text)
                continue
            elif state == 'admin':
                if text == "💰 Выдать золото":
                    handle_admin_give_gold(user_id)
                elif text == "👑 Выдать честь":
                    handle_admin_give_honor(user_id)
                elif text == "⭐ Выдать оружие":
                    handle_admin_give_weapon(user_id)
                elif text == "📈 Повысить уровень":
                    handle_admin_upgrade_level(user_id)
                elif text == "⚔️ Сбросить монстров":
                    handle_reset_all_monsters(user_id)
                elif text == "📊 Умная статистика":
                    handle_admin_smart_stats(user_id)
                elif text == "👥 Список героев":
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
            elif state in ['admin_give_gold', 'admin_give_honor', 'admin_give_weapon', 'admin_upgrade_level']:
                if execute_admin_action(user_id, text):
                    continue
            elif state == 'admin_clear_confirm':
                if execute_admin_action(user_id, text):
                    continue
        
        if text == "📜 Личное дело":
            handle_profile(user_id)
        elif text == "⚔️ Охота":
            handle_monster_list(user_id)
        elif text == "💼 Работа":
            handle_work(user_id)
        elif text == "🏪 Торговец":
            handle_shop(user_id)
        elif text == "📦 Сундук":
            handle_inventory(user_id)
        elif text == "🏆 Рейтинг":
            handle_ranking(user_id)
        elif text == "🍺 Трактир":
            handle_daily_bonus(user_id)
        elif text == "👥 Поход":
            handle_raid(user_id)
        elif text == "❓ Помощь":
            handle_help(user_id)
        elif text == "◀️ Назад":
            handle_start(user_id)
        elif any(monster['name'] in text for monster in MONSTERS.values()):
            handle_monster_selection(user_id, text)
        else:
            conn = sqlite3.connect('kingdom.db')
            c = conn.cursor()
            c.execute('SELECT user_id FROM heroes WHERE user_id = ?', (user_id,))
            exists = c.fetchone()
            conn.close()
            if not exists:
                handle_start(user_id)

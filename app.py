import os
import json
import sqlite3
from PIL import Image
from telebot import TeleBot, types
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from bot_token import BOT_TOKEN
from user_utils import check_user
from TEXT import translations

load_dotenv()

bot = TeleBot(BOT_TOKEN)
bot_id = bot.get_me().id

def save_data(key, data):
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS bot_data
                          (key TEXT PRIMARY KEY, data TEXT)''')
        serialized_data = json.dumps(data)
        cursor.execute("INSERT OR REPLACE INTO bot_data (key, data) VALUES (?, ?)", (key, serialized_data))
        conn.commit()
        conn.close()
        return True
    except Exception:
        return False

def get_data(key):
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT data FROM bot_data WHERE key=?", (key,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return json.loads(result[0])
        else:
            return None
    except Exception:
        return None

def get_translation(key, lang_code='en', **kwargs):
    try:
        text = translations.get(lang_code, translations['en']).get(key, '')
        return text.format(**kwargs)
    except Exception:
        return translations['en'][key].format(**kwargs)

def init_image_table():
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS images
                          (chat_id INTEGER, file_id TEXT, file_path TEXT)''')
        conn.commit()
        conn.close()
    except Exception:
        pass

def add_image(chat_id, file_id, file_path):
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO images (chat_id, file_id, file_path) VALUES (?, ?, ?)", (chat_id, file_id, file_path))
        conn.commit()
        conn.close()
    except Exception:
        pass

def get_images(chat_id):
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path FROM images WHERE chat_id=?", (chat_id,))
        result = cursor.fetchall()
        conn.close()
        return [row[0] for row in result]
    except Exception:
        return []

def delete_images(chat_id):
    try:
        db_name = f"{bot.get_me().id}.db"
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM images WHERE chat_id=?", (chat_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass

init_image_table()

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, this is the Flask app running alongside the Telegram bot!'

@bot.message_handler(commands=['start'])
def start(message):
    try:
        lang_code = get_data(f'lang_{message.chat.id}') or 'en'
        broadcast = get_data('broadcast') or []
        if message.from_user.id not in broadcast:
            bot.send_message(5797764799, f"*🆕 New User Started The Bot*\n\n*👤 User Name : *{message.from_user.first_name}\n*🆔 User Id : {message.chat.id}\n\n💰 Total User in Bot {len(broadcast) + 1}*", parse_mode="markdown")
            broadcast.append(message.from_user.id)
            save_data('broadcast', broadcast)
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Updates Channel", url="https://t.me/Fire_Botz"),
                   types.InlineKeyboardButton("Developer", url="https://t.me/Fire_162"))
        welcome_msg = get_translation('welcome', lang_code, name=message.from_user.first_name)
        bot.reply_to(message, welcome_msg, reply_markup=markup, parse_mode="HTML")
    except Exception:
        pass

@bot.message_handler(commands=['language'])
def choose_language(message):
    try:
        markup = types.InlineKeyboardMarkup()
        languages = [
            ('English', 'en'), ('Hindi', 'hi'),
            ('Русский', 'ru'), ('Français', 'fr'),
            ('Español', 'es')
        ]
        for lang_name, lang_code in languages:
            markup.row(types.InlineKeyboardButton(lang_name, callback_data=f'lang_{lang_code}'))
        bot.reply_to(message, get_translation('choose_lang'), reply_markup=markup)
    except Exception:
        pass

@bot.callback_query_handler(func=lambda call: call.data.startswith('lang_'))
def set_language(call):
    try:
        lang_code = call.data.split('_')[1]
        save_data(f'lang_{call.message.chat.id}', lang_code)
        bot.answer_callback_query(call.id, f'{lang_code} - ✅', show_alert=True)
    except Exception:
        pass

@bot.message_handler(content_types=['photo'])
def pdf(message):
    try:
        lang_code = get_data(f'lang_{message.chat.id}') or 'en'
        chat_id = message.chat.id
        if not check_user(['@Fire_Botz'], chat_id, bot):
            bot.send_message(chat_id, get_translation('join_channel', lang_code), parse_mode="HTML")
            start(message)
            return
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_path = f"{file_id}.jpg"
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        add_image(chat_id, file_id, file_path)
        bot.reply_to(message, get_translation('added_images', lang_code, count=len(get_images(chat_id))))
    except Exception:
        pass

@bot.message_handler(commands=['done'])
def done(message):
    try:
        lang_code = get_data(f'lang_{message.chat.id}') or 'en'
        chat_id = message.chat.id
        image_paths = get_images(chat_id)
        if image_paths:
            pdf_path = f"{chat_id}.pdf"
            images = [Image.open(p).convert('RGB') for p in image_paths]
            images[0].save(pdf_path, save_all=True, append_images=images[1:])
            with open(pdf_path, "rb") as pdf_file:
                bot.send_document(chat_id, pdf_file, caption=get_translation('pdf_ready', lang_code))
            os.remove(pdf_path)
            for path in image_paths:
                os.remove(path)
            delete_images(chat_id)
        else:
            bot.reply_to(message, get_translation('no_images', lang_code))
    except Exception:
        pass

def run_flask():
    app.run(host='0.0.0.0', port=8000)

def run_telegram_bot():
    bot.infinity_polling()

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    telegram_thread = Thread(target=run_telegram_bot)

    flask_thread.start()
    telegram_thread.start()

    flask_thread.join()
    telegram_thread.join()
                            

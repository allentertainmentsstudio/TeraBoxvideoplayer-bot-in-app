from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as ikm, InlineKeyboardButton as ikb, WebAppInfo
from pyrogram.filters import create
import random
import pymongo
import pyshorteners
import os
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return {"status": "running"}

PORT = int(os.environ.get("PORT", 5000))

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ================== DB ==================
client = pymongo.MongoClient("YOUR_MONGO_URI")
db = client['terabox2']
users_collection = db['users']

# ================== URL ==================
def create_mini_app_url(user_link):
    base_url = "https://muddy-flower-20ec.arjunavai273.workers.dev/?id="
    return f"{base_url}{user_link}"

# ================== USER ==================
def store_user_info(user_id, username, first_name):
    if not users_collection.find_one({"user_id": user_id}):
        users_collection.insert_one({
            "user_id": user_id,
            "username": username,
            "first_name": first_name
        })

# ================== BOT ==================
bot = Client(
    "bot",
    api_id=int(os.environ.get("API_ID")),
    api_hash=os.environ.get("API_HASH"),
    bot_token=os.environ.get("BOT_TOKEN")
)

# ================== START ==================
@bot.on_message(filters.command("start") & filters.private)
async def start(bot, message):
    await message.reply_text("Send TeraBox link")

# ================== MAIN ==================
@bot.on_message(filters.text & filters.private)
async def process_link(bot, message):

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    store_user_info(user_id, username, first_name)

    msg = message.text.replace("@", "")
    print(f"Received message from {user_id}: {msg}")

    sticker = 'CAACAgUAAxkBAAEV_8RnkPiFEzAKWVUgzWeNcLTOWjsBkAACpwgAAtu6GFQ4oUoIL-_BgzYE'
    w1 = await message.reply_sticker(sticker)

    if msg.startswith('https://'):
        try:
            if '/s/' in msg:
                surl = msg.split('/s/')[1].split('?')[0].split('#')[0]
            elif 'surl=' in msg:
                surl = msg.split('surl=')[1].split('&')[0].split('?')[0].split('#')[0]
            elif 'id=' in msg:
                surl = msg.split('id=')[1].split('&')[0].split('?')[0].split('#')[0]
            else:
                surl = msg.split('/')[-1].split('?')[0].split('#')[0]

            streaming_url = f"https://muddy-flower-20ec.arjunavai273.workers.dev/?id={surl}"

            keyboard = ikm([
                [ikb(
                    text="Open Streaming Player",
                    web_app=WebAppInfo(url=streaming_url)
                )]
            ])

            await w1.delete()

            await message.reply_text(
                "<b>🎬Your streaming link is ready!\n\nClick the button below to open the player</b>",
                reply_markup=keyboard,
                reply_to_message_id=message.id
            )

        except Exception as e:
            await w1.delete()
            await message.reply_text(f"Error: {e}")

    else:
        await w1.delete()
        await message.reply_text("🎉Send valid link")

# ================== RUN ==================
if __name__ == "__main__":
    print("Starting Bot + Flask...")
    Thread(target=run_flask, daemon=True).start()
    bot.run()

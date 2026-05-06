from threading import Thread
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as ikm, InlineKeyboardButton as ikb, WebAppInfo
import random
import pymongo
import pyshorteners
from pyrogram.enums import ChatMemberStatus
import config
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

# Validate configuration before starting
if not config.validate_config():
    import sys
    sys.exit(1)

# Stickers for bot responses
stickers = [
    'CAACAgIAAxkBAAEVZQVnQeBXL7vxQRzEvPhwCHNdAudu6gAC0UQAAnf8YEitLhXjRxtXITYE',
    'CAACAgIAAxkBAAEVZP5nQeAr0iGTxNEzDOd1J026NV2-bgACEj4AAhqDIEnivD3_9OafqzYE',
]

# Initialize the bot
bot = Client(
    "terabox_bot",
    bot_token=config.BOT_TOKEN,
    api_id=config.API_ID,
    api_hash=config.API_HASH
)

# Configuration
admin_id = config.ADMIN_IDS

# Global variables
under_maintainance = False
broadcast_on = False

# ❌ check_joined() FUNCTION REMOVED

# Connect to MongoDB
client = pymongo.MongoClient(config.MONGODB_URI)
db = client['terabox2']
users_collection = db['users']

# URL shortening functions
def shorten_url(long_url):
    """Shorten a URL using TinyURL"""
    s = pyshorteners.Shortener()
    short_url = s.tinyurl.short(long_url)
    return short_url

def shorten_url2(long_url):
    """Backup URL shortening using is.gd"""
    s = pyshorteners.Shortener()
    short_url = s.isgd.short(long_url)
    return short_url

def url_create(user_input):
    """Create a TeraBox embedded URL from user input"""
    t1 = user_input.split('/')[-1]
    if t1[0].isdigit():
        t1 = t1[1:]
    t2 = f'https://www.1024terabox.com/sharing/embed?autoplay=true&resolution=1080&mute=false&surl={t1}' 
    return t2

# Function to create the mini app URL with the user's terabox link
def create_mini_app_url(user_link):
    """Create a URL for the Mini App with the user's TeraBox link"""
    base_url = "https://muddy-flower-20ec.arjunavai273.workers.dev/?id="
    return f"{base_url}{user_link}"

# Store user information in MongoDB
def store_user_info(user_id, username, first_name):
    """Store user information in the database if they don't exist"""
    if not users_collection.find_one({"user_id": user_id}):
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name
        }
        users_collection.insert_one(user_data)

# Start command handler
@bot.on_message(filters.command("start"))
async def start(client, message):
    """Handle the /start command"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    store_user_info(user_id, username, first_name)
    await message.reply_sticker("CAACAgQAAxkBAAEVZtZnQsjj3_Hmwg91m57GXua6E1bqfwACqgsAAsDqEFDQ3jt1DpvhoDYE")
    await message.reply_text("Hello! I am a TeraBox Link Processor Bot. Send me any TeraBox link!")

# Fetch all users from the database
async def fetch_all_users():
    """Fetch all user IDs from the database"""
    users = users_collection.find()
    return [user['user_id'] for user in users]

# Users command handler (admin only)
@bot.on_message(filters.command("users"))
async def users(client, message):
    """Show total user count (admin only)"""
    if message.from_user.id in admin_id:
        users = await fetch_all_users()
        await message.reply_text(f"<b><i>Total users: {len(users)}</i></b>")
    else:
        await message.reply_text("You are not authorized to use this command.")

# Broadcast command handler (admin only)
@bot.on_message(filters.command("broadcast"))
async def broadcast(client, message):
    """Broadcast a message to all users (admin only)"""
    global broadcast_on
    if message.from_user.id in admin_id:
        if message.reply_to_message:
            br = await message.reply_text("<b>Broadcasting...</b>")
            broadcast_on = True
            text = message.reply_to_message.text
            print(f"Broadcasting message: {text}")
            users = await fetch_all_users()
            broadcast_count = 0
            errors_count = 0
            for user_id in users:
                try:
                    await bot.send_message(user_id, text)
                    broadcast_count += 1
                except Exception as e:
                    print(f"Error broadcasting to user {user_id}: {e}")
                    errors_count += 1
            await br.edit_text(f"<b>Broadcast completed.\nSent to {broadcast_count} users. Failed to send to {errors_count} users.</b>")
            broadcast_on = False
        else:
            await message.reply_text("Reply to a message to broadcast it to all users.")
    else:
        await message.reply_text("Only Admins can use this command...")

# Stop/activate command handler (admin only)
@bot.on_message(filters.command('stop') | filters.command('activate'))
async def maintenance_toggle(client, message):
    """Toggle maintenance mode (admin only)"""
    if message.from_user.id in admin_id:
        global under_maintainance
        if message.text == '/stop':
            under_maintainance = True
            await message.reply_text('Bot Set to Maintenance Mode...')
        elif message.text == '/activate':
            under_maintainance = False
            await message.reply_text('Bot Set to Active Mode...')
    else:
        await message.reply_text('Only Admins can use this command...')

# Main message handler (NO FORCE JOIN)
@bot.on_message(filters.text)
async def process_link(bot, message):
    
    if under_maintainance:
        await message.reply_text("<b><i>Bot is under maintenance. Please try again later.</i></b>")
        return
    
    user_id = message.from_user.id
    sticker = 'CAACAgUAAxkBAAEV_8RnkPiFEzAKWVUgzWeNcLTOWjsBkAACpwgAAtu6GFQ4oUoIL-_BgzYE'
    w1 = await message.reply_sticker(sticker)
    username = message.from_user.username
    first_name = message.from_user.first_name
    store_user_info(user_id, username, first_name)
    
    msg = message.text.replace("@", "")
    print(f"Received message from {user_id}: {msg}")
    
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
                    text="🎬 Open Streaming Player",
                    web_app=WebAppInfo(url=streaming_url)
                )]
            ])
            
            await w1.delete()
            await message.reply_text(
                "<b>🎉 Your streaming link is ready!\n\nClick the button below to open the player 👇</b>",
                reply_markup=keyboard,
                reply_to_message_id=message.id
            )

        except Exception as e:
            print(f"Error processing link: {e}")
            await w1.delete()
            await message.reply_text('Error processing the link. Please make sure it\'s a valid link.')
    else:
        await w1.delete()
        await message.reply_text('Please send a valid link. Make sure it starts with https://')

# Run the bot
if __name__ == "__main__":
    print("Starting Bot + Flask...")
    Thread(target=run_flask, daemon=True).start()
    bot.run()@bot.on_message(filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    store_user_info(user_id, username, first_name)
    await message.reply_sticker("CAACAgQAAxkBAAEVZtZnQsjj3_Hmwg91m57GXua6E1bqfwACqgsAAsDqEFDQ3jt1DpvhoDYE")
    await message.reply_text("Hello! I am a TeraBox Link Processor Bot. Send me any TeraBox link!")

async def fetch_all_users():
    users = users_collection.find()
    return [user['user_id'] for user in users]

@bot.on_message(filters.command("users"))
async def users(client, message):
    if message.from_user.id in admin_id:
        users = await fetch_all_users()
        await message.reply_text(f"<b><i>Total users: {len(users)}</i></b>")
    else:
        await message.reply_text("You are not authorized to use this command.")

@bot.on_message(filters.command("broadcast"))
async def broadcast(client, message):
    global broadcast_on
    if message.from_user.id in admin_id:
        if message.reply_to_message:
            br = await message.reply_text("<b>Broadcasting...</b>")
            broadcast_on = True
            text = message.reply_to_message.text
            users = await fetch_all_users()
            broadcast_count = 0
            errors_count = 0
            for user_id in users:
                try:
                    await bot.send_message(user_id, text)
                    broadcast_count += 1
                except Exception as e:
                    errors_count += 1
            await br.edit_text(f"<b>Broadcast completed.\nSent to {broadcast_count} users. Failed to send to {errors_count} users.</b>")
            broadcast_on = False
        else:
            await message.reply_text("Reply to a message to broadcast it to all users.")
    else:
        await message.reply_text("Only Admins can use this command...")

@bot.on_message(filters.command('stop') | filters.command('activate'))
async def maintenance_toggle(client, message):
    if message.from_user.id in admin_id:
        global under_maintainance
        if message.text == '/stop':
            under_maintainance = True
            await message.reply_text('Bot Set to Maintenance Mode...')
        elif message.text == '/activate':
            under_maintainance = False
            await message.reply_text('Bot Set to Active Mode...')
    else:
        await message.reply_text('Only Admins can use this command...')

# ✅ MAIN HANDLER (NO FORCE JOIN)
@bot.on_message(filters.text)
async def process_link(bot, message):

    if under_maintainance:
        await message.reply_text("<b><i>Bot is under maintenance. Please try again later.</i></b>")
        return
    
    user_id = message.from_user.id
    sticker = 'CAACAgUAAxkBAAEV_8RnkPiFEzAKWVUgzWeNcLTOWjsBkAACpwgAAtu6GFQ4oUoIL-_BgzYE'
    w1 = await message.reply_sticker(sticker)
    username = message.from_user.username
    first_name = message.from_user.first_name
    store_user_info(user_id, username, first_name)
    
    msg = message.text.replace("@", "")
    print(f"Received message from {user_id}: {msg}")
    
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
                    text="🎬 Open Streaming Player",
                    web_app=WebAppInfo(url=streaming_url)
                )]
            ])
            
            await w1.delete()
            await message.reply_text(
                "<b>🎉 Your streaming link is ready!\n\nClick the button below to open the player 👇</b>",
                reply_markup=keyboard,
                reply_to_message_id=message.id
            )

        except Exception as e:
            print(f"Error processing link: {e}")
            await w1.delete()
            await message.reply_text('Error processing the link. Please make sure it\'s a valid link.')
    else:
        await w1.delete()
        await message.reply_text('Please send a valid link. Make sure it starts with https://')

# Run the bot
if __name__ == "__main__":
    print("Starting Bot + Flask...")
    Thread(target=run_flask, daemon=True).start()
    bot.run()

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup as ikm, InlineKeyboardButton as ikb, WebAppInfo
import random
import pymongo
import pyshorteners
from pyrogram.enums import ChatMemberStatus
import config

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
channel_username = config.CHANNEL_USERNAME

# Global variables
under_maintainance = False
broadcast_on = False

# Check if user has joined the required channel
def check_joined():
    async def func(flt, bot, message):
        join_msg = f"**To use this bot, Please join our channel.\nJoin From The Link Below 👇**"
        user_id = message.from_user.id
        chat_id = message.chat.id
        try:
            member_info = await bot.get_chat_member(channel_username, user_id)
            if member_info.status in (ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER):
                return True
            else:
                await bot.send_message(chat_id, join_msg, reply_markup=ikm([[ikb("✅ Join Channel", url=f"https://t.me/{channel_username.replace('@', '')}")]])) 
                return False
        except Exception:
            await bot.send_message(chat_id, join_msg, reply_markup=ikm([[ikb("✅ Join Channel", url=f"https://t.me/{channel_username.replace('@', '')}")]])) 
            return False

    return filters.create(func)

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
    # Base URL for the mini app
    base_url = "https://muddy-flower-20ec.arjunavai273.workers.dev/?id="
    # Combine with user's link
    return f"{base_url}{user_link}"

# Store user information in MongoDB
def store_user_info(user_id, username, first_name):
    """Store user information in the database if they don't exist"""
    # Check if the user already exists
    if not users_collection.find_one({"user_id": user_id}):
        user_data = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name
        }
        # Insert user data into MongoDB
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

# Main message handler
@bot.on_message(filters.text & filters.private & check_joined())
async def process_link(bot, message):
    
    """Process user messages containing links"""
    # Check if bot is in maintenance mode
    if under_maintainance:
        await message.reply_text("<b><i>Bot is under maintenance. Please try again later.</i></b>")
        return
    
    # Get user information
    user_id = message.from_user.id
    sticker = 'CAACAgUAAxkBAAEV_8RnkPiFEzAKWVUgzWeNcLTOWjsBkAACpwgAAtu6GFQ4oUoIL-_BgzYE'
    w1 = await message.reply_sticker(sticker)
    username = message.from_user.username
    first_name = message.from_user.first_name
    store_user_info(user_id, username, first_name)
    
    # Get the message text and remove @ if present
    msg = message.text.replace("@", "")
    print(f"Received message from {user_id}: {msg}")
    
    # Process the link if it's a URL
    if msg.startswith('https://'):
        try:
            # Extract ID from URL - try different patterns
            if '/s/' in msg:
                # For URLs with /s/ pattern
                surl = msg.split('/s/')[1].split('?')[0].split('#')[0]
            elif 'surl=' in msg:
                # For URLs with surl parameter
                surl = msg.split('surl=')[1].split('&')[0].split('?')[0].split('#')[0]
            elif 'id=' in msg:
                # For URLs with id parameter
                surl = msg.split('id=')[1].split('&')[0].split('?')[0].split('#')[0]
            else:
                # Get the last part of the URL
                surl = msg.split('/')[-1].split('?')[0].split('#')[0]
            
            # Create the streaming URL
            streaming_url = f"https://muddy-flower-20ec.arjunavai273.workers.dev/?id={surl}"
            
            print(f"Processing URL: {msg}")
            print(f"Extracted ID: {surl}")
            print(f"Streaming URL: {streaming_url}")
            
            # Create Mini App button
            keyboard = ikm([
                [ikb(
                    text="🎬 Open Streaming Player",
                    web_app=WebAppInfo(url=streaming_url)
                )]
            ])
            
            await w1.delete()
            await message.reply_text(
                "<b>🎉 Your streaming link is ready!\n\n"
                "Click the button below to open the player 👇</b>",
                reply_markup=keyboard,
                reply_to_message_id=message.id
            )
            
            # Log to admin channel
            try:
                await bot.send_message(-1002699356033, f"User {user_id} accessed: {surl}")
            except Exception:
                pass
        except Exception as e:
            print(f"Error processing link: {e}")
            await w1.delete()
            await message.reply_text('Error processing the link. Please make sure it\'s a valid link.')
    else:
        await w1.delete()
        await message.reply_text('Please send a valid link. Make sure it starts with https://')

# Run the bot
if __name__ == "__main__":
    print("Starting TeraBox Link Processor Bot...")
    bot.run()


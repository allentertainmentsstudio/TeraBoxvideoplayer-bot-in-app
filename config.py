

# Load environment variables from .env file

# Bot configuration
BOT_TOKEN = "8735534617:AAFNBedzWsDRcsiw6GXBq7QAHbqJSJiDw0w"
API_ID = 34446649
API_HASH = "8dc570c08d8e35e88fb9bfc73c65d7fa"

# MongoDB configuration
MONGODB_URI = "mongodb+srv://Anujedit:Anujedit@cluster0.7cs2nhd.mongodb.net/?appName=Cluster0"

# Admin configuration
ADMIN_IDS = [7892805795]
CHANNEL_USERNAME = "@log_ak_bot"

# Validate required configuration
def validate_config():
    """Validate that all required configuration variables are set."""
    missing = []
    
    if not BOT_TOKEN:
        missing.append("BOT_TOKEN")
    if not API_ID:
        missing.append("API_ID")
    if not API_HASH:
        missing.append("API_HASH")
    if not MONGODB_URI:
        missing.append("MONGODB_URI")
    if not ADMIN_IDS:
        missing.append("ADMIN_IDS")
    if not CHANNEL_USERNAME:
        missing.append("CHANNEL_USERNAME")
    
    if missing:
        print(f"Error: Missing required configuration: {', '.join(missing)}")
        print("Please check your configuration")
        return False
    
    return True 

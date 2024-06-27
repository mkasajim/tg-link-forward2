import os
from dotenv import load_dotenv
from db_operations import create_connection, create_table
from telegram_clients import setup_telegram_clients
from utilities import is_connected

# Load environment variables
dotenv_path = '.env'
load_dotenv(dotenv_path=dotenv_path)

# Initialize variables from environment
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
phone_number = os.getenv('PHONE_NUMBER')
bot_token = os.getenv('BOT_TOKEN')
chat_id_str = os.getenv('CHAT_ID')
admin_chat_id_str = os.getenv('ADMIN_CHAT_ID')

if chat_id_str is not None:
    chat_id = int(chat_id_str)
else:
    raise ValueError("CHAT_ID environment variable not found. Please check your .env file.")

if admin_chat_id_str is not None:
    admin_chat_id = int(admin_chat_id_str)
else:
    raise ValueError("CHAT_ID environment variable not found. Please check your .env file.")

# Create connections to databases
conn = create_connection('links.db')
if conn is not None:
    create_table_sql = """ CREATE TABLE IF NOT EXISTS links (
                            id integer PRIMARY KEY,
                            url text NOT NULL,
                            full_url text NOT NULL UNIQUE
                        ); """
    create_table(conn, create_table_sql)

blacklist_conn = create_connection('blacklist.db')
if blacklist_conn is not None:
    create_blacklist_table_sql = """CREATE TABLE IF NOT EXISTS blacklist (
                                    id integer PRIMARY KEY,
                                    domain text NOT NULL UNIQUE
                                );"""
    create_table(blacklist_conn, create_blacklist_table_sql)

bots_conn = create_connection('bots.db')
if bots_conn is not None:
    create_bots_table_sql = """ CREATE TABLE IF NOT EXISTS bots (
                                id integer PRIMARY KEY,
                                username text NOT NULL UNIQUE
                            ); """
    create_table(bots_conn, create_bots_table_sql)

conn_webpages = create_connection('webpages.db')
cursor_webpages = conn_webpages.cursor()
if conn_webpages is not None:
    create_table_sql = '''CREATE TABLE IF NOT EXISTS web_content (
                            url TEXT,
                            content_hash TEXT UNIQUE
                          );'''
    create_table(conn_webpages, create_table_sql)

# Set up Telegram clients
user_client, bot_client = setup_telegram_clients(api_id, api_hash, bot_token, phone_number, chat_id, admin_chat_id, conn, blacklist_conn, cursor_webpages)

def main():
    while True:
        try:
            print("Listening for incoming messages and bot commands...")
            user_client.start(phone=phone_number)
            bot_client.run_until_disconnected()
        except Exception as e:
            print(f"Error occurred: {e}")
            print("Checking internet connection...")

            while not is_connected("one.one.one.one"):
                print("Internet connection lost. Waiting for connection...")
                time.sleep(5)

            print("Internet connection regained. Restarting bot...")

if __name__ == '__main__':
    main()

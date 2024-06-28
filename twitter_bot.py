import asyncio
import json
import re
from twscrape import API, gather
from db_operations import extract_domain, is_domain_blacklisted, insert_link, create_connection, create_table
from url_processing import check_and_insert, normalize_url
from telethon import TelegramClient
from dotenv import load_dotenv
import os
import time

# Function to convert cookies from list of dictionaries to a simple key-value format
def convert_cookies(cookie_list):
    return "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookie_list])

# Load environment variables
dotenv_path = '.env'
load_dotenv(dotenv_path)

# Initialize variables from environment
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')
chat_id_str = os.getenv('CHAT_ID')

if chat_id_str is not None:
    chat_id = int(chat_id_str)
else:
    raise ValueError("CHAT_ID environment variable not found. Please check your .env file.")

async def send_telegram_message(client, message):
    await client.send_message(chat_id, message, parse_mode='md')

def extract_urls(text):
    url_pattern = r'(?:(?:https?|ftp):\/\/)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:\/[^\s]*)?'
    return re.findall(url_pattern, text)

def extract_tokens(text):
    # This regex will match both ${key} and $KEY formats
    token_pattern = r'\$\{?([A-Z0-9]+)\}?'
    return set(re.findall(token_pattern, text))

async def main():
    telegram_client = TelegramClient('bot', api_id, api_hash)
    await telegram_client.start(bot_token=bot_token)

    try:
        api = API()  # or API("path-to.db") - default is `accounts.db`

        # Load cookies from file
        with open("cookies.txt", "r") as file:
            cookie_list = json.load(file)
        
        cookies = convert_cookies(cookie_list)

        # Add account with COOKIES (only cookies are necessary)
        await api.pool.add_account(username="placeholder_username", password="placeholder_password", email="placeholder_email", email_password="placeholder_email_password", cookies=cookies)

        # Log in to all accounts (not necessary if using cookies, but good practice)
        await api.pool.login_all()

        # Keep track of the latest tweet ID we've seen
        latest_tweet_id = None

        while True:
            try:
                tweets = await gather(api.search("#Airdrop", limit=50))

                new_tweets = []
                for tweet in tweets:
                    if latest_tweet_id is None or tweet.id > latest_tweet_id:
                        new_tweets.append(tweet)
                    else:
                        break  # We've reached tweets we've already seen

                if new_tweets:
                    latest_tweet_id = new_tweets[0].id

                    for tweet in new_tweets:
                        print(f"-------------------------------------------------------------\n")
                        print(tweet.id, tweet.user.username, tweet.rawContent)
                        print(f"-------------------------------------------------------------\n")
                        urls = extract_urls(tweet.rawContent)
                        tokens = extract_tokens(tweet.rawContent)
                        
                        for url in urls:
                            base_url, _ = normalize_url(url)
                            domain = extract_domain(url)

                            if not is_domain_blacklisted(blacklist_conn, domain):
                                if not insert_link(conn, domain, url):
                                    continue
                                if check_and_insert(url, cursor_webpages, conn_webpages):
                                    print(f"New valid link found: {url}")
                                    
                                    # Prepare token string if tokens are found
                                    token_str = ""
                                    if tokens:
                                        token_str = "\n**Tokens found:** " + ", ".join(tokens)
                                    
                                    message_text = (f"**New Tweet Link Found:**\n\n"
                                                    f"**Tweet ID:** {tweet.id}\n"
                                                    f"**Username:** {tweet.user.username}\n"
                                                    f"**Content:** \n{tweet.rawContent}\n\n"
                                                    f"**Link:** {url}\n"
                                                    f"{token_str}")
                                    print("\033[92mSending message by bot.............\n-------------------------------------------------------------\n")
                                    print(message_text)
                                    print("\n-------------------------------------------------------------\n\033[0m")
                                    await send_telegram_message(telegram_client, message_text)

                await asyncio.sleep(60)  # Wait for 60 seconds before the next check

            except Exception as e:
                print(f"An error occurred: {e}")
                # Wait for a bit before trying again
                await asyncio.sleep(60)

    finally:
        await telegram_client.disconnect()
        
async def send_telegram_message(client, message):
    await client.send_message(chat_id, message, parse_mode='md')

def run_twitter_bot():
    # Initialize database connections
    global conn, blacklist_conn, conn_webpages, cursor_webpages
    conn = create_connection('links.db')
    create_table(conn, """ CREATE TABLE IF NOT EXISTS links (
                            id integer PRIMARY KEY,
                            url text NOT NULL,
                            full_url text NOT NULL UNIQUE
                        ); """)

    blacklist_conn = create_connection('blacklist.db')
    create_table(blacklist_conn, """CREATE TABLE IF NOT EXISTS blacklist (
                                    id integer PRIMARY KEY,
                                    domain text NOT NULL UNIQUE
                                );""")

    conn_webpages = create_connection('webpages.db')
    cursor_webpages = conn_webpages.cursor()
    create_table(conn_webpages, '''CREATE TABLE IF NOT EXISTS web_content (
                                    url TEXT,
                                    content_hash TEXT UNIQUE
                                  );''')

    asyncio.run(main())

if __name__ == "__main__":
    run_twitter_bot()
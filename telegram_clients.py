from telethon import TelegramClient
from telethon import events
import re
from db_operations import extract_domain, is_domain_blacklisted, insert_link, list_links, is_new_bot, insert_bot
from url_processing import check_and_insert

def setup_telegram_clients(api_id, api_hash, bot_token, phone_number, chat_id, admin_chat_id, conn, blacklist_conn, cursor_webpages):
    user_client = TelegramClient('anon', api_id, api_hash)
    bot_client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

    @user_client.on(events.NewMessage(incoming=True))
    async def user_message_handler(event):
        url_pattern = r'(?:(?:https?|ftp):\/\/)?(?:www\.)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}(?:\/[^\s]*)?'
        urls = re.findall(url_pattern, event.message.text)
        if urls:
            for url in urls:
                chat_title = ''
                sender_name = 'Unknown'
                source = ''
                post_source = 'Unknown'
                chat_link_available = False
                chat_link = ''

                if hasattr(event.chat, 'username') and event.chat.username:
                    chat_link_available = True
                    chat_link = f"https://t.me/{event.chat.username}/{event.message.id}"
                elif hasattr(event.message, 'id'):
                    chat_link_available = False
                    chat_link = f"Message ID: {event.message.id} in Chat ID: {event.chat_id} (Direct link not available for private chats)"
                else:
                    chat_link_available = False
                    chat_link = "Direct link not available."

                sender = await event.get_sender()
                if sender:
                    if hasattr(sender, 'first_name') and hasattr(sender, 'last_name'):
                        sender_name = f"{sender.first_name} {sender.last_name if sender.last_name else ''}"
                    else:
                        sender_name = "Anonymous"
                    post_source = sender_name

                if event.is_private:
                    pass
                elif event.is_group or event.is_channel:
                    chat = await event.get_chat()
                    chat_title = chat.title
                    if event.is_group:
                        sender_name += f" (Group: {chat_title})"
                        source = "Group"
                    else:
                        sender_name = f"Channel: {chat_title}"
                        source = "Channel"

                print(f"New message from {sender_name}: \n{event.text}\n-------------------------------------------------------------")

                base_url, _ = normalize_url(url)
                domain = extract_domain(url)

                if is_new_bot(bots_conn, event.message.text):
                    print("New bot detected!\n-------------------------------------------------------------\n")
                    bot_link_match = re.search(r'(?:https?://)?t\.me/([^/?]+)', event.message.text)
                    if bot_link_match:
                        bot_username = bot_link_match.group(1)
                        insert_bot(bots_conn, bot_username)
                        message_text = (f"**Full Post:-**\n{event.text}\n\n"
                                        f"**Event Link:-**\n{url}\n\n"
                                        f"**Post Source:-** {post_source} ({chat_link})\n"
                                        f"**{source}:-** {chat_title}"
                                    )
                        print(f"Sending message by bot.............\n-------------------------------------------------------------\n")
                        await user_client.send_message(chat_id, message_text, parse_mode='md')
                        break

                if not is_domain_blacklisted(blacklist_conn, domain):
                    print("Link is not in blacklist\n-------------------------------------------------------------\n")
                    if not insert_link(conn, domain, url):
                        break
                    if check_and_insert(url, cursor_webpages):
                        print("Link does not exist\n-------------------------------------------------------------\n")
                        if chat_link_available:
                            message_text = (f"**Full Post:-**\n{event.text}\n\n"
                                f"**Event Link:-**\n{url}\n\n"
                                f"**Post Source:-** [{post_source}]({chat_link})\n"
                                f"**{source}:-** {chat_title}"
                            )
                        else:
                            message_text = (f"**Full Post:-**\n{event.text}\n\n"
                                f"**Event Link:-**\n{url}\n\n"
                                f"**Post Source:-** {post_source} ({chat_link})\n"
                                f"**{source}:-** {chat_title}"
                            )
                        print("\033[92mSending message by bot.............\n-------------------------------------------------------------\n")
                        print(message_text)
                        await user_client.send_message(chat_id, message_text, parse_mode='md')
                        break

    bot_client.add_event_handler(lambda event: command_handler(event, admin_chat_id, conn, blacklist_conn))

    return user_client, bot_client

from telethon import events
from db_operations import is_domain_blacklisted, list_blacklist, add_to_blacklist, remove_from_blacklist, extract_domain

async def command_handler(event, admin_chat_id, conn, blacklist_conn):
    sender = await event.get_sender()
    sender_id = sender.id
    
    if event.raw_text.startswith('/ping'):
        await event.reply('Pong!')

    elif event.raw_text.startswith('/start'):
        await event.reply('The bot has started!')

    elif event.raw_text.startswith('/links') and sender_id == admin_chat_id:
        domains = list_links(conn)
        if domains:
            message = "All Links Sent:\n" + "\n".join([domain[0] for domain in domains])
            await event.reply(message)
        else:
            await event.reply("The list is currently empty")

    elif event.raw_text.startswith('/block') and sender_id == admin_chat_id:
        domain_to_block = extract_domain(event.raw_text.split()[1])
        if not is_domain_blacklisted(blacklist_conn, domain_to_block):
            add_to_blacklist(blacklist_conn, domain_to_block)
            await event.reply(f"Domain {domain_to_block} has been added to the blacklist.")
        else:
            await event.reply(f"Domain {domain_to_block} is already in the blacklist.")

    elif event.raw_text.startswith('/unblock') and sender_id == admin_chat_id:
        domain_to_unblock = extract_domain(event.raw_text.split()[1])
        if is_domain_blacklisted(blacklist_conn, domain_to_unblock):
            remove_from_blacklist(blacklist_conn, domain_to_unblock)
            await event.reply(f"Domain {domain_to_unblock} has been removed from the blacklist.")
        else:
            await event.reply(f"Domain {domain_to_unblock} is not in the blacklist.")

    elif event.raw_text.startswith('/blacklist') and sender_id == admin_chat_id:
        blacklist_domains = list_blacklist(blacklist_conn)
        if blacklist_domains:
            message = "Blacklisted domains:\n" + "\n".join([domain[0] for domain in blacklist_domains])
            await event.reply(message)
        else:
            await event.reply("The blacklist is currently empty.")

    elif event.raw_text.startswith('/status') and sender_id == admin_chat_id:
        await event.reply("The Bot is up and running.")

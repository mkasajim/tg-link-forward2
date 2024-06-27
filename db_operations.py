import sqlite3

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def normalize_url(url):
    from urllib.parse import urlparse, parse_qs, urlunparse
    
    url_parts = list(urlparse(url))
    query = dict(parse_qs(url_parts[4]))
    for param in ['Code', 'invite', 'refercode', 'referral_code', 'invite_code']:
        query.pop(param, None)
    url_parts[4] = ''
    return urlunparse(url_parts), query

def link_exists(conn, full_url):
    sql = '''SELECT id FROM links WHERE full_url=?'''
    cur = conn.cursor()
    cur.execute(sql, (full_url,))
    return cur.fetchone() is not None

def insert_link(conn, domain, full_url):
    if not link_exists(conn, full_url):
        sql = '''INSERT INTO links(url, full_url) VALUES(?, ?)'''
        try:
            c = conn.cursor()
            c.execute(sql, (domain, full_url))
            conn.commit()
            return True
        except sqlite3.IntegrityError as e:
            print(f"Link insertion failed due to IntegrityError: {e}")
            return False
    else:
        print(f"Link already exists: {full_url}")
        return False

def list_links(conn):
    sql = '''SELECT url FROM links'''
    try:
        c = conn.cursor()
        c.execute(sql)
        return c.fetchall()
    except sqlite3.Error as e:
        return []

def add_to_blacklist(conn, domain):
    sql = '''INSERT INTO blacklist(domain) VALUES(?)'''
    try:
        c = conn.cursor()
        c.execute(sql, (domain,))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None

def remove_from_blacklist(conn, domain):
    sql = '''DELETE FROM blacklist WHERE domain=?'''
    try:
        c = conn.cursor()
        c.execute(sql, (domain,))
        conn.commit()
    except sqlite3.Error as e:
        print(e)

def list_blacklist(conn):
    sql = '''SELECT domain FROM blacklist'''
    try:
        c = conn.cursor()
        c.execute(sql)
        return c.fetchall()
    except sqlite3.Error as e:
        return []

def is_domain_blacklisted(conn, domain):
    sql = '''SELECT id FROM blacklist WHERE domain=?'''
    cur = conn.cursor()
    cur.execute(sql, (domain,))
    return cur.fetchone() is not None

def extract_domain(url):
    from urllib.parse import urlparse
    
    parsed_uri = urlparse(url)
    domain = '{uri.netloc}'.format(uri=parsed_uri)
    if domain.startswith('www.'):
        domain = domain[4:]
    return domain

def create_bots_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)

def bot_exists(conn, bot_username):
    sql = '''SELECT id FROM bots WHERE username=?'''
    cur = conn.cursor()
    cur.execute(sql, (bot_username,))
    return cur.fetchone() is not None

def insert_bot(conn, bot_username):
    if not bot_exists(conn, bot_username):
        sql = '''INSERT INTO bots(username) VALUES(?)'''
        try:
            c = conn.cursor()
            c.execute(sql, (bot_username,))
            conn.commit()
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None
    return None

def is_new_bot(conn, text_msg):
    import re

    bot_link_match = re.search(r'(?:https?://)?t\.me/([^/?]+)', text_msg)

    if bot_link_match:
        bot_username = bot_link_match.group(1)
        if re.search(r'_bot$|bot$|Bot$', bot_username):
            return not bot_exists(conn, bot_username)
    return False

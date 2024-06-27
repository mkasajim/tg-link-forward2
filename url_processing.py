import requests
import hashlib
from bs4 import BeautifulSoup

def fetch_and_hash(url):
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url

    try:
        response = requests.get(url)
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        webpage_content = soup.get_text()

        hasher = hashlib.sha256()
        hasher.update(webpage_content.encode('utf-8'))
        return hasher.hexdigest()
    else:
        return None
    
def check_and_insert(url, cursor):
    content_hash = fetch_and_hash(url)
    if content_hash:
        try:
            cursor.execute('INSERT INTO web_content (url, content_hash) VALUES (?, ?)', (url, content_hash))
            conn.commit()
            print(f"Inserted: {url}")
            return True
        except sqlite3.IntegrityError:
            print(f"Same website already exists: {url}")
            return False
    else:
        print(f"Failed to fetch or hash content for URL: {url}")
        return False

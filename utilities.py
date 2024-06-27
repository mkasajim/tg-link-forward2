import socket

def is_connected(hostname):
    try:
        host = socket.gethostbyname(hostname)
        with socket.create_connection((host, 80), 2):
            return True
    except Exception:
        pass
    return False

import time
import requests

def retry(fn, attempts: int = 3, delay: float = 3.0):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if i < attempts - 1:
                time.sleep(delay * (i + 1))
    raise last

session = requests.Session()
session.headers.update({"User-Agent": "daily-status-bot/1.0"})

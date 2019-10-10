import requests
from icecream import ic
import time


def get(url, sleep=1, retries=0):
    """Requests wrapper that spins until it gets a 200."""
    ic(url)
    current_retry = 0
    while current_retry <= retries:
        req = requests.get(url)
        if req.status_code != 200:
            # Only increment if we have specified a retry limit.
            if retries > 0:
                current_retry = current_retry + 1
            time.sleep(sleep)
            continue
        return req.text

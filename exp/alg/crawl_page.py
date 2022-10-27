from urllib import request
import time


def crawl_content(url, retries=3):
    for _ in range(retries):
        try:
            response = request.urlopen(url, timeout=15)
            content = response.read()
            return content
        except Exception:
            time.sleep(0.5)
            print("Access request failed ", url)
    return None
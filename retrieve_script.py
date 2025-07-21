import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import signal
import sys

# Constants
BASE_TEMPLATE = "https://www.examtopics.com/discussions/splunk/view/{uid}-exam-splk-1003-topic-1-question-{qnum}-discussion/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
UID_RANGE = range(10000, 80000)
QUESTION_COUNT = 300
MAX_WORKERS = 20

# Lock and control flag
output_lock = Lock()
stop_requested = False


# Logging setup
def setup_logger(name, path, level):
    handler = logging.FileHandler(path, mode="w")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


valid_logger = setup_logger("valid", "valid_urls.log", logging.INFO)
bad_logger = setup_logger("bad", "bad_requests.log", logging.WARNING)


# Handle Ctrl+C
def signal_handler(sig, frame):
    global stop_requested
    print("Gracefully stopping... (Ctrl+C again to force quit)")
    stop_requested = True


signal.signal(signal.SIGINT, signal_handler)


def check_url(uid, qnum):
    if stop_requested:
        return None
    url = BASE_TEMPLATE.format(uid=uid, qnum=qnum)
    print(f"Trying: {url}")
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200 and not response.history:
            with output_lock:
                print(f"Found: {url}")
                valid_logger.info(url)
            return url
        elif response.status_code >= 400:
            bad_logger.warning(f"{response.status_code} - {url}")
    except requests.RequestException as e:
        bad_logger.warning(f"Exception - {url} - {e}")
    return None


def find_valid_url_for_question(qnum):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, uid, qnum): uid for uid in UID_RANGE}
        for future in as_completed(futures):
            if stop_requested:
                break
            result = future.result()
            if result:
                # Cancel remaining futures
                for f in futures:
                    f.cancel()
                return  # move to next question immediately


if __name__ == "__main__":
    try:
        for qnum in range(1, QUESTION_COUNT + 1):
            if stop_requested:
                break
            print(f"\Searching for Question {qnum}...")
            find_valid_url_for_question(qnum)
    except KeyboardInterrupt:
        print("Script interrupted.")
        sys.exit(1)

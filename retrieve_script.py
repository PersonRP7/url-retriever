import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import signal
import sys
from typing import Optional

# Constants
BASE_TEMPLATE = "https://www.examtopics.com/discussions/splunk/view/{uid}-exam-splk-1003-topic-1-question-{qnum}-discussion/"
HEADERS = {"User-Agent": "Mozilla/5.0"}
UID_RANGE = range(10000, 80000)
QUESTION_COUNT = 300
MAX_WORKERS = 20

# Lock and control flag
output_lock = Lock()
stop_requested = False


def setup_logger(name: str, path: str, level: int) -> logging.Logger:
    """
    Create and configure a logger.

    Args:
        name (str): Name of the logger.
        path (str): File path for the log file.
        level (int): Logging level.

    Returns:
        logging.Logger: Configured logger instance.
    """
    handler = logging.FileHandler(path, mode="w")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


# Keep valid URLs logged to a file
valid_logger = setup_logger("valid", "valid_urls.log", logging.INFO)


def signal_handler(sig: int, frame) -> None:
    """Handle Ctrl+C (SIGINT) for graceful shutdown."""
    global stop_requested
    print("Gracefully stopping... (Ctrl+C again to force quit)")
    stop_requested = True


signal.signal(signal.SIGINT, signal_handler)


def check_url(uid: int, qnum: int) -> Optional[str]:
    """
    Check if a given URL exists and is valid.

    Args:
        uid (int): Unique identifier in the URL.
        qnum (int): Question number in the URL.

    Returns:
        Optional[str]: The valid URL if found, otherwise None.
    """
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
            print(f"[BAD] {response.status_code} - {url}")
    except requests.RequestException as e:
        print(f"[ERROR] Exception - {url} - {e}")
    return None


def find_valid_url_for_question(qnum: int) -> None:
    """Search for a valid URL for a specific question number."""
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(check_url, uid, qnum): uid for uid in UID_RANGE}
        for future in as_completed(futures):
            if stop_requested:
                break
            result = future.result()
            if result:
                # Cancel remaining futures once a valid URL is found
                for f in futures:
                    f.cancel()
                return


def main() -> None:
    """Main entry point of the script."""
    start_qnum = 1
    if len(sys.argv) > 1:
        try:
            arg_val = int(sys.argv[1])
            if arg_val > 0:
                start_qnum = arg_val
            else:
                print("Error: Starting question number must be a positive integer.")
                sys.exit(1)
        except ValueError:
            print("Error: Invalid argument. Please provide a positive integer.")
            sys.exit(1)

    try:
        for qnum in range(start_qnum, QUESTION_COUNT + 1):
            if stop_requested:
                break
            print(f"Searching for Question {qnum}...")
            find_valid_url_for_question(qnum)
    except KeyboardInterrupt:
        print("Script interrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()

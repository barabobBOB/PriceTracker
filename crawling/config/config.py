import logging
import random
import time

from fake_useragent import UserAgent

def set_header() -> dict[str, str]:
    return {
        "User-Agent": UserAgent().random,
        "Accept-Language": "ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3"
    }


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    return logging.getLogger(__name__)

def crawling_waiting_time() -> None:
    return time.sleep(random.randint(1, 3))

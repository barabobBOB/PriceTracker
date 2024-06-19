import logging

from selenium.webdriver.chrome.options import Options
from fake_useragent import UserAgent

def set_chrome_options() -> Options:
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument(f"user-agent={UserAgent().random}")
    return chrome_options

def setup_logging() -> logging.Logger:
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    return logging.getLogger(__name__)

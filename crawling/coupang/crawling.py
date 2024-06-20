import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from crawling.config.config import setup_logging, set_chrome_options
from crawling.database.manager import DatabaseManager, db_config


def construct_url(category_id):
    return (f'https://www.coupang.com/np/categories/{category_id}'
            f'?listSize=120&brand=&offerCondition=&filterType='
            f'&isPriceRange=false&minPrice=&maxPrice=&channel=user'
            f'&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0')


def setup_categories_id():
    return [
        194286, 194287, 194290, 194291, 194292, 194296, 194302, 194303, 194310, 194311,
        194312, 194313, 194319, 194322, 194324, 194328, 194329, 194330, 194333, 194334,
        194335, 194340, 194341, 194344, 194436, 194437, 194438, 194447, 194448, 194456,
        194460, 194464, 194465, 194476, 194482, 194487, 194488, 194492, 194507, 194514,
        194515, 194520, 194524, 194527, 194539, 194540, 194561, 194562, 194564, 194571,
        194572, 194577, 194578, 194579, 194586, 194587, 194588, 194589, 194590, 194694,
        194695, 194698, 194699, 194700, 194701, 194706, 194707, 194708, 194711, 194712,
        194713, 194730, 194731, 194732, 194733, 194736, 194737, 194738, 194742, 194743,
        194744, 194745, 194746, 194812
    ]


class CoupangCrawler:
    def __init__(self, max_pages=10):
        self.categories_id = setup_categories_id()
        self.driver = None
        self.logger = setup_logging()
        self.max_pages = max_pages
        self.chrome_options = set_chrome_options()
        self.database_manager = DatabaseManager(db_config=db_config)

    def start_driver(self):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=self.chrome_options)

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def crawl(self):
        try:
            self.database_manager.connect()
            for category_id in self.categories_id:
                self.crawl_category(category_id)
        finally:
            self.database_manager.close()

    def crawl_category(self, category_id):
        self.start_driver()
        base_url = construct_url(category_id)
        self.driver.get(base_url)
        page = 1

        while page <= self.max_pages:
            if not self.load_page(category_id, page):
                break

            items = self.get_items()

            if not items:
                self.logger.info(f"더 이상 항목이 없습니다: 카테고리 {category_id}, 페이지 {page}")
                break

            self.extract_items(items, category_id)

            if not self.go_to_next_page(page):
                self.logger.info(f"다음 페이지로 이동할 수 없습니다: 카테고리 {category_id}, 페이지 {page}")
                break

            page += 1

        self.close_driver()

    def load_page(self, category_id, page):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'baby-product-link'))
            )
            return True
        except Exception as e:
            self.logger.error(f"페이지 로드 오류: 카테고리 {category_id}, 페이지 {page}")
            self.logger.error(f"Error: {e}")
            return False

    def get_items(self):
        return self.driver.find_elements(By.CLASS_NAME, 'baby-product-link')

    def extract_items(self, items, category_id):
        for item in items:
            try:
                product_id = item.get_attribute('data-product-id')
                title = item.find_element(By.CLASS_NAME, 'name').text.strip()
                price = item.find_element(By.CLASS_NAME, 'price-value').text.strip()
                star = item.find_element(By.CLASS_NAME, 'rating').text.strip()

                # per_price 괄호와 "100g당", "원" 제거
                per_price = item.find_element(By.CLASS_NAME, 'unit-price').text.strip()
                per_price = re.sub(r'\(100g당\s*|\s*원\)|\(|\)', '', per_price).strip()

                # review_count 괄호 제거
                review_count = item.find_element(By.CLASS_NAME, 'rating-total-count').text.strip()
                review_count = re.sub(r'[\(\)]', '', review_count).strip()

                # price와 per_price에서 쉼표 제거
                price = int(price.replace(',', ''))
                per_price = int(per_price.replace(',', ''))

                self.logger.info(
                    f"category_id: {category_id}, product_id: {product_id}, title: {title}, price: {price}, "
                    f"per_price: {per_price}, star: {star}, review_cnt: {review_count}")

                self.database_manager.insert_product(int(product_id),
                                                     title,
                                                     price,
                                                     per_price,
                                                     float(star),
                                                     int(review_count),
                                                     category_id)

            except Exception:
                # 리뷰, 별점 등의 정보가 없는 경우
                continue

    def go_to_next_page(self, page):
        try:
            next_page_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, f'//*[@id="product-list-paging"]/div/a[{page + 2}]'))
            )
            self.driver.execute_script("arguments[0].click();", next_page_button)
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'baby-product-link'))
            )
            return True
        except Exception as e:
            self.logger.error(f"다음 페이지로 이동할 수 없습니다: 페이지 {page}")
            self.logger.error(f"Error: {e}")
            return False


if __name__ == '__main__':
    crawler = CoupangCrawler()
    crawler.crawl()
    crawler.close_driver()

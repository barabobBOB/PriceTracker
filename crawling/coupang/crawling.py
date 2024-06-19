import re
import time
import random
import requests

from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

from crawling.config.config import *
from crawling.database.manager import DatabaseManager, db_config


def construct_url(category_id, page):
    return (f'https://www.coupang.com/np/categories/{category_id}'
            f'?listSize=120&brand=&offerCondition=&filterType='
            f'&isPriceRange=false&minPrice=&maxPrice=&channel=user'
            f'&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0&page={page}')


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
        self.logger = setup_logging()
        self.max_pages = max_pages
        self.database_manager = DatabaseManager(db_config=db_config)

    def check_last_page(self, category_id):
        response = requests.get(construct_url(category_id, 1), headers=set_header())
        response.raise_for_status()
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            page = soup.find('div', class_='product-list-paging')
            return int(page['data-total'])
        return 1

    def crawl(self):
        try:
            self.database_manager.connect()
            for category_id in self.categories_id:
                self.crawl_category(category_id)
        finally:
            self.database_manager.close()

    def crawl_category(self, category_id):
        last_page = self.check_last_page(category_id)
        time.sleep(random.randint(1, 3))
        for page in range(1, min(last_page, self.max_pages) + 1):
            self.crawl_page(category_id, page)
            logging.info(f"------category_id: {category_id}, page: {page}------")
            time.sleep(random.randint(1, 3))

    def crawl_page(self, category_id, page):
        url = construct_url(category_id, page)
        response = requests.get(url, headers=set_header())
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find('ul', id='productList').find_all('li')
        self.extract_items(items, category_id)

    def extract_items(self, items, category_id):
        for item in items:
            try:
                product_id = item['data-product-id']
                title = item.find('div', class_='name').text
                price = item.find('strong', class_='price-value').text
                star = item.find('em', class_='rating').text

                # per_price 괄호와 "100g당", "원" 제거
                per_price = item.find('span', class_='unit-price').text
                per_price = re.sub(r'\(100g당\s*|\s*원\)|\(|\)', '', per_price).strip()

                # review_count 괄호 제거
                review_count = item.find('span', class_='rating-total-count').text
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


if __name__ == '__main__':
    crawler = CoupangCrawler()
    crawler.crawl()
import requests

from bs4 import BeautifulSoup
from ..config.set_up import set_header, setup_logging, crawling_waiting_time
from ..database.handler import DatabaseHandler


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

def requests_get_html(url):
    response = requests.get(url, headers=set_header())
    response.raise_for_status()
    return response.text

def check_last_page(category_id):
    response = requests.get(construct_url(category_id, 1), headers=set_header())
    crawling_waiting_time()
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    page = soup.find('div', class_='product-list-paging')
    return int(page['data-total'])

def get_last_pages(**context):
    categories_id = setup_categories_id()
    last_pages = [check_last_page(category_id) for category_id in categories_id]
    context["task_instance"].xcom_push(key="last_pages", value=last_pages)

def create_url_list(**context):
    last_pages = context["task_instance"].xcom_pull(
        task_ids="get_last_pages", key="last_pages"
    )
    url_list = []
    for category_id, last_page in zip(setup_categories_id(), last_pages):
        for page in range(1, last_page + 1):
            url_list.append([construct_url(category_id, page), category_id])
    context["task_instance"].xcom_push(key="url_list", value=url_list)

class CoupangCrawler:
    def __init__(self):
        self.logger = setup_logging()
        self.db_handler = DatabaseHandler()
        self.db_handler.create_coupang_products()

    def crawl(self, url_list):
        for url in url_list:
            self.crawl_page(url[0], url[1])
            crawling_waiting_time()

    def crawl_page(self, url, category_id):
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
                per_price = item.find('span', class_='unit-price').text
                review_count = item.find('span', class_='rating-total-count').text

                self.db_handler.insert_product(product_id, title, price, per_price, star, review_count, category_id)

            except Exception:
                # 리뷰, 별점 등의 정보가 없는 경우
                continue

def crawl(**context):
    url_list = context["task_instance"].xcom_pull(
        task_ids="create_url_list", key="url_list"
    )
    crawler = CoupangCrawler()
    crawler.crawl(url_list)

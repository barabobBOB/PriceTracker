import requests

from bs4 import BeautifulSoup
from ..config.set_up import set_header, setup_logging, crawling_waiting_time
from ..database.handler import DatabaseHandler


def construct_url(category_id, page):
    return (f'https://www.coupang.com/np/categories/{category_id}'
            f'?listSize=120&brand=&offerCondition=&filterType='
            f'&isPriceRange=false&minPrice=&maxPrice=&channel=user'
            f'&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0&page={page}')

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

def get_last_pages(categories_id, idx, **context):
    last_pages = [check_last_page(category_id) for category_id in categories_id]
    context["task_instance"].xcom_push(key="last_pages_"+idx, value=last_pages)

def create_url_list(categories_id, idx, **context):
    last_pages = context["task_instance"].xcom_pull(
        key="last_pages_"+idx
    )
    url_list = [
        [construct_url(category_id, page), category_id]
        for category_id, last_page in zip(categories_id, last_pages)
        for page in range(1, last_page + 1)
    ]
    context["task_instance"].xcom_push(key="url_list_"+idx, value=url_list)

class CoupangCrawler:
    def __init__(self):
        self.logger = setup_logging()
        self.db_handler = DatabaseHandler()
        self.db_handler.create_coupang_products()

    def crawl(self, idx, **context):
        url_list = context["task_instance"].xcom_pull(
            key="url_list_"+idx
        )
        print("url", url_list)
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
    # def find_data_element(item: ):
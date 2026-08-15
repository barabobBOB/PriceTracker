import bs4
import requests
import datetime
import re
import os

import pyarrow as pa
import pyarrow.parquet as pq

from bs4 import BeautifulSoup

from ..config.set_up import set_header, setup_logging, crawling_waiting_time
from ..database.handler import DatabaseHandler

def construct_url(category_id: int, page: int) -> str:
    return (f'https://www.coupang.com/np/categories/{category_id}'
            f'?listSize=120&brand=&offerCondition=&filterType='
            f'&isPriceRange=false&minPrice=&maxPrice=&channel=user'
            f'&fromComponent=N&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=194186&rating=0&page={page}')


def check_last_page(category_id: int) -> int:
    response = requests.get(construct_url(category_id, 1), headers=set_header())
    crawling_waiting_time()
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    page = soup.find('div', class_='product-list-paging')
    return int(page['data-total'])


def get_last_pages(categories_id: list, idx: str, **context) -> None:
    last_pages = [check_last_page(category_id) for category_id in categories_id]
    context["task_instance"].xcom_push(key="last_pages_" + idx, value=last_pages)


def create_url_list(categories_id: list[int], idx: str, **context) -> None:
    last_pages = context["task_instance"].xcom_pull(
        key="last_pages_" + idx
    )
    url_list = [
        [construct_url(category_id, page), category_id]
        for category_id, last_page in zip(categories_id, last_pages)
        for page in range(1, last_page + 1)
    ]
    context["task_instance"].xcom_push(key="url_list_" + idx, value=url_list)

class CoupangCrawler:
    def __init__(self) -> None:
        self.logger = setup_logging()
        self.db_handler = DatabaseHandler()
        self.db_handler.create_coupang_products()

    def crawl(self, idx: str, **context) -> None:
        url_list = context["task_instance"].xcom_pull(
            key="url_list_" + idx
        )
        collection_datetime = datetime.datetime.now()
        raw_data: list[dict] = []
        for url in url_list:
            self.crawl_page(url[0], url[1], idx, collection_datetime, raw_data, **context)
            crawling_waiting_time()
        self.save_raw_data(idx, raw_data)

    def crawl_page(self, url: str, category_id: int, idx: str, collection_datetime: datetime, raw_data: list[dict], **context) -> None:
        response = requests.get(url, headers=set_header())
        response.raise_for_status()
        raw_data.append({
            "url": url,
            "category_id": category_id,
            "raw_html": response.text,
            "collection_datetime": collection_datetime,
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        try:
            items = soup.find('ul', id='productList').find_all('li')
            self.extract_items(items, category_id, collection_datetime)

        except AttributeError as e:
            error_info = {
                "error_message": str(e),
                "failed_url": url,
                "index": idx,
                "success": False,
                "timestamp": collection_datetime
            }
            context["task_instance"].xcom_push(key="error_log_" + idx, value=error_info)

    def save_raw_data(self, idx: str, raw_data: list[dict]) -> None:
        if not raw_data:
            return

        raw_data_dir = os.environ.get("RAW_DATA_DIR", "raw_data")
        os.makedirs(raw_data_dir, exist_ok=True)
        file_path = os.path.join(raw_data_dir, f"coupang_raw_{idx}.parquet")

        table = pa.table(
            {
                "url": [record["url"] for record in raw_data],
                "category_id": [record["category_id"] for record in raw_data],
                "raw_html": [record["raw_html"] for record in raw_data],
                "collection_datetime": [record["collection_datetime"] for record in raw_data],
            }
        )
        pq.write_table(table, file_path)
        self.logger.info(f"Raw data saved to {file_path}")

    def extract_items(self, items: list[bs4.BeautifulSoup], category_id: int, collection_datetime: datetime) -> None:
        product = {}
        for item in items:
            try:
                product["product_id"] = item['data-product-id']
                product["title"] = item.find('div', class_='name').text

                price = item.find('strong', class_='price-value').text
                product["price"] = int(price.replace(',', ''))
                product["star"] = item.find('em', class_='rating').text

                per_price = item.find('span', class_='unit-price').text
                per_price = re.sub(r'\(100g당\s*|\s*원\)|\(|\)', '', per_price).strip()
                product["per_price"] = int(per_price.replace(',', ''))

                review_count = item.find('span', class_='rating-total-count').text
                product["review_count"] = re.sub(r'[\(\)]', '', review_count).strip()

                product["category_id"] = category_id
                product["collection_datetime"] = collection_datetime

                self.db_handler.insert_product(product)

                product["collection_datetime"] = str(collection_datetime)

            except Exception:
                # 리뷰, 별점 등의 정보가 없는 경우
                continue

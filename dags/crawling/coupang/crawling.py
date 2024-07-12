import json
import bs4
import requests
import datetime
import logging
import re

from bs4 import BeautifulSoup
from ..config.set_up import set_header, setup_logging, crawling_waiting_time
from ..database.handler import DatabaseHandler
from kafka import KafkaProducer


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


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def produce_to_kafka(data: dict) -> None:
    logger.info("Kafka producer를 생성합니다.")
    producer = KafkaProducer(
        bootstrap_servers='kafka:29092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    try:
        if data:
            logger.info("데이터를 Kafka 토픽으로 전송합니다: %s", data)
            future = producer.send('coupang_crawling_topic', value=data)
            logger.info("Kafka로 데이터 전송을 플러시합니다.")
            producer.flush()
            logger.info("데이터 전송이 성공적으로 완료되었습니다.")
    except Exception as e:
        logger.error("Kafka로 데이터 전송 중 오류 발생: %s", e)
    finally:
        logger.info("Kafka producer를 닫습니다.")
        producer.close()


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
        for url in url_list:
            self.crawl_page(url[0], url[1], idx, collection_datetime, **context)
            crawling_waiting_time()

    def crawl_page(self, url: str, category_id: int, idx: str, collection_datetime: datetime, **context) -> None:
        response = requests.get(url, headers=set_header())
        response.raise_for_status()
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
                produce_to_kafka(product)

            except Exception:
                # 리뷰, 별점 등의 정보가 없는 경우
                continue

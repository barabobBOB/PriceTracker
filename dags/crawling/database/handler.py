import logging

from airflow.providers.postgres.hooks.postgres import PostgresHook


class DatabaseHandler:
    """
    데이터베이스와 상호작용을 합니다.
    """

    def __init__(self) -> None:
        self.hook = PostgresHook(postgres_conn_id='postgres_conn')
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_coupang_products(self) -> None:
        """
        쿠팡 상품 목록을 저장하는 테이블을 생성합니다.
        """
        query = """
        CREATE TABLE IF NOT EXISTS coupang_products (
            id SERIAL PRIMARY KEY,
            product_id BIGINT,
            title TEXT,
            price TEXT,
            per_price TEXT,
            star FLOAT,
            review_count TEXT,
            category_id BIGINT,
            collection_datetime TIMESTAMP
        )
        """
        self.hook.run(query)
        self.logger.info("Table coupang_products created successfully.")

    def insert_product(self, product: dict) -> None:
        """
        쿠팡 사이트의 상품을 저장합니다.
        """
        query = """
        INSERT INTO coupang_products (product_id, title, price, per_price, star, review_count, category_id, collection_datetime)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        self.hook.run(query, parameters=(product["product_id"],
                                         product["title"],
                                         product["price"],
                                         product["per_price"],
                                         product["star"],
                                         product["review_count"],
                                         product["category_id"],
                                         product["collection_datetime"]))
        self.logger.info(f"Product {product['title']} inserted successfully.")

    def insert_error(self, idx: int, **context) -> None:
        """
        발생된 에러를 저장합니다.
        """
        query = """
        INSERT INTO error_log (error_message, failed_url, index, success, timestamp)
        VALUES (%s, %s, %s, %s, %s)
        """
        error_info = context["task_instance"].xcom_pull(key="error_log_" + idx)
        parameters = (
            error_info["error_message"],
            error_info["failed_url"],
            error_info["index"],
            error_info["success"],
            error_info["timestamp"]
        )
        self.hook.run(query, parameters=parameters)
        self.logger.info(f"Error logged: {error_info['error_message']}")

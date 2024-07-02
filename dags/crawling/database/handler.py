import logging

from airflow.providers.postgres.hooks.postgres import PostgresHook

class DatabaseHandler:
    def __init__(self):
        self.hook = PostgresHook(postgres_conn_id='postgres_conn')
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_coupang_products(self):
        query = """
        CREATE TABLE IF NOT EXISTS coupang_products (
            id SERIAL PRIMARY KEY,
            product_id BIGINT,
            title TEXT,
            price TEXT,
            per_price TEXT,
            star FLOAT,
            review_count TEXT,
            category_id BIGINT
        )
        """
        self.hook.run(query)
        self.logger.info("Table coupang_products created successfully.")

    def insert_product(self, product_id, title, price, per_price, star, review_count, category_id):
        query = """
        INSERT INTO coupang_products (product_id, title, price, per_price, star, review_count, category_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        self.hook.run(query, parameters=(product_id, title, price, per_price, star, review_count, category_id))
        self.logger.info(f"Product {title} inserted successfully.")

    def insert_error(self, idx, **context):
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
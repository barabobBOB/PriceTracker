import logging

import psycopg2

from psycopg2._psycopg import Error

db_config = {
    'dbname': 'price_tracker',
    'user': 'postgres',
    'password': 'postgres',
    'host': 'localhost',
    'port': '5460'
}


class DatabaseManager:
    def __init__(self, db_config):
        self.db_host = db_config['host']
        self.db_port = db_config['port']
        self.db_name = db_config['dbname']
        self.db_user = db_config['user']
        self.db_password = db_config['password']
        self.connection = None
        self.logger = logging.getLogger(__name__)  # 클래스 이름을 기반으로 로거를 설정합니다.

        # 로거 설정
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                user=self.db_user,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port,
                database=self.db_name
            )
            self.logger.info("PostgreSQL 데이터베이스에 연결되었습니다.")
        except (Exception, Error) as error:
            self.logger.error(f"PostgreSQL 연결 오류: {error}")

    def close(self):
        try:
            if self.connection:
                self.connection.close()
                self.logger.info("PostgreSQL 연결이 닫혔습니다.")
        except (Exception, Error) as error:
            self.logger.error(f"PostgreSQL 연결 종료 오류: {error}")

    def insert_product(self, product_id, title, price, per_price, star, review_count, category_id):
        try:
            cursor = self.connection.cursor()

            insert_query = """ 
            INSERT INTO 
                coupang_products 
                (product_id, title, price, per_price, star, review_count, category_id) 
            VALUES 
                (%s,%s,%s,%s,%s,%s,%s) """
            record_to_insert = (product_id, title, price, per_price, star, review_count, category_id)
            cursor.execute(insert_query, record_to_insert)

            self.connection.commit()
        except (Exception, Error) as error:
            self.logger.error(f"데이터 삽입 오류: {error}")
        finally:
            if cursor:
                cursor.close()
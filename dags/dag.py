import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from crawling.coupang import crawling

kst = pendulum.timezone("Asia/Seoul")

default_args = {
    'owner': 'seyeon',
    'depends_on_past': False,
    'start_date': datetime(2023, 4, 1),
    'email': ['choi20014830@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

with DAG(
        dag_id='coupang_crawling',
        default_args=default_args,
        start_date=datetime(2024, 6, 29, tzinfo=kst),
        description='쿠팡 식료품 카테고리별 크롤링',
        schedule_interval='@once',
        tags=['test']
) as dag:
    get_last_pages_task = PythonOperator(
        task_id='get_last_pages',
        python_callable=crawling.get_last_pages,
    )

    create_url_list = PythonOperator(
        task_id='create_url_list',
        python_callable=crawling.create_url_list,
    )

    coupang_crawling = PythonOperator(
        task_id='coupang_crawling',
        python_callable=crawling.crawl
    )

    get_last_pages_task >> create_url_list >> coupang_crawling
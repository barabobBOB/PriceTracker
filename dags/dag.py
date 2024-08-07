from __future__ import annotations

import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from crawling.coupang import crawling
from crawling.database.handler import DatabaseHandler
from typing import List

kst = pendulum.timezone("Asia/Seoul")

def category_division(division_count: int) -> List[List[int]]:
    categories_id = [194286, 194287, 194290, 194291, 194292, 194296, 194302, 194303, 194310, 194311,
                     194312, 194313, 194319, 194322, 194324, 194328, 194329, 194330, 194333, 194334,
                     194335, 194340, 194341, 194344, 194436, 194437, 194438, 194447, 194448, 194456,
                     194460, 194464, 194465, 194476, 194482, 194487, 194488, 194492, 194507, 194514,
                     194515, 194520, 194524, 194527, 194539, 194540, 194561, 194562, 194564, 194571,
                     194572, 194577, 194578, 194579, 194586, 194587, 194588, 194589, 194590, 194694,
                     194695, 194698, 194699, 194700, 194701, 194706, 194707, 194708, 194711, 194712,
                     194713, 194730, 194731, 194732, 194733, 194736, 194737, 194738, 194742, 194743,
                     194744, 194745, 194746, 194812]
    category_data = int(len(categories_id) / division_count)
    return [categories_id[i * category_data: category_data * (i + 1)] for i in range(division_count)]


def error_branch(idx: int, **context: dict) -> str:
    try:
        error_log = context["task_instance"].xcom_pull(key="error_log_" + str(idx))
        if not error_log["success"]:
            return "error_db_insert_" + str(error_log["index"])
    except Exception:
        return "success_crawling_" + str(idx)


default_args = {
    'owner': 'seyeon',
    'depends_on_past': False,
    'start_date': datetime(2024, 7, 1),
    'email': ['choi20014830@gmail.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}


def coupang_with_dag(data: List[List[int]], dag: DAG, start_dag: BashOperator) -> DAG:
    for i in range(len(data)):
        idx = str(i)
        get_last_pages = PythonOperator(
            task_id='get_last_pages_' + idx,
            op_kwargs={"categories_id": data[i], "idx": idx},
            python_callable=crawling.get_last_pages,
            provide_context=True,
            dag=dag
        )

        create_url_list = PythonOperator(
            task_id='create_url_list_' + idx,
            op_kwargs={"categories_id": data[i], "idx": idx},
            python_callable=crawling.create_url_list,
            provide_context=True,
            dag=dag
        )

        coupang_crawling = PythonOperator(
            task_id='coupang_crawling_' + idx,
            op_kwargs={"idx": idx},
            python_callable=crawling.CoupangCrawler().crawl,
            provide_context=True,
            dag=dag
        )

        error_log_branch = BranchPythonOperator(
            task_id="error_log_branch_" + idx,
            op_kwargs={"idx": idx},
            python_callable=error_branch,
            provide_context=True,
            trigger_rule='all_done',
            dag=dag
        )

        error_db_insert = PythonOperator(
            task_id="error_db_insert_" + idx,
            op_kwargs={"idx": idx},
            python_callable=DatabaseHandler().insert_error,
            provide_context=True,
            dag=dag,
        )

        success_crawling = BashOperator(
            task_id="success_crawling_" + idx,
            bash_command="echo crawling success!!",
            dag=dag,
        )

        start_dag >> get_last_pages >> create_url_list >> coupang_crawling >> error_log_branch
        error_log_branch >> error_db_insert
        error_log_branch >> success_crawling

    return dag


with DAG(
        dag_id='coupang_crawling',
        default_args=default_args,
        start_date=datetime(2024, 7, 1, tzinfo=kst),
        description='쿠팡 식료품 카테고리별 크롤링',
        schedule_interval='@once',
        tags=['test']
) as dag:
    start = BashOperator(
        task_id="start",
        bash_command="echo crawling start!!",
        dag=dag,
    )
    coupang_dags = coupang_with_dag(category_division(7), dag, start)

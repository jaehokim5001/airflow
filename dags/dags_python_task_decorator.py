from airflow import DAG
from airflow.decorators import task
from datetime import datetime
import pendulum
import logging

# DAG 기본 설정
with DAG(
    dag_id='dags_python_task_decorator',
    schedule='@daily',
    start_date=pendulum.datetime(2023, 3, 1, tz='Asia/Seoul'),
    catchup=False,
    tags=['example']
) as dag:
    
    @task(task_id="python_task1")
    def print_context(some_input: str):
        """입력값을 로그와 print로 출력"""
        print(some_input)
        logging.info(some_input)

    # 태스크 정의 (Airflow 3.0에서도 동일)
    python_task1 = print_context('task_decorator_실행')
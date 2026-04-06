from datetime import datetime, timezone
import logging

from airflow import DAG
from airflow.operators.python import PythonOperator

def print_current_time():
    current_time = datetime.now(timezone.utc)
    logging.info(f"Current UTC time is: {current_time}")
    print(f"Current UTC time is: {current_time}")

with DAG(
    dag_id='antigravity_test_dag',
    schedule='*/5 * * * *',
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['antigravity'],
) as dag:

    log_time_task = PythonOperator(
        task_id='log_current_time',
        python_callable=print_current_time,
    )

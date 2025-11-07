from airflow import DAG
import pendulum
from airflow.decorators import task

# DAG 기본 설정
with DAG(
    dag_id='dags_python_show_templates',
    schedule="30 9 * * *",
    start_date=pendulum.datetime(2025, 11, 1, tz='Asia/Seoul'),
    catchup=True
) as dag:
    
    @task(task_id='python_task')
    def show_templates(**kwargs):
        from pprint import pprint
        pprint(kwargs)

    show_templates()
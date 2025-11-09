from airflow import DAG
import pendulum
from airflow.decorators import task
import datetime

# DAG 기본 설정
with DAG(
    dag_id='dags_python_with_xcom_eg1',
    schedule="30 6 * * *",
    start_date=pendulum.datetime(2025, 11, 1, tz='Asia/Seoul'),
    catchup=False  
) as dag:
    
    @task(task_id='python_xcom_push_task1')
    def xcom_push1(**kwargs):
        ti = kwargs['ti']
        ti.xcom_push(key='result_1', value="Value_1")
        ti.xcom_push(key='result_2', value=[1,2,3])

    @task(task_id='python_xcom_push_task2')
    def xcom_push2(**kwargs):
        ti = kwargs['ti']
        ti.xcom_push(key='result_1', value="Value_2")
        ti.xcom_push(key='result_2', value=[1,2,3,4])

    
    @task(task_id='python_xcom_pull_task')
    def xcom_pull(**kwargs):
        ti = kwargs['ti']
        value1 = ti.xcom_pull(key="result_1")
        value2 = ti.xcom_pull(key="result_2", task_ids='python_xcom_push_task1')
        print(f"Pulled Value 1: {value1}")
        print(f"Pulled Value 2: {value2}")


        xcom_push1() >> xcom_push2() >> xcom_pull()

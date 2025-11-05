from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
from datetime import datetime
import pendulum
from common.common_func import regist

# DAG 기본 설정
with DAG(
    dag_id='dags_python_with_op_args',
    schedule="30 6 * * *",
    start_date=pendulum.datetime(2023, 3, 1, tz='Asia/Seoul'),
    catchup=False
) as dag:
    
    # PythonOperator를 사용하여 태스크 정의
    regist_t1 = PythonOperator(
        task_id='regist_t1',
        python_callable=regist,
        op_args=['홍길동', '남자', 'kr', '서울']
    )

    regist_t1
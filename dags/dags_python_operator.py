import pendulum
import random
from airflow.sdk import DAG
from airflow.providers.standard.operators.python import PythonOperator


with DAG(
    dag_id="dags_python_operator",
    schedule="30 6 * * *",
    start_date=pendulum.datetime(2023, 3, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:
    
    def select_fruit():
        fruits = ['apple', 'banana', 'cherry', 'date', 'elderberry']
        rand_int = random.randint(0, 4)
        print(fruits[rand_int])

    py_t1 = PythonOperator(
        task_id='py_t1',
        python_callable=select_fruit
    )

py_t1
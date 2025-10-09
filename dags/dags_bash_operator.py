
import pendulum
from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator    

with DAG(
    dag_id="dags_bash_operator",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2023, 3, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:
    bash_t1 = BashOperator(
        task_id="bash_t1",
        bash_command="echo whoami",
    )
    bash_t2 = BashOperator(
        task_id="bash_t2",
        bash_command="echo $HOSTNAME; echo good",
    )

    bash_t3 = BashOperator(
        task_id="bash_t3",
        bash_command="echo $HOSTNAME; echo good",
    )

    bash_t4 = BashOperator(
        task_id="bash_t4",
        bash_command="echo $HOSTNAME; echo good",
    )

    bash_t1 >> bash_t2 >> bash_t3 >> bash_t4
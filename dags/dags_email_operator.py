import pendulum
from airflow.sdk import DAG
from airflow.providers.smtp.operators.smtp import EmailOperator

with DAG(
    dag_id="dags_email_operator",
    schedule="0 8 1 * *",
    start_date=pendulum.datetime(2023, 3, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:
    
    send_email = EmailOperator(
        task_id='send_email_task',
        conn_id='smtp_smtp_gmail',
        to='jhk5055@nate.com',
        subject='airflow 성공 알림',
        html_content='<h3>Airflow DAG가 성공적으로 실행되었습니다!</h3>'
    )


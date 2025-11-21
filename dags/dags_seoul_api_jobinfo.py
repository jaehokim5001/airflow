from operators.seoul_api_to_csv_operator import SeoulApiToCsvOperator
import pendulum
from airflow.sdk import DAG

with DAG(
    dag_id="dags_seoul_api_jobinfo",
    schedule=None,
    start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Seoul"),
    catchup=False
) as dag:
    
    tb_seoul_jobinfo = SeoulApiToCsvOperator(
        task_id='tb_seoul_jobinfo',
        dataset_nm='Tbseoul_jobinfo',
        path='/opt/airflow/files/Tbseoul_jobinfo/{{data_interval_end.in_timezone("Asia/Seoul") | ds_nodash }}',
        file_name='Tbseoul_jobinfo.csv'
    )  

    tb_seoul_jobinfo
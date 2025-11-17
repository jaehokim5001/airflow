import pendulum
from airflow.providers.http.operators.http import HttpOperator
from airflow import DAG,task

with DAG(
    dag_id="dags_http_operator",
    start_date=pendulum.datetime(2023, 1, 1, tz="Asia/Seoul"),
    catchup=False,
    schedule=None
) as dag:
    
    ##서울시 공공데이터
    http_task = HttpOperator(
        task_id='tb_seoul_jobinfo',
        method='GET',
        http_conn_id='openapi.seoul.go.kr',
        endpoint='{{var.value.apikey_openapi_seoul_go_kr}}/JSON/GetJobInfo/1/5/',
        method ='GET',
        headers= {'Content-Type': 'application/json',
                        'charset': 'utf-8',
                        'Accept': '*/*'
                        }
    )

    @task(task_id='python_2')
    def python_2(**kwargs):
        ti = kwargs['ti']
        rslt = ti.xcom_pull(task_ids='tb_seoul_jobinfo')
        import json
        from pprint import pprint
        json_rslt = json.loads(rslt)
        pprint(json_rslt)

    http_task >> python_2()
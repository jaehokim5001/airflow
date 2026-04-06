#!/bin/bash
docker exec airflow-airflow-scheduler-1 airflow connections delete conn_smtp_gmail
docker exec airflow-airflow-scheduler-1 airflow connections add 'conn_smtp_gmail' \
  --conn-type 'smtp' \
  --conn-host 'smtp.gmail.com' \
  --conn-login 'j.h.kim6844@gmail.com' \
  --conn-password 'twsexivomyswgeca' \
  --conn-port '465' \
  --extra '{"use_ssl": true}'

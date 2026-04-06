import sys
import os

# 모듈 경로 추가
sys.path.append(r"c:\\vscode\\airflow\\dags")
from naver_news_summary_mail_dag import crawler_agent, analyst_agent

# DATA_DIR 재지정 (windows 로컬 테스트용)
import naver_news_summary_mail_dag
naver_news_summary_mail_dag.DATA_DIR = r"c:\\vscode\\airflow\\data"

print("--- Crawler 실행 중 ---")
crawler_res = crawler_agent()
print("Crawler 반환값:", crawler_res)

print("--- Analyst 실행 중 ---")
analyst_res = analyst_agent()
print("Analyst 반환값:")
print(analyst_res[:300] + "...(생략)")

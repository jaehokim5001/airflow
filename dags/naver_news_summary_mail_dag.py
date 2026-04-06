"""
프로그램 명칭: 네이버 경제 뉴스 상위 10개 요약 및 메일 발송 파이프라인 (완결본)
주요 기능 설명:
  - Crawler: BeautifulSoup 기반 네이버 경제 뉴스 스크래핑
  - Analyst: 기사 요약 및 HTML 리포트 생성 (XCom 전달)
  - Messenger: smtplib 직접 연동을 통한 무결성 메일 전송 (EmailOperator 우회)
작업 목적 및 기대 결과:
  - Airflow 3 환경에서의 SMTP 연결 호환성 문제를 직접 발송 방식으로 해결
  - 안정적인 데일리 뉴스 리포트 수신 서비스 구축
"""

import os
import json
import time
import smtplib
import requests
from bs4 import BeautifulSoup
from collections import Counter
from email.mime.text import MIMEText
from email.header import Header
import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# 데이터를 저장할 절대경로 지정
DATA_DIR = "/opt/airflow/data"

def crawler_agent() -> str:
    """역할: Crawler - 뉴스 스크래핑 및 JSON 저장"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    file_path = os.path.join(DATA_DIR, "raw_news.json")
    url = "https://news.naver.com/section/101"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    scraped_data = []

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.select('.sa_text_title')[:10]
        
        for idx, article in enumerate(articles):
            title = article.text.strip()
            link = article['href']
            time.sleep(0.5)
            try:
                article_res = requests.get(link, headers=headers)
                article_soup = BeautifulSoup(article_res.text, 'html.parser')
                content_area = article_soup.select_one('#dic_area')
                content = content_area.text.strip() if content_area else "본문 없음"
            except:
                content = "크롤링 실패"
            
            scraped_data.append({"id": idx+1, "title": title, "link": link, "content": content})
            print(f"[{idx+1}/10] 수집 완료")

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=4)
        return file_path
    except Exception as e:
        print(f"Crawler Error: {str(e)}")
        raise

def analyst_agent(**kwargs) -> str:
    """역할: Analyst - 데이터 분석 및 HTML 리포트 생성"""
    file_path = os.path.join(DATA_DIR, "raw_news.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html_lines = ["<h2>네이버 경제 뉴스 일일 요약</h2><ul>"]
    for item in data:
        sentences = [s.strip() + "." for s in item["content"].split(".") if len(s.strip()) > 10]
        summary = " ".join(sentences[:3]) if sentences else "요약 불가"
        
        html_lines.append(f"<li><h4>{item['title']}</h4>")
        html_lines.append(f"<p>{summary}</p>")
        html_lines.append(f"<a href='{item['link']}'>기사 보기</a></li>")
    
    html_lines.append("</ul>")
    return "".join(html_lines)

def messenger_agent(**kwargs):
    """
    역할: Messenger (Airflow Connection을 우회하여 직접 smtplib으로 발송)
    """
    ti = kwargs['ti']
    html_content = ti.xcom_pull(task_ids='analyst_task')
    
    # 이메일 설정
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "j.h.kim6844@gmail.com"
    smtp_password = "twsexivomyswgeca"  # 검증된 새로운 앱 비밀번호
    recipient = "jhk5055@nate.com"

    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = Header("[일간 리포트] 네이버 경제 뉴스 요약", 'utf-8')
    msg['From'] = smtp_user
    msg['To'] = recipient

    try:
        print(f"Connecting to {smtp_host}:{smtp_port} with STARTTLS...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print(f"Email successfully sent to {recipient}")
    except Exception as e:
        print(f"Messenger Error: {str(e)}")
        raise

with DAG(
    dag_id="naver_news_summary_mail_dag",
    schedule="0 9 * * *",
    start_date=pendulum.datetime(2023, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    default_args={"owner": "antigravity", "retries": 1},
    tags=["final_version"]
) as dag:
    
    crawler_task = PythonOperator(task_id="crawler_task", python_callable=crawler_agent)
    analyst_task = PythonOperator(task_id="analyst_task", python_callable=analyst_agent)
    
    messenger_task = PythonOperator(
        task_id="messenger_task", 
        python_callable=messenger_agent,
        provide_context=True
    )

    crawler_task >> analyst_task >> messenger_task

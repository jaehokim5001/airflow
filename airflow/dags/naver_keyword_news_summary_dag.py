"""
프로그램 명칭: 키워드 맞춤형 뉴스 요약 시스템 (Multi-Agent Team Project 2)
주요 기능 설명:
  - Crawler: data/keywords.txt의 검색어를 동적으로 읽어 네이버 뉴스 검색 상위 5개 수집
  - Analyst: 수집된 데이터를 키워드별 핵심 이슈 위주로 분석 및 마크다운 리포트 생성
  - Messenger: 분석된 리포트를 SMTP(STARTTLS)를 통해 지정된 메일로 전송
작업 목적 및 기대 결과:
  - 관심 키워드에 대한 최신 뉴스를 자동으로 모니터링하고 요약본을 수신
  - 검색어 변경 시에도 코드 수정 없이 유연하게 대응 가능
"""

import os
import json
import time
import requests
import smtplib
from bs4 import BeautifulSoup
from collections import Counter
from email.mime.text import MIMEText
from email.header import Header
import pendulum

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

# 데이터 저장 및 로드 경로 (컨테이너 기준)
DATA_DIR = "/opt/airflow/data"
KEYWORDS_FILE = os.path.join(DATA_DIR, "keywords.txt")
RAW_RESULTS_FILE = os.path.join(DATA_DIR, "raw_search_results.json")
FINAL_REPORT_FILE = os.path.join(DATA_DIR, "final_news_report.md")

def crawler_agent() -> str:
    """
    역할: Crawler
    기능: keywords.txt에서 키워드를 읽어 네이버 뉴스 검색결과 상위 5개를 수집
    반환값: 수집 완료된 JSON 파일 경로
    """
    # 1. 키워드 파일 읽기
    if not os.path.exists(KEYWORDS_FILE):
        print(f"Error: {KEYWORDS_FILE} 가 존재하지 않습니다.")
        return ""

    with open(KEYWORDS_FILE, "r", encoding="utf-8") as f:
        keywords = [line.strip() for line in f if line.strip()]

    if not keywords:
        print("Error: keywords.txt 에 등록된 키워드가 없습니다.")
        return ""

    all_results = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    # 2. 키워드별 순회 검색 수행
    for keyword in keywords:
        print(f"[{keyword}] 검색 데이터 수집 중...")
        search_url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
        
        try:
            time.sleep(1) # 차단 방지를 위한 지연
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 뉴스 검색 결과의 제목 요소 선택 (네이버 뉴스 검색결과 구조 기준)
            news_items = soup.select('.news_tit')[:5]
            keyword_data = []

            for item in news_items:
                title = item.text.strip()
                link = item['href']
                
                # 본문 내용을 긁어오기 위한 추가 시도 (뉴스 상세 페이지 대신 검색 결과의 요약 텍스트 수집)
                # 검색 결과 페이지의 .news_dsc .dsc_txt_wrap 클래스에 요약이 있음
                dsc_wrap = item.find_parent('div', class_='news_wrap').select_one('.news_dsc')
                snippet = dsc_wrap.text.strip() if dsc_wrap else "요약 정보 없음"

                keyword_data.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet
                })
            
            all_results[keyword] = keyword_data
            print(f"[{keyword}] {len(keyword_data)}개 기사 수집 완료")

        except Exception as e:
            print(f"[{keyword}] 검색 중 에러 발생 (건너뜀): {str(e)}")
            continue

    # 3. 수집 결과 JSON 저장
    with open(RAW_RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=4)
    
    return RAW_RESULTS_FILE

def analyst_agent(**kwargs) -> str:
    """
    역할: Analyst
    기능: 수집된 JSON 데이터를 분석하여 키워드별 핵심 이슈 요약 및 리포트 생성
    반환값: 메일 발송용 HTML 본문
    """
    if not os.path.exists(RAW_RESULTS_FILE):
        return "수집된 데이터가 없습니다."

    with open(RAW_RESULTS_FILE, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    md_lines = [f"# 키워드별 맞춤 뉴스 요약 리포트 ({pendulum.now().format('YYYY-MM-DD HH:mm')})\n"]
    html_lines = [f"<h2>키워드별 맞춤 뉴스 요약 리포트</h2><p>생성일시: {pendulum.now().format('YYYY-MM-DD HH:mm')}</p><hr>"]

    for keyword, news_list in all_data.items():
        md_lines.append(f"## 키워드: {keyword}")
        html_lines.append(f"<h3>검색어: <span style='color: #007bff;'>{keyword}</span></h3><ul>")

        if not news_list:
            md_lines.append("- 검색 결과가 없습니다.\n")
            html_lines.append("<li>검색 결과가 없습니다.</li>")
        else:
            for news in news_list:
                title = news["title"]
                link = news["link"]
                snippet = news["snippet"]

                # 마크다운 리포트 구성
                md_lines.append(f"### {title}")
                md_lines.append(f"- **요약**: {snippet}")
                md_lines.append(f"- **링크**: [기사 바로가기]({link})\n")

                # HTML 리포트 구성
                html_lines.append(f"<li><b>{title}</b><br>{snippet}<br><a href='{link}'>기사 바로가기</a></li><br>")

        html_lines.append("</ul><br>")

    # 4. 분석 결과 파일(MD) 저장
    with open(FINAL_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    
    print(f"리포트 생성 완료: {FINAL_REPORT_FILE}")
    return "".join(html_lines)

def messenger_agent(**kwargs):
    """
    역할: Messenger
    기능: Analyst로부터 전달받은 HTML 리포트를 이메일로 전송 (Verified smtplib 방식)
    """
    ti = kwargs['ti']
    html_content = ti.xcom_pull(task_ids='analyst_task')
    
    # 이메일 설정 (기존 검증된 정보 사용)
    smtp_host = "smtp.gmail.com"
    smtp_port = 587
    smtp_user = "j.h.kim6844@gmail.com"
    smtp_password = "twsexivomyswgeca" # 사용자 맞춤형 앱 비밀번호
    recipient = "jhk5055@nate.com"

    msg = MIMEText(html_content, 'html', 'utf-8')
    msg['Subject'] = Header(f"[맞춤 뉴스 리포트] 등록 키워드 분석 결과 ({pendulum.now().format('YYYY-MM-DD')})", 'utf-8')
    msg['From'] = smtp_user
    msg['To'] = recipient

    try:
        print(f"메일 발송 시도 ({recipient})...")
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            print(f"메일 전송 완료!")
    except Exception as e:
        print(f"메일 발송 중 에러 발생 (과정 무시): {str(e)}")
        # 메일 발송 실패가 전체 파이프라인 중단으로 이어지지 않도록 pass 가능 (여기서는 로그만 출력)


with DAG(
    dag_id="naver_keyword_news_summary_dag",
    schedule="0 9 * * *", # 매일 오전 9시
    start_date=pendulum.datetime(2023, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    default_args={
        "owner": "antigravity",
        "retries": 1,
    },
    tags=["project2", "dynamic", "multi-agent"]
) as dag:
    
    # 1. 검색어별 뉴스 수집 태스크
    crawler_task = PythonOperator(
        task_id="crawler_task",
        python_callable=crawler_agent
    )

    # 2. 결과 분석 및 리포트 작성 태스크
    analyst_task = PythonOperator(
        task_id="analyst_task",
        python_callable=analyst_agent
    )

    # 3. 메일 전송 태스크
    messenger_task = PythonOperator(
        task_id="messenger_task",
        python_callable=messenger_agent
    )

    # 워크플로우 정의
    crawler_task >> analyst_task >> messenger_task

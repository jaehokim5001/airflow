"""
프로그램 명칭: 네이버 경제 뉴스 상위 10개 요약 및 메일 발송 파이프라인
주요 기능 설명:
  - 크롤러(Crawler) 태스크: 네이버 경제 뉴스 상위에 노출된 기사 10개의 제목, 링크, 본문을 스크래핑
  - 분석가(Analyst) 태스크: 스크래핑된 기사의 기초 키워드를 분석하고 주요 3줄 요약 리포트를 마크다운 형식으로 생성
  - 메신저(Messenger) 태스크: 요약된 리포트 내용을 이메일을 통해 발송
작업 목적 및 기대 결과:
  - 분업화된 에이전트 역할(크롤링, 분석, 전송)을 기반으로 자동화 워크플로우(Airflow DAG) 구축
  - 시의성 있는 경제 뉴스 및 요약을 메일로 간편하게 파악
"""

import os
import json
import time
import requests
from bs4 import BeautifulSoup
from collections import Counter
import pendulum

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.smtp.operators.smtp import EmailOperator

# 데이터를 저장할 절대경로 지정 (보통 Airflow docker 컨테이너 내부의 /opt/airflow/data 이거나 컨테이너 CWD/data)
DATA_DIR = "/opt/airflow/data"

def crawler_agent() -> str:
    """
    역할: Crawler (안티그래비티 브라우저 컨셉 대체 스크립트)
    입력 파라미터: 없음
    반환값: 수집된 데이터가 저장된 json 파일의 경로 (문자열)
    """
    # 1. 저장 디렉토리가 없으면 생성 (작업 준비 단계)
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
    
    file_path = os.path.join(DATA_DIR, "raw_news.json")
    url = "https://news.naver.com/section/101"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    scraped_data = []

    try:
        # 2. 메인 페이지 크롤링을 통해 기사 링크 확보 시작
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # 네이버 뉴스 section 페이지의 주요 기사 제목들을 찾기 위한 셀렉터 (2024년 기준 헤드라인 클래스)
        # 여러 구조가 있을 수 있으므로 범용적으로 링크를 포함하는 주요 엘리먼트를 가져옵니다.
        articles = soup.select('.sa_text_title')[:10]
        
        # 3. 확보된 각 링크별 본문 접근 및 세부 크롤링 수행
        for idx, article in enumerate(articles):
            title = article.text.strip()
            link = article['href']
            
            # 본문을 가져오기 위해 상세 기사 페이지로 이동
            time.sleep(1) # 사이트 부하를 줄이기 위한 지연 시간 (time.sleep)
            
            try:
                article_res = requests.get(link, headers=headers)
                article_res.raise_for_status()
                article_soup = BeautifulSoup(article_res.text, 'html.parser')
                
                # 네이버 뉴스의 본문 영역. (기사 제공 매체에 따라 차이가 있을 수 있으나 일반적으로 dic_area 사용)
                content_area = article_soup.select_one('#dic_area')
                content = content_area.text.strip() if content_area else "본문 크롤링 실패 (구조 변경 또는 미지원 기사)"
            except Exception as e:
                content = f"본문 크롤링 중 에러 발생: {str(e)}"
            
            scraped_data.append({
                "id": idx + 1,
                "title": title,
                "link": link,
                "content": content
            })

            print(f"[{idx+1}/10] {title} 수집 완료")

    except Exception as e:
        print(f"Crawler 에러 발생: {str(e)}")
        raise e # 에러 발생 시 태스크가 실패하도록 raise

    # 4. JSON 파일로 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(scraped_data, f, ensure_ascii=False, indent=4)
    print(f"크롤링 완료. 데이터 저장 위치: {file_path}")

    return file_path

def analyst_agent(**kwargs) -> str:
    """
    역할: Analyst
    입력 파라미터: kwargs (XCom에서 파일 경로를 읽기 위해 airflow context 사용)
    반환값: 이메일 전송을 위해 구성된 HTML 형식의 리포트 본문 문자열
    """
    file_path = os.path.join(DATA_DIR, "raw_news.json")
    report_path = os.path.join(DATA_DIR, "summary_report.md")

    # 1. 크롤링된 데이터 파일 로드
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"{file_path} 파일이 존재하지 않습니다. 앞선 Crawler 작업을 점검해주세요.")

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    md_lines = ["# 네이버 경제 뉴스 일일 요약 리포트\n"]
    html_lines = ["<h2>네이버 경제 뉴스 일일 요약 리포트</h2><ul>"]

    # 2. 데이터를 순회하며 기사별 주요 문장(3줄 요약) 및 키워드 추출 분석 로직
    for item in data:
        title = item["title"]
        link = item["link"]
        content = item["content"]

        # 본문을 마침표('.')를 기준으로 나누어 3문장을 추출 (3줄 요약)
        sentences = [s.strip() + "." for s in content.split(".") if len(s.strip()) > 10]
        summary = " ".join(sentences[:3]) if sentences else "요약 불가 기사입니다."
        
        # 형태소 분석기 없이 띄어쓰기 기반으로 단순 단어 빈도 분석 (키워드 추출)
        words = [w for w in content.split() if len(w) >= 2]
        common_words = [word for word, count in Counter(words).most_common(3)]
        keywords = ", ".join(common_words)

        # 3. MD 및 HTML 형식으로 내용을 구조화
        md_lines.append(f"### [{item['id']}] {title}")
        md_lines.append(f"- **핵심 키워드**: {keywords}")
        md_lines.append(f"- **3줄 요약**: {summary}")
        md_lines.append(f"- **[기사 바로가기]({link})**\n")

        html_lines.append(f"<li>")
        html_lines.append(f"<h4>[{item['id']}] {title}</h4>")
        html_lines.append(f"<ul>")
        html_lines.append(f"<li><b>핵심 키워드</b>: {keywords}</li>")
        html_lines.append(f"<li><b>3줄 요약</b>: {summary}</li>")
        html_lines.append(f"<li><a href='{link}'>기사 바로가기</a></li>")
        html_lines.append(f"</ul></li>")

    html_lines.append("</ul>")
    
    # 4. 분석 결과를 마크다운 파일로 저장
    full_md = "\n".join(md_lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(full_md)
    print(f"분석 완료. 리포트 저장 위치: {report_path}")

    # Messenger 단계에서 사용할 이메일 HTML 본문 반환 (XCom으로 전달)
    return "".join(html_lines)


with DAG(
    dag_id="naver_news_summary_mail_dag",
    schedule="0 9 * * *", # 매일 오전 9시에 실행
    start_date=pendulum.datetime(2023, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    default_args={
        "owner": "antigravity",
        "retries": 1,
    },
    tags=["crawler", "analyst", "messenger"]
) as dag:
    
    # Task 1: 크롤링을 수행하는 Crawler Agent
    crawler_task = PythonOperator(
        task_id="crawler_task",
        python_callable=crawler_agent,
    )

    # Task 2: 요약 및 분석을 수행하는 Analyst Agent
    analyst_task = PythonOperator(
        task_id="analyst_task",
        python_callable=analyst_agent,
    )

    # Task 3: 메일을 전송하는 Messenger Agent
    # XCom을 통해 analyst_task 의 반환값(HTML)을 html_content로 받음
    messenger_task = EmailOperator(
        task_id="messenger_task",
        conn_id="conn_smtp_gmail",
        to="jhk5055@nate.com",
        subject="[일간 리포트] 네이버 경제 뉴스 상위 10선 핵심 요약",
        html_content="{{ task_instance.xcom_pull(task_ids='analyst_task') }}"
    )

    # 태스크 간의 의존성(Workflow) 명확한 시각화 밑 설정
    crawler_task >> analyst_task >> messenger_task

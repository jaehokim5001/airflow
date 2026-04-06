import requests
from bs4 import BeautifulSoup
import json

def debug_search(keyword):
    print(f"--- Debugging Keyword: {keyword} ---")
    url = f"https://search.naver.com/search.naver?where=news&query={keyword}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 1. 기존 셀렉터 테스트
        news_items = soup.select(".news_tit")
        print(f"Count of '.news_tit': {len(news_items)}")
        
        # 2. 보조 셀렉터 테스트 (클래식 구조)
        if len(news_items) == 0:
            print("Trying fallback selectors...")
            alt_items = soup.select("a.news_tit") or soup.select(".news_area a")
            print(f"Count of fallback '.news_area a': {len(alt_items)}")
            
            # 3. HTML 힌트 확인 (봇 차단 여부 등)
            if "captcha" in response.text.lower() or "spam" in response.text.lower():
                print("CAPTCHA or Bot block detected!")
            else:
                # 첫 10개 태그 이름만 출력하여 구조 파악
                tags = [tag.name for tag in soup.find_all(True)[:10]]
                print(f"First 10 tags: {tags}")
                
        else:
            for i, item in enumerate(news_items[:3]):
                print(f"[{i+1}] {item.text[:30]}...")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    debug_search("미국증시전망")

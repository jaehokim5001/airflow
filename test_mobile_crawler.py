import requests
from bs4 import BeautifulSoup

url = "https://m.search.naver.com/search.naver?where=m_news&query=%EB%AF%B8%EA%B5%AD%EC%A6%9D%EC%8B%9C%EC%A0%84%EB%A7%9D"
headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
}

res = requests.get(url, headers=headers)
print(f"Status: {res.status_code}")

soup = BeautifulSoup(res.text, "html.parser")

# 기존 셀렉터 테스트
items = soup.select(".news_tit")
print(f"Count of .news_tit: {len(items)}")

if not items:
    print("Could not find .news_tit. Dumping common links to find the correct selector...")
    # 네이버 뉴스 모바일은 보통 .news_tit 대신 다른 클래스(.tit, .title 등)를 사용할 수 있음
    for div in soup.select('.news_wrap')[:5]:
        tit = div.select_one('.tit, .news_tit, .title')
        dsc = div.select_one('.dsc, .api_txt_lines, .news_dsc')
        print("---")
        print(f"Title: {tit.text.strip() if tit else 'None'}")
        print(f"Desc: {dsc.text.strip() if dsc else 'None'}")
        
    print("\nOr dumping generic anchor tags with text:")
    for a in soup.find_all('a')[:30]:
        cls = a.get('class')
        txt = a.text.strip()
        if txt and len(txt) > 10:
            print(f"Class: {cls}, Text: {txt[:40]}")

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import os

DB_FILE = "lotto_data.db"

def get_lotto_numbers(draw_no):
    url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            print(f"[{draw_no}회차] 요청 실패: {res.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"[{draw_no}회차] 요청 예외: {e}")
        return None

    soup = BeautifulSoup(res.text, 'html.parser')
    numbers = soup.select('div.num.win p span')

    try:
        main_numbers = [int(n.text) for n in numbers[:6]]
        bonus = int(soup.select_one('div.num.bonus p span').text)
        return main_numbers + [bonus]
    except (ValueError, AttributeError) as e:
        print(f"[{draw_no}회차] 파싱 실패: {e}")
        return None

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS lotto (
            draw_no INTEGER PRIMARY KEY,
            num1 INTEGER,
            num2 INTEGER,
            num3 INTEGER,
            num4 INTEGER,
            num5 INTEGER,
            num6 INTEGER,
            bonus INTEGER
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(draw_no, numbers):
    if len(numbers) != 7:
        print(f"[{draw_no}회차] 저장 실패 - 숫자 개수 오류: {numbers}")
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO lotto (
                draw_no, num1, num2, num3, num4, num5, num6, bonus
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (draw_no, *numbers))
        conn.commit()
        print(f"[{draw_no}회차] 저장 완료: {numbers}")
    except sqlite3.IntegrityError:
        print(f"[{draw_no}회차] 이미 저장됨")
    conn.close()

def get_latest_draw_number_from_site():
    draw_no = 1100
    while True:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url)
        if res.status_code != 200 or '"returnValue":"fail"' in res.text:
            return draw_no - 1  # 직전 회차가 마지막 유효 회차
        draw_no += 1

def crawl_lotto_data(start=1000, end=None):
    if end is None:
        end = get_latest_draw_number_from_site()
    print(f"📥 {start}회부터 {end}회까지 크롤링합니다")
    for draw_no in range(start, end + 1):
        numbers = get_lotto_numbers(draw_no)
        if numbers:
            save_to_db(draw_no, numbers)
        time.sleep(0.2)

if __name__ == "__main__":
    print("로또 번호 크롤링 시작")
    init_db()
    crawl_lotto_data(start=1000)
    print("크롤링 완료")

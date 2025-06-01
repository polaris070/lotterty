import requests
from bs4 import BeautifulSoup
import sqlite3

DB_FILE = "lotto_data.db"

def get_lotto_numbers(draw_no):
    url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    res = requests.get(url)
    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "html.parser")
    numbers = soup.select("div.num.win p span")
    try:
        main_numbers = [int(n.text) for n in numbers[:6]]
        bonus = int(soup.select_one("div.num.bonus p span").text)
        return main_numbers + [bonus]
    except:
        return None

def init_db():
    """테이블이 없다면 생성"""
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

def get_latest_draw_no():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT MAX(draw_no) FROM lotto")
    result = cur.fetchone()
    conn.close()
    return result[0] if result and result[0] else 0

def save_to_db(draw_no, numbers):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO lotto (
            draw_no, num1, num2, num3, num4, num5, num6, bonus
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (draw_no, *numbers))
    conn.commit()
    conn.close()

def update_latest_lotto():
    init_db()  # ← 테이블을 먼저 생성해주는 부분!
    latest_no = get_latest_draw_no()
    next_no = latest_no + 1
    numbers = get_lotto_numbers(next_no)
    if numbers:
        save_to_db(next_no, numbers)
        print(f"[{next_no}회차] 업데이트 완료: {numbers}")
    else:
        print(f"[{next_no}회차] 아직 발표되지 않았거나 접근 실패")

if __name__ == "__main__":
    update_latest_lotto()

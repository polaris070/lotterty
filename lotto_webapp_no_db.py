import requests
import sqlite3
from bs4 import BeautifulSoup
import streamlit as st
import random
from collections import Counter
import plotly.graph_objects as go
from datetime import datetime, timedelta

DB_FILE = "lotto_cache.db"

# ✅ DB 초기화
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value INTEGER,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

# ✅ 최신 회차 캐시에 저장
def save_latest_draw_no(latest):
    now = datetime.now().isoformat()
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO cache (key, value, updated_at) VALUES (?, ?, ?)", 
                ('latest_draw_no', latest, now))
    conn.commit()
    conn.close()

# ✅ 캐시 불러오기
def load_latest_draw_no():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT value, updated_at FROM cache WHERE key = ?", ('latest_draw_no',))
    row = cur.fetchone()
    conn.close()
    if row:
        value, updated_at = row
        updated_at_dt = datetime.fromisoformat(updated_at) if updated_at else None
        return value, updated_at_dt
    else:
        return 0, None

# ✅ API 이진 탐색
def get_latest_draw_no_api():
    low = 1
    high = 1200
    latest = 1
    while low <= high:
        mid = (low + high) // 2
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={mid}"
        try:
            res = requests.get(url, timeout=1.5)
            if '"returnValue":"fail"' in res.text:
                high = mid - 1
            else:
                latest = mid
                low = mid + 1
        except:
            break
    return latest

# ✅ 단일 회차 번호 가져오기
def get_lotto_numbers(draw_no):
    url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    try:
        res = requests.get(url, timeout=1.5)
        soup = BeautifulSoup(res.text, "html.parser")
        return [int(n.text) for n in soup.select("div.num.win p span")[:6]]
    except:
        return []

# ✅ 범위 내 번호 수집
def collect_numbers_by_range(start, end):
    numbers = []
    for i in range(end, start - 1, -1):
        nums = get_lotto_numbers(i)
        if nums:
            numbers.extend(nums)
    return numbers

# ✅ 추천 번호 생성
def generate_recommendations(number_pool, combo_count=5):
    recommendations = []
    tries = 0
    while len(recommendations) < combo_count and tries < 500:
        combo = sorted(random.sample(number_pool, 6))
        if is_valid_combo(combo):
            recommendations.append(combo)
        tries += 1
    return recommendations

# ✅ 필터 조건
def is_valid_combo(combo):
    even = sum(1 for n in combo if n % 2 == 0)
    total = sum(combo)
    consecutive = sum(1 for i in range(5) if combo[i+1] - combo[i] == 1)
    return (2 <= even <= 4) and (100 <= total <= 180) and (consecutive <= 2)

# ✅ Streamlit UI
init_db()
st.set_page_config(page_title="로또 추천 (자동 최신 회차)", page_icon="🎰")
st.title("🎰 Lotto Number Recommender (Auto Update Latest Draw)")

# ✅ 최신 회차 자동 갱신 로직
latest_cached, updated_at = load_latest_draw_no()

need_update = False
if updated_at is None:
    need_update = True
elif datetime.now() - updated_at > timedelta(days=7):
    need_update = True

if need_update:
    with st.spinner("Auto-updating latest draw number..."):
        latest = get_latest_draw_no_api()
        save_latest_draw_no(latest)
    st.success(f"Latest draw number auto-updated: **{latest}**")
    latest_cached = latest
else:
    st.info(f"Current cached latest draw number: **{latest_cached}** (updated at {updated_at.strftime('%Y-%m-%d')})")

# ✅ 수동 최신 회차 갱신 버튼
if st.button("🔄 Manually refresh latest draw number"):
    with st.spinner("Refreshing via API..."):
        latest = get_latest_draw_no_api()
        save_latest_draw_no(latest)
    st.success(f"Latest draw number refreshed: **{latest}**")
    latest_cached = latest

# ✅ 사용자 입력
start = st.number_input("Start draw number", 1, latest_cached - 1, latest_cached - 20)
end = st.number_input("End draw number", start, latest_cached, latest_cached)
count = st.slider("Number of combinations to recommend", 1, 10, 5)

if st.button("🔮 Generate recommendations"):
    with st.spinner("Collecting lotto data..."):
        collected = collect_numbers_by_range(start, end)
        freq = Counter(collected)
        top_items = freq.most_common(20)
        top_nums = [n for n, _ in top_items]

        st.subheader("📊 Top 20 Most Frequent Numbers")
        for i, (num, cnt) in enumerate(top_items, 1):
            st.write(f"**TOP {i}: Number {num} ({cnt} times)**")

        fig = go.Figure([go.Bar(x=[str(n) for n, _ in top_items], y=[c for _, c in top_items])])
        fig.update_layout(
            title="Frequency of Winning Numbers (Selected Rounds)",
            xaxis_title="Lotto Number",
            yaxis_title="Occurrences",
            font=dict(family="Arial, sans-serif", size=14)
        )
        st.plotly_chart(fig, use_container_width=True)

        combos = generate_recommendations(top_nums, count)
    st.success("✅ Recommended Lotto Combinations:")
    for i, combo in enumerate(combos, 1):
        st.write(f"**Combination {i}:** {combo}")

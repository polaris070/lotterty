import requests
from bs4 import BeautifulSoup
import streamlit as st
import random
from collections import Counter
import plotly.graph_objects as go

# ✅ 최신 회차 번호 가져오기
def get_latest_draw_no_fast():
    try:
        url = "https://www.dhlottery.co.kr/gameResult.do?method=byWin"
        res = requests.get(url, timeout=2)
        soup = BeautifulSoup(res.text, 'html.parser')
        title = soup.select_one('div.win_result h4 strong').text
        return int(title.replace("회", "").strip())
    except:
        return 1100

# ✅ 단일 회차 번호 가져오기
def get_lotto_numbers(draw_no):
    url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    try:
        res = requests.get(url, timeout=2)
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

# ✅ 조건 필터링된 추천 조합 생성
def generate_recommendations(number_pool, combo_count=5):
    recommendations = []
    tries = 0
    while len(recommendations) < combo_count and tries < 500:
        combo = sorted(random.sample(number_pool, 6))
        if is_valid_combo(combo):
            recommendations.append(combo)
        tries += 1
    return recommendations

# ✅ 필터 조건 함수
def is_valid_combo(combo):
    even = sum(1 for n in combo if n % 2 == 0)
    total = sum(combo)
    consecutive = sum(1 for i in range(5) if combo[i+1] - combo[i] == 1)
    return (2 <= even <= 4) and (100 <= total <= 180) and (consecutive <= 2)

# ✅ Streamlit UI
st.set_page_config(page_title="로또 추천", page_icon="🎰")
st.title("🎰 로또 번호 추천기 (Plotly 시각화)")

with st.spinner("최신 회차 확인 중..."):
    latest = get_latest_draw_no_fast()
st.success(f"현재 최신 회차는 **{latest}회차**입니다.")

start = st.number_input("시작 회차", 1, latest - 1, latest - 20)
end = st.number_input("마지막 회차", start, latest, latest)
count = st.slider("추천 조합 개수", 1, 10, 5)

if st.button("🔮 추천 번호 생성"):
    with st.spinner("로또 데이터 수집 중..."):
        collected = collect_numbers_by_range(start, end)
        freq = Counter(collected)
        top_items = freq.most_common(20)
        top_nums = [n for n, _ in top_items]

        st.subheader("📊 출현 빈도 상위 20개 번호 (TOP 순위)")
        for i, (num, cnt) in enumerate(top_items, 1):
            st.write(f"**TOP {i}: {num}번 ({cnt}회 출현)**")

        # ✅ Plotly 시각화
        labels = [str(n) for n, _ in top_items]
        values = [c for _, c in top_items]

        fig = go.Figure([go.Bar(x=labels, y=values)])
        fig.update_layout(
            title="출현 빈도 (최근 선택 회차 기준)",
            xaxis_title="로또 번호",
            yaxis_title="등장 횟수",
            font=dict(family="Nanum Gothic, Arial", size=14)
        )
        st.plotly_chart(fig)

        # ✅ 추천 번호 조합 출력
        combos = generate_recommendations(top_nums, count)
    st.success("✅ 추천 번호 조합:")
    for i, combo in enumerate(combos, 1):
        st.write(f"**{i}번 조합:** {combo}")

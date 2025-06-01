import requests
from bs4 import BeautifulSoup
import streamlit as st
import numpy as np
import random
from collections import Counter

# --- 최신 회차 번호 자동 감지 ---
def get_latest_draw_no():
    draw_no = 1100
    while True:
        url = f"https://www.dhlottery.co.kr/common.do?method=getLottoNumber&drwNo={draw_no}"
        res = requests.get(url)
        if res.status_code != 200 or '"returnValue":"fail"' in res.text:
            return draw_no - 1
        draw_no += 1

# --- 회차별 로또 번호 가져오기 ---
def get_lotto_numbers(draw_no):
    url = f"https://www.dhlottery.co.kr/gameResult.do?method=byWin&drwNo={draw_no}"
    try:
        res = requests.get(url, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        numbers = [int(n.text) for n in soup.select("div.num.win p span")[:6]]
        return numbers
    except:
        return []

# --- 사용자 범위 내 번호 수집 ---
def collect_numbers_by_range(start, end):
    all_numbers = []
    for i in range(end, start - 1, -1):
        nums = get_lotto_numbers(i)
        if nums:
            all_numbers.extend(nums)
    return all_numbers

# --- 추천 조합 생성 ---
def generate_recommendations(number_pool, combo_count=5):
    recommendations = []
    tries = 0
    while len(recommendations) < combo_count and tries < 500:
        combo = sorted(random.sample(number_pool, 6))
        if is_valid_combo(combo):
            recommendations.append(combo)
        tries += 1
    return recommendations

# --- 조건 필터링 ---
def is_valid_combo(combo):
    even = sum(1 for n in combo if n % 2 == 0)
    total = sum(combo)
    if not (2 <= even <= 4):
        return False
    if not (100 <= total <= 180):
        return False
    if sum(1 for i in range(5) if combo[i + 1] - combo[i] == 1) > 2:
        return False
    return True

# --- Streamlit UI ---
st.set_page_config(page_title="로또 추천 (범위 설정)", page_icon="🎯")
st.title("🎯 로또 번호 추천 (원하는 회차 범위로 분석)")

with st.spinner("최신 회차 확인 중..."):
    latest_draw = get_latest_draw_no()

# 사용자 설정
st.markdown("📌 원하는 회차 범위를 지정해주세요.")
col1, col2 = st.columns(2)
with col1:
    start = st.number_input("시작 회차", min_value=1, max_value=latest_draw - 1, value=latest_draw - 20)
with col2:
    end = st.number_input("마지막 회차", min_value=start, max_value=latest_draw, value=latest_draw)

combo_count = st.slider("🔁 추천 조합 개수", 1, 10, 5)

# 분석 시작
if st.button("번호 추천 시작"):
    with st.spinner("로또 데이터 수집 및 분석 중..."):
        collected = collect_numbers_by_range(start, end)
        freq = Counter(collected)
        top_numbers = [num for num, _ in freq.most_common(20)]

        st.subheader("📊 선택한 회차 내 자주 나온 번호")
        st.write(sorted(top_numbers))

        recommendations = generate_recommendations(top_numbers, combo_count)

    st.success("✅ 추천 번호 생성 완료!")
    for i, combo in enumerate(recommendations, 1):
        st.write(f"**{i}번 조합:** {combo}")

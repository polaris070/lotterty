import streamlit as st
import sqlite3
import numpy as np
import random
from sklearn.ensemble import RandomForestClassifier

DB_FILE = "lotto_data.db"

# --- 데이터 로딩 및 전처리 ---
def load_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto ORDER BY draw_no")
    rows = cur.fetchall()
    conn.close()
    return rows

def to_vector(numbers):
    vec = [0] * 45
    for n in numbers:
        vec[n - 1] = 1
    return vec

def prepare_dataset(rows):
    X, y = [], []
    for i in range(1, len(rows)):
        X.append(to_vector(rows[i - 1][1:]))
        y.append(to_vector(rows[i][1:]))
    return np.array(X), np.array(y)

def count_consecutive(combo):
    return sum(1 for i in range(5) if combo[i + 1] - combo[i] == 1)

def is_valid_combo(combo):
    even = sum(1 for n in combo if n % 2 == 0)
    total = sum(combo)
    ranges = [0, 0, 0]
    for n in combo:
        if n <= 15:
            ranges[0] += 1
        elif n <= 30:
            ranges[1] += 1
        else:
            ranges[2] += 1
    if not (2 <= even <= 4): return False
    if not (100 <= total <= 180): return False
    if count_consecutive(combo) > 2: return False
    if max(ranges) > 4: return False
    return True

def generate_combinations(probabilities, top_n=20, count=5):
    top_indices = np.argsort(probabilities)[-top_n:]
    pool = [i + 1 for i in top_indices]
    combinations = []
    tries = 0
    while len(combinations) < count and tries < 1000:
        combo = sorted(random.sample(pool, 6))
        if is_valid_combo(combo):
            combinations.append([int(n) for n in combo])
        tries += 1
    return combinations

# --- Streamlit UI 시작 ---
st.set_page_config(page_title="로또 추천 시스템", page_icon="🎯")
st.title("🎯 머신러닝 기반 로또 번호 추천")
st.markdown("💡 최신 회차를 기반으로 확률 높은 번호 조합을 추천합니다.\n조건 필터링(짝/홀, 합계, 구간 등)도 포함되어 있습니다.")

with st.spinner("모델 학습 및 예측 중..."):
    rows = load_data()
    X, y = prepare_dataset(rows)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)

    latest = rows[-1][1:]
    input_vec = np.array([to_vector(latest)])
    probs = model.predict_proba(input_vec)
    output_probs = [p[0][1] for p in probs]

    # 사용자 옵션
    top_n = st.slider("🎯 후보 Pool 상위 개수 (Top N)", 10, 30, 20)
    count = st.slider("🔁 추천 조합 개수", 1, 10, 5)

    results = generate_combinations(output_probs, top_n=top_n, count=count)

st.success("✅ 추천 번호 생성 완료!")
for i, combo in enumerate(results, 1):
    st.write(f"**{i}번 조합:** {combo}")
    
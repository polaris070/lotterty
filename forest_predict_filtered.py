import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import random

DB_FILE = "lotto_data.db"

def load_data():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT draw_no, num1, num2, num3, num4, num5, num6 FROM lotto ORDER BY draw_no")
    rows = cur.fetchall()
    conn.close()
    return rows

def to_feature_vector(numbers):
    vec = [0] * 45
    for num in numbers:
        vec[num - 1] = 1
    return vec

def prepare_dataset(rows):
    X, y = [], []
    for i in range(1, len(rows)):
        X.append(to_feature_vector(rows[i - 1][1:]))
        y.append(to_feature_vector(rows[i][1:]))
    return np.array(X), np.array(y)

def train_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predict_probabilities(model, latest_numbers):
    input_vec = np.array([to_feature_vector(latest_numbers)])
    probs = model.predict_proba(input_vec)
    output_probs = [p[0][1] for p in probs]  # 1일 확률
    return output_probs

def generate_combinations(probabilities, top_n=20, count=10):
    top_indices = np.argsort(probabilities)[-top_n:]
    pool = [i + 1 for i in top_indices]
    combinations = []
    tries = 0
    while len(combinations) < count and tries < 1000:
        combo = sorted(random.sample(pool, 6))
        if is_valid_combo(combo):
            combinations.append(combo)
        tries += 1
    return combinations

# 🎯 조건 필터링 함수
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

    # 조건: 짝수 2~4개, 총합 100~180, 연속번호 2개 이하, 구간 치우침 방지
    if not (2 <= even <= 4):
        return False
    if not (100 <= total <= 180):
        return False
    if count_consecutive(combo) > 2:
        return False
    if max(ranges) > 4:
        return False
    return True

def count_consecutive(combo):
    return sum(1 for i in range(5) if combo[i+1] - combo[i] == 1)

# 🔽 실행
if __name__ == "__main__":
    rows = load_data()
    X, y = prepare_dataset(rows)
    model = train_model(X, y)

    latest_numbers = rows[-1][1:]
    probs = predict_probabilities(model, latest_numbers)

    print("🔮 추천 번호 조합 (조건 필터링 적용):")
    results = generate_combinations(probs, top_n=20, count=5)
    for i, combo in enumerate(results, 1):
        int_combo = [int(n) for n in combo]
        print(f"{i}번: {int_combo}")

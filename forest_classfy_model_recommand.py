import sqlite3
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

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
    X = []
    y = []
    for i in range(1, len(rows)):
        prev_numbers = to_feature_vector(rows[i - 1][1:])
        curr_numbers = to_feature_vector(rows[i][1:])
        X.append(prev_numbers)
        y.append(curr_numbers)
    return np.array(X), np.array(y)

def train_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model

def predict_next(model, latest_numbers):
    input_vec = np.array([to_feature_vector(latest_numbers)])
    probs = model.predict_proba(input_vec)  # list of 45 elements (1 for each output)

    # 각 번호(1~45)의 '출현할 확률'만 추출
    # probs[i][0][1] 은 i번째 번호(1~45)의 1일 확률
    output_probs = [p[0][1] for p in probs]  # 45개의 확률값

    # 확률이 높은 상위 6개 번호 추출
    top_indices = np.argsort(output_probs)[-6:]  # index = 번호 - 1
    predicted_numbers = sorted([i + 1 for i in top_indices])
    return predicted_numbers

if __name__ == "__main__":
    rows = load_data()
    X, y = prepare_dataset(rows)
    model = train_model(X, y)

    latest_numbers = rows[-1][1:]  # 가장 최근 회차의 번호
    predicted = predict_next(model, latest_numbers)
    

    print(f"🔮 최신 회차 기준 예측 번호 조합: {[int(n) for n in predicted]}")


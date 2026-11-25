# 6단계 독립 재계산 — 최근대출일의 월별 분포 (N1~N119, 보조 값 S)
# 읽는 것: 원자료, 데이터코드북.docx, 이 폴더 계산명세.md·승인기록.md. 분석/ 결과는 읽지 않는다.
# 실행: 프로젝트 폴더에서  .venv/bin/python "작업/20261125_월별_최근대출일/검증/재계산.py"
# 난수 없음, 시드 없음.
import csv
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_월별_최근대출일/검증/"
DROP = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 삭제


def load(keep_na):
    df = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=keep_na)
    return df.drop(columns=DROP)


df = load(True)
raw = df["최근대출일"].fillna("").astype(str).str.strip()
blank = raw == ""

# 결측 판정이 pandas 기본 NA 표기("NA", "null" 등)에 좌우되지 않는지 확인 (같으면 모호 없음)
raw2 = load(False)["최근대출일"].astype(str).str.strip()
assert ((raw2 == "") == blank).all(), "pandas NA 표기 처리에 따라 빈칸 수가 달라진다 — 계산명세 모호"

# 날짜 변환: 실패 값이 하나라도 있으면 멈춤 (strptime이 예외를 낸다)
dates = [datetime.strptime(v, "%Y-%m-%d").date() for v in raw[~blank]]
assert all(date(2023, 1, 1) <= d <= date(2025, 12, 30) for d in dates), "대상 기간 밖 날짜"

# 각주 ② 확인용: 빈칸 행 대출횟수가 모두 0인지 (핵심 수치 아님)
loan0 = (df.loc[blank, "대출횟수"].astype(str).str.strip() == "0").all()

months = [f"{y:04d}-{m:02d}" for y in (2023, 2024, 2025) for m in range(1, 13)]
count = {m: 0 for m in months}
for d in dates:
    count[f"{d.year:04d}-{d.month:02d}"] += 1  # 36개 달 밖이면 KeyError로 멈춤

N1, N2, N3 = len(df), int((~blank).sum()), int(blank.sum())


def pct(k):  # 정확한 Decimal 나눗셈 후 소수 둘째 자리 사사오입
    return str((Decimal(k * 100) / Decimal(N2)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


order = sorted(months, key=lambda m: (-count[m], m))
rank = {m: i + 1 for i, m in enumerate(order)}

rows = [("N1", "전체 권수", N1), ("N2", "최근대출일 있는 권수", N2), ("N3", "최근대출일 빈칸 권수", N3)]
for i, m in enumerate(months):
    rows.append((f"N{i + 4}", f"{m} 권수", count[m]))
for i, m in enumerate(months):
    rows.append((f"N{i + 40}", f"{m} 비율(%)", pct(count[m])))
for i, m in enumerate(months):
    rows.append((f"N{i + 76}", f"{m} 순위", rank[m]))
y = {yr: sum(count[m] for m in months if m[:4] == yr) for yr in ("2023", "2024", "2025")}
total = sum(count.values())
rows += [
    ("N112", "2023년 합", y["2023"]),
    ("N113", "2024년 합", y["2024"]),
    ("N114", "2025년 합", y["2025"]),
    ("N115", "1위 달", order[0]),
    ("N116", "1위 달 권수", count[order[0]]),
    ("N117", "36위 달", order[-1]),
    ("N118", "36위 달 권수", count[order[-1]]),
    ("N119", "36개 달 권수 합", total),
]

# 멈춤 조건
assert total == N2 and N2 + N3 == N1 and sum(y.values()) == total
assert sorted(rank.values()) == list(range(1, 37))
assert len(rows) == 119

with open(OUT + "검증값.csv", "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)

S = sum(Decimal(pct(count[m])) for m in months)
second = order[1]
with open(OUT + "보조값.txt", "w", encoding="utf-8") as f:
    f.write(f"S (N40~N75 반올림 문자열을 Decimal로 합) = {S.quantize(Decimal('0.01'))}\n")
    f.write(f"S == 100.00: {S == Decimal('100.00')}\n")
    f.write(f"빈칸 행 대출횟수 모두 0 (각주 ② assert): {bool(loan0)}\n")
    f.write(f"연도별 합 2023 < 2024 < 2025: {y['2023'] < y['2024'] < y['2025']}\n")
    f.write(f"순위 2위 달 (꼭 넣을 문장 2): {second}, {count[second]}권\n")
    f.write(f"입력 행 수: {N1}, 시드: 없음\n")
print(open(OUT + "보조값.txt", encoding="utf-8").read())

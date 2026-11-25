# 5단계 분석 — 최근대출일의 월별 분포 (계산명세.md 그대로)
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_월별_최근대출일/분석/분석.py
import csv
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

import pandas as pd
from matplotlib import font_manager, pyplot as plt

OUT = "작업/20261125_월별_최근대출일/분석/"
DROP = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 삭제 7열

# 2절 입력: 모든 열 문자열, 읽은 직후 삭제 7열 drop
df = pd.read_csv("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", dtype=str)
df = df.drop(columns=DROP)

# 2절 빈칸: NaN도 빈 문자열, 앞뒤 공백 제거 후 빈 문자열이면 빈칸
v = df["최근대출일"].fillna("").str.strip()
blank = v == ""
N1 = len(df)
N2 = int((~blank).sum())
N3 = int(blank.sum())

# 2절 날짜 변환: 실패하면 멈춤 (strptime이 예외를 낸다)
dates = [datetime.strptime(s, "%Y-%m-%d").date() for s in v[~blank]]
# 2절 기간 확인
out_of_range = [d for d in dates if not (date(2023, 1, 1) <= d <= date(2025, 12, 30))]
assert not out_of_range, f"기간 밖 날짜 {len(out_of_range)}건 — 멈춤"

# 표 1 각주 ② 문구 확인: 빈칸 행의 대출횟수가 모두 0
assert (df.loc[blank, "대출횟수"].str.strip() == "0").all(), "빈칸 행 중 대출횟수 0이 아닌 행 있음 — 각주 ② 문구 빼고 보고"

# 연-월, 36개 달
ym = [f"{d.year:04d}-{d.month:02d}" for d in dates]
MONTHS = [f"{y:04d}-{m:02d}" for y in (2023, 2024, 2025) for m in range(1, 13)]
count = {m: 0 for m in MONTHS}
for k in ym:
    count[k] += 1  # 36개 달 밖 값이면 KeyError로 멈춤

def pct(n):  # 6절: 정확한 분수 → 소수 둘째 자리 ROUND_HALF_UP
    f = Fraction(n * 100, N2)
    return (Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
# ponytail: Decimal 나눗셈은 기본 28자리 정밀도라 셋째 자리 사사오입에 충분

ratio = {m: pct(count[m]) for m in MONTHS}
order = sorted(MONTHS, key=lambda m: (-count[m], m))  # 2절 순위: 권수 내림차순, 동점은 이른 달 먼저
rank = {m: i + 1 for i, m in enumerate(order)}

year_sum = {y: sum(count[m] for m in MONTHS if m[:4] == y) for y in ("2023", "2024", "2025")}
N119 = sum(count.values())

# 멈춤 조건
assert N119 == N2, "N119 != N2"
assert N2 + N3 == N1, "N2 + N3 != N1"
assert sum(year_sum.values()) == N119, "연도별 합 != N119"
assert sorted(rank.values()) == list(range(1, 37)), "순위 1~36 아님"
assert year_sum["2023"] < year_sum["2024"] < year_sum["2025"], "N112 < N113 < N114 아님 — 꼭 넣을 문장 1 멈춤"

# 핵심수치.csv
rows = [("N1", "전체 권수", N1), ("N2", "최근대출일 있는 권수", N2), ("N3", "최근대출일 빈칸 권수", N3)]
for i, m in enumerate(MONTHS):
    rows.append((f"N{i + 4}", f"{m} 권수", count[m]))
for i, m in enumerate(MONTHS):
    rows.append((f"N{i + 40}", f"{m} 비율(%)", f"{ratio[m]:.2f}"))
for i, m in enumerate(MONTHS):
    rows.append((f"N{i + 76}", f"{m} 순위", rank[m]))
rows += [
    ("N112", "2023년 합", year_sum["2023"]),
    ("N113", "2024년 합", year_sum["2024"]),
    ("N114", "2025년 합", year_sum["2025"]),
    ("N115", "1위 달", order[0]),
    ("N116", "1위 달 권수", count[order[0]]),
    ("N117", "36위 달", order[-1]),
    ("N118", "36위 달 권수", count[order[-1]]),
    ("N119", "36개 달 권수 합", N119),
]
assert len(rows) == 119
with open(OUT + "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)

# 보조 값 S: 반올림한 비율 문자열을 Decimal로 더함
S = sum((Decimal(f"{ratio[m]:.2f}") for m in MONTHS), Decimal("0.00"))
with open(OUT + "보조값.txt", "w", encoding="utf-8") as f:
    f.write(f"S (N40~N75 반올림 비율 36개의 Decimal 합) = {S:.2f}\n")
    f.write(f"표 1 각주 ⑤ 필요 = {'예' if S != Decimal('100.00') else '아니오'}\n")
    f.write(f"순위 2위 달 = {order[1]} ({count[order[1]]}권)\n")

# 표 1: 순위 1 → 36
with open(OUT + "표1_월별권수_내림차순.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["순위", "연-월", "권수", "비율(%)", "주석"])
    for m in order:
        w.writerow([rank[m], m, count[m], f"{ratio[m]:.2f}", "30일까지" if m == "2025-12" else ""])

# 그림 1 (공통규칙 10 폰트 등록)
FONT = "NanumGothic.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(14, 6))
heights = [count[m] for m in MONTHS]
ax.bar(MONTHS, heights, color="#4C72B0")
ax.text(35, count["2025-12"], "30일까지", ha="center", va="bottom")
ax.set_ylim(0, max(heights) * 1.08)
ax.set_title("최근대출일이 그 달인 책의 권수 (2023-01~2025-12)")
ax.set_xlabel("최근대출일 연-월")
ax.set_ylabel("책의 권수(권)")
ax.tick_params(axis="x", rotation=90)
fig.text(0.5, 0.01, "책마다 마지막 대출일 하나로 센 값이며, 그 달의 대출 건수가 아니다. 2025-12는 30일까지.", ha="center")
fig.tight_layout(rect=(0, 0.04, 1, 1))
fig.savefig(OUT + "그림1_월별_최근대출일_권수.png", dpi=150)

print(f"N1={N1} N2={N2} N3={N3} 연도별 합={year_sum} 1위={order[0]}({count[order[0]]}) "
      f"2위={order[1]}({count[order[1]]}) 36위={order[-1]}({count[order[-1]]}) S={S:.2f}")

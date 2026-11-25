# 질문 5 (다시 하기) — 무대출 장서의 구입가격 비중. 계산명세.md 2·6·7절대로.
# 프로젝트 폴더에서 실행: .venv/bin/python 작업/20261125_무대출_구입비비중/분석/분석.py
import csv
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

import pandas as pd
from matplotlib import font_manager, pyplot as plt

OUT = "작업/20261125_무대출_구입비비중/분석/"
COLS = ["자료ID", "구입일", "대출횟수", "최근대출일", "구입가격"]  # 계산명세 3절


def stop(msg):
    sys.exit(f"멈춤: {msg}")


df = pd.read_csv("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig",
                 dtype=str, keep_default_na=False, usecols=COLS)
df = df.apply(lambda s: s.str.strip())

# 읽기 (바뀌지 않는 칸이 하나라도 있으면 멈춤)
buy = pd.to_datetime(df["구입일"], format="%Y-%m-%d", errors="coerce")
if buy.isna().any():
    stop(f"구입일 날짜 변환 실패 {int(buy.isna().sum())}칸")
for c in ["대출횟수", "구입가격"]:
    if not df[c].str.fullmatch(r"-?\d+").all():
        stop(f"{c} 정수 변환 실패")
loans = df["대출횟수"].map(int)
price = df["구입가격"].map(int)  # 파이썬 int, 정수 덧셈
blank = df["최근대출일"] == ""
last = pd.to_datetime(df.loc[~blank, "최근대출일"], format="%Y-%m-%d", errors="coerce")
if last.isna().any():
    stop(f"최근대출일이 날짜도 빈칸도 아닌 칸 {int(last.isna().sum())}개")

target = buy <= pd.Timestamp("2022-12-31")
noloan = target & (loans == 0)
rest = ~noloan

N1 = len(df)
N2 = int(noloan.sum())
N3 = int(rest.sum())
N4 = sum(price[noloan])
N5 = sum(price[rest])
N6 = sum(price)


def pct(a, b):  # 정확한 분수 → 소수 둘째 자리 사사오입
    f = Fraction(a, b) * 100
    return (Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.01"), ROUND_HALF_UP)


N7 = pct(N4, N6)
N8 = pct(N5, N6)
N9 = int((target & (blank ^ (loans == 0))).sum())

# 합 확인 (계산명세 6절)
if N1 != 28000: stop(f"N1={N1}")
if N2 + N3 != N1: stop("N2+N3!=N1")
if N4 + N5 != N6: stop("N4+N5!=N6")
if N9 != 0: stop(f"N9={N9}")

rows = [
    ("N1", "전체 권수", N1),
    ("N2", "무대출 권수", N2),
    ("N3", "나머지 권수", N3),
    ("N4", "무대출 구입가격 합계", N4),
    ("N5", "나머지 구입가격 합계", N5),
    ("N6", "구입가격 합계(현재 목록 28,000권)", N6),
    ("N7", "무대출 비중", f"{N7:.2f}"),
    ("N8", "나머지 비중", f"{N8:.2f}"),
    ("N9", "무대출 정의 어긋남 수", N9),
]
with open(OUT + "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)
for r in rows:
    print(*r, sep=",")

# 그림 1 (계산명세 7절), 규칙 10 폰트
FONT = "NanumGothic.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 8))
ax.pie([N4, N5],
       labels=[f"무대출\n{N7:.2f}%\n{N4:,}원", f"나머지\n{N8:.2f}%\n{N5:,}원"],
       colors=["#d9534f", "#9fb7cc"], startangle=90, counterclock=False,
       wedgeprops={"edgecolor": "white"}, textprops={"fontsize": 13})
ax.set_title(f"3년 무대출 장서의 구입가격 비중\n구입가격 합계(현재 목록 {N1:,}권) {N6:,}원 기준", fontsize=15)
ax.axis("equal")
fig.text(0.5, 0.02,
         "무대출 = 구입일 2022-12-31 이하이면서 2023-01-01~2025-12-30 대출횟수 0인 책. "
         "나머지 = 그 밖의 모든 책(2023년 이후 구입한 책 포함).\n"
         "구입가격은 구입 당시 단가이며, 현재 목록 28,000권의 합계로 도서관 예산 집행액이 아니다.",
         ha="center", fontsize=9)
fig.savefig(OUT + "무대출_구입비비중_원그래프.png", dpi=150, bbox_inches="tight")

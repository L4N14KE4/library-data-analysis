# 질문 4 다시 하기 — 주제별 대출횟수·이상치·구입가격과 배분 비율 시나리오 (전체 도서 28,000권)
# 계산명세.md 그대로. 프로젝트 폴더에서 실행:
#   .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/분석/분석.py
import csv
import math
import re
import sys
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import font_manager, pyplot as plt

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261125_주제별_예산근거_전체도서/분석")
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 2절 주제 번호 j
CUT = pd.Timestamp("2023-01-01")


def stop(msg):
    sys.exit(f"멈춤: {msg}")


def r2(x):
    """정확한 분수 -> 소수 둘째 자리 ROUND_HALF_UP 문자열 (6-1)."""
    x = Fraction(x)
    k = math.floor(100 * x + Fraction(1, 2)) if x >= 0 else -math.floor(100 * -x + Fraction(1, 2))
    if k == 0:
        return "0.00"
    return ("-" if k < 0 else "") + f"{abs(k) // 100}.{abs(k) % 100:02d}"


def r4(v):
    return str(Decimal(repr(float(v))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def med(vals):
    """보간 없는 중앙값: 오름차순 ceil(n/2)번째 실제 값 (2절)."""
    s = sorted(vals)
    return s[math.ceil(len(s) / 2) - 1]


def rank(vals):
    """공동 순위: 1 + (정확한 값이 더 큰 주제 수) (2절)."""
    return [1 + sum(w > v for w in vals) for v in vals]


def largest_remainder(a):
    """a: 합 1인 분수 10개 -> 보고 문자열 10개, 합 100.00 (6-5)."""
    v = [x * 10000 for x in a]
    q = [math.floor(x) for x in v]
    r = [x - qq for x, qq in zip(v, q)]
    R = 10000 - sum(q)
    if not 0 <= R <= 9:
        stop(f"최대 잔여 R={R}")
    order = sorted(range(len(a)), key=lambda i: r[i], reverse=True)
    if 0 < R < len(a) and r[order[R - 1]] == r[order[R]]:
        stop("최대 잔여 동률")
    for i in order[:R]:
        q[i] += 1
    assert sum(q) == 10000
    return [f"{x // 100}.{x % 100:02d}" for x in q]


# ---- 입력 (2절) ----
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
df = raw[["자료ID", "주제분류명", "구입일", "구입가격", "대출횟수"]].copy()  # 삭제 7열·쓰지 않는 열은 고르지 않음
for c in ["구입가격", "대출횟수"]:
    s = df[c].str.strip()
    bad = ~s.str.fullmatch(r"-?[0-9]+")
    if bad.any():
        stop(f"{c} 정수 아님 {int(bad.sum())}칸")
    df[c] = s.map(int)
try:
    df["구입일"] = pd.to_datetime(df["구입일"].str.strip(), format="%Y-%m-%d")
except ValueError as e:
    stop(f"구입일 변환 실패: {e}")
if set(df["주제분류명"]) - set(SUBJ):
    stop(f"10개 밖 주제 {set(df['주제분류명']) - set(SUBJ)}")

N = {}
N[1] = len(raw)
N[2] = len(df)  # 대상 = 전부 (승인 1번)
if N[2] != N[1]:
    stop("N2 != N1")

loan = df["대출횟수"].to_numpy()
mu = float(loan.sum()) / len(loan)
sd = float(np.std(loan.astype(np.float64), ddof=1))
lo, hi = mu - 3 * sd, mu + 3 * sd
df["이상치"] = (df["대출횟수"] > hi) | (df["대출횟수"] < lo)
out_rows, keep_rows = df[df["이상치"]], df[~df["이상치"]]

N[3], N[4], N[5], N[6] = r4(mu), r4(sd), r4(lo), r4(hi)
N[7] = int(df["이상치"].sum())
N[8] = int((~df["이상치"]).sum())
if N[7] == 0:
    stop("이상치 0권")
N[9] = int(df["대출횟수"].sum())
N[10] = int(keep_rows["대출횟수"].sum())
N[11] = int(out_rows["대출횟수"].sum())
N[12] = r2(Fraction(N[11], N[9]) * 100)
N[13] = r2(Fraction(N[7], N[2]) * 100)
N[14] = int(out_rows["대출횟수"].min())
N[15] = int(out_rows["대출횟수"].max())
N[16] = r2(Fraction(N[9], N[2]))
N[17] = med(df["대출횟수"].tolist())
N[18] = r2(Fraction(N[10], N[8]))
N[19] = med(keep_rows["대출횟수"].tolist())
N[20] = int(df["구입가격"].sum())
N[21] = r2(Fraction(N[20], N[2]))
N[22] = med(df["구입가격"].tolist())
N[25] = int((df["대출횟수"] == 0).sum())
N[26] = r2(Fraction(N[25], N[2]) * 100)
N[27] = int((df["구입일"] >= CUT).sum())
if N[27] == 0:
    stop("2023년 이후 구입 0권")
N[28] = r2(Fraction(N[27], N[2]) * 100)

# ---- 주제별 정확한 값 ----
F = {}  # F[f] = 주제 10개 정확한 값 리스트 (반올림 전)
g = {s: df[df["주제분류명"] == s] for s in SUBJ}
F[0] = [len(g[s]) for s in SUBJ]
F[1] = [int(g[s]["대출횟수"].sum()) for s in SUBJ]
F[5] = [int((~g[s]["이상치"]).sum()) for s in SUBJ]
F[6] = [int(g[s].loc[~g[s]["이상치"], "대출횟수"].sum()) for s in SUBJ]
F[10] = [int(g[s]["이상치"].sum()) for s in SUBJ]
F[15] = [int(g[s].loc[g[s]["이상치"], "대출횟수"].sum()) for s in SUBJ]
F[17] = [int(g[s]["구입가격"].sum()) for s in SUBJ]
F[33] = [int((g[s]["구입일"] >= CUT).sum()) for s in SUBJ]
if min(F[0]) == 0 or min(F[5]) == 0 or min(F[1]) == 0 or min(F[6]) == 0:
    stop("권수 0 또는 대출 합 0인 주제")
F[2] = [Fraction(a, b) for a, b in zip(F[1], F[0])]
F[3] = [med(g[s]["대출횟수"].tolist()) for s in SUBJ]
F[7] = [Fraction(a, b) for a, b in zip(F[6], F[5])]
F[8] = [med(g[s].loc[~g[s]["이상치"], "대출횟수"].tolist()) for s in SUBJ]
F[11] = [Fraction(a, b) * 100 for a, b in zip(F[10], F[0])]
F[12] = [Fraction(a, N[7]) * 100 for a in F[10]]
F[13] = [Fraction(a, N[2]) * 100 for a in F[0]]
F[14] = [a - b for a, b in zip(F[12], F[13])]
F[16] = [Fraction(a, b) * 100 for a, b in zip(F[15], F[1])]
F[18] = [Fraction(a, b) for a, b in zip(F[17], F[0])]
F[19] = [med(g[s]["구입가격"].tolist()) for s in SUBJ]
F[21] = [Fraction(a, N[9]) * 100 for a in F[1]]
F[22] = [Fraction(a, N[10]) * 100 for a in F[6]]
F[23] = [Fraction(a, N[20]) * 100 for a in F[17]]
F[34] = [Fraction(a, b) * 100 for a, b in zip(F[33], F[0])]
F[4], F[9], F[20] = rank(F[2]), rank(F[7]), rank(F[18])
F[31], F[32] = rank(F[1]), rank(F[6])

# 시나리오 (6-5)
B, P = F[0], F[18]
def sc1(L): return [Fraction(x, sum(L)) for x in L]
def sc2(L):
    w = [x * p for x, p in zip(L, P)]
    return [x / sum(w) for x in w]
def sc4(L): return [Fraction(b, sum(B)) / 2 + Fraction(x, sum(L)) / 2 for b, x in zip(B, L)]
sc = {24: sc1(F[1]), 25: sc1(F[6]), 26: sc2(F[1]), 27: sc2(F[6]),
      28: [Fraction(x, N[20]) for x in F[17]], 29: sc4(F[1]), 30: sc4(F[6])}
for f, a in sc.items():
    assert sum(a) == 1
    F[f] = largest_remainder(a)

N[23] = r2(max(F[18]) - min(F[18]))
N[24] = r2((max(F[18]) - min(F[18])) / Fraction(N[20], N[2]) * 100)

# ---- 합 확인 (6-6) ----
assert N[7] + N[8] == N[2] and N[10] + N[11] == N[9] and N[27] <= N[2]
assert sum(F[0]) == N[2] and sum(F[5]) == N[8] and sum(F[1]) == N[9] and sum(F[6]) == N[10]
assert sum(F[10]) == N[7] and sum(F[15]) == N[11] and sum(F[17]) == N[20] and sum(F[33]) == N[27]
for f in range(24, 31):
    assert sum(int(x.replace(".", "")) for x in F[f]) == 10000

# ---- 핵심수치.csv ----
INT_F = {0, 1, 3, 4, 5, 6, 8, 9, 10, 15, 17, 19, 20, 31, 32, 33}
STR_F = set(range(24, 31))
NAME = {
    0: "유지 권수", 1: "유지 대출 합", 2: "유지 대출 평균", 3: "유지 대출 중앙값", 4: "유지 대출 평균 순위",
    5: "제외 권수", 6: "제외 대출 합", 7: "제외 대출 평균", 8: "제외 대출 중앙값", 9: "제외 대출 평균 순위",
    10: "이상치 권수", 11: "주제 안 이상치 비율", 12: "이상치 중 비중", 13: "권수 비중",
    14: "이상치 중 비중 - 권수 비중", 15: "이상치 대출 합", 16: "주제 대출 합 중 이상치 비중",
    17: "구입가격 합", 18: "구입가격 평균", 19: "구입가격 중앙값", 20: "구입가격 평균 순위",
    21: "유지 대출 비중", 22: "제외 대출 비중", 23: "가격합 비중",
    24: "유지 시나리오 1", 25: "제외 시나리오 1", 26: "유지 시나리오 2", 27: "제외 시나리오 2",
    28: "시나리오 3", 29: "유지 시나리오 4", 30: "제외 시나리오 4",
    31: "유지 대출 비중 순위", 32: "제외 대출 비중 순위",
    33: "2023년 이후 구입 권수", 34: "2023년 이후 구입 비율",
}
COMMON = {
    1: "입력 행 수", 2: "대상 권수", 3: "대상 대출횟수 평균", 4: "대상 대출횟수 표본 표준편차",
    5: "이상치 아래 경계", 6: "이상치 위 경계", 7: "이상치 권수", 8: "제외 후 권수",
    9: "유지 대상 대출 합", 10: "제외 후 대출 합", 11: "이상치 대출 합", 12: "이상치 대출 합 비중",
    13: "이상치 권수 비율", 14: "이상치 대출횟수 최솟값", 15: "이상치 대출횟수 최댓값",
    16: "유지 대상 대출 평균", 17: "유지 대상 대출 중앙값", 18: "제외 후 대출 평균", 19: "제외 후 대출 중앙값",
    20: "대상 구입가격 합", 21: "대상 구입가격 평균", 22: "대상 구입가격 중앙값",
    23: "주제별 구입가격 평균의 최댓값 - 최솟값", 24: "N23의 대상 평균 대비 크기",
    25: "대상 대출 0회 권수", 26: "대상 대출 0회 비율",
    27: "2023년 이후 구입 권수 (대상 전체)", 28: "2023년 이후 구입 비율 (대상 전체)",
}


def fval(f, j):
    v = F[f][j]
    return v if f in STR_F else (str(int(v)) if f in INT_F else r2(v))


def item(f, s):
    n = NAME[f]
    for t in ("유지 ", "제외 "):
        if n.startswith(t):
            return f"{t}{s} {n[len(t):]}"
    return f"{s} {n}"


V = {k: str(v) for k, v in N.items()}
rows = [(f"N{k}", COMMON[k], V[k]) for k in range(1, 29)]
for j, s in enumerate(SUBJ):
    for f in range(35):
        k = 29 + 35 * j + f
        V[k] = fval(f, j)
        rows.append((f"N{k}", item(f, s), V[k]))
assert len(rows) == 378
OUT.mkdir(parents=True, exist_ok=True)
with open(OUT / "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)

# ---- 표 1~5 (7-2) ----
if len(set(F[0])) != 10:
    stop("유지 권수가 같은 주제 있음 (행 순서)")
ORDER = sorted(range(10), key=lambda j: -F[0][j])


def v(j, f):
    return V[29 + 35 * j + f]


def table(name, header, fs, total):
    with open(OUT / name, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["주제분류명"] + header)
        for j in ORDER:
            w.writerow([SUBJ[j]] + [v(j, f) for f in fs])
        w.writerow(["대상 전체"] + [V[t] if isinstance(t, int) else t for t in total])


table("표1_주제별_장서수_대출횟수.csv",
      ["유지 권수", "유지 대출 합", "유지 평균", "유지 중앙값", "유지 평균 순위",
       "제외 권수", "제외 대출 합", "제외 평균", "제외 중앙값", "제외 평균 순위",
       "2023년 이후 구입 권수", "2023년 이후 구입 비율%"],
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 33, 34],
      [2, 9, 16, 17, "", 8, 10, 18, 19, "", 27, 28])
table("표2_대출이상치_주제별.csv",
      ["대상 권수", "이상치 권수", "주제 안 이상치 비율%", "이상치 중 비중%", "권수 비중%", "차이 %p",
       "이상치 대출 합", "주제 대출 합 중 이상치 비중%"],
      [0, 10, 11, 12, 13, 14, 15, 16],
      [2, 7, 13, "", "", "", 11, 12])
table("표3_주제별_구입가격.csv",
      ["권수", "구입가격 합", "평균", "평균 순위", "중앙값"],
      [0, 17, 18, 20, 19],
      [2, 20, 21, "", 22])
table("표4_배분근거지표.csv",
      ["권수 비중%", "대출 비중% 유지", "대출 비중 순위 유지", "대출 비중% 제외", "대출 비중 순위 제외",
       "가격합 비중%", "구입가격 평균", "2023년 이후 구입 비율%"],
      [13, 21, 31, 22, 32, 23, 18, 34],
      ["", "", "", "", "", "", 21, 28])
table("표5_배분비율_시나리오.csv",
      ["시나리오 1 유지", "시나리오 1 제외", "시나리오 2 유지", "시나리오 2 제외",
       "시나리오 3 (대상 장서 구입가격 구성대로)", "시나리오 4 유지", "시나리오 4 제외"],
      [24, 25, 26, 27, 28, 29, 30],
      ["100.00"] * 7)

# ---- 그림 1 (7-3, 규칙 10) ----
FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

names = [SUBJ[j] for j in ORDER]
x = np.arange(10)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 9))
b = a1.bar(x, [int(v(j, 0)) for j in ORDER], color="#4C72B0")
a1.bar_label(b, labels=[f"{int(v(j, 0)):,}" for j in ORDER], padding=2)
a1.set_xticks(x, names)
a1.set_ylabel("장서 수 (권)")
a1.set_xlabel("주제분류명")
wd = 0.38
b1 = a2.bar(x - wd / 2, [float(v(j, 2)) for j in ORDER], wd, label="평균", color="#DD8452")
b2 = a2.bar(x + wd / 2, [int(v(j, 3)) for j in ORDER], wd, label="중앙값", color="#55A868")
a2.bar_label(b1, labels=[v(j, 2) for j in ORDER], padding=2)
a2.bar_label(b2, labels=[v(j, 3) for j in ORDER], padding=2)
a2.set_xticks(x, names)
a2.set_ylabel("대출횟수 (회)")
a2.set_xlabel("주제분류명")
a2.legend()
for a in (a1, a2):
    a.margins(y=0.15)
fig.suptitle("주제분류명별 장서 수와 대출횟수(2023~2025년) 평균·중앙값")
note = (f"대상: P02_장서목록_대출횟수의 책 {N[2]:,}권 전부. 대출횟수는 2023~2025년 3년간 대출된 횟수이며, "
        f"이상치 {N[7]:,}권을 포함한 값이다.\n2023년 이후 구입분 {N[27]:,}권({V[28]}%)이 들어 있다.")
med01 = all(m in (0, 1) for m in F[3])
if med01:
    note += f" 대상의 {V[26]}%가 대출 0회이고, 주제별 중앙값은 0 또는 1이다."
else:
    print("알림: f3이 0/1 밖 값이 있어 그림 각주 마지막 문장을 뺌")
fig.text(0.01, -0.02, note, ha="left", va="top", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "그림1_주제별_장서수_대출횟수_유지.png", dpi=150, bbox_inches="tight")

print("완료:", len(rows), "개 핵심 수치")
print("N3~N8:", N[3], N[4], N[5], N[6], N[7], N[8])

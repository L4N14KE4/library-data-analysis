# 6단계 독립 재계산 — 질문 4 다시 하기 (전체 도서). 프로젝트 폴더에서 실행:
#   .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/검증/재계산.py
# 읽는 것: 원자료 CSV, 계산명세.md·승인기록.md의 정의 (분석/ 결과는 읽지 않음). 난수 없음 (시드 없음).
import csv, math, sys
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F
import numpy as np

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_주제별_예산근거_전체도서/검증/검증값.csv"
TOPICS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
CUT = datetime(2023, 1, 1)


def stop(msg):
    sys.exit("멈춤: " + msg)


def r2(x):  # 계산명세 6-1: 분수 -> ROUND_HALF_UP 소수 둘째, 정수 연산
    x = F(x)
    k = math.floor(100 * x + F(1, 2)) if x >= 0 else -math.floor(100 * -x + F(1, 2))
    if k == 0:
        return "0.00"
    s = "-" if k < 0 else ""
    k = abs(k)
    return f"{s}{k // 100}.{k % 100:02d}"


def r4(x):  # N3~N6: Decimal(repr(float)) ROUND_HALF_UP 넷째
    return str(Decimal(repr(float(x))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def med(v):  # ceil(n/2)번째 값 (1부터)
    v = sorted(v)
    return v[math.ceil(len(v) / 2) - 1]


def rank(vals):  # 공동 순위: 1 + 더 큰 값 수
    return [1 + sum(w > x for w in vals) for x in vals]


def largest_remainder(a):  # 6-5 최대 잔여, a: 분수 10개 (합 1)
    assert sum(a) == 1
    v = [x * 10000 for x in a]
    q = [math.floor(x) for x in v]
    r = [x - qq for x, qq in zip(v, q)]
    R = 10000 - sum(q)
    if not 0 <= R <= 9:
        stop(f"잔여 R={R}")
    order = sorted(range(10), key=lambda j: r[j], reverse=True)
    if 0 < R < 10 and r[order[R - 1]] == r[order[R]]:
        stop("최대 잔여 동률")
    for j in order[:R]:
        q[j] += 1
    assert sum(q) == 10000
    return [f"{x // 100}.{x % 100:02d}" for x in q]


# ---- 읽기 ----
with open(SRC, encoding="utf-8-sig", newline="") as fh:
    rows = list(csv.DictReader(fh))
N1 = len(rows)
data = []
for r in rows:
    t = r["주제분류명"]
    if t not in TOPICS:
        stop(f"주제 밖 값 {t!r}")
    try:
        d = datetime.strptime(r["구입일"].strip(), "%Y-%m-%d")
        loan = int(r["대출횟수"].strip())
        price = int(r["구입가격"].strip())
    except ValueError as e:
        stop(f"변환 실패 {r['자료ID']}: {e}")
    data.append((t, d, loan, price))
N2 = len(data)
if N2 != N1:
    stop("N2 != N1")

loans = np.array([x[2] for x in data], dtype=np.int64)
mu = loans.sum() / N2
s = float(np.std(loans.astype(np.float64), ddof=1))
lo, hi = mu - 3 * s, mu + 3 * s
is_out = [(l > hi) or (l < lo) for l in loans.tolist()]

N7 = sum(is_out)
N8 = sum(not o for o in is_out)
N9 = sum(x[2] for x in data)
N10 = sum(x[2] for x, o in zip(data, is_out) if not o)
N11 = sum(x[2] for x, o in zip(data, is_out) if o)
out_loans = [x[2] for x, o in zip(data, is_out) if o]
N20 = sum(x[3] for x in data)
N25 = sum(x[2] == 0 for x in data)
N27 = sum(x[1] >= CUT for x in data)
if N7 == 0 or N27 == 0:
    stop("N7 또는 N27 = 0")
assert N7 + N8 == N2 and N10 + N11 == N9

res = [
    ("N1", "입력 행 수", N1),
    ("N2", "대상 권수", N2),
    ("N3", "대상 대출횟수 평균", r4(mu)),
    ("N4", "대상 대출횟수 표본 표준편차", r4(s)),
    ("N5", "이상치 아래 경계", r4(lo)),
    ("N6", "이상치 위 경계", r4(hi)),
    ("N7", "이상치 권수", N7),
    ("N8", "제외 후 권수", N8),
    ("N9", "유지 대상 대출 합", N9),
    ("N10", "제외 대출 합", N10),
    ("N11", "이상치 대출 합", N11),
    ("N12", "이상치 대출 합 비중", r2(F(N11, N9) * 100)),
    ("N13", "이상치 권수 비율", r2(F(N7, N2) * 100)),
    ("N14", "이상치 대출횟수 최솟값", min(out_loans)),
    ("N15", "이상치 대출횟수 최댓값", max(out_loans)),
    ("N16", "유지 대상 대출 평균", r2(F(N9, N2))),
    ("N17", "유지 대상 대출 중앙값", med([x[2] for x in data])),
    ("N18", "제외 대출 평균", r2(F(N10, N8))),
    ("N19", "제외 대출 중앙값", med([x[2] for x, o in zip(data, is_out) if not o])),
    ("N20", "대상 구입가격 합", N20),
    ("N21", "대상 구입가격 평균", r2(F(N20, N2))),
    ("N22", "대상 구입가격 중앙값", med([x[3] for x in data])),
]

# ---- 주제별 ----
T = {}
for j, t in enumerate(TOPICS):
    keep = [(x, o) for x, o in zip(data, is_out) if x[0] == t]
    g = {}
    g[0] = len(keep)
    g[1] = sum(x[2] for x, _ in keep)
    g[5] = sum(not o for _, o in keep)
    g[6] = sum(x[2] for x, o in keep if not o)
    g[10] = sum(o for _, o in keep)
    g[15] = sum(x[2] for x, o in keep if o)
    g[17] = sum(x[3] for x, _ in keep)
    g[33] = sum(x[1] >= CUT for x, _ in keep)
    if g[0] == 0 or g[5] == 0 or g[1] == 0 or g[6] == 0:
        stop(f"{t} 권수·대출 합 0")
    g["mean_k"] = F(g[1], g[0])
    g["mean_x"] = F(g[6], g[5])
    g["price"] = F(g[17], g[0])
    g["med_k"] = med([x[2] for x, _ in keep])
    g["med_x"] = med([x[2] for x, o in keep if not o])
    g["med_p"] = med([x[3] for x, _ in keep])
    T[t] = g

f0s = [T[t][0] for t in TOPICS]
if len(set(f0s)) != 10:
    stop("권수 동률 (표 순서)")
assert sum(f0s) == N2 and sum(T[t][5] for t in TOPICS) == N8
assert sum(T[t][1] for t in TOPICS) == N9 and sum(T[t][6] for t in TOPICS) == N10
assert sum(T[t][10] for t in TOPICS) == N7 and sum(T[t][15] for t in TOPICS) == N11
assert sum(T[t][17] for t in TOPICS) == N20 and sum(T[t][33] for t in TOPICS) == N27

rk4 = rank([T[t]["mean_k"] for t in TOPICS])
rk9 = rank([T[t]["mean_x"] for t in TOPICS])
rk20 = rank([T[t]["price"] for t in TOPICS])
rk31 = rank([T[t][1] for t in TOPICS])
rk32 = rank([T[t][6] for t in TOPICS])

prices = [T[t]["price"] for t in TOPICS]
N23 = max(prices) - min(prices)
res += [
    ("N23", "주제별 구입가격 평균의 최댓값 - 최솟값", r2(N23)),
    ("N24", "N23의 대상 구입가격 평균 대비 크기", r2(N23 / F(N20, N2) * 100)),
    ("N25", "대상 대출 0회 권수", N25),
    ("N26", "대상 대출 0회 비율", r2(F(N25, N2) * 100)),
    ("N27", "2023년 이후 구입 권수", N27),
    ("N28", "2023년 이후 구입 비율", r2(F(N27, N2) * 100)),
]

# 시나리오 (6-5)
B = [F(T[t][0], N2) for t in TOPICS]
Lk = [F(T[t][1], N9) for t in TOPICS]
Lx = [F(T[t][6], N10) for t in TOPICS]
G = [F(T[t][17], N20) for t in TOPICS]


def s2(L):
    w = [l * p for l, p in zip(L, prices)]
    return [x / sum(w) for x in w]


SC = {
    24: largest_remainder(Lk),
    25: largest_remainder(Lx),
    26: largest_remainder(s2(Lk)),
    27: largest_remainder(s2(Lx)),
    28: largest_remainder(G),
    29: largest_remainder([(b + l) / 2 for b, l in zip(B, Lk)]),
    30: largest_remainder([(b + l) / 2 for b, l in zip(B, Lx)]),
}

NAMES = {
    0: "유지 {t} 권수", 1: "유지 {t} 대출 합", 2: "유지 {t} 대출 평균", 3: "유지 {t} 대출 중앙값",
    4: "유지 {t} 대출 평균 순위", 5: "제외 {t} 권수", 6: "제외 {t} 대출 합", 7: "제외 {t} 대출 평균",
    8: "제외 {t} 대출 중앙값", 9: "제외 {t} 대출 평균 순위", 10: "{t} 이상치 권수",
    11: "{t} 주제 안 이상치 비율", 12: "{t} 이상치 중 비중", 13: "{t} 권수 비중",
    14: "{t} 이상치 중 비중 - 권수 비중", 15: "{t} 이상치 대출 합", 16: "{t} 주제 대출 합 중 이상치 비중",
    17: "{t} 구입가격 합", 18: "{t} 구입가격 평균", 19: "{t} 구입가격 중앙값", 20: "{t} 구입가격 평균 순위",
    21: "유지 {t} 대출 비중", 22: "제외 {t} 대출 비중", 23: "{t} 가격합 비중",
    24: "유지 {t} 시나리오 1", 25: "제외 {t} 시나리오 1", 26: "유지 {t} 시나리오 2", 27: "제외 {t} 시나리오 2",
    28: "{t} 시나리오 3", 29: "유지 {t} 시나리오 4", 30: "제외 {t} 시나리오 4",
    31: "유지 {t} 대출 비중 순위", 32: "제외 {t} 대출 비중 순위",
    33: "{t} 2023년 이후 구입 권수", 34: "{t} 2023년 이후 구입 비율",
}

for j, t in enumerate(TOPICS):
    g = T[t]
    f12 = F(g[10], N7) * 100
    f13 = F(g[0], N2) * 100
    v = {
        0: g[0], 1: g[1], 2: r2(g["mean_k"]), 3: g["med_k"], 4: rk4[j],
        5: g[5], 6: g[6], 7: r2(g["mean_x"]), 8: g["med_x"], 9: rk9[j],
        10: g[10], 11: r2(F(g[10], g[0]) * 100), 12: r2(f12), 13: r2(f13), 14: r2(f12 - f13),
        15: g[15], 16: r2(F(g[15], g[1]) * 100), 17: g[17], 18: r2(g["price"]), 19: g["med_p"],
        20: rk20[j], 21: r2(Lk[j] * 100), 22: r2(Lx[j] * 100), 23: r2(G[j] * 100),
        31: rk31[j], 32: rk32[j], 33: g[33], 34: r2(F(g[33], g[0]) * 100),
    }
    for f in range(24, 31):
        v[f] = SC[f][j]
    for f in range(35):
        res.append((f"N{29 + 35 * j + f}", NAMES[f].format(t=t), v[f]))

assert len(res) == 378 and [n for n, _, _ in res] == [f"N{i}" for i in range(1, 379)]
with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    w.writerows(res)
print("저장:", OUT, len(res), "행")


def _selfcheck():  # 반올림·중앙값·순위 확인
    assert r2(F(1235, 1000)) == "1.24" and r2(F(-1235, 1000)) == "-1.24" and r2(F(-1, 1000)) == "0.00"
    assert med([3, 1, 2, 4]) == 2 and med([5]) == 5
    assert rank([3, 2, 2, 1]) == [1, 2, 2, 4]


_selfcheck()

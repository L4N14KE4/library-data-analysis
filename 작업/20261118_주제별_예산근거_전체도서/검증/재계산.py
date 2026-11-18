# 6단계 독립 재계산 — 질문 4 전체 도서 (계산명세.md N1~N378)
# 실행: 프로젝트 폴더에서  .venv/bin/python "작업/20261118_주제별_예산근거_전체도서/검증/재계산.py"
# 방법: pandas/numpy 없이 csv 모듈 + 정수 + fractions.Fraction. N3~N6만 float (명세 6-1).
import csv, math, re, sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261118_주제별_예산근거_전체도서/검증/검증값.csv"
TOPICS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
INT_RE = re.compile(r"-?[0-9]+")
CUT = date(2023, 1, 1)


def stop(msg):
    print("멈춤:", msg)
    sys.exit(1)


def to_int(s, col, rid):
    t = s.strip()
    if not INT_RE.fullmatch(t):  # ponytail: int()는 '1_0'·'+1'도 받으므로 정규식으로 엄격히
        stop(f"{col} 정수 변환 불가 {rid!r}: {s!r}")
    return int(t)


# ---- 읽기 (모든 칸 문자열, 결측 변환 없음)
rows = []
with open(SRC, encoding="utf-8-sig", newline="") as fh:
    for r in csv.DictReader(fh):
        rid = r["자료ID"]
        try:
            d = datetime.strptime(r["구입일"].strip(), "%Y-%m-%d").date()
        except ValueError:
            stop(f"구입일 변환 불가 {rid!r}: {r['구입일']!r}")
        t = r["주제분류명"]
        if t not in TOPICS:
            stop(f"10개 밖 주제 {rid!r}: {t!r}")
        rows.append((TOPICS.index(t), to_int(r["대출횟수"], "대출횟수", rid),
                     to_int(r["구입가격"], "구입가격", rid), d))

N = {}
N[1] = len(rows)
target = rows  # 대상 = 입력 전부 (승인 1번)
N[2] = len(target)
if N[2] != N[1]:
    stop("N2 != N1")
n = N[2]
loans = [r[1] for r in target]

# ---- N3~N6 (float). mu = 정수합/n, s = sqrt(정확한 표본분산) 을 float로
S = sum(loans)
mu = S / n
var_exact = F(sum(x * x for x in loans) * n - S * S, n * (n - 1))
s = math.sqrt(var_exact)  # ponytail: numpy std(ddof=1)와 마지막 ulp가 다를 수 있으나 넷째 자리 보고엔 무관
lo, hi = mu - 3 * s, mu + 3 * s
is_out = [x > hi or x < lo for x in loans]
# 경계 민감도 확인: 정확한 분수 기준 판정 (x-mu)^2 > 9*var 와 같아야 한다
mu_e = F(S, n)
exact_out = [(x - mu_e) ** 2 > 9 * var_exact for x in loans]
if exact_out != is_out:
    stop("float 판정과 정확 판정이 다름 (경계 근처 값)")


def d4(x):
    return str(Decimal(repr(float(x))).quantize(Decimal("0.0001"), ROUND_HALF_UP))


def r2(x):
    x = F(x)
    k = math.floor(100 * x + F(1, 2)) if x >= 0 else -math.floor(100 * -x + F(1, 2))
    sign = "-" if k < 0 else ""
    k = abs(k)
    return f"{sign}{k // 100}.{k % 100:02d}"


def med(v):
    v = sorted(v)
    return v[(len(v) + 1) // 2 - 1]  # ceil(n/2)번째, 1부터 셈


def ranks(vals):
    return [1 + sum(1 for w in vals if w > v) for v in vals]


def largest_remainder(a):
    v = [x * 10000 for x in a]
    q = [math.floor(x) for x in v]
    rem = [x - qq for x, qq in zip(v, q)]
    R = 10000 - sum(q)
    if not 0 <= R <= 9:
        stop(f"최대 잔여 R={R}")
    order = sorted(range(10), key=lambda j: rem[j], reverse=True)
    if 0 < R < 10 and rem[order[R - 1]] == rem[order[R]]:
        stop("최대 잔여 경계 동률")
    for j in order[:R]:
        q[j] += 1
    assert sum(q) == 10000
    return [f"{x // 100}.{x % 100:02d}" for x in q]


N[3], N[4], N[5], N[6] = d4(mu), d4(s), d4(lo), d4(hi)
outl = [x for x, o in zip(loans, is_out) if o]
kept = [x for x, o in zip(loans, is_out) if not o]
N[7] = sum(is_out)
N[8] = sum(1 for o in is_out if not o)
if N[7] == 0:
    stop("N7 = 0")
N[9], N[10], N[11] = S, sum(kept), sum(outl)
N[12] = r2(F(N[11], N[9]) * 100)
N[13] = r2(F(N[7], N[2]) * 100)
N[14], N[15] = min(outl), max(outl)
N[16] = r2(F(N[9], N[2])); N[17] = med(loans)
N[18] = r2(F(N[10], N[8])); N[19] = med(kept)
prices = [r[2] for r in target]
N[20] = sum(prices); N[21] = r2(F(N[20], n)); N[22] = med(prices)
N[25] = sum(1 for x in loans if x == 0); N[26] = r2(F(N[25], n) * 100)
N[27] = sum(1 for r in target if r[3] >= CUT)
if N[27] == 0:
    stop("N27 = 0")
N[28] = r2(F(N[27], n) * 100)

# ---- 주제별 원값
T = []
for j in range(10):
    g = [(r, o) for r, o in zip(target, is_out) if r[0] == j]
    keep = [r for r, o in g if not o]
    out = [r for r, o in g if o]
    t = dict(f0=len(g), f1=sum(r[1] for r, _ in g), f3=med([r[1] for r, _ in g]),
             f5=len(keep), f6=sum(r[1] for r in keep), f8=med([r[1] for r in keep]) if keep else None,
             f10=len(out), f15=sum(r[1] for r in out), f17=sum(r[2] for r, _ in g),
             f19=med([r[2] for r, _ in g]) if g else None, f33=sum(1 for r, _ in g if r[3] >= CUT))
    if t["f0"] == 0 or t["f5"] == 0 or t["f1"] == 0 or t["f6"] == 0:
        stop(f"{TOPICS[j]} 권수 또는 대출 합 0")
    T.append(t)

mean_k = [F(t["f1"], t["f0"]) for t in T]
mean_x = [F(t["f6"], t["f5"]) for t in T]
price_m = [F(t["f17"], t["f0"]) for t in T]
share_b = [F(t["f0"], N[2]) for t in T]
share_lk = [F(t["f1"], N[9]) for t in T]
share_lx = [F(t["f6"], N[10]) for t in T]
rk4, rk9, rk20 = ranks(mean_k), ranks(mean_x), ranks(price_m)
rk31, rk32 = ranks([t["f1"] for t in T]), ranks([t["f6"] for t in T])

N[23] = r2(max(price_m) - min(price_m))
N[24] = r2((max(price_m) - min(price_m)) / F(N[20], n) * 100)


def norm(w):
    s_ = sum(w)
    return [x / s_ for x in w]


sc = {
    24: largest_remainder(share_lk),
    25: largest_remainder(share_lx),
    26: largest_remainder(norm([t["f1"] * p for t, p in zip(T, price_m)])),
    27: largest_remainder(norm([t["f6"] * p for t, p in zip(T, price_m)])),
    28: largest_remainder([F(t["f17"], N[20]) for t in T]),
    29: largest_remainder([(b + l) / 2 for b, l in zip(share_b, share_lk)]),
    30: largest_remainder([(b + l) / 2 for b, l in zip(share_b, share_lx)]),
}

NAMES = {0: "유지 {} 권수", 1: "유지 {} 대출 합", 2: "유지 {} 대출 평균", 3: "유지 {} 대출 중앙값",
         4: "유지 {} 대출 평균 순위", 5: "제외 {} 권수", 6: "제외 {} 대출 합", 7: "제외 {} 대출 평균",
         8: "제외 {} 대출 중앙값", 9: "제외 {} 대출 평균 순위", 10: "{} 이상치 권수",
         11: "{} 주제 안 이상치 비율", 12: "{} 이상치 중 비중", 13: "{} 권수 비중",
         14: "{} 이상치 중 비중 - 권수 비중", 15: "{} 이상치 대출 합", 16: "{} 주제 대출 합 중 이상치 비중",
         17: "{} 구입가격 합", 18: "{} 구입가격 평균", 19: "{} 구입가격 중앙값", 20: "{} 구입가격 평균 순위",
         21: "유지 {} 대출 비중", 22: "제외 {} 대출 비중", 23: "{} 가격합 비중",
         24: "유지 {} 시나리오 1", 25: "제외 {} 시나리오 1", 26: "유지 {} 시나리오 2",
         27: "제외 {} 시나리오 2", 28: "{} 시나리오 3", 29: "유지 {} 시나리오 4", 30: "제외 {} 시나리오 4",
         31: "유지 {} 대출 비중 순위", 32: "제외 {} 대출 비중 순위",
         33: "{} 2023년 이후 구입 권수", 34: "{} 2023년 이후 구입 비율"}
LBL = {1: "입력 행 수", 2: "대상 권수", 3: "대상 대출횟수 평균", 4: "대상 대출횟수 표본 표준편차",
       5: "이상치 아래 경계", 6: "이상치 위 경계", 7: "이상치 권수", 8: "제외 후 권수",
       9: "유지 대상 대출 합", 10: "제외 후 대출 합", 11: "이상치 대출 합", 12: "이상치 대출 합 비중",
       13: "이상치 권수 비율", 14: "이상치 대출횟수 최솟값", 15: "이상치 대출횟수 최댓값",
       16: "유지 대상 대출 평균", 17: "유지 대상 대출 중앙값", 18: "제외 후 대출 평균",
       19: "제외 후 대출 중앙값", 20: "대상 구입가격 합", 21: "대상 구입가격 평균",
       22: "대상 구입가격 중앙값", 23: "주제별 구입가격 평균 최댓값 - 최솟값",
       24: "주제별 구입가격 평균 차이의 대상 평균 대비", 25: "대상 대출 0회 권수",
       26: "대상 대출 0회 비율", 27: "2023년 이후 구입 권수", 28: "2023년 이후 구입 비율"}

out_rows = [(f"N{k}", LBL[k], str(N[k])) for k in range(1, 29)]
for j, t in enumerate(T):
    v = {0: t["f0"], 1: t["f1"], 2: r2(mean_k[j]), 3: t["f3"], 4: rk4[j],
         5: t["f5"], 6: t["f6"], 7: r2(mean_x[j]), 8: t["f8"], 9: rk9[j],
         10: t["f10"], 11: r2(F(t["f10"], t["f0"]) * 100), 12: r2(F(t["f10"], N[7]) * 100),
         13: r2(share_b[j] * 100), 14: r2(F(t["f10"], N[7]) * 100 - share_b[j] * 100),
         15: t["f15"], 16: r2(F(t["f15"], t["f1"]) * 100),
         17: t["f17"], 18: r2(price_m[j]), 19: t["f19"], 20: rk20[j],
         21: r2(share_lk[j] * 100), 22: r2(share_lx[j] * 100), 23: r2(F(t["f17"], N[20]) * 100),
         31: rk31[j], 32: rk32[j], 33: t["f33"], 34: r2(F(t["f33"], t["f0"]) * 100)}
    for f in range(24, 31):
        v[f] = sc[f][j]
    for f in range(35):
        out_rows.append((f"N{29 + 35 * j + f}", NAMES[f].format(TOPICS[j]), str(v[f])))

# ---- 6-6 합 확인
chk = {
    "N2 = N1": N[2] == N[1], "N7 + N8 = N2": N[7] + N[8] == N[2],
    "N10 + N11 = N9": N[10] + N[11] == N[9], "N27 <= N2": N[27] <= N[2],
    "Σf0 = N2": sum(t["f0"] for t in T) == N[2], "Σf5 = N8": sum(t["f5"] for t in T) == N[8],
    "Σf1 = N9": sum(t["f1"] for t in T) == N[9], "Σf6 = N10": sum(t["f6"] for t in T) == N[10],
    "Σf10 = N7": sum(t["f10"] for t in T) == N[7], "Σf15 = N11": sum(t["f15"] for t in T) == N[11],
    "Σf17 = N20": sum(t["f17"] for t in T) == N[20], "Σf33 = N27": sum(t["f33"] for t in T) == N[27],
    "순위 동률 없음(f4,f9,f20,f31,f32 각각 1~10 한 번씩)":
        all(sorted(r) == list(range(1, 11)) for r in (rk4, rk9, rk20, rk31, rk32)),
    "시나리오 7열 합 100.00": all(sum(int(x.replace(".", "")) for x in sc[f]) == 10000 for f in sc),
    "행 순서용 f0 동률 없음": len({t["f0"] for t in T}) == 10,
}
for k, ok in chk.items():
    print(("OK  " if ok else "실패 ") + k)
# 순위 동률은 공동 순위(승인 9번)라 멈춤 아님. 나머지는 멈춤 조건.
hard = [k for k, ok in chk.items() if not ok and not k.startswith("순위")]
if hard:
    stop("합 확인 실패: " + ", ".join(hard))
assert len(out_rows) == 378

with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    w.writerows(out_rows)
print("저장", OUT, len(out_rows), "행")
for k in range(3, 9):
    print(f"N{k}", N[k])

# 질문 4 독립 재계산 (검증 담당). 프로젝트 폴더에서 실행:
#   .venv/bin/python 작업/20261117_주제별_예산근거_보관_구입일2022이하/검증/재계산.py
# 분석 담당 코드와 다른 길: 표준 라이브러리 csv, Fraction 정확 계산, 중앙값·최대 잔여 반올림 직접 구현.
# N3~N6만 계산명세 6-1절대로 float64. 난수 없음.
import csv
import math
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261117_주제별_예산근거_보관_구입일2022이하/검증/검증값.csv"
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
CUT = date(2022, 12, 31)
stops = []


def stop(msg):
    stops.append(msg)
    print("멈춤 조건:", msg, file=sys.stderr)


def r2(x):
    """Fraction -> 소수 둘째 자리 문자열 (0에서 먼 쪽 사사오입, -0.00 없음)."""
    x = Fraction(x)
    k = math.floor(abs(x) * 100 + Fraction(1, 2))
    if x < 0:
        k = -k
    s = "-" if k < 0 else ""
    k = abs(k)
    return f"{s}{k // 100}.{k % 100:02d}"


def r4(f):
    return str(Decimal(repr(float(f))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def median(vals):
    v = sorted(vals)
    return v[(len(v) + 1) // 2 - 1]  # ceil(n/2)번째, 1부터 셈


def rank_desc(d):
    """d: {j: Fraction}. 큰 값 = 1. 동률이면 멈춤."""
    if len(set(d.values())) != len(d):
        stop(f"순위 동률: {d}")
    order = sorted(d, key=lambda j: -d[j])
    return {j: i + 1 for i, j in enumerate(order)}


def largest_remainder(a, label):
    """a: {j: Fraction}, 합 1. 반환 {j: 문자열}."""
    if sum(a.values()) != 1:
        stop(f"{label}: 식 합이 1이 아님")
    v = {j: a[j] * 10000 for j in a}
    q = {j: math.floor(v[j]) for j in a}
    r = {j: v[j] - q[j] for j in a}
    R = 10000 - sum(q.values())
    if not 0 <= R <= 9:
        stop(f"{label}: R={R}")
    order = sorted(a, key=lambda j: -r[j])
    if 0 < R < len(order) and r[order[R - 1]] == r[order[R]]:
        stop(f"{label}: R번째와 R+1번째 잔여 동률")
    for j in order[:R]:
        q[j] += 1
    if sum(q.values()) != 10000:
        stop(f"{label}: 합이 100.00 아님")
    return {j: f"{q[j] // 100}.{q[j] % 100:02d}" for j in a}


# ---- 읽기 ----
rows = []
with open(SRC, encoding="utf-8-sig", newline="") as fh:
    for rec in csv.DictReader(fh):
        try:
            y, m, d = (int(p) for p in rec["구입일"].strip().split("-"))
            dt = date(y, m, d)
        except ValueError:
            stop(f"구입일 변환 실패: {rec['자료ID']}")
            continue
        try:
            loan = int(rec["대출횟수"].strip())
            price = int(rec["구입가격"].strip())
        except ValueError:
            stop(f"정수 변환 실패: {rec['자료ID']}")
            continue
        s = rec["주제분류명"]
        if s not in SUBJ:
            stop(f"주제 밖 값: {s!r}")
        rows.append((s, dt, price, loan))

N1 = len(rows)
tgt = [r for r in rows if r[1] <= CUT]
N2 = len(tgt)
N27 = sum(1 for r in rows if r[1] > CUT)

loans = [r[3] for r in tgt]
# N3~N6: float64 (명세 6-1). 합은 정수, 편차 제곱합은 정확 계산 뒤 float로 -> 검산 겸용
mu = sum(loans) / N2
ss = sum((Fraction(x) - Fraction(sum(loans), N2)) ** 2 for x in loans)
sd = math.sqrt(float(ss / (N2 - 1)))
lo, hi = mu - 3 * sd, mu + 3 * sd
is_out = lambda x: x > hi or x < lo  # noqa: E731
# 경계 판정이 float 오차에 민감한지 정확 비교로 확인
mu_ex = Fraction(sum(loans), N2)
for x in set(loans):
    ex = (x - mu_ex) ** 2 > 9 * (ss / (N2 - 1))
    if ex != is_out(x):
        stop(f"float 판정과 정확 판정이 다른 값 {x}")

out_rows = [r for r in tgt if is_out(r[3])]
exc_rows = [r for r in tgt if not is_out(r[3])]
N7, N8 = len(out_rows), len(exc_rows)
N9 = sum(loans)
N10 = sum(r[3] for r in exc_rows)
N11 = sum(r[3] for r in out_rows)
N20 = sum(r[2] for r in tgt)

V = {}
V[1] = ("입력 행 수", str(N1))
V[2] = ("대상 권수", str(N2))
V[3] = ("대상 대출횟수 평균", r4(mu))
V[4] = ("대상 대출횟수 표본 표준편차", r4(sd))
V[5] = ("이상치 아래 경계", r4(lo))
V[6] = ("이상치 위 경계", r4(hi))
V[7] = ("이상치 권수", str(N7))
V[8] = ("제외 후 권수", str(N8))
V[9] = ("유지 대상 대출 합", str(N9))
V[10] = ("제외 후 대출 합", str(N10))
V[11] = ("이상치 대출 합", str(N11))
V[12] = ("이상치 대출 합 비중", r2(Fraction(N11, N9) * 100))
V[13] = ("이상치 권수 비율", r2(Fraction(N7, N2) * 100))
V[14] = ("이상치 대출횟수 최솟값", str(min(r[3] for r in out_rows)))
V[15] = ("이상치 대출횟수 최댓값", str(max(r[3] for r in out_rows)))
V[16] = ("유지 대상 대출 평균", r2(Fraction(N9, N2)))
V[17] = ("유지 대상 대출 중앙값", str(median(loans)))
V[18] = ("제외 후 대출 평균", r2(Fraction(N10, N8)))
V[19] = ("제외 후 대출 중앙값", str(median([r[3] for r in exc_rows])))
V[20] = ("대상 구입가격 합", str(N20))
V[21] = ("대상 구입가격 평균", r2(Fraction(N20, N2)))
V[22] = ("대상 구입가격 중앙값", str(median([r[2] for r in tgt])))

# ---- 주제별 ----
S = {}
for j, s in enumerate(SUBJ):
    keep = [r for r in tgt if r[0] == s]
    exc = [r for r in keep if not is_out(r[3])]
    outj = [r for r in keep if is_out(r[3])]
    g = dict(B=len(keep), L=sum(r[3] for r in keep), B5=len(exc), L6=sum(r[3] for r in exc),
             O=len(outj), OL=sum(r[3] for r in outj), G=sum(r[2] for r in keep),
             med_keep=median([r[3] for r in keep]) if keep else None,
             med_exc=median([r[3] for r in exc]) if exc else None,
             med_price=median([r[2] for r in keep]) if keep else None)
    if g["B"] == 0 or g["B5"] == 0 or g["L"] == 0 or g["L6"] == 0:
        stop(f"{s}: 권수 또는 대출 합 0")
    S[j] = g

mean_keep = {j: Fraction(S[j]["L"], S[j]["B"]) for j in S}
mean_exc = {j: Fraction(S[j]["L6"], S[j]["B5"]) for j in S}
pmean = {j: Fraction(S[j]["G"], S[j]["B"]) for j in S}
rk4, rk9, rk20 = rank_desc(mean_keep), rank_desc(mean_exc), rank_desc(pmean)
rk31 = rank_desc({j: Fraction(S[j]["L"]) for j in S})
rk32 = rank_desc({j: Fraction(S[j]["L6"]) for j in S})
if len({S[j]["B"] for j in S}) != 10:
    stop("유지 권수 동률 (표 행 순서)")

V[23] = ("주제별 구입가격 평균 최댓값-최솟값", r2(max(pmean.values()) - min(pmean.values())))
V[24] = ("주제별 구입가격 평균 차이의 대상 평균 대비", r2((max(pmean.values()) - min(pmean.values())) / Fraction(N20, N2) * 100))
V[25] = ("대상 대출 0회 권수", str(sum(1 for x in loans if x == 0)))
V[26] = ("대상 대출 0회 비율", r2(Fraction(sum(1 for x in loans if x == 0), N2) * 100))
V[27] = ("대상 밖 권수 (2023년 이후 구입)", str(N27))

# 시나리오
sc = {}
for T, Lk, LS in (("유지", "L", N9), ("제외", "L6", N10)):
    sc[("1", T)] = largest_remainder({j: Fraction(S[j][Lk], LS) for j in S}, f"시나리오1 {T}")
    den = sum(S[j][Lk] * pmean[j] for j in S)
    sc[("2", T)] = largest_remainder({j: S[j][Lk] * pmean[j] / den for j in S}, f"시나리오2 {T}")
    sc[("4", T)] = largest_remainder(
        {j: Fraction(1, 2) * Fraction(S[j]["B"], N2) + Fraction(1, 2) * Fraction(S[j][Lk], LS) for j in S},
        f"시나리오4 {T}")
sc[("3", "")] = largest_remainder({j: Fraction(S[j]["G"], N20) for j in S}, "시나리오3")

for j, s in enumerate(SUBJ):
    g = S[j]
    f12 = Fraction(g["O"], N7) * 100
    f13 = Fraction(g["B"], N2) * 100
    items = [
        (f"유지 {s} 권수", str(g["B"])),
        (f"유지 {s} 대출 합", str(g["L"])),
        (f"유지 {s} 대출 평균", r2(mean_keep[j])),
        (f"유지 {s} 대출 중앙값", str(g["med_keep"])),
        (f"유지 {s} 대출 평균 순위", str(rk4[j])),
        (f"제외 {s} 권수", str(g["B5"])),
        (f"제외 {s} 대출 합", str(g["L6"])),
        (f"제외 {s} 대출 평균", r2(mean_exc[j])),
        (f"제외 {s} 대출 중앙값", str(g["med_exc"])),
        (f"제외 {s} 대출 평균 순위", str(rk9[j])),
        (f"{s} 이상치 권수", str(g["O"])),
        (f"{s} 주제 안 이상치 비율", r2(Fraction(g["O"], g["B"]) * 100)),
        (f"{s} 이상치 중 비중", r2(f12)),
        (f"{s} 권수 비중", r2(f13)),
        (f"{s} 이상치 중 비중-권수 비중", r2(f12 - f13)),
        (f"{s} 이상치 대출 합", str(g["OL"])),
        (f"{s} 주제 대출 합 중 이상치 비중", r2(Fraction(g["OL"], g["L"]) * 100)),
        (f"{s} 구입가격 합", str(g["G"])),
        (f"{s} 구입가격 평균", r2(pmean[j])),
        (f"{s} 구입가격 중앙값", str(g["med_price"])),
        (f"{s} 구입가격 평균 순위", str(rk20[j])),
        (f"유지 {s} 대출 비중", r2(Fraction(g["L"], N9) * 100)),
        (f"제외 {s} 대출 비중", r2(Fraction(g["L6"], N10) * 100)),
        (f"{s} 가격합 비중", r2(Fraction(g["G"], N20) * 100)),
        (f"유지 {s} 시나리오 1", sc[("1", "유지")][j]),
        (f"제외 {s} 시나리오 1", sc[("1", "제외")][j]),
        (f"유지 {s} 시나리오 2", sc[("2", "유지")][j]),
        (f"제외 {s} 시나리오 2", sc[("2", "제외")][j]),
        (f"{s} 시나리오 3", sc[("3", "")][j]),
        (f"유지 {s} 시나리오 4", sc[("4", "유지")][j]),
        (f"제외 {s} 시나리오 4", sc[("4", "제외")][j]),
        (f"유지 {s} 대출 비중 순위", str(rk31[j])),
        (f"제외 {s} 대출 비중 순위", str(rk32[j])),
    ]
    assert len(items) == 33
    for f, it in enumerate(items):
        V[28 + 33 * j + f] = it

# ---- 합 확인 (6-6) ----
chk = [
    N7 + N8 == N2, N10 + N11 == N9, N2 + N27 == N1,
    sum(S[j]["B"] for j in S) == N2, sum(S[j]["B5"] for j in S) == N8,
    sum(S[j]["L"] for j in S) == N9, sum(S[j]["L6"] for j in S) == N10,
    sum(S[j]["O"] for j in S) == N7, sum(S[j]["OL"] for j in S) == N11,
    sum(S[j]["G"] for j in S) == N20,
]
for rk in (rk4, rk9, rk20, rk31, rk32):
    chk.append(sorted(rk.values()) == list(range(1, 11)))
for key, col in sc.items():
    chk.append(sum(Fraction(v) for v in col.values()) == 100)
if not all(chk):
    stop(f"합 확인 실패: {[i for i, c in enumerate(chk) if not c]}")

assert sorted(V) == list(range(1, 358))
with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    for n in range(1, 358):
        w.writerow([f"N{n}", V[n][0], V[n][1]])

print(f"저장: {OUT} (357개). 멈춤 조건: {len(stops)}건")
for k, col in sc.items():
    print("시나리오", k, "합", sum(Fraction(v) for v in col.values()))

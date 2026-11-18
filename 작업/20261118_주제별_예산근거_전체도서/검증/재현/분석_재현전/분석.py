# 5단계 분석 — 계산명세.md (승인기록 12번) 그대로. 프로젝트 폴더에서 실행:
#   .venv/bin/python 작업/20261118_주제별_예산근거_전체도서/분석/분석.py
# 검정 없음, 난수 없음 (시드 없음).
import csv
import math
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

import numpy as np
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261118_주제별_예산근거_전체도서/분석/"
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 2절 주제 번호 j


def stop(msg):
    raise SystemExit("멈춤: " + msg)


# ---------- 6-1 반올림·표기 ----------
def r2(x):
    """Fraction -> 소수 둘째 자리 문자열, ROUND_HALF_UP (정수 연산)."""
    x = F(x)
    k = math.floor(100 * x + F(1, 2)) if x >= 0 else -math.floor(100 * -x + F(1, 2))
    if k == 0:
        return "0.00"
    s = "-" if k < 0 else ""
    k = abs(k)
    return f"{s}{k // 100}.{k % 100:02d}"


def r4(x):
    d = Decimal(repr(float(x))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return "0.0000" if d == 0 else str(d)


def median(vals):
    """보간 없음: 오름차순 ⌈n/2⌉번째 값 (1부터)."""
    v = sorted(vals)
    return v[math.ceil(len(v) / 2) - 1]


def ranks(vals):
    """공동 순위: 1 + (값이 더 큰 주제 수)."""
    return [1 + sum(w > v for w in vals) for v in vals]


def largest_remainder(a, name):
    """a: Fraction 10개 (합 1). 최대 잔여 방식 -> 보고 문자열 10개."""
    if sum(a) != 1:
        stop(f"{name} 식의 합이 1이 아님")
    v = [x * 10000 for x in a]
    q = [math.floor(x) for x in v]
    r = [x - qi for x, qi in zip(v, q)]
    R = 10000 - sum(q)
    if not 0 <= R <= 9:
        stop(f"{name} R={R}")
    order = sorted(range(10), key=lambda j: r[j], reverse=True)
    if 0 < R < 10 and r[order[R - 1]] == r[order[R]]:
        stop(f"{name} 최대 잔여 경계 동률 ({SUBJ[order[R - 1]]}, {SUBJ[order[R]]})")
    for j in order[:R]:
        q[j] += 1
    if sum(q) != 10000:
        stop(f"{name} 합 확인 실패")
    return [f"{x // 100}.{x % 100:02d}" for x in q]


# ---------- 읽기 (2절) ----------
df = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
df = df[["자료ID", "주제분류명", "구입일", "구입가격", "대출횟수"]]  # 3절 쓰는 열만
N1 = len(df)

subj = df["주제분류명"].str.strip().tolist()
bad = sorted(set(subj) - set(SUBJ))
if bad:
    stop(f"주제 밖 값 {bad}")

date = pd.to_datetime(df["구입일"].str.strip(), format="%Y-%m-%d", errors="coerce")
if date.isna().any():
    stop(f"구입일 날짜 변환 실패 {int(date.isna().sum())}칸")


def to_int(col):
    out = []
    for i, s in enumerate(df[col].str.strip()):
        try:
            out.append(int(s))
        except ValueError:
            stop(f"{col} 정수 변환 실패 (행 {i + 2}: {s!r})")
    return out


loan = to_int("대출횟수")
price = to_int("구입가격")
after23 = (date >= pd.Timestamp("2023-01-01")).tolist()

# 대상 = 입력 전체
N2 = len(loan)
if N2 != N1:
    stop("N2 != N1")

# ---------- 평균±3SD (float, 6-1) ----------
arr = np.array(loan, dtype=np.float64)
mu = np.float64(sum(loan)) / N2
sd = np.std(arr, ddof=1)
lo, hi = mu - 3 * sd, mu + 3 * sd
out = [(x > hi) or (x < lo) for x in loan]

N7 = sum(out)
N8 = sum(not o for o in out)
if N7 == 0:
    stop("N7 = 0")
N9 = sum(loan)
N10 = sum(x for x, o in zip(loan, out) if not o)
N11 = sum(x for x, o in zip(loan, out) if o)
olo = [x for x, o in zip(loan, out) if o]
keep_loan = [x for x, o in zip(loan, out) if not o]
N20 = sum(price)
N25 = sum(x == 0 for x in loan)
N27 = sum(after23)
if N27 == 0:
    stop("N27 = 0")

K = {}  # 번호 -> (항목, 값 문자열)
K[1] = ("입력 행 수", str(N1))
K[2] = ("대상 권수", str(N2))
K[3] = ("대상 대출횟수 평균", r4(mu))
K[4] = ("대상 대출횟수 표본 표준편차", r4(sd))
K[5] = ("이상치 아래 경계", r4(lo))
K[6] = ("이상치 위 경계", r4(hi))
K[7] = ("이상치 권수", str(N7))
K[8] = ("제외 후 권수", str(N8))
K[9] = ("유지 대상 대출 합", str(N9))
K[10] = ("제외 후 대출 합", str(N10))
K[11] = ("이상치 대출 합", str(N11))
K[12] = ("이상치 대출 합 비중", r2(F(N11, N9) * 100))
K[13] = ("이상치 권수 비율", r2(F(N7, N2) * 100))
K[14] = ("이상치 대출횟수 최솟값", str(min(olo)))
K[15] = ("이상치 대출횟수 최댓값", str(max(olo)))
K[16] = ("유지 대상 대출 평균", r2(F(N9, N2)))
K[17] = ("유지 대상 대출 중앙값", str(median(loan)))
K[18] = ("제외 후 대출 평균", r2(F(N10, N8)))
K[19] = ("제외 후 대출 중앙값", str(median(keep_loan)))
K[20] = ("대상 구입가격 합", str(N20))
K[21] = ("대상 구입가격 평균", r2(F(N20, N2)))
K[22] = ("대상 구입가격 중앙값", str(median(price)))
# N23, N24는 주제별 값 뒤에
K[25] = ("대상 대출 0회 권수", str(N25))
K[26] = ("대상 대출 0회 비율", r2(F(N25, N2) * 100))
K[27] = ("2023년 이후 구입 권수", str(N27))
K[28] = ("2023년 이후 구입 비율", r2(F(N27, N2) * 100))

# ---------- 주제별 정확한 값 ----------
rows = list(zip(subj, loan, price, out, after23))
S = []  # 주제 j마다 dict (정확한 값)
for s in SUBJ:
    g = [r for r in rows if r[0] == s]
    gk = [r for r in g if not r[3]]
    go = [r for r in g if r[3]]
    d = dict(
        f0=len(g), f1=sum(r[1] for r in g), f3=median([r[1] for r in g]),
        f5=len(gk), f6=sum(r[1] for r in gk), f8=median([r[1] for r in gk]) if gk else None,
        f10=len(go), f15=sum(r[1] for r in go),
        f17=sum(r[2] for r in g), f19=median([r[2] for r in g]),
        f33=sum(r[4] for r in g),
    )
    if d["f0"] == 0 or d["f5"] == 0:
        stop(f"{s} 권수 0")
    if d["f1"] == 0 or d["f6"] == 0:
        stop(f"{s} 대출 합 0")
    d["f2"] = F(d["f1"], d["f0"])
    d["f7"] = F(d["f6"], d["f5"])
    d["f11"] = F(d["f10"], d["f0"]) * 100
    d["f12"] = F(d["f10"], N7) * 100
    d["f13"] = F(d["f0"], N2) * 100
    d["f14"] = d["f12"] - d["f13"]
    d["f16"] = F(d["f15"], d["f1"]) * 100
    d["f18"] = F(d["f17"], d["f0"])
    d["f21"] = F(d["f1"], N9) * 100
    d["f22"] = F(d["f6"], N10) * 100
    d["f23"] = F(d["f17"], N20) * 100
    d["f34"] = F(d["f33"], d["f0"]) * 100
    S.append(d)

for key, src in [("f4", "f2"), ("f9", "f7"), ("f20", "f18"), ("f31", "f1"), ("f32", "f6")]:
    for d, rk in zip(S, ranks([d[src] for d in S])):
        d[key] = rk

# 6-5 시나리오 (정확한 분수)
B = [F(d["f0"], N2) for d in S]
P = [d["f18"] for d in S]
for T, Lkey, Ltot, f1c, f2c, f4c in [("유지", "f1", N9, "f24", "f26", "f29"), ("제외", "f6", N10, "f25", "f27", "f30")]:
    L = [F(d[Lkey], Ltot) for d in S]
    LP = [F(d[Lkey]) * p for d, p in zip(S, P)]
    a1 = L
    a2 = [x / sum(LP) for x in LP]
    a4 = [F(1, 2) * b + F(1, 2) * l for b, l in zip(B, L)]
    for key, a in [(f1c, a1), (f2c, a2), (f4c, a4)]:
        for d, v in zip(S, largest_remainder(a, f"{key} ({T})")):
            d[key] = v
for d, v in zip(S, largest_remainder([F(d["f17"], N20) for d in S], "f28")):
    d["f28"] = v

f18s = [d["f18"] for d in S]
N23 = max(f18s) - min(f18s)
K[23] = ("주제별 구입가격 평균의 최댓값 - 최솟값", r2(N23))
K[24] = ("N23의 대상 구입가격 평균 대비 크기", r2(N23 / F(N20, N2) * 100))

NAMES = [  # f -> (처리, 수치 이름, 형식)  형식: i 정수, p Fraction 둘째, s 이미 문자열
    ("유지", "권수", "i"), ("유지", "대출 합", "i"), ("유지", "대출 평균", "p"), ("유지", "대출 중앙값", "i"),
    ("유지", "대출 평균 순위", "i"), ("제외", "권수", "i"), ("제외", "대출 합", "i"), ("제외", "대출 평균", "p"),
    ("제외", "대출 중앙값", "i"), ("제외", "대출 평균 순위", "i"), ("", "이상치 권수", "i"),
    ("", "주제 안 이상치 비율", "p"), ("", "이상치 중 비중", "p"), ("", "권수 비중", "p"),
    ("", "이상치 중 비중 - 권수 비중", "p"), ("", "이상치 대출 합", "i"), ("", "주제 대출 합 중 이상치 비중", "p"),
    ("", "구입가격 합", "i"), ("", "구입가격 평균", "p"), ("", "구입가격 중앙값", "i"), ("", "구입가격 평균 순위", "i"),
    ("유지", "대출 비중", "p"), ("제외", "대출 비중", "p"), ("", "가격합 비중", "p"),
    ("유지", "시나리오 1", "s"), ("제외", "시나리오 1", "s"), ("유지", "시나리오 2", "s"), ("제외", "시나리오 2", "s"),
    ("", "시나리오 3", "s"), ("유지", "시나리오 4", "s"), ("제외", "시나리오 4", "s"),
    ("유지", "대출 비중 순위", "i"), ("제외", "대출 비중 순위", "i"),
    ("", "2023년 이후 구입 권수", "i"), ("", "2023년 이후 구입 비율", "p"),
]
for j, (s, d) in enumerate(zip(SUBJ, S)):
    for f, (t, nm, fm) in enumerate(NAMES):
        v = d[f"f{f}"]
        val = str(v) if fm == "i" else r2(v) if fm == "p" else v
        K[29 + 35 * j + f] = (" ".join(x for x in (t, s, nm) if x), val)

if sorted(K) != list(range(1, 379)):
    stop("핵심 수치 번호 1~378이 아님")

# ---------- 6-6 합 확인 ----------
def tot(f):
    return sum(d[f] for d in S)


checks = {
    "N2 = N1": N2 == N1, "N7 + N8 = N2": N7 + N8 == N2, "N10 + N11 = N9": N10 + N11 == N9, "N27 <= N2": N27 <= N2,
    "Σf0 = N2": tot("f0") == N2, "Σf5 = N8": tot("f5") == N8, "Σf1 = N9": tot("f1") == N9,
    "Σf6 = N10": tot("f6") == N10, "Σf10 = N7": tot("f10") == N7, "Σf15 = N11": tot("f15") == N11,
    "Σf17 = N20": tot("f17") == N20, "Σf33 = N27": tot("f33") == N27,
}
for rk, src in [("f4", "f2"), ("f9", "f7"), ("f20", "f18"), ("f31", "f1"), ("f32", "f6")]:
    checks[f"{rk} 순위 식"] = [d[rk] for d in S] == ranks([d[src] for d in S])
    checks[f"{rk} 1~10 한 번씩"] = sorted(d[rk] for d in S) == list(range(1, 11))
for f in range(24, 31):
    checks[f"f{f} 합 100.00"] = sum(Decimal(d[f"f{f}"]) for d in S) == Decimal("100.00")
checks["처리마다 권수·대출 합 1 이상"] = all(d["f0"] >= 1 and d["f5"] >= 1 and d["f1"] >= 1 and d["f6"] >= 1 for d in S)
for k, ok in checks.items():
    print(f"[합 확인] {k}: {'통과' if ok else '실패'}")
fails = [k for k, ok in checks.items() if not ok and "한 번씩" not in k]
if fails:
    stop(f"합 확인 실패 {fails}")
# '1~10 한 번씩' 실패는 공동 순위(승인 9번)일 때 허용 — 순위 식 확인만 멈춤 조건

# ---------- 행 순서 (f0 내림차순, 동률이면 멈춤) ----------
f0s = [d["f0"] for d in S]
if len(set(f0s)) != 10:
    stop("행 순서: 유지 권수 동률")
ORDER = sorted(range(10), key=lambda j: -f0s[j])


def kv(j, f):
    return K[29 + 35 * j + f][1]


def V(n):
    return K[n][1]


# ---------- CSV 쓰기 ----------
def write_csv(name, header, body):
    for r in body:
        if len(r) != len(header):
            stop(f"{name} 열 수 불일치")
    with open(OUT + name, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(body)
    with open(OUT + name, encoding="utf-8-sig", newline="") as fh:
        got = list(csv.reader(fh))
    assert all(len(r) == len(header) for r in got) and len(got) == len(body) + 1, name
    print(f"[저장] {name}: {len(got)}줄 x {len(header)}열")


write_csv("핵심수치.csv", ["번호", "항목", "값"], [[f"N{n}", K[n][0], K[n][1]] for n in range(1, 379)])


def table(name, header, fs, total):
    body = [[SUBJ[j]] + [kv(j, f) for f in fs] for j in ORDER]
    body.append(["대상 전체"] + total)
    write_csv(name, header, body)


table("표1_주제별_장서수_대출횟수.csv",
      ["주제분류명", "유지 권수", "유지 대출 합", "유지 평균", "유지 중앙값", "유지 평균 순위",
       "제외 권수", "제외 대출 합", "제외 평균", "제외 중앙값", "제외 평균 순위",
       "2023년 이후 구입 권수", "2023년 이후 구입 비율%"],
      [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 33, 34],
      [V(2), V(9), V(16), V(17), "", V(8), V(10), V(18), V(19), "", V(27), V(28)])
table("표2_대출이상치_주제별.csv",
      ["주제분류명", "대상 권수", "이상치 권수", "주제 안 이상치 비율%", "이상치 중 비중%", "권수 비중%",
       "차이 %p", "이상치 대출 합", "주제 대출 합 중 이상치 비중%"],
      [0, 10, 11, 12, 13, 14, 15, 16],
      [V(2), V(7), V(13), "", "", "", V(11), V(12)])
table("표3_주제별_구입가격.csv",
      ["주제분류명", "권수", "구입가격 합", "평균", "평균 순위", "중앙값"],
      [0, 17, 18, 20, 19],
      [V(2), V(20), V(21), "", V(22)])
table("표4_배분근거지표.csv",
      ["주제분류명", "권수 비중%", "대출 비중% 유지", "대출 비중 순위 유지", "대출 비중% 제외", "대출 비중 순위 제외",
       "가격합 비중%", "구입가격 평균", "2023년 이후 구입 비율%"],
      [13, 21, 31, 22, 32, 23, 18, 34],
      ["", "", "", "", "", "", V(21), V(28)])
table("표5_배분비율_시나리오.csv",
      ["주제분류명", "시나리오 1 유지", "시나리오 1 제외", "시나리오 2 유지", "시나리오 2 제외",
       "시나리오 3 (대상 장서 구입가격 구성대로)", "시나리오 4 유지", "시나리오 4 제외"],
      [24, 25, 26, 27, 28, 29, 30],
      ["100.00"] * 7)

# ---------- 그림 1 (유지만, 규칙 10) ----------
from matplotlib import font_manager, pyplot as plt
FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

names = [SUBJ[j] for j in ORDER]
cnt = [int(kv(j, 0)) for j in ORDER]
mean_s = [kv(j, 2) for j in ORDER]
med_s = [kv(j, 3) for j in ORDER]
x = np.arange(10)
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 9))
b = a1.bar(x, cnt, color="#4C72B0")
a1.bar_label(b, labels=[f"{c:,}" for c in cnt], padding=2)
a1.set_ylabel("장서 수 (권)")
a1.set_xlabel("주제분류명")
a1.set_xticks(x, names)
a1.margins(y=0.12)
w = 0.38
b1 = a2.bar(x - w / 2, [float(v) for v in mean_s], w, label="평균", color="#4C72B0")
b2 = a2.bar(x + w / 2, [float(v) for v in med_s], w, label="중앙값", color="#DD8452")
a2.bar_label(b1, labels=mean_s, padding=2)
a2.bar_label(b2, labels=med_s, padding=2)
a2.set_ylabel("대출횟수 (회)")
a2.set_xlabel("주제분류명")
a2.set_xticks(x, names)
a2.legend()
a2.margins(y=0.15)
fig.suptitle("주제분류명별 장서 수와 대출횟수(2023~2025년) 평균·중앙값", fontsize=15)
note = (f"대상: P02_장서목록_대출횟수의 책 {int(V(2)):,}권 전부. 대출횟수는 2023~2025년 3년간 대출된 횟수이며, "
        f"이상치 {int(V(7)):,}권을 포함한 값이다. 2023년 이후 구입분 {int(V(27)):,}권({V(28)}%)이 들어 있다.")
med_01 = all(kv(j, 3) in ("0", "1") for j in range(10))
if med_01:
    note += f"\n대상의 {V(26)}%가 대출 0회이고, 주제별 중앙값은 0 또는 1이다."
else:
    print("[알림] f3 중 0·1 밖 값이 있어 그림 각주 마지막 문장을 뺐다")
fig.text(0.5, -0.01, note, ha="center", va="top", fontsize=10)
fig.tight_layout()
fig.savefig(OUT + "그림1_주제별_장서수_대출횟수_유지.png", dpi=150, bbox_inches="tight")
print("[저장] 그림1_주제별_장서수_대출횟수_유지.png")

# ---------- 7단계용 참고 출력 (새 수치 아님, 보고만) ----------
print("[참고] 행 순서:", " ".join(names))
print("[참고] f3·f8 모두 0 또는 1:", med_01 and all(kv(j, 8) in ("0", "1") for j in range(10)))
for rk, src, fv in [("f4", "f2", 2), ("f9", "f7", 7), ("f20", "f18", 18), ("f31", "f21", 21), ("f32", "f22", 22)]:
    for i in range(10):
        for k in range(i + 1, 10):
            if kv(i, fv) == kv(k, fv) and S[i][rk] != S[k][rk]:
                print(f"[참고] {rk}: {SUBJ[i]}·{SUBJ[k]} 보고 값 {kv(i, fv)} 같고 순위 {S[i][rk]}·{S[k][rk]}")
f14r = [kv(j, 14) for j in range(10)]
for i in range(10):
    for k in range(i + 1, 10):
        if f14r[i] == f14r[k] and S[i]["f14"] == S[k]["f14"]:
            print(f"[참고] f14 보고 값·정확한 값 모두 같음: {SUBJ[i]}·{SUBJ[k]} (6-4절 멈춤 조건)")

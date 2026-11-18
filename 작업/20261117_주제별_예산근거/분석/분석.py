# 질문 4 — 주제별 대출횟수·이상치·구입가격과 배분 비율 시나리오 (계산명세.md, 승인기록 13번)
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261117_주제별_예산근거/분석/분석.py
# 난수 없음. 원자료는 읽기만 한다. 결과.md 의 "분석.py n" 은 이 파일의 줄 번호다 (# @표지 로 찾는다).
import csv
import math
import re
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction as F

import numpy as np
import pandas as pd
from matplotlib import font_manager, pyplot as plt

OUT = "작업/20261117_주제별_예산근거/분석/"
SRC = open(__file__, encoding="utf-8").read().splitlines()


def L(tag):  # '# @tag' 표지가 있는 줄 번호
    hits = [i + 1 for i, s in enumerate(SRC) if s.rstrip().endswith("# @" + tag)]
    assert len(hits) == 1, tag
    return hits[0]


def stop(msg):
    print("멈춤 (진행 담당에게 보고): " + msg)
    sys.exit(1)


def r2(x):  # 6-1: 분수 -> 소수 둘째 문자열, 사사오입(0에서 먼 쪽), -0.00 없음
    x = F(x)
    k = math.floor(100 * x + F(1, 2)) if x >= 0 else -math.floor(100 * -x + F(1, 2))
    a = abs(k)
    return ("-" if k < 0 else "") + f"{a // 100}.{a % 100:02d}"


def r4(x):  # N3~N6
    return str(Decimal(repr(float(x))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


def median(v):  # 2절: 보간 없이 ceil(n/2)번째 값
    s = sorted(v)
    m = s[math.ceil(len(s) / 2) - 1]
    assert m == int(np.quantile(np.array(s), 0.5, method="inverted_cdf"))
    return m


def rank(vals):  # 가장 큰 값 = 1, 동률이면 멈춤
    if len(set(vals.values())) != len(vals):
        stop("순위 동률")
    order = sorted(vals, key=lambda s: vals[s], reverse=True)
    return {s: i + 1 for i, s in enumerate(order)}


def largest_remainder(a):  # 6-5 최대 잔여 방식, a: 주제 -> 분수(합 1)
    assert sum(a.values()) == 1
    v = {s: a[s] * 10000 for s in a}
    q = {s: math.floor(v[s]) for s in a}
    r = {s: v[s] - q[s] for s in a}
    R = 10000 - sum(q.values())
    if not 0 <= R <= 9:
        stop(f"최대 잔여 R={R}")
    order = sorted(a, key=lambda s: r[s], reverse=True)
    if 0 < R < len(order) and r[order[R - 1]] == r[order[R]]:
        stop("최대 잔여 경계 동률")
    for s in order[:R]:
        q[s] += 1
    assert sum(q.values()) == 10000  # 열 합 = 100.00
    return {s: f"{q[s] // 100}.{q[s] % 100:02d}" for s in a}


# ---------- 읽기 (2절) ----------
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 2절 주제 번호 j
raw = pd.read_csv("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
df = raw[["자료ID", "주제분류명", "구입일", "구입가격", "대출횟수"]].copy()  # 3절 쓰는 열
for c in df.columns:
    df[c] = df[c].str.strip()
date = pd.to_datetime(df["구입일"], format="%Y-%m-%d", errors="coerce")
if date.isna().any():
    stop("구입일 변환 실패")
for c in ["구입가격", "대출횟수"]:
    if not df[c].str.fullmatch(r"-?[0-9]+").all():
        stop(c + " 정수 변환 실패")
if not df["주제분류명"].isin(SUBJ).all():
    stop("주제 10개 밖 값")
rows = list(zip(df["주제분류명"], (date <= pd.Timestamp("2022-12-31")).tolist(),
                [int(x) for x in df["구입가격"]], [int(x) for x in df["대출횟수"]]))

tgt = [(s, p, n) for s, t, p, n in rows if t]  # 대상
loans = [n for _, _, n in tgt]

C = {}  # 번호 -> 값 문자열
NAME = {}
C[1] = str(len(rows))  # @N1
C[2] = str(len(tgt))  # @N2
mu = float(np.sum(np.array(loans, dtype=np.float64))) / len(loans)  # @N3
sd = float(np.std(np.array(loans, dtype=np.float64), ddof=1))  # @N4
lo, hi = mu - 3 * sd, mu + 3 * sd  # @N5N6
C[3], C[4], C[5], C[6] = r4(mu), r4(sd), r4(lo), r4(hi)
is_out = lambda n: n > hi or n < lo  # @OUT
out = [(s, p, n) for s, p, n in tgt if is_out(n)]
keep = [(s, p, n) for s, p, n in tgt if not is_out(n)]
N7, N8 = len(out), len(keep)  # @N7N8
N9, N10, N11 = sum(loans), sum(n for *_, n in keep), sum(n for *_, n in out)  # @N9N11
N20 = sum(p for _, p, _ in tgt)  # @N20
C[7], C[8], C[9], C[10], C[11] = map(str, (N7, N8, N9, N10, N11))
C[12] = r2(F(N11, N9) * 100)  # @N12
C[13] = r2(F(N7, len(tgt)) * 100)  # @N13
C[14] = str(min(n for *_, n in out))  # @N14
C[15] = str(max(n for *_, n in out))  # @N15
C[16] = r2(F(N9, len(tgt)))  # @N16
C[17] = str(median(loans))  # @N17
C[18] = r2(F(N10, N8))  # @N18
C[19] = str(median([n for *_, n in keep]))  # @N19
C[20] = str(N20)
C[21] = r2(F(N20, len(tgt)))  # @N21
C[22] = str(median([p for _, p, _ in tgt]))  # @N22
N25 = sum(1 for n in loans if n == 0)  # @N25
C[25] = str(N25)
C[26] = r2(F(N25, len(tgt)) * 100)  # @N26
C[27] = str(int((date > pd.Timestamp("2022-12-31")).sum()))  # 조건으로 셈 # @N27
for k, v in {1: "입력 행 수", 2: "대상 권수", 3: "대상 대출횟수 평균", 4: "대상 대출횟수 표본 표준편차",
             5: "이상치 아래 경계", 6: "이상치 위 경계", 7: "이상치 권수", 8: "제외 후 권수",
             9: "유지 대상 대출 합", 10: "제외 대상 대출 합", 11: "이상치 대출 합", 12: "이상치 대출 합 비중",
             13: "이상치 권수 비율", 14: "이상치 대출횟수 최솟값", 15: "이상치 대출횟수 최댓값",
             16: "유지 대상 대출 평균", 17: "유지 대상 대출 중앙값", 18: "제외 대상 대출 평균",
             19: "제외 대상 대출 중앙값", 20: "대상 구입가격 합", 21: "대상 구입가격 평균",
             22: "대상 구입가격 중앙값", 23: "주제별 구입가격 평균 최댓값 - 최솟값",
             24: "주제별 구입가격 평균 차이의 대상 평균 대비 크기", 25: "대상 대출 0회 권수",
             26: "대상 대출 0회 비율", 27: "대상 밖 권수 (2023년 이후 구입)"}.items():
    NAME[k] = v

# ---------- 주제별 (6-3) ----------
X = {}  # 주제 -> 정확한 값(분수·정수) 사전
for s in SUBJ:
    a = [x for x in tgt if x[0] == s]
    k = [x for x in keep if x[0] == s]
    o = [x for x in out if x[0] == s]
    if not a or not k:
        stop(s + " 권수 0")
    d = dict(f0=len(a), f1=sum(x[2] for x in a), f5=len(k), f6=sum(x[2] for x in k),  # @F0156
             f10=len(o), f15=sum(x[2] for x in o), f17=sum(x[1] for x in a))  # @F101517
    if d["f1"] == 0 or d["f6"] == 0:
        stop(s + " 대출 합 0")
    d["f2"] = F(d["f1"], d["f0"])  # @F2
    d["f3"] = median([x[2] for x in a])  # @F3
    d["f7"] = F(d["f6"], d["f5"])  # @F7
    d["f8"] = median([x[2] for x in k])  # @F8
    d["f11"] = F(d["f10"], d["f0"]) * 100  # @F11
    d["f12"] = F(d["f10"], N7) * 100  # @F12
    d["f13"] = F(d["f0"], len(tgt)) * 100  # @F13
    d["f14"] = d["f12"] - d["f13"]  # @F14
    d["f16"] = F(d["f15"], d["f1"]) * 100  # @F16
    d["f18"] = F(d["f17"], d["f0"])  # @F18
    d["f19"] = median([x[1] for x in a])  # @F19
    d["f21"] = F(d["f1"], N9) * 100  # @F21
    d["f22"] = F(d["f6"], N10) * 100  # @F22
    d["f23"] = F(d["f17"], N20) * 100  # @F23
    X[s] = d
for f, src in [("f4", "f2"), ("f9", "f7"), ("f20", "f18"), ("f31", "f1"), ("f32", "f6")]:  # @RANK
    for s, rk in rank({s: X[s][src] for s in SUBJ}).items():
        X[s][f] = rk

# 시나리오 (6-5): B 권수, L 대출 합(T), P 가격 평균(유지), G 가격 합
sc = {}
for T, Lf, LS in [("유지", "f1", N9), ("제외", "f6", N10)]:
    sc["1" + T] = {s: F(X[s][Lf], LS) for s in SUBJ}  # @SC1
    w = {s: X[s][Lf] * X[s]["f18"] for s in SUBJ}
    sc["2" + T] = {s: w[s] / sum(w.values()) for s in SUBJ}  # @SC2
    sc["4" + T] = {s: F(1, 2) * F(X[s]["f0"], len(tgt)) + F(1, 2) * F(X[s][Lf], LS) for s in SUBJ}  # @SC4
sc["3"] = {s: F(X[s]["f17"], N20) for s in SUBJ}  # @SC3
for f, key in [("f24", "1유지"), ("f25", "1제외"), ("f26", "2유지"), ("f27", "2제외"),
               ("f28", "3"), ("f29", "4유지"), ("f30", "4제외")]:
    for s, v in largest_remainder(sc[key]).items():  # @LR
        X[s][f] = v

f18s = {s: X[s]["f18"] for s in SUBJ}
N23 = max(f18s.values()) - min(f18s.values())  # @N23
C[23] = r2(N23)
C[24] = r2(N23 / F(N20, len(tgt)) * 100)  # @N24

FN = {0: ("유지", "권수"), 1: ("유지", "대출 합"), 2: ("유지", "대출 평균"), 3: ("유지", "대출 중앙값"),
      4: ("유지", "대출 평균 순위"), 5: ("제외", "권수"), 6: ("제외", "대출 합"), 7: ("제외", "대출 평균"),
      8: ("제외", "대출 중앙값"), 9: ("제외", "대출 평균 순위"), 10: ("", "이상치 권수"),
      11: ("", "주제 안 이상치 비율"), 12: ("", "이상치 중 비중"), 13: ("", "권수 비중"),
      14: ("", "이상치 중 비중 - 권수 비중"), 15: ("", "이상치 대출 합"), 16: ("", "주제 대출 합 중 이상치 비중"),
      17: ("", "구입가격 합"), 18: ("", "구입가격 평균"), 19: ("", "구입가격 중앙값"), 20: ("", "구입가격 평균 순위"),
      21: ("유지", "대출 비중"), 22: ("제외", "대출 비중"), 23: ("", "가격합 비중"), 24: ("유지", "시나리오 1"),
      25: ("제외", "시나리오 1"), 26: ("유지", "시나리오 2"), 27: ("제외", "시나리오 2"), 28: ("", "시나리오 3"),
      29: ("유지", "시나리오 4"), 30: ("제외", "시나리오 4"), 31: ("유지", "대출 비중 순위"), 32: ("제외", "대출 비중 순위")}
INT_F = {0, 1, 3, 4, 5, 6, 8, 9, 10, 15, 17, 19, 20, 31, 32}
for j, s in enumerate(SUBJ):
    for f in range(33):
        v = X[s][f"f{f}"]
        n = 28 + 33 * j + f
        C[n] = v if isinstance(v, str) else (str(v) if f in INT_F else r2(v))
        NAME[n] = " ".join(x for x in (FN[f][0], s, FN[f][1]) if x)
V = lambda s, f: C[28 + 33 * SUBJ.index(s) + f]  # 보고 값 문자열

# ---------- 합 확인 (6-6) ----------
assert N7 + N8 == len(tgt) and N10 + N11 == N9 and len(tgt) + int(C[27]) == len(rows)
for f, tot in [("f0", len(tgt)), ("f5", N8), ("f1", N9), ("f6", N10), ("f10", N7), ("f15", N11), ("f17", N20)]:
    assert sum(X[s][f] for s in SUBJ) == tot, f
for f in ["f4", "f9", "f20", "f31", "f32"]:
    assert sorted(X[s][f] for s in SUBJ) == list(range(1, 11)), f
for f in range(24, 31):
    assert sum(Decimal(V(s, f)) for s in SUBJ) == Decimal("100.00"), f  # 시나리오 열 합 = 100.00
assert len(C) == 357 and sorted(C) == list(range(1, 358))

with open(OUT + "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    for n in range(1, 358):
        w.writerow([f"N{n}", NAME[n], C[n]])

# ---------- 표 (7-2), 행 순서 = 유지 권수 내림차순 ----------
if len({X[s]["f0"] for s in SUBJ}) != 10:
    stop("권수 동률 (행 순서)")
ORD = sorted(SUBJ, key=lambda s: X[s]["f0"], reverse=True)  # @ORDER


def table(name, cols, fs, total):
    rows_ = [[s] + [V(s, f) for f in fs] for s in ORD] + [["대상 전체"] + total]
    with open(OUT + name, "w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows([["주제분류명"] + cols] + rows_)
    return [["주제분류명"] + cols] + rows_


T1 = table("표1_주제별_장서수_대출횟수.csv",
           ["유지 권수", "유지 대출 합", "유지 평균", "유지 중앙값", "유지 평균 순위",
            "제외 권수", "제외 대출 합", "제외 평균", "제외 중앙값", "제외 평균 순위"],
           [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [C[2], C[9], C[16], C[17], "", C[8], C[10], C[18], C[19], ""])
T2 = table("표2_대출이상치_주제별.csv",
           ["대상 권수", "이상치 권수", "주제 안 이상치 비율%", "이상치 중 비중%", "권수 비중%", "차이 %p",
            "이상치 대출 합", "주제 대출 합 중 이상치 비중%"],
           [0, 10, 11, 12, 13, 14, 15, 16], [C[2], C[7], C[13], "", "", "", C[11], C[12]])
T3 = table("표3_주제별_구입가격.csv", ["권수", "구입가격 합", "평균", "평균 순위", "중앙값"],
           [0, 17, 18, 20, 19], [C[2], C[20], C[21], "", C[22]])
T4 = table("표4_배분근거지표.csv",
           ["권수 비중%", "대출 비중% 유지", "대출 비중 순위 유지", "대출 비중% 제외", "대출 비중 순위 제외",
            "가격합 비중%", "구입가격 평균"],
           [13, 21, 31, 22, 32, 23, 18], ["", "", "", "", "", "", C[21]])
SCN = ["시나리오 1 유지", "시나리오 1 제외", "시나리오 2 유지", "시나리오 2 제외",
       "시나리오 3 (대상 장서 구입가격 구성대로)", "시나리오 4 유지", "시나리오 4 제외"]
T5 = table("표5_배분비율_시나리오.csv", SCN, [24, 25, 26, 27, 28, 29, 30], ["100.00"] * 7)

# ---------- 그림 1 (7-3) ----------
FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

f3_01 = all(X[s]["f3"] in (0, 1) for s in SUBJ)
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 9))
xs = np.arange(10)
ax1.bar(xs, [X[s]["f0"] for s in ORD], color="#4C72B0")
for i, s in enumerate(ORD):
    ax1.text(i, X[s]["f0"], f"{int(V(s, 0)):,}", ha="center", va="bottom", fontsize=9)
ax1.set_xticks(xs, ORD)
ax1.set_ylabel("장서 수 (권)")
ax1.set_xlabel("주제분류명")
ax1.set_ylim(0, max(X[s]["f0"] for s in SUBJ) * 1.12)
wd = 0.38
ax2.bar(xs - wd / 2, [float(X[s]["f2"]) for s in ORD], wd, label="평균", color="#DD8452")
ax2.bar(xs + wd / 2, [X[s]["f3"] for s in ORD], wd, label="중앙값", color="#55A868")
for i, s in enumerate(ORD):
    ax2.text(i - wd / 2, float(X[s]["f2"]), V(s, 2), ha="center", va="bottom", fontsize=8)
    ax2.text(i + wd / 2, X[s]["f3"], V(s, 3), ha="center", va="bottom", fontsize=8)
ax2.set_xticks(xs, ORD)
ax2.set_ylabel("대출횟수 (회)")
ax2.set_xlabel("주제분류명")
ax2.set_ylim(0, max(float(X[s]["f2"]) for s in SUBJ) * 1.15)
ax2.legend()
fig.suptitle("주제분류명별 장서 수와 대출횟수(2023~2025년) 평균·중앙값")
note = (f"대상: 2022-12-31 이전에 구입한 책 {int(C[2]):,}권. 대출횟수는 2023~2025년 3년간 대출된 횟수이며, "
        f"이상치 {int(C[7]):,}권을 포함한 값이다.")
if f3_01:
    note += f" 대상의 {C[26]}%가 대출 0회라 중앙값은 0 또는 1에 머문다."
else:
    print("알림: f3 가 0/1 밖 값이 있어 그림 각주 마지막 문장을 뺐다")
fig.text(0.5, -0.01, note, ha="center", va="top", fontsize=9)
fig.tight_layout()
# 그림 숫자 = 핵심수치.csv 값 확인 (저장한 csv를 다시 읽어 대조)
KC = {r["번호"]: r["값"] for r in csv.DictReader(open(OUT + "핵심수치.csv", encoding="utf-8-sig"))}
kv = lambda s, f: KC[f"N{28 + 33 * SUBJ.index(s) + f}"]
assert [t.get_text().replace(",", "") for t in ax1.texts] == [kv(s, 0) for s in ORD]
assert [t.get_text() for t in ax2.texts] == [x for s in ORD for x in (kv(s, 2), kv(s, 3))]
assert note.replace(",", "").count(KC["N2"]) == 1 and f"이상치 {KC['N7']}권" in note.replace(",", "")
assert (not f3_01) or f"{KC['N26']}%" in note
fig.savefig(OUT + "그림1_주제별_장서수_대출횟수_유지.png", dpi=150, bbox_inches="tight")
plt.close(fig)

# ---------- 결과.md (7-4) ----------
P = lambda tag: f"분석.py {L(tag)}"
sg = lambda d: ("+" if d > 0 else "") + f"{d:.2f}"  # Decimal 차이 부호 표기


def md(tb):
    out_ = ["| " + " | ".join(tb[0]) + " |", "|" + "---|" * len(tb[0])]
    return "\n".join(out_ + ["| " + " | ".join(r) + " |" for r in tb[1:]])


# 문장 1
ch_mean = [s for s in ORD if X[s]["f4"] != X[s]["f9"]]
ch_share = [s for s in ORD if X[s]["f31"] != X[s]["f32"]]
def chg(lst, a, b):
    return ", ".join(f"{s} {X[s][a]}위 → {X[s][b]}위" for s in lst)
s1 = (f"대출횟수 이상치 {C[7]}권을 빼면 대출 평균 순위가 바뀌는 주제는 "
      + (f"{len(ch_mean)}개" if ch_mean else "없어 바뀌지 않는다")
      + (", " if ch_mean else ". ")
      + (f"대출 비중 순위가 바뀌는 주제는 {len(ch_share)}개다" if ch_share else "대출 비중 순위는 바뀌지 않는다")
      + " (" + "; ".join(x for x in [("대출 평균 순위: " + chg(ch_mean, "f4", "f9")) if ch_mean else "",
                                     ("대출 비중 순위: " + chg(ch_share, "f31", "f32")) if ch_share else ""] if x)
      + f"). 순위 1 = 가장 큼. 근거: 핵심 수치 f4·f9·f31·f32 ({P('RANK')}).")

# 문장 2
s2_ok = all(X[s]["f3"] in (0, 1) and X[s]["f8"] in (0, 1) for s in SUBJ)
s2 = (f"대상의 {C[26]}%가 대출 0회라 주제별 중앙값이 0 또는 1뿐이다. 중앙값으로는 주제 사이를 거의 가를 수 없어, "
      f"주제 비교는 평균과 대출 합으로 본다. (N26 {P('N26')}, f3 {P('F3')}, f8 {P('F8')})") if s2_ok else ""

# 문장 3 (6-4 분류와 순서)
d14 = {s: Decimal(V(s, 14)) for s in SUBJ}
def grp(cond, rev):
    g = [s for s in SUBJ if cond(d14[s])]
    for a in g:
        for b in g:
            if a != b and d14[a] == d14[b] and X[a]["f14"] == X[b]["f14"]:
                stop("f14 동률")
    return sorted(g, key=lambda s: (d14[s], X[s]["f14"]), reverse=rev)
hi_, lo_, eq_ = grp(lambda d: d > 0, True), grp(lambda d: d < 0, False), grp(lambda d: d == 0, False)
f10s = [X[s]["f10"] for s in SUBJ]
s3 = (f"대상 전체 기준 평균±3표준편차로 고른 이상치는 {C[7]}권(대상의 {C[13]}%)이고, 대출 합의 {C[12]}%를 차지한다. "
      + (f"이상치 중 비중이 권수 비중보다 높은 주제는 {', '.join(f'{s}(+{V(s, 14)}%p)' for s in hi_)}이고" if hi_ else "")
      + (", " if hi_ and lo_ else "")
      + (f"낮은 주제는 {', '.join(f'{s}({V(s, 14)}%p)' for s in lo_)}이다. " if lo_ else ". ")
      + (f"같은 주제는 {', '.join(eq_)}이다. " if eq_ else "")
      + f"이것은 센 값의 비교다. 그 차이가 우연히 생길 수 있는 범위를 넘는지는 검정하지 않아 말할 수 없고, "
        f"주제마다 이상치가 {min(f10s)}~{max(f10s)}권이라 몇 권 차이로 비중이 크게 움직인다. "
        f"(N7 {P('N7N8')}, N12 {P('N12')}, N13 {P('N13')}, f10 {P('F101517')}, f14 {P('F14')})")

# 문장 4
smin = min(SUBJ, key=lambda s: X[s]["f18"]); smax = max(SUBJ, key=lambda s: X[s]["f18"])
med_groups = {}
for s in ORD:
    med_groups.setdefault(X[s]["f19"], []).append(s)
s4 = (f"주제별 구입가격 평균은 {smin} {V(smin, 18)}원 ~ {smax} {V(smax, 18)}원으로, 차이가 {C[23]}원"
      f"(대상 평균 {C[21]}원의 {C[24]}%)이다. 중앙값은 "
      + ", ".join(f"{m}원({'·'.join(g)})" for m, g in sorted(med_groups.items()))
      + f"이며 순위를 매기지 않았다. 평균 순위(f20)로 주제 사이 가격 차이를 말할 때는 이 차이 {C[23]}원(대상 평균의 {C[24]}%)과 함께 읽는다. "
        f"(f18 {P('F18')}, f19 {P('F19')}, f20 {P('RANK')}, N21 {P('N21')}, N23 {P('N23')}, N24 {P('N24')})")

# 문장 6
s6 = []
for k, (fu, fe) in [("1", (24, 25)), ("2", (26, 27)), ("4", (29, 30))]:
    dd = {s: Decimal(V(s, fe)) - Decimal(V(s, fu)) for s in SUBJ}
    mx = max(abs(x) for x in dd.values())
    top = [s for s in ORD if abs(dd[s]) == mx]
    s6.append(f"시나리오 {k}에서 |제외 − 유지|가 가장 큰 주제는 "
              + ", ".join(f"{s}({sg(dd[s])}%p)" for s in top) + "이다 (반올림한 표 값끼리 뺀 값이다, 제외 − 유지).")

A = {"1": "2027년 예산 금액의 주제 구성을 2023~2025년 대출횟수의 주제 구성과 같게 둔다 (주제마다 책값이 다른 것은 반영하지 않음).",
     "2": "사들일 권수를 대출횟수 구성대로 나누고, 한 권 값은 대상 책의 그 주제 구입가격(자료 구입 단가) 평균과 같다고 보고 금액으로 바꾼다.",
     "3": "사들일 권수를 대상 책(2022-12-31 이전 구입분)의 주제별 권수 구성대로 나누고, 한 권 값은 그 주제 구입가격 평균과 같다고 본다 (= 대상 책 구입가격 합의 주제 구성 그대로).",
     "4": "대상 책(2022-12-31 이전 구입분)의 권수 구성과 2023~2025년 대출 구성을 같은 무게(반반)로 섞어 금액 구성으로 쓴다. 반반이라는 무게에는 근거가 없고 정한 값이다."}

line_f = lambda fs: ", ".join(f"{f} {P(t)}" for f, t in fs)
R = f"""# 결과 — 주제별 대출횟수·이상치·구입가격과 2027년 예산 배분 근거 (질문 4)

**검증 일치 357/357 (검증/대조표.md), 표·그림 대조 일치, 규칙 위반 0 (검증/규칙점검표.md).**

작성: 분석 담당 / 2026-11-18. 산출 코드: `작업/20261117_주제별_예산근거/분석/분석.py` (프로젝트 폴더에서 `.venv/bin/python 작업/20261117_주제별_예산근거/분석/분석.py`). 난수 없음, 시드 없음.
이 파일은 분석.py가 만든다. "분석.py n"은 그 파일의 n번째 줄이다. 모든 수치는 `분석/핵심수치.csv`의 같은 번호 값이다 (주제별 번호 N = 28 + 33j + f, 계산명세 6-3절).
입력: `P02_장서목록_대출횟수 original.csv` {C[1]}행 (N1, {P('N1')}). 대상: 구입일 2022-12-31 이하 {C[2]}권 (N2, {P('N2')}). 대상 밖(2023년 이후 구입) {C[27]}권 (N27, {P('N27')}).

## 맨 앞: 이상치 처리에 따른 순위 차이

{s1}

## 산출물 ② 주제별 장서 수와 대출횟수 (표 1, 그림 1)

{md(T1)}

- 대상: 2022-12-31 이전에 구입한 책 (대출을 센 2023~2025년보다 먼저 구입). 그 책이 3년 동안 서가에 계속 있었는지는 이 자료로 알 수 없다.
- 대출횟수: 2023~2025년 3년간 대출된 횟수의 합 (한 칸).
- 제외 = 대출횟수 {C[6]}회 초과 또는 {C[5]}회 미만인 {C[7]}권을 뺀 값. 경계는 대상 전체의 평균 ± 3 × 표본 표준편차다. 표준편차는 값이 평균에서 흩어진 정도이고, 표본 표준편차는 그것을 구할 때 권수 n 대신 n−1로 나누는 방식이다 (질문 3과 같음). 평균±3표준편차는 평균에서 표준편차의 3배보다 멀리 떨어진 값을 이상치로 보는 기준이다.
- 중앙값은 값을 크기순으로 놓았을 때 가운데 값이다. 중앙값 규칙: 권수가 짝수여도 두 값의 평균을 내지 않고 가운데 쪽 앞의 실제 값(⌈n/2⌉번째)을 쓴다.
- 순위 1 = 평균이 가장 큼. 대상의 {C[25]}권({C[26]}%)이 대출 0회다 (N25 {P('N25')}, N26 {P('N26')}).
- 산출 코드: {line_f([('f0·f1·f5·f6', 'F0156'), ('f2', 'F2'), ('f3', 'F3'), ('f7', 'F7'), ('f8', 'F8'), ('f4·f9', 'RANK')])}, N8 {P('N7N8')}, N9·N10 {P('N9N11')}, N16 {P('N16')}, N17 {P('N17')}, N18 {P('N18')}, N19 {P('N19')}. 행 순서(유지 권수 내림차순) {P('ORDER')}.
- 표 파일: `분석/표1_주제별_장서수_대출횟수.csv`

![그림 1](그림1_주제별_장서수_대출횟수_유지.png)

그림 1: `분석/그림1_주제별_장서수_대출횟수_유지.png` (유지 처리만. 제외 처리는 표 1). 그림의 숫자는 핵심수치.csv 값과 같은지 코드로 대조했다.

{s2}

## 산출물 ③ 대출횟수 이상치 (표 2)

{md(T2)}

- 이상치 기준: 평균 {C[3]}회 ± 3 × 표본 표준편차 {C[4]}회, 경계 {C[5]} ~ {C[6]}회, 대상 전체 기준 하나 (주제별로 따로 구하지 않음). 이상치 대출횟수 범위 {C[14]}~{C[15]}회. (N3 {P('N3')}, N4 {P('N4')}, N5·N6 {P('N5N6')}, 판정 {P('OUT')}, N14 {P('N14')}, N15 {P('N15')})
- 차이 %p = 이상치 중 비중 − 권수 비중. %p(퍼센트포인트)는 두 비율의 차이를 뺄셈으로 나타낸 단위다 (10%와 12%의 차이는 2%p). 이상치가 주제와 관계없이 고르게 나왔다면 각 주제의 이상치 중 비중은 그 주제의 권수 비중과 같아진다. 양수 = 이상치 {C[7]}권 안에서의 몫이 대상 전체 안에서의 몫보다 크다.
- 산출 코드: {line_f([('f10·f15', 'F101517'), ('f11', 'F11'), ('f12', 'F12'), ('f13', 'F13'), ('f14', 'F14'), ('f16', 'F16')])}, N7 {P('N7N8')}, N11 {P('N9N11')}, N12 {P('N12')}, N13 {P('N13')}.
- 표 파일: `분석/표2_대출이상치_주제별.csv`

{s3}

## 산출물 ④ 주제별 구입가격 (표 3)

{md(T3)}

- 구입가격은 코드북 2절의 '자료 구입 단가'(원)다. 대상 책 = 2022-12-31 이전 구입분. 주제별 평균의 최대−최소 차이 {C[23]}원(대상 평균의 {C[24]}%). 중앙값은 ⌈n/2⌉번째 실제 값이며 순위를 매기지 않는다.
- 산출 코드: {line_f([('f17', 'F101517'), ('f18', 'F18'), ('f19', 'F19'), ('f20', 'RANK')])}, N20 {P('N20')}, N21 {P('N21')}, N22 {P('N22')}, N23 {P('N23')}, N24 {P('N24')}.
- 표 파일: `분석/표3_주제별_구입가격.csv`

{s4}

## 산출물 ⑤ 배분 근거 지표 (표 4)

{md(T4)}

- 분모: 권수 비중 = 대상 권수 {C[2]}권(N2), 대출 비중 유지 = 대상 대출 합 {C[9]}회(N9), 대출 비중 제외 = 제외 후 대출 합 {C[10]}회(N10), 가격합 비중 = 대상 구입가격 합 {C[20]}원(N20). 비중은 하나씩 반올림해 열 합이 100.00과 조금 다를 수 있다.
- 권수 비중·가격합 비중·구입가격 평균은 두 처리 모두 대상 전체(유지) 값이다 (승인 7·8번).
- 산출 코드: {line_f([('f13', 'F13'), ('f21', 'F21'), ('f22', 'F22'), ('f23', 'F23'), ('f18', 'F18'), ('f31·f32', 'RANK')])}.
- 표 파일: `분석/표4_배분근거지표.csv`

## 산출물 ⑤ 배분 비율 시나리오 (표 5, 단위 %)

{md(T5)}

열 이름의 '유지·제외'는 대출횟수 이상치 처리를 뜻한다. 식의 기호: B = 주제 권수, L = 처리별 주제 대출 합, P = 주제 구입가격 평균(유지 행), G = 주제 구입가격 합. 각 식은 10개 주제 합이 1이다.

- 시나리오 1. 대출 비중대로: a = L / ΣL (유지·제외). 가정: {A['1']}
- 시나리오 2. 대출 비중 × 가격 평균: a = L·P / Σ(L·P) (유지·제외). 가정: {A['2']}
- 시나리오 3. 대상 장서 구입가격 구성대로: a = G / ΣG (대출 처리와 무관, 1개). 가정: {A['3']}
- 시나리오 4. 권수와 대출의 중간: a = ½·(B / ΣB) + ½·(L / ΣL) (유지·제외). 가정: {A['4']}
  시나리오 4의 반반(0.5·0.5) 무게는 이 자료나 다른 근거에서 나온 값이 아니라, 두 구성을 같은 무게로 섞어 보기 위해 정한 값이다.
- 최대 잔여 방식: 소수 둘째 자리 아래를 버린 뒤, 버린 몫이 큰 주제부터 0.01씩 더해 합을 100.00으로 맞추는 반올림 방법. 열마다 합이 정확히 100.00인지 코드로 확인했다.
- 이 값은 금액이 아니라 비율이다. 팀이 예산 총액을 정하면 '총액 × 비율'로 바꿀 수 있다.
- 산출 코드: 시나리오 1 {P('SC1')}, 2 {P('SC2')}, 3 {P('SC3')}, 4 {P('SC4')}, 최대 잔여 반올림 {P('LR')} (함수 largest_remainder).
- 표 파일: `분석/표5_배분비율_시나리오.csv`

시나리오 사이의 선택은 팀이 기획회의에서 한다. 이 비율은 금액이 아니며, 예산 총액이 이 자료에 없어 금액을 계산하지 않았다.

두 처리의 차이:
{chr(10).join('- ' + x for x in s6)}

시나리오 비율은 합이 100.00이 되도록 최대 잔여 방식으로 반올림했다. 그래서 같은 식인 시나리오 1(유지)과 대출 비중(유지), 시나리오 1(제외)과 대출 비중(제외), 시나리오 3과 가격합 비중이 0.01%p 다를 수 있다.

## 산출물 ⑥ 한계와, 시나리오 식의 전제가 맞지 않을 수 있는 요인

시나리오 비율은 2027년의 대출이나 바른 배분을 미리 계산한 값이 아니다. 2023~2025년 대출 구성과 대상 책의 구성·구입가격을 정해진 식으로 나눈 비율이며, 아래는 그 식의 전제(예: 2023~2025년 구성이 2027년에도 이어진다)가 맞지 않을 수 있는 이유다.

- 가. 대출횟수는 2023-01-01~2025-12-30의 3년을 합친 한 칸이다. 해마다 늘었는지 줄었는지 알 수 없으므로, 2023~2025년의 대출 구성이 2027년에도 이어진다는 전제를 이 자료로 확인할 수 없다.
- 나. 2023년 이후 구입한 {C[27]}권은 대상에서 빠져 어느 비중에도 들어가지 않는다. 최근 3년 구입 경향은 반영되지 않았다.
- 다. 이상치 {C[7]}권(대상의 {C[13]}%)이 대출 합의 {C[12]}%를 차지한다. 소수의 책이 대출 비중을 움직이며, 그 정도는 표 4·5의 유지·제외 열 차이로 보인다. 이상치 기준은 평균±3표준편차 하나만 썼고, 다른 기준(예: IQR)을 쓰면 제외 열 값이 달라질 수 있다.
- 라. 구입가격은 코드북의 '자료 구입 단가'다. 대상 책은 2005~2022년에 구입했으므로 이 단가는 그때의 값으로 읽힌다 (구입일에서 나온 해석이며 코드북 표현은 아니다). 2027년 단가는 이 자료에 없다. 시나리오 2·3의 가격 반영은 이 과거 단가 기준이다.
- 마. 대출 외 이용(관내 열람 등)은 이 자료에 없다 (코드북 7절 ③). 대출이 적은 주제가 덜 이용된다고 말할 수 없다.
- 바. 대상 책이 3년 동안 서가에 계속 있었는지(분실·제적·대출 불가 기간)는 알 수 없다.
- 사. 주제별 장서 보유량은 이 파일의 대상 권수로만 근사했다. 장서 회전율·이용계수처럼 도서관 전체 소장 장서를 분모로 쓰는 지표는 만들 수 없다.
- 아. 대출 비중이 큰 주제에 책이 더 필요하다는 뜻인지, 이미 많이 갖고 있어 대출이 많은 것인지는 이 자료로 가를 수 없다. 대출 비중대로 예산을 나누면 대출이 늘어난다고도 말할 수 없다 (관찰 자료, 규칙 9). 어느 기준을 쓸지는 팀의 판단이다.

## 산출물 ⑦ 분석할 수 없는 항목과 이유

| 항목 | 이유 | 근거 |
|---|---|---|
| 2027년 주제별 대출 수치를 미리 계산하는 방법(시계열·회귀·기계학습) | 대출횟수가 3년 합계 한 칸이라 연도별 흐름이 없다 | 코드북 2절, 질문.md '뺀 것' |
| 2027년 주제별 예산 금액 | 예산 총액이 어느 파일에도 없다 | 질문.md '뺀 것' |
| 2027년 단가·물가 반영 | 2027년 단가 자료가 없다. 구입가격은 대상 책의 '자료 구입 단가'다 | 코드북 2절 |
| 2023년 이후 구입 책의 대출 구성 | 대상에서 뺐다 (대출을 센 기간 안에 구입되어 대출 가능 기간이 책마다 다름) | 승인 1번 |
| 장서 회전율·이용계수 등 소장 장서 전체를 분모로 하는 지표 | 도서관 전체 주제별 소장 권수가 없다 (P03은 쓰지 않음) | 승인 4번 |
| 주제별 이용자 수·1인당 대출 | 이용자 정보가 없다 | 코드북 2절 |
| 책의 가치, 적정 장서량 | 가치 기준을 알 수 없다 | 맥락 파일 3절, 코드북 7절 ① |
| 대출 외 이용 | 관내 이용 기록이 없다 | 맥락 파일 3절, 코드북 7절 ③ |

## 검정

없음 (검정 0회). 대상 행을 모두 센 값이라 신뢰구간을 붙이지 않는다 (계산명세 5절).

## 수정 기록

| 날짜 | 고친 곳 | 내용 | 수치 영향 |
|---|---|---|---|
| 2026-11-18 | 맨 위 상태 표시 | '독립 검증 전'을 검증 결과(일치 357/357, 표·그림 대조 일치, 규칙 위반 0)로 바꿨다 (진행 담당 요청, 7단계) | 없음 |
| 2026-11-18 | 산출물 ⑥ 다 | '다른 기준(예: IQR)을 쓰면 제외 열 값이 달라진다'를 '달라질 수 있다'로 바꿨다. 다른 기준은 계산하지 않았으므로 단정하지 않는다 (진행 담당 요청) | 없음 |

두 곳 모두 분석.py의 문장 틀에서 고치고 분석.py를 다시 돌려 만들었다. 핵심수치.csv·표 CSV 5개·그림 1은 수정 전과 바이트 단위로 같다 (cmp).
"""
assert "예측" not in R and "추천" not in R and "권장" not in R
open(OUT + "결과.md", "w", encoding="utf-8").write(R)
if not s2_ok:
    print("알림: f3·f8 가 0/1 밖 값이 있어 결과 문장 2를 뺐다")
print("완료", C[2], C[7], C[9])

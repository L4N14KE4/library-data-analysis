# 5단계 분석 — 질문 3 (전체 도서판) 발행년·주제분류별 대출횟수와 적게 대출된 책의 특징
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261118_발행년주제_대출횟수_전체도서/분석/분석.py
# 계산명세.md(승인기록 13번)대로만 계산한다. 원자료는 읽기만 한다.
# 난수: 부트스트랩 신뢰구간에만 쓴다. 시드 20261117, 호출마다 새 생성기, 5000회, batch=None (8번 호출).
import math
import sys
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from matplotlib import font_manager, pyplot as plt
from matplotlib.patches import Patch
from scipy import stats

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261118_발행년주제_대출횟수_전체도서/분석")
USE = ["자료ID", "발행년", "주제분류명", "구입일", "구입가격", "대출횟수"]  # 명세 3절. 삭제 7열·KDC·최근대출일 안 씀
D2023 = pd.Timestamp("2023-01-01")  # 2023년 이후 구입 = 구입일 >= 2023-01-01 (2절)
YEARS = list(range(2005, 2026))  # 5-4절 순서, k = 발행년 - 2005 (0~20)
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 5-4절 순서, j
SEED = 20261117
TNAME = {"keep": "유지", "excl": "평균±3SD 제외"}

FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다 (규칙 10)
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False


def stop(msg):
    sys.exit(f"멈춤: {msg}")


def fr2(f):  # 정확한 분수 -> ROUND_HALF_UP 소수 둘째 (값은 모두 0 이상)
    n = math.floor(Fraction(f) * 100 + Fraction(1, 2))
    return f"{n // 100}.{n % 100:02d}"


def fl(x, nd):  # float -> Decimal(repr(float(x))) ROUND_HALF_UP
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP))


def pfmt(p):
    return format(float(p), ".2e")


def fr2s(f):  # 보충 보-2: 부호 있는 정확한 분수 -> 절댓값 기준 ROUND_HALF_UP 소수 둘째, 0이면 0.00
    f = Fraction(f)
    r = fr2(abs(f))
    return "-" + r if f < 0 and r != "0.00" else r


def med(a):  # 보간 없는 중앙값: 오름차순 ceil(n/2)번째
    a = np.sort(np.asarray(a))
    return a[math.ceil(len(a) / 2) - 1]


R = {}  # 번호 -> (항목, 값 문자열)


def put(n, item, val):
    if n in R:
        stop(f"N{n} 중복")
    R[n] = (item, val)


# ---------------------------------------------------------------- 0. 읽기 (2절)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[USE].copy()
for c in ["발행년", "구입가격", "대출횟수"]:
    s = d[c].str.strip()
    if not s.str.fullmatch(r"[+-]?\d+").all():
        stop(f"{c} 정수로 바뀌지 않는 칸 있음")
    d[c] = s.astype(np.int64)
d["구입일"] = pd.to_datetime(d["구입일"].str.strip(), format="%Y-%m-%d", errors="coerce")
if d["구입일"].isna().any():
    stop("구입일 날짜로 바뀌지 않는 칸 있음")
if not set(d["주제분류명"]) <= set(SUBJ):
    stop(f"주제분류명 10개 밖 값: {sorted(set(d['주제분류명']) - set(SUBJ))}")
d["후"] = d["구입일"] >= D2023  # 2023년 이후 구입

t = d  # 대상 = 입력 행 전부 (승인 1번, 입력 행 순서 유지)
N1, N2 = len(raw), len(t)
if N2 != N1:
    stop("N2 ≠ N1")
x_all = t["대출횟수"].to_numpy()
mu = int(x_all.sum()) / N2  # float64
sd = float(np.std(x_all.astype(np.float64), ddof=1))
lo, hi = mu - 3 * sd, mu + 3 * sd
out_mask = (t["대출횟수"] > hi) | (t["대출횟수"] < lo)
keep_mask = ~((t["대출횟수"] > hi) | (t["대출횟수"] < lo))
N7, N8 = int(out_mask.sum()), int(keep_mask.sum())
gap = t["구입일"].dt.year - t["발행년"]
if int((gap < 0).sum()) > 0:
    stop(f"발행년 > 구입연도 {int((gap < 0).sum())}건")
N9, N10, N11 = (int((gap == v).sum()) for v in (0, 1, 2))
N12 = int((~gap.isin([0, 1, 2])).sum())
if N7 + N8 != N2 or N9 + N10 + N11 + N12 != N2:
    stop("N7+N8 또는 N9~N12 합이 N2와 다름")

put(1, "입력 행 수", str(N1))
put(2, "대상 권수 (유지)", str(N2))
put(3, "대상 대출횟수 평균 μ", fl(mu, 4))
put(4, "대상 대출횟수 표본 표준편차 s", fl(sd, 4))
put(5, "제외 아래 경계 μ−3s", fl(lo, 4))
put(6, "제외 위 경계 μ+3s", fl(hi, 4))
put(7, "제외한 권수", str(N7))
put(8, "제외 후 권수", str(N8))
put(9, "구입연도−발행년=0 권수", str(N9))
put(10, "구입연도−발행년=1 권수", str(N10))
put(11, "구입연도−발행년=2 권수", str(N11))
put(12, "구입연도−발행년이 0·1·2 아닌 권수", str(N12))

TDATA = {"keep": t, "excl": t[keep_mask]}
BASE = {"keep": 13, "excl": 284}                  # 6-3절 묶음 시작 S
DIST = {"keep": (555, 618), "excl": (648, 711)}   # 6-5절 (발행년, 주제) 시작
REST = {("keep", "A"): 741, ("keep", "B"): 742, ("excl", "A"): 743, ("excl", "B"): 744}  # 6-6절
DIM = [("발행년", "발행년", YEARS), ("주제", "주제분류명", SUBJ)]


def eta2(*g):  # 5-3절 η² = SS_between / SS_total, float64
    g = [np.asarray(a, dtype=np.float64) for a in g]
    allx = np.concatenate(g)
    m = allx.mean()
    sst = ((allx - m) ** 2).sum()
    ssb = sum(len(a) * (a.mean() - m) ** 2 for a in g)
    return ssb / sst


def eps2(*g):  # 5-3절 ε² = H / (N − 1), H는 동점 보정 kruskal
    n = sum(len(a) for a in g)
    return stats.kruskal(*g).statistic / (n - 1)


def welch_df2(g):  # 5-2절 식
    n = np.array([len(a) for a in g], dtype=np.float64)
    v = np.array([np.var(a.astype(np.float64), ddof=1) for a in g])
    w = n / v
    k = len(g)
    lam = (((1 - w / w.sum()) ** 2) / (n - 1)).sum()
    return (k * k - 1) / (3 * lam)


def boot(g, fn):  # 5-3절 호출 그대로, 호출마다 새 생성기
    try:
        r = stats.bootstrap(tuple(g), fn, n_resamples=5000, batch=None, confidence_level=0.95,
                            method="percentile", paired=False, vectorized=False,
                            rng=np.random.default_rng(SEED))
    except MemoryError:
        stop("부트스트랩 메모리 부족 (batch를 넣지 않고 멈춤)")
    return r.confidence_interval.low, r.confidence_interval.high


TABLES = {}    # 표 1·2용
TESTS = []     # 표 3용
CI_CHECK = []  # 점추정이 구간 안인지 (5-5절)
PICK = {}      # 표 4·5용
EXACT = {}     # 조건부 문장용 정확한 분수: (T, 'mean'|'f4', 발행년) -> Fraction
SUPP = {}      # 보충 N745~N752: 번호 -> (항목, 정확한 분수)
SUPP_N = {("keep", "발행년"): 745, ("keep", "주제"): 746, ("excl", "발행년"): 747, ("excl", "주제"): 748,
          ("keep", "A"): 749, ("keep", "B"): 750, ("excl", "A"): 751, ("excl", "B"): 752}

for T, df in TDATA.items():
    tn, S, NT = TNAME[T], BASE[T], len(df)
    # 2절 '발행년 집단' 확인 (두 처리 각각)
    if sorted(df["발행년"].unique()) != YEARS or sorted(df["주제분류명"].unique()) != sorted(SUBJ):
        stop(f"{tn}: 집단 구성이 2005~2025 21개 / 주제 10개가 아님")
    for _, col, lv in DIM:
        for v in lv:
            xg = df.loc[df[col] == v, "대출횟수"].to_numpy()
            if len(xg) < 2 or np.var(xg.astype(np.float64), ddof=1) <= 0:
                stop(f"{tn} {v}: 2권 미만 또는 분산 0")

    # ---------------- ① 집단별 표 (6-3 ①)
    n_after = 0  # 발행년별 2023년 이후 구입 권수 합 (6-4 합 확인)
    for di, (dn, col, lv) in enumerate(DIM):
        start, step = (S, 5) if di == 0 else (S + 105, 4)
        cnt = {v: int((df[col] == v).sum()) for v in lv}
        tot = {v: int(df.loc[df[col] == v, "대출횟수"].sum()) for v in lv}
        mean = {v: Fraction(tot[v], cnt[v]) for v in lv}
        if len(set(mean.values())) != len(lv):
            stop(f"{tn} {dn}: 평균 동률")
        order = sorted(lv, key=lambda v: mean[v])
        rank = {v: i + 1 for i, v in enumerate(order)}
        if sum(cnt.values()) != NT:
            stop(f"{tn} {dn}: 권수 합 불일치")
        for i, v in enumerate(lv):
            n0 = start + step * i
            put(n0, f"{tn} {dn} {v} 권수", str(cnt[v]))
            put(n0 + 1, f"{tn} {dn} {v} 총합", str(tot[v]))
            put(n0 + 2, f"{tn} {dn} {v} 평균", fr2(mean[v]))
            put(n0 + 3, f"{tn} {dn} {v} 평균 오름차순 순위", str(rank[v]))
            if di == 0:
                ca = int(df.loc[df[col] == v, "후"].sum())
                n_after += ca
                EXACT[(T, "mean", v)] = mean[v]
                EXACT[(T, "f4", v)] = Fraction(ca * 100, cnt[v])
                put(n0 + 4, f"{tn} {dn} {v} 2023년 이후 구입 비율", fr2(EXACT[(T, "f4", v)]))
        TABLES[(T, dn)] = [(rank[v], v, start + step * lv.index(v)) for v in order]
        # 보충 N745~N748: 정확한 분수 평균의 최댓값 − 최솟값 (순위 최대 집단 − 순위 1 집단)
        rng_ = mean[order[-1]] - mean[order[0]]
        if rng_ != max(mean.values()) - min(mean.values()) or rng_ < 0:
            stop(f"{tn} {dn}: 평균 최댓값−최솟값 확인 실패 또는 음수")
        SUPP[SUPP_N[(T, dn)]] = (f"{tn} {dn} 집단 평균 최댓값 − 최솟값", rng_)
    if sum(int(df.loc[df["발행년"] == v, "대출횟수"].sum()) for v in YEARS) != \
            sum(int(df.loc[df["주제분류명"] == v, "대출횟수"].sum()) for v in SUBJ):
        stop(f"{tn}: 발행년 총합 합 ≠ 주제 총합 합")
    NA = int(df["후"].sum())  # 처리 전체 2023년 이후 구입 권수
    if NA == 0:
        stop(f"{tn}: 2023년 이후 구입 0권")
    if n_after != NA:
        stop(f"{tn}: 발행년별 2023년 이후 구입 권수 합 ≠ 처리 전체")
    put(S + 145, f"{tn} 전체 2023년 이후 구입 권수", str(NA))
    put(S + 146, f"{tn} 전체 2023년 이후 구입 비율", fr2(Fraction(NA * 100, NT)))

    # ---------------- ② 검정 (5절, 6-3 ②)
    for di, (dn, col, lv) in enumerate(DIM):
        n0 = S + 147 + 11 * di  # 위치 1 = S + 146 + 1 (발행년), S + 157 + 1 (주제)
        g = [df.loc[df[col] == v, "대출횟수"].to_numpy() for v in lv]
        try:
            w = stats.f_oneway(*g, equal_var=False)
        except TypeError as ex:
            stop(f"f_oneway equal_var 인자 오류: {ex}")
        df2 = welch_df2(g)
        e = eta2(*g)
        elo, ehi = boot(g, eta2)
        kw = stats.kruskal(*g)
        ep = kw.statistic / (NT - 1)
        plo, phi = boot(g, eps2)
        vals = [("웰치 F", fl(w.statistic, 2)), ("웰치 분모 자유도 df2", fl(df2, 2)), ("웰치 p", pfmt(w.pvalue)),
                ("η²", fl(e, 4)), ("η² 95% 신뢰구간 하한", fl(elo, 4)), ("η² 95% 신뢰구간 상한", fl(ehi, 4)),
                ("크러스컬-월리스 H", fl(kw.statistic, 2)), ("크러스컬-월리스 p", pfmt(kw.pvalue)),
                ("ε²", fl(ep, 4)), ("ε² 95% 신뢰구간 하한", fl(plo, 4)), ("ε² 95% 신뢰구간 상한", fl(phi, 4))]
        for i, (nm, v) in enumerate(vals):
            put(n0 + i, f"{tn} {dn} {nm}", v)
        k = len(lv)
        TESTS.append([tn, dn, "웰치 분산분석", vals[0][1], f"{k - 1}, {vals[1][1]}", vals[2][1], "η²",
                      vals[3][1], vals[4][1], vals[5][1]])
        TESTS.append([tn, dn, "크러스컬-월리스", vals[6][1], f"{k - 1}", vals[7][1], "ε²",
                      vals[8][1], vals[9][1], vals[10][1]])
        for nm, pe, l_, h_ in [("η²", vals[3][1], vals[4][1], vals[5][1]), ("ε²", vals[8][1], vals[9][1], vals[10][1])]:
            CI_CHECK.append((tn, dn, nm, pe, l_, h_, Decimal(l_) <= Decimal(pe) <= Decimal(h_)))

    # ---------------- ③ 고른 책 A·B (2절, 6-3 ③) + 6-6 나머지 비율
    for pi, (dn, col, lv) in enumerate(DIM):
        n0 = S + 169 + 51 * pi  # m = 1 위치: S + 168 + 1 (A), S + 219 + 1 (B)
        gn = df.groupby(col)["대출횟수"].transform("size").astype(np.int64)
        gs = df.groupby(col)["대출횟수"].transform("sum").astype(np.int64)
        sel = df["대출횟수"] * gn < gs  # 정수 곱 비교
        a, r = df[sel], df[~sel]
        m1 = len(a)
        m46 = int(a["후"].sum())
        rows = [("고른 권수", str(m1)), ("고른 비율", fr2(Fraction(m1 * 100, NT))),
                ("고른 책 대출횟수 최댓값", str(int(a["대출횟수"].max()))),
                ("고른 책 중 대출 0회 비율", fr2(Fraction(int((a["대출횟수"] == 0).sum()) * 100, m1)))]
        sy = sj = 0
        for v in YEARS:
            c = int((a["발행년"] == v).sum())
            sy += c
            rows.append((f"발행년 {v} 고른 비율", fr2(Fraction(c * 100, int((df["발행년"] == v).sum())))))
        for v in SUBJ:
            c = int((a["주제분류명"] == v).sum())
            sj += c
            rows.append((f"주제 {v} 고른 비율", fr2(Fraction(c * 100, int((df["주제분류명"] == v).sum())))))
        if sy != m1 or sj != m1 or m46 > m1:
            stop(f"{tn} {dn}: 고른 권수 합 불일치 또는 m46 > m1")
        rows += [("고른 책 발행년 평균", fr2(Fraction(int(a["발행년"].sum()), len(a)))),
                 ("나머지 발행년 평균", fr2(Fraction(int(r["발행년"].sum()), len(r)))),
                 ("고른 책 발행년 중앙값", str(int(med(a["발행년"])))),
                 ("나머지 발행년 중앙값", str(int(med(r["발행년"])))),
                 ("고른 책 구입일 중앙값", str(pd.Timestamp(med(a["구입일"].to_numpy())).date())),
                 ("나머지 구입일 중앙값", str(pd.Timestamp(med(r["구입일"].to_numpy())).date())),
                 ("고른 책 구입가격 평균", fr2(Fraction(int(a["구입가격"].sum()), len(a)))),
                 ("나머지 구입가격 평균", fr2(Fraction(int(r["구입가격"].sum()), len(r)))),
                 ("고른 책 구입가격 중앙값", str(int(med(a["구입가격"])))),
                 ("나머지 구입가격 중앙값", str(int(med(r["구입가격"])))),
                 ("고른 책 중 2023년 이후 구입 권수", str(m46)),
                 ("고른 책 중 2023년 이후 구입 비율", fr2(Fraction(m46 * 100, m1))),
                 ("2023년 이후 구입분 중 고른 비율", fr2(Fraction(m46 * 100, NA)))]
        for y in (2023, 2024, 2025):
            ay = a.loc[a["발행년"] == y, "대출횟수"]
            if len(ay) == 0:
                stop(f"{tn} {dn}: {y}년 발행 고른 책 0권")
            rows.append((f"{y}년 발행 고른 책 대출횟수 최댓값", str(int(ay.max()))))
        lab = "A" if pi == 0 else "B"
        if len(rows) != 51:
            stop("m 개수 51 아님")
        for i, (nm, v) in enumerate(rows):
            put(n0 + i, f"{tn} {lab}({dn} 평균 미만) {nm}", v)
        # 6-6: 나머지 중 2023년 이후 구입 비율 (분자·분모 모두 조건으로 센다)
        rest = df[~(df["대출횟수"] * gn < gs)]
        if len(rest) == 0:
            stop(f"{tn} {lab}: 나머지 0권")
        ra = int(rest["후"].sum())
        if ra + m46 != NA:
            stop(f"{tn} {lab}: 나머지 2023년 이후 + m46 ≠ 처리 전체")
        put(REST[(T, lab)], f"{tn} {lab} 나머지 중 2023년 이후 구입 비율", fr2(Fraction(ra * 100, len(rest))))
        # 보충 N749~N752: (고른 책 중 2023년 이후 비율 − 나머지 중 2023년 이후 비율), 반올림 전 정확한 분수
        SUPP[SUPP_N[(T, lab)]] = (f"{tn} {lab} 2023년 이후 구입 비율 차이 (고른 책 − 나머지)",
                                  Fraction(m46 * 100, m1) - Fraction(ra * 100, len(rest)))
        PICK[(T, lab)] = (n0, NT - m1)

    # ---------------- 6-5 규칙 5 (가) 분포 수치
    for di, (dn, col, lv) in enumerate(DIM):
        n0 = DIST[T][di]
        for i, v in enumerate(lv):
            xg = df.loc[df[col] == v, "대출횟수"].to_numpy().astype(np.float64)
            put(n0 + 3 * i, f"{tn} {dn} {v} 표준편차", fl(np.std(xg, ddof=1), 2))
            put(n0 + 3 * i + 1, f"{tn} {dn} {v} 왜도", fl(stats.skew(xg, bias=False), 2))
            put(n0 + 3 * i + 2, f"{tn} {dn} {v} 0 비율", fr2(Fraction(int((xg == 0).sum()) * 100, len(xg))))

for n in sorted(SUPP):  # 보충 보-2
    put(n, SUPP[n][0], fr2s(SUPP[n][1]))
if sorted(R) != list(range(1, 753)):
    stop("핵심 수치 번호가 N1~N752가 아님")

# ---------------------------------------------------------------- 7절 조건부 문장 판정 (멈추지 않고 출력)
COND = {}
for T in TDATA:  # 문장 1(나): 2023~2025년 정확한 분수 평균 셋 모두 < 1
    COND[f"1(나) {TNAME[T]}"] = all(EXACT[(T, "mean", y)] < 1 for y in (2023, 2024, 2025))
COND["2 N12 = 0"] = N12 == 0
COND["3(나) f=4 여섯 개 = 100"] = all(EXACT[(T, "f4", y)] == 100 for T in TDATA for y in (2023, 2024, 2025))
COND["그림1 빗금 (유지 f=4 셋 = 100)"] = all(EXACT[("keep", "f4", y)] == 100 for y in (2023, 2024, 2025))
COND["3(다) N97·N102 > 0"] = EXACT[("keep", "f4", 2021)] > 0 and EXACT[("keep", "f4", 2022)] > 0

# ---------------------------------------------------------------- 저장: 핵심수치.csv
V = {n: R[n][1] for n in R}
pd.DataFrame([(f"N{n}", R[n][0], R[n][1]) for n in sorted(R)], columns=["번호", "항목", "값"]) \
    .to_csv(OUT / "핵심수치.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 표 1·2 (각주는 결과.md에 둔다)
for T in TDATA:
    for dn, col, fname in [("발행년", "발행년", "표1_발행년별_대출횟수"), ("주제", "주제분류명", "표2_주제별_대출횟수")]:
        rows = [[V[n0 + 3], str(v), V[n0], V[n0 + 1], V[n0 + 2]] + ([V[n0 + 4]] if dn == "발행년" else [])
                for _, v, n0 in TABLES[(T, dn)]]
        cols = ["순위", col, "권수", "대출횟수 총합", "평균 대출횟수"] + (["2023년 이후 구입 비율(%)"] if dn == "발행년" else [])
        pd.DataFrame(rows, columns=cols).to_csv(OUT / f"{fname}_{'유지' if T == 'keep' else '3SD제외'}.csv",
                                                index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 표 3
pd.DataFrame(TESTS, columns=["처리", "구분", "검정", "통계량", "자유도", "p", "효과크기 이름", "효과크기",
                             "95% 신뢰구간 하한", "상한"]).to_csv(OUT / "표3_검정결과.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 표 4
rows4 = []
for T in TDATA:
    for lab in ("A", "B"):
        n0, nrest = PICK[(T, lab)]
        g = lambda m: V[n0 + m - 1]
        rows4.append([TNAME[T], lab, "고른 책", g(1), g(2), g(3), g(4), g(36), g(38), g(40), g(42), g(44),
                      g(46), g(47), g(48), f"{g(49)} / {g(50)} / {g(51)}"])
        rows4.append([TNAME[T], lab, "나머지", str(nrest), "", "", "", g(37), g(39), g(41), g(43), g(45),
                      "", V[REST[(T, lab)]], "", ""])
pd.DataFrame(rows4, columns=["처리", "기준", "책", "권수", "대상 중 비율(%)", "대출횟수 최댓값", "대출 0회 비율(%)",
                             "발행년 평균", "발행년 중앙값", "구입일 중앙값", "구입가격 평균", "구입가격 중앙값",
                             "2023년 이후 구입 권수", "2023년 이후 구입 비율(%)", "2023년 이후 구입분 중 고른 비율(%)",
                             "2023·2024·2025년 발행 고른 책 최댓값"]) \
    .to_csv(OUT / "표4_평균미만_비교.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 표 5
rows5 = []
for i, v in enumerate([str(y) for y in YEARS] + SUBJ):
    rows5.append(["발행년" if i < 21 else "주제", v] + [V[PICK[(T, lab)][0] + 4 + i] for T in TDATA for lab in ("A", "B")])
rows5.append(["전체", "전체"] + [V[PICK[(T, lab)][0] + 1] for T in TDATA for lab in ("A", "B")])
pd.DataFrame(rows5, columns=["구분", "집단", "유지 A 고른 비율(%)", "유지 B 고른 비율(%)",
                             "제외 A 고른 비율(%)", "제외 B 고른 비율(%)"]).to_csv(OUT / "표5_평균미만_집단별비율.csv",
                                                                             index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 표 6
rows6 = []
for T in TDATA:
    for di, (dn, col, lv) in enumerate(DIM):
        for i, v in enumerate(lv):
            n0 = DIST[T][di] + 3 * i
            ncnt = BASE[T] + 5 * i if di == 0 else BASE[T] + 105 + 4 * i
            rows6.append([TNAME[T], dn, v, V[ncnt], V[n0], V[n0 + 1], V[n0 + 2]])
pd.DataFrame(rows6, columns=["처리", "구분", "집단", "권수", "표준편차", "왜도", "0 비율(%)"]) \
    .to_csv(OUT / "표6_집단별분포.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 그림 1·2 (유지만)
HATCH = COND["그림1 빗금 (유지 f=4 셋 = 100)"]
foot1 = f"대상: P02_장서목록_대출횟수의 책 {int(V[2]):,}권 전부. 대출횟수는 2023~2025년 3년간 대출된 횟수." + \
    (" 2023~2025년 발행 책은 모두 2023-01-01 이후 구입분이라, 구입 전에는 대출될 수 없어 대출될 수 있었던 기간이 짧다."
     if HATCH else "")
foot2 = f"대상: P02_장서목록_대출횟수의 책 {int(V[2]):,}권 전부. 대출횟수는 2023~2025년 3년간 대출된 횟수. " \
    f"2023년 이후 구입분 {int(V[158]):,}권({V[159]}%)이 들어 있다."
FIGS = [("발행년", "발행년", "그림1_발행년별_대출횟수_유지.png", "발행년별 대출횟수(2023~2025년) — 평균 오름차순",
         (14, 9), foot1),
        ("주제", "주제분류명", "그림2_주제별_대출횟수_유지.png", "주제분류명별 대출횟수(2023~2025년) — 평균 오름차순",
         (12, 9), foot2)]
for dn, xlab, fname, title, size, foot in FIGS:
    rows = TABLES[("keep", dn)]
    labels = [str(v) for _, v, _ in rows]
    mean_s = [V[n0 + 2] for _, _, n0 in rows]        # 핵심 수치 문자열 그대로
    tot_i = [int(V[n0 + 1]) for _, _, n0 in rows]
    hat = [("//" if (dn == "발행년" and HATCH and v in (2023, 2024, 2025)) else "") for _, v, _ in rows]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=size)
    b1 = a1.bar(labels, [float(s) for s in mean_s], color="#4C72B0", hatch=hat, edgecolor="white")
    a1.bar_label(b1, labels=mean_s, fontsize=9)
    a1.set_ylabel("평균 대출횟수 (회)")
    a1.set_xlabel(xlab)
    b2 = a2.bar(labels, tot_i, color="#DD8452", hatch=hat, edgecolor="white")
    a2.bar_label(b2, labels=[f"{v:,}" for v in tot_i], fontsize=9)
    a2.set_ylabel("대출횟수 총합 (회)")
    a2.set_xlabel(xlab)
    for ax in (a1, a2):
        ax.margins(y=0.12)
        if any(hat):
            ax.legend(handles=[Patch(facecolor="#999999", hatch="//", edgecolor="white",
                                     label="2023년 이후 구입분만 있는 해")], loc="upper left")
    fig.suptitle(title, fontsize=14)
    fig.text(0.5, -0.01, foot, ha="center", fontsize=10, wrap=True)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=150, bbox_inches="tight")
    # 그림 숫자 = 핵심 수치 확인
    assert [tx.get_text() for tx in a1.texts] == mean_s
    assert [tx.get_text() for tx in a2.texts] == [f"{v:,}" for v in tot_i]
    assert [h.get_height() for h in b2] == tot_i
    assert [round(h.get_height(), 2) for h in b1] == [float(s) for s in mean_s]
    plt.close(fig)

chk = pd.read_csv(OUT / "핵심수치.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
assert dict(zip(chk["번호"], chk["값"])) == {f"N{n}": V[n] for n in V}  # 저장된 값 = 그림·표에 쓴 값

# ---------------------------------------------------------------- 확인 출력 (핵심 수치 아님, 결과.md 맨 앞·1절 문장의 근거)
for dn in ("발행년", "주제"):  # 유지 vs 제외 순위 변화: 바뀐 집단 수, 최대 이동 칸
    rk = {T: {v: int(V[n0 + 3]) for _, v, n0 in TABLES[(T, dn)]} for T in TDATA}
    mv = {v: rk["excl"][v] - rk["keep"][v] for v in rk["keep"]}
    mx = max(abs(x) for x in mv.values())
    print("RANK", dn, "바뀐 수", sum(x != 0 for x in mv.values()), "최대 이동", mx,
          {v: (rk["keep"][v], rk["excl"][v]) for v in mv if abs(mv[v]) == mx})
print("EXCL 제외한 책 대출횟수 최솟값", int(t.loc[out_mask, "대출횟수"].min()),
      "아래 경계 밖 권수", int((t["대출횟수"] < lo).sum()))
for c in CI_CHECK:
    print("CI", *c)
for kk, vv in COND.items():
    print("COND", kk, vv)
print("완료: 핵심 수치", len(R), "개")

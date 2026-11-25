# 질문 3 다시 하기 — 5단계 분석 (계산명세.md 그대로)
# 실행: 프로젝트 폴더에서 `.venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/분석/분석.py`
import csv
import math
import sys
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import stats
from matplotlib import font_manager, pyplot as plt

OUT = "작업/20261125_발행년주제_대출횟수_전체도서/분석/"
SRC = "P02_장서목록_대출횟수 original.csv"
SEED = 20261117
N_BOOT = 5000
YEARS = list(range(2005, 2026))
SUBJECTS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
CUT = pd.Timestamp("2023-01-01")


def stop(msg):
    print("멈춤:", msg)
    sys.exit(1)


# ---------- 반올림 (6-1) ----------
def fr(x, d=2):
    """정확한 분수 -> ROUND_HALF_UP 문자열 (절댓값 기준, -0.00 없음)."""
    x = Fraction(x)
    q = math.floor(abs(x) * 10**d + Fraction(1, 2))
    s = f"{q // 10**d}.{q % 10**d:0{d}d}" if d else str(q)
    return "-" + s if x < 0 and q != 0 else s


def fl(x, d):
    """float -> Decimal(repr(float)) ROUND_HALF_UP 문자열."""
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def pfmt(p):
    return format(float(p), ".2e")


def median_inv(vals):
    """보간 없음: 오름차순 ceil(n/2)번째 (1부터)."""
    v = sorted(vals)
    return v[math.ceil(len(v) / 2) - 1]


# ---------- 입력 (2절) ----------
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
N1 = len(raw)
df = pd.DataFrame({"자료ID": raw["자료ID"].str.strip(), "주제": raw["주제분류명"].str.strip()})
for col in ["발행년", "대출횟수", "구입가격"]:
    s = raw[col].str.strip()
    if not s.str.fullmatch(r"-?\d+").all():
        stop(f"{col} 정수 변환 불가 칸 있음")
    df[col] = s.astype(np.int64)
df["구입일"] = pd.to_datetime(raw["구입일"].str.strip(), format="%Y-%m-%d", errors="coerce")
if df["구입일"].isna().any():
    stop("구입일 날짜 변환 불가 칸 있음")
if not set(df["주제"]).issubset(SUBJECTS):
    stop(f"코드북 밖 주제: {set(df['주제']) - set(SUBJECTS)}")
df["후"] = df["구입일"] >= CUT
df["구입일문자"] = df["구입일"].dt.strftime("%Y-%m-%d")
gap = df["구입일"].dt.year - df["발행년"]
if (gap < 0).any():
    stop(f"발행년 > 구입연도 {int((gap < 0).sum())}건")

NUM = {}  # 번호 -> (항목, 값 문자열)
EXACT = {}  # 조건 판정용 반올림 전 값


def put(n, name, val):
    if n in NUM:
        stop(f"N{n} 중복")
    NUM[n] = (name, str(val))


N2 = len(df)
if N2 != N1:
    stop("N2 != N1")
x_all = df["대출횟수"].to_numpy()
mu = float(x_all.sum()) / N2
sd = float(np.std(x_all.astype(np.float64), ddof=1))
lo, hi = mu - 3 * sd, mu + 3 * sd
excl = (x_all > hi) | (x_all < lo)
N7 = int(excl.sum())
N8 = int(((x_all <= hi) & (x_all >= lo)).sum())
if N7 + N8 != N2:
    stop("N7+N8 != N2")
put(1, "입력 행 수", N1)
put(2, "대상 권수 (유지)", N2)
put(3, "대상 대출횟수 평균", fl(mu, 4))
put(4, "대상 대출횟수 표본 표준편차", fl(sd, 4))
put(5, "제외 아래 경계 (평균-3SD)", fl(lo, 4))
put(6, "제외 위 경계 (평균+3SD)", fl(hi, 4))
put(7, "제외한 권수", N7)
put(8, "제외 후 권수", N8)
g = gap.to_numpy()
c = [int((g == 0).sum()), int((g == 1).sum()), int((g == 2).sum())]
c.append(int((~np.isin(g, [0, 1, 2])).sum()))
if sum(c) != N2:
    stop("N9~N12 합 != N2")
for i, (v, nm) in enumerate(zip(c, ["0", "1", "2", "0·1·2가 아닌"])):
    put(9 + i, f"구입연도-발행년 = {nm} 권수" if i < 3 else "구입연도-발행년이 0·1·2가 아닌 권수", v)

TREAT = {"유지": df, "제외": df[~excl].copy()}
TNAME = {"유지": "유지", "제외": "평균±3SD 제외"}


# ---------- 효과크기 statistic (5-3) ----------
def eta2(*samples):
    x = np.concatenate(samples).astype(np.float64)
    xbar = x.mean()
    ss_t = np.sum((x - xbar) ** 2)
    ss_b = sum(len(s) * (np.mean(s.astype(np.float64)) - xbar) ** 2 for s in samples)
    return ss_b / ss_t


def eps2(*samples):
    n = sum(len(s) for s in samples)
    return stats.kruskal(*samples).statistic / (n - 1)


def welch(groups):
    k = len(groups)
    n = np.array([len(a) for a in groups], dtype=np.float64)
    m = np.array([a.mean() for a in groups])
    v = np.array([a.var(ddof=1) for a in groups])
    w = n / v
    W = w.sum()
    xw = (w * m).sum() / W
    A = (w * (m - xw) ** 2).sum() / (k - 1)
    lam = ((1 - w / W) ** 2 / (n - 1)).sum()
    F = A / (1 + 2 * (k - 2) * lam / (k**2 - 1))
    df2 = (k**2 - 1) / (3 * lam)
    return F, df2


def boot_ci(groups, fn):
    r = stats.bootstrap(tuple(groups), fn, n_resamples=N_BOOT, batch=None, confidence_level=0.95,
                        method="percentile", paired=False, vectorized=False,
                        rng=np.random.default_rng(SEED))
    return r.confidence_interval.low, r.confidence_interval.high


TEST_ROWS, T4_ROWS, T6_ROWS = [], [], []
PICK_RATE = {}  # (처리, A/B) -> 집단별 고른 비율 문자열 목록 + 전체
GROUP_TABLE = {}  # (처리, 구분) -> 표 행
CI_FLAG = []

for tkey, S, NREST, NDIST in [("유지", 13, 741, 555), ("제외", 284, 743, 648)]:
    d = TREAT[tkey]
    NT = len(d)
    tn = TNAME[tkey]
    after_T = int(d["후"].sum())
    if after_T == 0:
        stop("2023년 이후 구입 0권")
    fx = d["대출횟수"].to_numpy()

    # 집단 확인 (2절)
    if sorted(d["발행년"].unique()) != YEARS:
        stop(f"{tkey} 발행년 집단이 2005~2025 21개가 아님")
    if sorted(d["주제"].unique()) != sorted(SUBJECTS):
        stop(f"{tkey} 주제 집단 10개 아님")

    gy = [d.loc[d["발행년"] == y, "대출횟수"].to_numpy() for y in YEARS]
    gs = [d.loc[d["주제"] == s, "대출횟수"].to_numpy() for s in SUBJECTS]
    for arrs in (gy, gs):
        for a in arrs:
            if len(a) < 2 or a.var(ddof=1) <= 0:
                stop(f"{tkey} 집단 크기<2 또는 분산 0")

    # ① 집단별 표
    sum_after = 0
    for kind, labels, arrs, base, step, colname in [
        ("발행년", YEARS, gy, S, 5, "발행년"), ("주제", SUBJECTS, gs, S + 105, 4, "주제")]:
        means = [Fraction(int(a.sum()), len(a)) for a in arrs]
        if len(set(means)) != len(means):
            stop(f"{tkey} {kind} 평균 동률")
        order = sorted(range(len(means)), key=lambda i: means[i])
        rank = {i: r + 1 for r, i in enumerate(order)}
        rows = []
        for i, (lab, a) in enumerate(zip(labels, arrs)):
            b = base + step * i
            pre = f"{tn} {kind} {lab}"
            put(b, f"{pre} 권수", len(a))
            put(b + 1, f"{pre} 총합", int(a.sum()))
            put(b + 2, f"{pre} 평균", fr(means[i]))
            put(b + 3, f"{pre} 평균 오름차순 순위", rank[i])
            EXACT[(tkey, kind, lab, "평균")] = means[i]
            row = [rank[i], lab, len(a), int(a.sum()), fr(means[i])]
            if kind == "발행년":
                na = int(d.loc[d["발행년"] == lab, "후"].sum())
                sum_after += na
                pr = Fraction(na * 100, len(a))
                EXACT[(tkey, "발행년", lab, "후비율")] = pr
                put(b + 4, f"{pre} 2023년 이후 구입 비율", fr(pr))
                row.append(fr(pr))
            rows.append(row)
        if sum(len(a) for a in arrs) != NT:
            stop("권수 합 불일치")
        GROUP_TABLE[(tkey, kind)] = sorted(rows)
        # 6-7 최고-최저
        diff = means[order[-1]] - means[order[0]]
        if diff < 0:
            stop("최고-최저 음수")
        nd = {("유지", "발행년"): 745, ("유지", "주제"): 746, ("제외", "발행년"): 747, ("제외", "주제"): 748}[(tkey, kind)]
        put(nd, f"{tn} {kind} 집단 평균 최댓값-최솟값", fr(diff))
    if sum(int(a.sum()) for a in gy) != sum(int(a.sum()) for a in gs):
        stop("총합 합 불일치")
    if sum_after != after_T:
        stop("발행년별 2023 이후 권수 합 != 전체")
    put(S + 145, f"{tn} 2023년 이후 구입 권수", after_T)
    put(S + 146, f"{tn} 2023년 이후 구입 비율", fr(Fraction(after_T * 100, NT)))

    # ② 검정
    for kind, arrs, base in [("발행년", gy, S + 146), ("주제", gs, S + 157)]:
        k = len(arrs)
        wr = stats.f_oneway(*arrs, equal_var=False)
        F2, df2 = welch([a.astype(np.float64) for a in arrs])
        if not np.isclose(wr.statistic, F2, rtol=1e-9):
            stop("웰치 F 함수값과 식 값 불일치")
        pw = stats.f.sf(wr.statistic, k - 1, df2)
        kr = stats.kruskal(*arrs)
        e2, ep2 = eta2(*arrs), eps2(*arrs)
        print(f"[{tkey} {kind}] 부트스트랩 시작", flush=True)
        el, eh = boot_ci(arrs, eta2)
        pl, ph = boot_ci(arrs, eps2)
        pre = f"{tn} {kind}"
        vals = [("웰치 F", fl(wr.statistic, 2)), ("웰치 분모 자유도 df2", fl(df2, 2)), ("웰치 p", pfmt(pw)),
                ("η²", fl(e2, 4)), ("η² 95% 신뢰구간 하한", fl(el, 4)), ("η² 95% 신뢰구간 상한", fl(eh, 4)),
                ("크러스컬-월리스 H", fl(kr.statistic, 2)), ("크러스컬-월리스 p", pfmt(kr.pvalue)),
                ("ε²", fl(ep2, 4)), ("ε² 95% 신뢰구간 하한", fl(pl, 4)), ("ε² 95% 신뢰구간 상한", fl(ph, 4))]
        for pos, (nm, v) in enumerate(vals, start=1):
            put(base + pos, f"{pre} {nm}", v)
        for nm, (pt, a, b) in [("η²", vals[3:6]), ("ε²", vals[8:11])]:
            inside = Decimal(a[1]) <= Decimal(pt[1]) <= Decimal(b[1])
            CI_FLAG.append(f"{tn} {kind} {nm}: 점추정 {pt[1]} 구간 [{a[1]}, {b[1]}] {'안' if inside else '밖'}")
        TEST_ROWS.append([tn, kind, "웰치 분산분석", vals[0][1], f"{k - 1}, {vals[1][1]}", vals[2][1],
                          "η²", vals[3][1], vals[4][1], vals[5][1]])
        TEST_ROWS.append([tn, kind, "크러스컬-월리스", vals[6][1], f"{k - 1}", vals[7][1],
                          "ε²", vals[8][1], vals[9][1], vals[10][1]])

    # ③ 고른 책 A·B
    for ab, col, base, nrest in [("A", "발행년", S + 168, NREST), ("B", "주제", S + 219, NREST + 1)]:
        cnt = d.groupby(col)["대출횟수"].transform("size")
        tot = d.groupby(col)["대출횟수"].transform("sum")
        pick = (d["대출횟수"] * cnt < tot).to_numpy()
        P, R = d[pick], d[~pick]
        m1 = len(P)
        pre = f"{tn} {ab}"
        M = {}
        M[1] = ("고른 권수", m1)
        M[2] = ("고른 비율", fr(Fraction(m1 * 100, NT)))
        M[3] = ("고른 책 대출횟수 최댓값", int(P["대출횟수"].max()))
        M[4] = ("고른 책 중 대출 0회 비율", fr(Fraction(int((P["대출횟수"] == 0).sum()) * 100, m1)))
        rates = []
        sy = ss = 0
        for i, y in enumerate(YEARS):
            np_ = int((P["발행년"] == y).sum())
            sy += np_
            v = fr(Fraction(np_ * 100, int((d["발행년"] == y).sum())))
            M[5 + i] = (f"발행년 {y} 고른 비율", v)
            rates.append(v)
        for j, s in enumerate(SUBJECTS):
            np_ = int((P["주제"] == s).sum())
            ss += np_
            v = fr(Fraction(np_ * 100, int((d["주제"] == s).sum())))
            M[26 + j] = (f"주제 {s} 고른 비율", v)
            rates.append(v)
        if sy != m1 or ss != m1:
            stop("고른 권수 합 불일치")
        rates.append(M[2][1])
        PICK_RATE[(tkey, ab)] = rates
        M[36] = ("고른 책 발행년 평균", fr(Fraction(int(P["발행년"].sum()), m1)))
        M[37] = ("나머지 발행년 평균", fr(Fraction(int(R["발행년"].sum()), len(R))))
        M[38] = ("고른 책 발행년 중앙값", median_inv(P["발행년"].tolist()))
        M[39] = ("나머지 발행년 중앙값", median_inv(R["발행년"].tolist()))
        M[40] = ("고른 책 구입일 중앙값", median_inv(P["구입일문자"].tolist()))
        M[41] = ("나머지 구입일 중앙값", median_inv(R["구입일문자"].tolist()))
        M[42] = ("고른 책 구입가격 평균", fr(Fraction(int(P["구입가격"].sum()), m1)))
        M[43] = ("나머지 구입가격 평균", fr(Fraction(int(R["구입가격"].sum()), len(R))))
        M[44] = ("고른 책 구입가격 중앙값", median_inv(P["구입가격"].tolist()))
        M[45] = ("나머지 구입가격 중앙값", median_inv(R["구입가격"].tolist()))
        m46 = int(P["후"].sum())
        if m46 > m1:
            stop("m46 > m1")
        M[46] = ("고른 책 중 2023년 이후 구입 권수", m46)
        f47 = Fraction(m46 * 100, m1)
        M[47] = ("고른 책 중 2023년 이후 구입 비율", fr(f47))
        M[48] = ("2023년 이후 구입분 중 고른 비율", fr(Fraction(m46 * 100, after_T)))
        for i, y in enumerate([2023, 2024, 2025]):
            py = P.loc[P["발행년"] == y, "대출횟수"]
            if len(py) == 0:
                stop(f"{y} 발행 고른 책 0권")
            M[49 + i] = (f"{y}년 발행 고른 책 대출횟수 최댓값", int(py.max()))
        for m, (nm, v) in M.items():
            put(base + m, f"{pre} {nm}", v)
        # 6-6, 6-7
        nr = len(R)
        if nr == 0:
            stop("나머지 0권")
        r_after = int(R["후"].sum())
        if r_after + m46 != after_T:
            stop("나머지+고른 2023 이후 권수 != 전체")
        f_rest = Fraction(r_after * 100, nr)
        put(nrest, f"{pre} 나머지 중 2023년 이후 구입 비율", fr(f_rest))
        nd = {("유지", "A"): 749, ("유지", "B"): 750, ("제외", "A"): 751, ("제외", "B"): 752}[(tkey, ab)]
        put(nd, f"{pre} 2023년 이후 구입 비율 차이 (고른 책-나머지)", fr(f47 - f_rest))
        T4_ROWS.append([tn, ab, "고른 책", m1, M[2][1], M[3][1], M[4][1], M[36][1], M[38][1], M[40][1],
                        M[42][1], M[44][1], m46, M[47][1], M[48][1], f"{M[49][1]} / {M[50][1]} / {M[51][1]}"])
        T4_ROWS.append([tn, ab, "나머지", NT - m1, "", "", "", M[37][1], M[39][1], M[41][1],
                        M[43][1], M[45][1], "", fr(f_rest), "", ""])

    # 6-5 분포 수치
    for kind, labels, arrs, base in [("발행년", YEARS, gy, NDIST), ("주제", SUBJECTS, gs, NDIST + 63)]:
        for i, (lab, a) in enumerate(zip(labels, arrs)):
            af = a.astype(np.float64)
            sdv = fl(np.std(af, ddof=1), 2)
            skv = fl(stats.skew(af, bias=False), 2)
            zr = fr(Fraction(int((a == 0).sum()) * 100, len(a)))
            pre = f"{tn} {kind} {lab}"
            put(base + 3 * i, f"{pre} 표준편차", sdv)
            put(base + 3 * i + 1, f"{pre} 왜도", skv)
            put(base + 3 * i + 2, f"{pre} 0 비율", zr)
            T6_ROWS.append([tn, kind, lab, len(a), sdv, skv, zr])

if sorted(NUM) != list(range(1, 753)):
    stop(f"핵심 수치 번호 누락: {sorted(set(range(1, 753)) - set(NUM))}")


# ---------- 저장 ----------
def wcsv(name, header, rows):
    with open(OUT + name, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


wcsv("핵심수치.csv", ["번호", "항목", "값"], [[f"N{n}", NUM[n][0], NUM[n][1]] for n in range(1, 753)])
for tkey, suf in [("유지", "유지"), ("제외", "3SD제외")]:
    wcsv(f"표1_발행년별_대출횟수_{suf}.csv",
         ["순위", "발행년", "권수", "대출횟수 총합", "평균 대출횟수", "2023년 이후 구입 비율(%)"],
         GROUP_TABLE[(tkey, "발행년")])
    wcsv(f"표2_주제별_대출횟수_{suf}.csv", ["순위", "주제분류명", "권수", "대출횟수 총합", "평균 대출횟수"],
         GROUP_TABLE[(tkey, "주제")])
wcsv("표3_검정결과.csv", ["처리", "구분", "검정", "통계량", "자유도", "p", "효과크기 이름", "효과크기",
                       "95% 신뢰구간 하한", "95% 신뢰구간 상한"], TEST_ROWS)
wcsv("표4_평균미만_비교.csv",
     ["처리", "기준", "책", "권수", "대상 중 비율(%)", "대출횟수 최댓값", "대출 0회 비율(%)", "발행년 평균",
      "발행년 중앙값", "구입일 중앙값", "구입가격 평균", "구입가격 중앙값", "2023년 이후 구입 권수",
      "2023년 이후 구입 비율(%)", "2023년 이후 구입분 중 고른 비율(%)", "2023·2024·2025년 발행 고른 책 최댓값"],
     T4_ROWS)
labels5 = [("발행년", y) for y in YEARS] + [("주제", s) for s in SUBJECTS] + [("전체", "전체")]
wcsv("표5_평균미만_집단별비율.csv",
     ["구분", "집단", "유지 A 고른 비율(%)", "유지 B 고른 비율(%)", "평균±3SD 제외 A 고른 비율(%)",
      "평균±3SD 제외 B 고른 비율(%)"],
     [[k, lab] + [PICK_RATE[(t, ab)][i] for t in ("유지", "제외") for ab in ("A", "B")]
      for i, (k, lab) in enumerate(labels5)])
wcsv("표6_집단별분포.csv", ["처리", "구분", "집단", "권수", "표준편차", "왜도", "0 비율(%)"], T6_ROWS)

# ---------- 그림 (유지만, 규칙 10) ----------
FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

hatch_ok = all(EXACT[("유지", "발행년", y, "후비율")] == 100 for y in (2023, 2024, 2025))
for kind, fname, size, xlabel, title in [
        ("발행년", "그림1_발행년별_대출횟수_유지.png", (14, 9), "발행년", "발행년별 대출횟수(2023~2025년) — 평균 오름차순"),
        ("주제", "그림2_주제별_대출횟수_유지.png", (12, 9), "주제분류명", "주제분류명별 대출횟수(2023~2025년) — 평균 오름차순")]:
    rows = GROUP_TABLE[("유지", kind)]
    labs = [str(r[1]) for r in rows]
    hat = [("//" if kind == "발행년" and hatch_ok and r[1] in (2023, 2024, 2025) else "") for r in rows]
    fig, axes = plt.subplots(2, 1, figsize=size)
    for ax, idx, ylab, txt in [(axes[0], 4, "평균 대출횟수 (회)", lambda v: v),
                               (axes[1], 3, "대출횟수 총합 (회)", lambda v: f"{v:,}")]:
        vals = [float(r[idx]) for r in rows]
        bars = ax.bar(labs, vals, color="#4C72B0", edgecolor="black", hatch=hat)
        for bar, r in zip(bars, rows):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), txt(r[idx]),
                    ha="center", va="bottom", fontsize=8)
        ax.set_ylabel(ylab)
        ax.set_xlabel(xlabel)
        if any(hat):
            from matplotlib.patches import Patch
            ax.legend(handles=[Patch(facecolor="#4C72B0", edgecolor="black", hatch="//",
                                     label="2023년 이후 구입분만 있는 해")])
    fig.suptitle(title)
    note = f"대상: P02_장서목록_대출횟수의 책 {N2:,}권 전부. 대출횟수는 2023~2025년 3년간 대출된 횟수."
    if kind == "발행년" and hatch_ok:
        note += ("\n2023~2025년 발행 책은 모두 2023-01-01 이후 구입분이라, 구입일 이전에는 대출될 수 없었다 "
                 "(대출될 수 있었던 기간이 구입일까지만큼 짧거나, 구입일이 2023-01-01이면 같다).")
    if kind == "주제":
        note += f"\n2023년 이후 구입분 {int(NUM[158][1]):,}권({NUM[159][1]}%)이 들어 있다."
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.text(0.01, 0.005, note, fontsize=9, va="bottom")
    fig.savefig(OUT + fname, dpi=150, bbox_inches="tight")
    plt.close(fig)

# ---------- 결과 문장 조건 확인 (7절, 진행 담당 보고용) ----------
print("그림1 빗금 조건 (유지 2023~2025 f=4 모두 100):", hatch_ok)
for t in ("유지", "제외"):
    print(f"문장1(나) 조건 {t} (2023~2025 평균 정확값 < 1):",
          all(EXACT[(t, "발행년", y, "평균")] < 1 for y in (2023, 2024, 2025)))
print("문장3(나) 조건 (두 처리 2023~2025 f=4 모두 100):",
      all(EXACT[(t, "발행년", y, "후비율")] == 100 for t in ("유지", "제외") for y in (2023, 2024, 2025)))
print("문장3(다) 조건 (N97, N102 > 0):", Fraction(NUM[97][1]) > 0 and Fraction(NUM[102][1]) > 0)
print("문장2 조건 (N12 = 0):", NUM[12][1] == "0")
print("\n".join(CI_FLAG))
print("완료: 핵심 수치", len(NUM), "개")

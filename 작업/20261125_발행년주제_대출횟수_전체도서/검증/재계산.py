# 검증 담당 독립 재계산 — 질문 3 다시 하기 (계산명세 N1~N752)
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/검증/재계산.py
# 읽는 것: 원자료 CSV, 계산명세.md·승인기록.md (사람이 읽음). 분석/ 결과는 읽지 않는다.
# 시드 20261117, 부트스트랩 5000회 (백분위수, batch=None, 호출마다 새 생성기)
import csv
import math
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

import numpy as np
import pandas as pd
from scipy import stats

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_발행년주제_대출횟수_전체도서/검증/검증값.csv"
SEED = 20261117
B = 5000
YEARS = list(range(2005, 2026))
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]


def stop(msg):
    raise SystemExit("멈춤: " + msg)


# ---- 반올림 ----
def fr(x, d=2):
    """정확한 분수 → ROUND_HALF_UP (절댓값 기준), 소수 d자리 문자열."""
    x = Fraction(x)
    s = -1 if x < 0 else 1
    q = abs(x) * 10 ** d
    n = math.floor(q + Fraction(1, 2))
    if n == 0:
        s = 1
    txt = f"{n // 10 ** d}.{n % 10 ** d:0{d}d}" if d else str(n)
    return ("-" if s < 0 else "") + txt


def ff(x, d):
    """float → Decimal(repr(float)) → ROUND_HALF_UP."""
    v = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    t = f"{v:.{d}f}"
    return "0." + "0" * d if t == "-0." + "0" * d else t


def pe(p):
    return format(float(p), ".2e")


def median_inv(vals):
    v = sorted(vals)
    return v[math.ceil(len(v) / 2) - 1]


# ---- 입력 ----
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
N1 = len(raw)
df = pd.DataFrame()
for c in ["발행년", "대출횟수", "구입가격"]:
    s = raw[c].str.strip()
    if not s.str.fullmatch(r"-?\d+").all():
        stop(f"{c} 정수 변환 실패")
    df[c] = s.astype(np.int64)
df["주제"] = raw["주제분류명"]
if not df["주제"].isin(SUBJ).all():
    stop("주제 10개 밖 값")
d = raw["구입일"].str.strip()
dt = pd.to_datetime(d, format="%Y-%m-%d", errors="coerce")
if dt.isna().any():
    stop("구입일 변환 실패")
df["구입일"] = dt.dt.strftime("%Y-%m-%d")  # 정규화된 문자열 (정렬 = 날짜순)
df["구입연도"] = dt.dt.year.astype(np.int64)
df["후"] = df["구입일"] >= "2023-01-01"  # 2023년 이후 구입
N2 = len(df)
if N2 != N1:
    stop("N2 != N1")
if (df["발행년"] > df["구입연도"]).any():
    stop("발행년 > 구입연도 행 있음")

out = []  # (번호, 항목, 값)


def put(n, item, val):
    out.append((n, item, val))


x_all = df["대출횟수"].to_numpy()
mu = x_all.sum() / len(x_all)
sd = float(np.std(x_all.astype(np.float64), ddof=1))
lo, hi = mu - 3 * sd, mu + 3 * sd
excl = (x_all > hi) | (x_all < lo)
N7, N8 = int(excl.sum()), int((~excl).sum())
if N7 + N8 != N2:
    stop("N7+N8")
gap = df["구입연도"] - df["발행년"]
n9, n10, n11 = int((gap == 0).sum()), int((gap == 1).sum()), int((gap == 2).sum())
n12 = int((~gap.isin([0, 1, 2])).sum())
if n9 + n10 + n11 + n12 != N2:
    stop("N9~N12 합")
for n, it, v in [(1, "입력 행 수", str(N1)), (2, "대상 권수 (유지)", str(N2)),
                 (3, "대상 대출횟수 평균", ff(mu, 4)), (4, "대상 대출횟수 표본 표준편차", ff(sd, 4)),
                 (5, "제외 아래 경계", ff(lo, 4)), (6, "제외 위 경계", ff(hi, 4)),
                 (7, "제외한 권수", str(N7)), (8, "제외 후 권수", str(N8)),
                 (9, "구입연도-발행년=0 권수", str(n9)), (10, "구입연도-발행년=1 권수", str(n10)),
                 (11, "구입연도-발행년=2 권수", str(n11)), (12, "구입연도-발행년 0·1·2 아님 권수", str(n12))]:
    put(n, it, v)


# ---- 검정 (직접 식) ----
def welch(groups):
    k = len(groups)
    n = np.array([len(g) for g in groups], float)
    m = np.array([g.mean() for g in groups])
    v = np.array([g.var(ddof=1) for g in groups])
    if (v <= 0).any():
        stop("s_i^2 = 0")
    w = n / v
    W = w.sum()
    xw = (w * m).sum() / W
    A = (w * (m - xw) ** 2).sum() / (k - 1)
    lam = ((1 - w / W) ** 2 / (n - 1)).sum()
    F = A / (1 + 2 * (k - 2) * lam / (k * k - 1))
    df2 = (k * k - 1) / (3 * lam)
    return F, df2, stats.f.sf(F, k - 1, df2)


def kw_H(groups):
    allv = np.concatenate(groups)
    N = len(allv)
    r = stats.rankdata(allv, method="average")
    H0, pos = 0.0, 0
    for g in groups:
        R = r[pos:pos + len(g)].sum()
        H0 += R * R / len(g)
        pos += len(g)
    H0 = 12 / (N * (N + 1)) * H0 - 3 * (N + 1)
    _, t = np.unique(allv, return_counts=True)
    t = t.astype(float)
    return H0 / (1 - (t ** 3 - t).sum() / (float(N) ** 3 - N))


def eta2(*groups):
    allv = np.concatenate(groups).astype(np.float64)
    xb = allv.mean()
    sst = ((allv - xb) ** 2).sum()
    ssb = sum(len(g) * (np.mean(g) - xb) ** 2 for g in groups)
    return ssb / sst


def eps2_boot(*groups):  # 계산명세 5-3: 재표본에 kruskal 그대로
    N = sum(len(g) for g in groups)
    return stats.kruskal(*groups).statistic / (N - 1)


def boot_ci(groups, fn):
    r = stats.bootstrap(tuple(groups), fn, n_resamples=B, batch=None, confidence_level=0.95,
                        method="percentile", paired=False, vectorized=False,
                        rng=np.random.default_rng(SEED))
    return r.confidence_interval.low, r.confidence_interval.high


def ranks(fracs):
    if len(set(fracs)) != len(fracs):
        stop("평균 동률")
    order = sorted(range(len(fracs)), key=lambda i: fracs[i])
    rk = [0] * len(fracs)
    for p, i in enumerate(order):
        rk[i] = p + 1
    return rk


def skewG1(x):
    x = x.astype(np.float64)
    n = len(x)
    dv = x - x.mean()
    m2, m3 = (dv ** 2).mean(), (dv ** 3).mean()
    return math.sqrt(n * (n - 1)) / (n - 2) * (m3 / m2 ** 1.5)


rest741 = {}
diffs = {}


def bundle(T, sub, S, dist_base_y, dist_base_s):
    nT = len(sub)
    x = sub["대출횟수"].to_numpy()
    # 집단
    gy = [sub[sub["발행년"] == y] for y in YEARS]
    gs = [sub[sub["주제"] == s] for s in SUBJ]
    for g in gy + gs:
        if len(g) < 2:
            stop("집단 2권 미만")
    if sum(map(len, gy)) != nT or sum(map(len, gs)) != nT:
        stop("권수 합")
    if sum(int(g["대출횟수"].sum()) for g in gy) != sum(int(g["대출횟수"].sum()) for g in gs):
        stop("총합 합")
    my = [Fraction(int(g["대출횟수"].sum()), len(g)) for g in gy]
    ms = [Fraction(int(g["대출횟수"].sum()), len(g)) for g in gs]
    ry, rs = ranks(my), ranks(ms)
    after_sum = 0
    for k, (y, g) in enumerate(zip(YEARS, gy)):
        b = S + 5 * k
        a = int(g["후"].sum())
        after_sum += a
        put(b, f"{T} 발행년 {y} 권수", str(len(g)))
        put(b + 1, f"{T} 발행년 {y} 총합", str(int(g["대출횟수"].sum())))
        put(b + 2, f"{T} 발행년 {y} 평균", fr(my[k]))
        put(b + 3, f"{T} 발행년 {y} 평균 오름차순 순위", str(ry[k]))
        put(b + 4, f"{T} 발행년 {y} 2023년 이후 구입 비율", fr(Fraction(a, len(g)) * 100))
    for j, (s, g) in enumerate(zip(SUBJ, gs)):
        b = S + 105 + 4 * j
        put(b, f"{T} 주제 {s} 권수", str(len(g)))
        put(b + 1, f"{T} 주제 {s} 총합", str(int(g["대출횟수"].sum())))
        put(b + 2, f"{T} 주제 {s} 평균", fr(ms[j]))
        put(b + 3, f"{T} 주제 {s} 평균 오름차순 순위", str(rs[j]))
    naft = int(sub["후"].sum())
    if naft == 0 or naft != after_sum:
        stop("2023년 이후 구입 권수")
    put(S + 145, f"{T} 전체 2023년 이후 구입 권수", str(naft))
    put(S + 146, f"{T} 전체 2023년 이후 구입 비율", fr(Fraction(naft, nT) * 100))
    # 검정
    for name, groups, base in [("발행년", [g["대출횟수"].to_numpy() for g in gy], S + 146),
                               ("주제", [g["대출횟수"].to_numpy() for g in gs], S + 157)]:
        F, df2, pw = welch(groups)
        e = eta2(*groups)
        H = kw_H(groups)
        Hs = stats.kruskal(*groups).statistic
        if not math.isclose(H, Hs, rel_tol=1e-9):
            stop(f"H 직접식 {H} vs scipy {Hs}")
        pk = stats.chi2.sf(H, len(groups) - 1)
        eps = H / (nT - 1)
        print(f"[{T} {name}] 부트스트랩 η² ...", flush=True)
        el, eh = boot_ci(groups, eta2)
        print(f"[{T} {name}] 부트스트랩 ε² ...", flush=True)
        sl, sh = boot_ci(groups, eps2_boot)
        vals = [("웰치 F", ff(F, 2)), ("웰치 df2", ff(df2, 2)), ("웰치 p", pe(pw)),
                ("η²", ff(e, 4)), ("η² 95% CI 하한", ff(el, 4)), ("η² 95% CI 상한", ff(eh, 4)),
                ("크러스컬-월리스 H", ff(H, 2)), ("크러스컬-월리스 p", pe(pk)),
                ("ε²", ff(eps, 4)), ("ε² 95% CI 하한", ff(sl, 4)), ("ε² 95% CI 상한", ff(sh, 4))]
        for pos, (it, v) in enumerate(vals, 1):
            put(base + pos, f"{T} {name} {it}", v)
    # 고른 책
    ny = sub["발행년"].map({y: len(g) for y, g in zip(YEARS, gy)})
    ty = sub["발행년"].map({y: int(g["대출횟수"].sum()) for y, g in zip(YEARS, gy)})
    ns = sub["주제"].map({s: len(g) for s, g in zip(SUBJ, gs)})
    ts = sub["주제"].map({s: int(g["대출횟수"].sum()) for s, g in zip(SUBJ, gs)})
    selA = (sub["대출횟수"] * ny) < ty
    selB = (sub["대출횟수"] * ns) < ts
    for lab, sel, base in [("A", selA, S + 168), ("B", selB, S + 219)]:
        c, r = sub[sel], sub[~sel]
        m1 = len(c)
        P = f"{T} {lab}"
        put(base + 1, f"{P} 고른 권수", str(m1))
        put(base + 2, f"{P} 고른 비율", fr(Fraction(m1, nT) * 100))
        put(base + 3, f"{P} 고른 책 대출횟수 최댓값", str(int(c["대출횟수"].max())))
        put(base + 4, f"{P} 고른 책 중 대출 0회 비율", fr(Fraction(int((c["대출횟수"] == 0).sum()), m1) * 100))
        cy = 0
        for k, (y, g) in enumerate(zip(YEARS, gy)):
            q = int((c["발행년"] == y).sum()); cy += q
            put(base + 5 + k, f"{P} 발행년 {y} 고른 비율", fr(Fraction(q, len(g)) * 100))
        cs = 0
        for j, (s, g) in enumerate(zip(SUBJ, gs)):
            q = int((c["주제"] == s).sum()); cs += q
            put(base + 26 + j, f"{P} 주제 {s} 고른 비율", fr(Fraction(q, len(g)) * 100))
        if cy != m1 or cs != m1:
            stop("고른 권수 합")
        put(base + 36, f"{P} 고른 책 발행년 평균", fr(Fraction(int(c["발행년"].sum()), m1)))
        put(base + 37, f"{P} 나머지 발행년 평균", fr(Fraction(int(r["발행년"].sum()), len(r))))
        put(base + 38, f"{P} 고른 책 발행년 중앙값", str(median_inv(c["발행년"].tolist())))
        put(base + 39, f"{P} 나머지 발행년 중앙값", str(median_inv(r["발행년"].tolist())))
        put(base + 40, f"{P} 고른 책 구입일 중앙값", median_inv(c["구입일"].tolist()))
        put(base + 41, f"{P} 나머지 구입일 중앙값", median_inv(r["구입일"].tolist()))
        put(base + 42, f"{P} 고른 책 구입가격 평균", fr(Fraction(int(c["구입가격"].sum()), m1)))
        put(base + 43, f"{P} 나머지 구입가격 평균", fr(Fraction(int(r["구입가격"].sum()), len(r))))
        put(base + 44, f"{P} 고른 책 구입가격 중앙값", str(median_inv(c["구입가격"].tolist())))
        put(base + 45, f"{P} 나머지 구입가격 중앙값", str(median_inv(r["구입가격"].tolist())))
        m46 = int(c["후"].sum())
        put(base + 46, f"{P} 고른 책 중 2023년 이후 구입 권수", str(m46))
        put(base + 47, f"{P} 고른 책 중 2023년 이후 구입 비율", fr(Fraction(m46, m1) * 100))
        put(base + 48, f"{P} 2023년 이후 구입분 중 고른 비율", fr(Fraction(m46, naft) * 100))
        for i, y in enumerate([2023, 2024, 2025]):
            cc = c[c["발행년"] == y]
            if len(cc) == 0:
                stop(f"{P} {y} 고른 책 0권")
            put(base + 49 + i, f"{P} {y}년 발행 고른 책 대출횟수 최댓값", str(int(cc["대출횟수"].max())))
        ra = int(r["후"].sum())
        if len(r) == 0 or ra + m46 != naft:
            stop("나머지 2023년 이후 구입 합")
        rest741[(T, lab)] = Fraction(ra, len(r)) * 100
        diffs[(T, lab)] = Fraction(m46, m1) * 100 - rest741[(T, lab)]
    # 6-5 분포 수치
    for k, (y, g) in enumerate(zip(YEARS, gy)):
        v = g["대출횟수"].to_numpy(); b = dist_base_y + 3 * k
        put(b, f"{T} 발행년 {y} 표준편차", ff(np.std(v.astype(np.float64), ddof=1), 2))
        put(b + 1, f"{T} 발행년 {y} 왜도", ff(skewG1(v), 2))
        put(b + 2, f"{T} 발행년 {y} 0 비율", fr(Fraction(int((v == 0).sum()), len(v)) * 100))
    for j, (s, g) in enumerate(zip(SUBJ, gs)):
        v = g["대출횟수"].to_numpy(); b = dist_base_s + 3 * j
        put(b, f"{T} 주제 {s} 표준편차", ff(np.std(v.astype(np.float64), ddof=1), 2))
        put(b + 1, f"{T} 주제 {s} 왜도", ff(skewG1(v), 2))
        put(b + 2, f"{T} 주제 {s} 0 비율", fr(Fraction(int((v == 0).sum()), len(v)) * 100))
    return max(my) - min(my), max(ms) - min(ms)


dy_k, ds_k = bundle("유지", df, 13, 555, 618)
dy_e, ds_e = bundle("제외", df[~excl].reset_index(drop=True), 284, 648, 711)

put(741, "유지 A 나머지 중 2023년 이후 구입 비율", fr(rest741[("유지", "A")]))
put(742, "유지 B 나머지 중 2023년 이후 구입 비율", fr(rest741[("유지", "B")]))
put(743, "제외 A 나머지 중 2023년 이후 구입 비율", fr(rest741[("제외", "A")]))
put(744, "제외 B 나머지 중 2023년 이후 구입 비율", fr(rest741[("제외", "B")]))
for n, it, v in [(745, "유지 발행년 집단 평균 최댓값-최솟값", dy_k), (746, "유지 주제 집단 평균 최댓값-최솟값", ds_k),
                 (747, "제외 발행년 집단 평균 최댓값-최솟값", dy_e), (748, "제외 주제 집단 평균 최댓값-최솟값", ds_e)]:
    if v < 0:
        stop("차이 음수")
    put(n, it, fr(v))
put(749, "유지 A 2023년 이후 구입 비율 차이 (고른-나머지)", fr(diffs[("유지", "A")]))
put(750, "유지 B 2023년 이후 구입 비율 차이 (고른-나머지)", fr(diffs[("유지", "B")]))
put(751, "제외 A 2023년 이후 구입 비율 차이 (고른-나머지)", fr(diffs[("제외", "A")]))
put(752, "제외 B 2023년 이후 구입 비율 차이 (고른-나머지)", fr(diffs[("제외", "B")]))

out.sort()
nums = [o[0] for o in out]
assert nums == list(range(1, 753)), "번호 빠짐/겹침"
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    for n, it, v in out:
        w.writerow([f"N{n}", it, v])
print("저장:", OUT, len(out))

if __name__ == "__main__":
    # ponytail: 반올림 도우미 자기 점검
    assert fr(Fraction(1235, 1000)) == "1.24" and fr(Fraction(-1235, 1000)) == "-1.24"
    assert fr(Fraction(-1, 1000)) == "0.00" and ff(1.2, 2) == "1.20"

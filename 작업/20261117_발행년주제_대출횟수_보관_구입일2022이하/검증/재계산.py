# 검증 담당 독립 재계산 — 질문 3 (발행년·주제분류별 대출횟수), 계산명세 N1~N616
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/검증/재계산.py
# 읽는 것: 원자료 CSV만 (계산명세.md·승인기록.md·데이터코드북.docx는 사람이 읽고 정의를 옮김)
# 분석 담당과 다른 길: 표준 라이브러리 csv로 읽기, 평균·비율은 Fraction, 웰치 F·KW H·η²·왜도·순위는 손계산
# (scipy는 손계산 대조와 p값 분포함수, 명세가 같은 호출을 요구한 부트스트랩에만 씀)
import csv
import math
import sys
from datetime import date, datetime
from fractions import Fraction

import numpy as np
from scipy import stats

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/검증/검증값.csv"
SEED = 20261117
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
YEARS = list(range(2005, 2023))
CUT = date(2022, 12, 31)
STOPS = []  # 멈추고 보고 조건


def stop(msg):
    STOPS.append(msg)
    print("[멈춤 조건]", msg)


# ---------- 반올림 ----------
def frac2(q):
    """정확한 분수 → ROUND_HALF_UP 소수 둘째 (값은 모두 0 이상)."""
    q = Fraction(q)
    assert q >= 0
    v = math.floor(q * 100 + Fraction(1, 2))
    return f"{v // 100}.{v % 100:02d}"


def fl(x, d):
    """float → Decimal(repr(float(x))) ROUND_HALF_UP d자리."""
    from decimal import Decimal, ROUND_HALF_UP
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP))


def pfmt(p):
    return format(float(p), ".2e")


# ---------- 읽기 ----------
rows = []
with open(SRC, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rows.append(r)
N1 = len(rows)

recs = []  # (발행년, 주제, 구입일, 구입가격, 대출횟수)  입력 행 순서
for r in rows:
    try:
        d = datetime.strptime(r["구입일"].strip(), "%Y-%m-%d").date()
    except ValueError:
        stop(f"구입일 변환 실패: {r['자료ID']} {r['구입일']!r}")
        continue
    try:
        y, price, loan = int(r["발행년"].strip()), int(r["구입가격"].strip()), int(r["대출횟수"].strip())
    except ValueError:
        stop(f"정수 변환 실패: {r['자료ID']}")
        continue
    s = r["주제분류명"]
    if s not in SUBJ:
        stop(f"주제 10개 밖 값: {r['자료ID']} {s!r}")
    recs.append((y, s, d, price, loan))

target = [t for t in recs if t[2] <= CUT]
N2 = len(target)

# ---------- N3~N8 ----------
xs = [t[4] for t in target]
mu = sum(xs) / N2  # 정수 합 / n, float
var_exact = sum((Fraction(x) - Fraction(sum(xs), N2)) ** 2 for x in xs) / (N2 - 1)
sd = math.sqrt(float(var_exact))
lo, hi = mu - 3 * sd, mu + 3 * sd
N7 = sum(1 for x in xs if x > hi or x < lo)
excl = [t for t in target if not (t[4] > hi or t[4] < lo)]
N8 = len(excl)
if N7 + N8 != N2:
    stop("N7 + N8 != N2")
assert abs(sd - float(np.std(np.array(xs), ddof=1))) < 1e-9

# ---------- N9~N12 ----------
gap = [t[2].year - t[0] for t in target]
N9, N10, N11 = gap.count(0), gap.count(1), gap.count(2)
N12 = sum(1 for g in gap if g not in (0, 1, 2))
if N9 + N10 + N11 + N12 != N2:
    stop("N9~N12 합 != N2")
if N12 != 0:
    stop(f"N12 = {N12} (0이 아님, 결과 문장 수정 필요)")

out = [("N1", "입력 행 수", str(N1)), ("N2", "대상 권수 (유지)", str(N2)),
       ("N3", "대상 대출횟수 평균 μ", fl(mu, 4)), ("N4", "대상 대출횟수 표본 표준편차 s", fl(sd, 4)),
       ("N5", "제외 아래 경계 μ−3s", fl(lo, 4)), ("N6", "제외 위 경계 μ+3s", fl(hi, 4)),
       ("N7", "제외한 권수", str(N7)), ("N8", "제외 후 권수", str(N8)),
       ("N9", "구입연도−발행년=0 권수", str(N9)), ("N10", "구입연도−발행년=1 권수", str(N10)),
       ("N11", "구입연도−발행년=2 권수", str(N11)), ("N12", "구입연도−발행년이 0·1·2 아닌 권수", str(N12))]


# ---------- 손계산 도구 ----------
def mean_f(v):
    return Fraction(sum(v), len(v))


def var_f(v):
    m = mean_f(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def welch(groups):
    k = len(groups)
    n = [len(g) for g in groups]
    m = [float(mean_f(g)) for g in groups]
    s2 = [float(var_f(g)) for g in groups]
    w = [n[i] / s2[i] for i in range(k)]
    W = math.fsum(w)
    xw = math.fsum(w[i] * m[i] for i in range(k)) / W
    A = math.fsum(w[i] * (m[i] - xw) ** 2 for i in range(k)) / (k - 1)
    lam = math.fsum((1 - w[i] / W) ** 2 / (n[i] - 1) for i in range(k))
    F = A / (1 + 2 * (k - 2) * lam / (k * k - 1))
    df2 = (k * k - 1) / (3 * lam)
    return F, k - 1, df2, stats.f.sf(F, k - 1, df2)


def avg_ranks(allv):
    """평균 순위를 정렬·묶음으로 직접 계산 (rankdata 미사용)."""
    order = sorted(range(len(allv)), key=lambda i: allv[i])
    rk = [0.0] * len(allv)
    ties = []
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and allv[order[j + 1]] == allv[order[i]]:
            j += 1
        r = (i + 1 + j + 1) / 2
        for t in range(i, j + 1):
            rk[order[t]] = r
        ties.append(j - i + 1)
        i = j + 1
    return rk, ties


def kw(groups):
    allv = [x for g in groups for x in g]
    N = len(allv)
    rk, ties = avg_ranks(allv)
    pos, s = 0, Fraction(0)
    for g in groups:
        R = Fraction(sum(Fraction(r) for r in rk[pos:pos + len(g)]))
        s += R * R / len(g)
        pos += len(g)
    H0 = Fraction(12, N * (N + 1)) * s - 3 * (N + 1)
    C = 1 - Fraction(sum(t ** 3 - t for t in ties), N ** 3 - N)
    H = float(H0 / C)
    return H, len(groups) - 1, stats.chi2.sf(H, len(groups) - 1)


def eta2_exact(groups):
    allv = [x for g in groups for x in g]
    m = mean_f(allv)
    sst = sum((x - m) ** 2 for x in allv)
    ssb = sum(len(g) * (mean_f(g) - m) ** 2 for g in groups)
    return float(ssb / sst)


def skew_G1(v):
    n = len(v)
    m = mean_f(v)
    m2 = sum((x - m) ** 2 for x in v) / n
    m3 = sum((x - m) ** 3 for x in v) / n
    g1 = float(m3) / float(m2) ** 1.5
    return math.sqrt(n * (n - 1)) / (n - 2) * g1


def median_low(v):
    s = sorted(v)
    return s[math.ceil(len(s) / 2) - 1]


# 부트스트랩 통계량 (명세 5-3: 재표본에 η²·ε² 식을 그대로)
def stat_eta(*s):
    a = np.concatenate(s).astype(np.float64)
    m = a.mean()
    sst = ((a - m) ** 2).sum()
    ssb = sum(len(g) * (g.mean() - m) ** 2 for g in s)
    return ssb / sst


def stat_eps(*s):
    N = sum(len(g) for g in s)
    return stats.kruskal(*s).statistic / (N - 1)


def boot(data, fn):
    r = stats.bootstrap(data, fn, n_resamples=5000, batch=None, confidence_level=0.95,
                        method="percentile", paired=False, vectorized=False,
                        rng=np.random.default_rng(SEED))
    return r.confidence_interval.low, r.confidence_interval.high


CI_NOTE = []


# ---------- 처리별 묶음 ----------
def bundle(rs, tname, base, dist_base_y, dist_base_s):
    res = []
    NT = len(rs)
    by_y = {y: [t for t in rs if t[0] == y] for y in sorted({t[0] for t in rs})}
    by_s = {s: [t for t in rs if t[1] == s] for s in sorted({t[1] for t in rs})}
    if sorted(by_y) != YEARS:
        stop(f"{tname}: 발행년 집단이 2005~2022 연속 18개가 아님 {sorted(by_y)}")
    if sorted(by_s) != sorted(SUBJ):
        stop(f"{tname}: 주제 집단이 10개가 아님")
    gy = [[t[4] for t in by_y[y]] for y in YEARS]
    gs = [[t[4] for t in by_s[s]] for s in SUBJ]
    for g in gy + gs:
        if len(g) < 2 or var_f(g) == 0:
            stop(f"{tname}: 집단 크기<2 또는 분산 0")
    if sum(map(len, gy)) != NT or sum(map(len, gs)) != NT or sum(map(sum, gy)) != sum(map(sum, gs)):
        stop(f"{tname}: 권수·총합 합 확인 어긋남")

    # ① 표
    def table(groups, labels, start, kind):
        means = [mean_f(g) for g in groups]
        if len(set(means)) != len(means):
            stop(f"{tname} {kind}: 정확한 분수 평균 동률")
        order = sorted(range(len(groups)), key=lambda i: means[i])
        rank = {i: order.index(i) + 1 for i in range(len(groups))}
        for i, (g, lab) in enumerate(zip(groups, labels)):
            n0 = start + 4 * i
            res.append((f"N{n0}", f"{tname} {kind} {lab} 권수", str(len(g))))
            res.append((f"N{n0+1}", f"{tname} {kind} {lab} 총합", str(sum(g))))
            res.append((f"N{n0+2}", f"{tname} {kind} {lab} 평균", frac2(means[i])))
            res.append((f"N{n0+3}", f"{tname} {kind} {lab} 평균 오름차순 순위", str(rank[i])))

    table(gy, YEARS, base, "발행년")
    table(gs, SUBJ, base + 72, "주제")

    # ② 검정
    def tests(groups, start, kind):
        F, df1, df2, p = welch(groups)
        sp = stats.f_oneway(*groups, equal_var=False)
        H, dfk, pk = kw(groups)
        sk = stats.kruskal(*groups)
        N = sum(map(len, groups))
        e2 = eta2_exact(groups)
        eps = H / (N - 1)
        print(f"[대조] {tname} {kind}: 웰치 F 손 {F:.10f} / scipy {sp.statistic:.10f}; p 손 {p:.6e} / scipy {sp.pvalue:.6e}")
        print(f"[대조] {tname} {kind}: KW H 손 {H:.10f} / scipy {sk.statistic:.10f}; p 손 {pk:.6e} / scipy {sk.pvalue:.6e}")
        assert abs(F - sp.statistic) < 1e-8 * max(1, F) and abs(H - sk.statistic) < 1e-8 * max(1, H)
        data = tuple(np.array(g, dtype=np.int64) for g in groups)
        assert abs(stat_eta(*data) - e2) < 1e-12 and abs(stat_eps(*data) - eps) < 1e-12
        el, eh = boot(data, stat_eta)
        pl, ph = boot(data, stat_eps)
        lab = f"{tname} {kind}"
        vals = [("웰치 F", fl(F, 2)), ("웰치 분모 자유도 df2", fl(df2, 2)), ("웰치 p", pfmt(p)),
                ("η²", fl(e2, 4)), ("η² 95% 신뢰구간 하한", fl(el, 4)), ("η² 95% 신뢰구간 상한", fl(eh, 4)),
                ("크러스컬-월리스 H", fl(H, 2)), ("크러스컬-월리스 p", pfmt(pk)),
                ("ε²", fl(eps, 4)), ("ε² 95% 신뢰구간 하한", fl(pl, 4)), ("ε² 95% 신뢰구간 상한", fl(ph, 4))]
        for i, (nm, v) in enumerate(vals):
            res.append((f"N{start+i}", f"{lab} {nm}", v))
        for nm, pt, a, b in (("η²", vals[3][1], vals[4][1], vals[5][1]), ("ε²", vals[8][1], vals[9][1], vals[10][1])):
            inside = float(a) <= float(pt) <= float(b)
            CI_NOTE.append(f"{lab} {nm}: 점추정 {pt}, 구간 [{a}, {b}] → {'안' if inside else '밖'}")

    tests(gy, base + 112, "발행년")
    tests(gs, base + 123, "주제")

    # ③ 고른 책
    tot_y = {y: (sum(t[4] for t in by_y[y]), len(by_y[y])) for y in YEARS}
    tot_s = {s: (sum(t[4] for t in by_s[s]), len(by_s[s])) for s in SUBJ}
    for key, tot, start, nm in ((0, tot_y, base + 134, "A"), (1, tot_s, base + 176, "B")):
        pick = [t[4] * tot[t[key]][1] < tot[t[key]][0] for t in rs]
        P = [t for t, p in zip(rs, pick) if p]
        O = [t for t, p in zip(rs, pick) if not p]
        m1 = len(P)
        if sum(1 for t in P if t[0] in YEARS) != m1 or sum(1 for t in P if t[1] in SUBJ) != m1:
            stop(f"{tname} {nm}: 고른 권수 합 확인 어긋남")
        v = [str(m1), frac2(Fraction(m1 * 100, NT)), str(max(t[4] for t in P)),
             frac2(Fraction(sum(1 for t in P if t[4] == 0) * 100, m1))]
        v += [frac2(Fraction(sum(1 for t in P if t[0] == y) * 100, len(by_y[y]))) for y in YEARS]
        v += [frac2(Fraction(sum(1 for t in P if t[1] == s) * 100, len(by_s[s]))) for s in SUBJ]
        v += [frac2(mean_f([t[0] for t in P])), frac2(mean_f([t[0] for t in O])),
              str(median_low([t[0] for t in P])), str(median_low([t[0] for t in O])),
              median_low([t[2] for t in P]).isoformat(), median_low([t[2] for t in O]).isoformat(),
              frac2(mean_f([t[3] for t in P])), frac2(mean_f([t[3] for t in O])),
              str(median_low([t[3] for t in P])), str(median_low([t[3] for t in O]))]
        names = ["고른 권수", "고른 비율", "고른 책 대출횟수 최댓값", "고른 책 중 대출 0회 비율"]
        names += [f"{y} 고른 비율" for y in YEARS] + [f"{s} 고른 비율" for s in SUBJ]
        names += ["고른 책 발행년 평균", "나머지 발행년 평균", "고른 책 발행년 중앙값", "나머지 발행년 중앙값",
                  "고른 책 구입일 중앙값", "나머지 구입일 중앙값", "고른 책 구입가격 평균", "나머지 구입가격 평균",
                  "고른 책 구입가격 중앙값", "나머지 구입가격 중앙값"]
        assert len(v) == 42
        for m, (a, b) in enumerate(zip(names, v)):
            res.append((f"N{start+m}", f"{tname} {nm} {a}", b))
        if not (70 <= float(v[1]) <= 80):
            stop(f"{tname} {nm} 고른 비율 {v[1]}%가 70.00~80.00 밖 ('약 3/4' 못 씀)")

    # 6-5 분포 수치
    for groups, labels, start, kind in ((gy, YEARS, dist_base_y, "발행년"), (gs, SUBJ, dist_base_s, "주제")):
        for i, (g, lab) in enumerate(zip(groups, labels)):
            sdv = math.sqrt(float(var_f(g)))
            G1 = skew_G1(g)
            assert abs(G1 - stats.skew(np.array(g, dtype=float), bias=False)) < 1e-9
            n0 = start + 3 * i
            res.append((f"N{n0}", f"{tname} {kind} {lab} 표준편차", fl(sdv, 2)))
            res.append((f"N{n0+1}", f"{tname} {kind} {lab} 왜도", fl(G1, 2)))
            res.append((f"N{n0+2}", f"{tname} {kind} {lab} 0 비율", frac2(Fraction(g.count(0) * 100, len(g)))))
    return res, [len(g) for g in gy]


r_keep, ny_keep = bundle(target, "유지", 13, 449, 503)
r_excl, _ = bundle(excl, "제외", 231, 533, 587)
out += r_keep + r_excl

# 그림 1 각주 조건 (N77·N81이 다른 16개 해 권수보다 모두 작은가) — 그림은 안 그림, 조건만 확인
if not max(ny_keep[16], ny_keep[17]) < min(ny_keep[:16]):
    stop("그림 1 각주 조건 불충족: N77·N81이 다른 16개 해보다 모두 작지 않음")

out.sort(key=lambda t: int(t[0][1:]))
nums = [int(t[0][1:]) for t in out]
assert nums == list(range(1, 617)), "번호 N1~N616 연속 아님"
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(out)

print("\n".join(CI_NOTE))
print("멈춤 조건:", STOPS if STOPS else "없음")
print(f"저장: {OUT} ({len(out)}개)")
sys.exit(1 if STOPS else 0)

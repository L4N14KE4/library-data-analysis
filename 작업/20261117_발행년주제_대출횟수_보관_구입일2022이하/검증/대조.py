# 검증 담당 6단계 ② 대조 — 분석/ 산출물과 검증/검증값.csv 비교
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/검증/대조.py
# 출력: 검증/대조표.md (N1~N616 표) + 화면에 표1~6·결과.md 대조와 경계 판정 확인
import csv
import re
from collections import Counter

import numpy as np
from scipy import stats

W = "작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/"
YEARS = list(range(2005, 2023))
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]


def load(p, enc):
    with open(p, encoding=enc, newline="") as f:
        return {r["번호"]: r for r in csv.DictReader(f)}


A = load(W + "분석/핵심수치.csv", "utf-8-sig")
V = load(W + "검증/검증값.csv", "utf-8")
v = lambda n: V[f"N{n}"]["값"]
keys = [f"N{i}" for i in range(1, 617)]
assert set(A) == set(V) == set(keys)

# ---------- 1. 핵심 수치 616개 (보고 자릿수 문자열 그대로 비교) ----------
rows, ok = [], 0
for k in keys:
    same = A[k]["값"] == V[k]["값"]
    ok += same
    rows.append(f"| {k} | {V[k]['항목']} | {A[k]['값']} | {V[k]['값']} | {'일치' if same else '불일치'} | {'' if same else '확인 필요'} |")
item_diff = [k for k in keys if A[k]["항목"].replace("(발행년 평균 미만) ", " ").replace("(주제 평균 미만) ", " ") != V[k]["항목"]]
print(f"핵심 수치 일치 {ok}/616")


# ---------- 2. 표 CSV (각주 '#' 줄 따로) ----------
def table(name):
    with open(W + "분석/" + name, encoding="utf-8-sig", newline="") as f:
        lines = f.read().splitlines()
    body = [l for l in lines if not l.startswith("#")]
    foot = [l for l in lines if l.startswith("#")]
    rr = list(csv.reader(body))
    # '#' 줄을 보통 csv로 읽으면 몇 칸이 되는지
    foot_cells = [len(next(csv.reader([l]))) for l in foot]
    return rr[0], rr[1:], foot, foot_cells


probs = []
FOOT = {}
for T, base in (("유지", 13), ("3SD제외", 231)):
    for fn, labels, start in ((f"표1_발행년별_대출횟수_{T}.csv", YEARS, base),
                              (f"표2_주제별_대출횟수_{T}.csv", SUBJ, base + 72)):
        h, body, foot, fc = table(fn)
        FOOT[fn] = (foot, fc)
        if len(body) != len(labels):
            probs.append(f"{fn}: 행 수 {len(body)}")
        exp = sorted(((int(v(start + 4 * i + 3)), str(lab), v(start + 4 * i), v(start + 4 * i + 1), v(start + 4 * i + 2))
                      for i, lab in enumerate(labels)))
        got = [(int(r[0]), r[1], r[2], r[3], r[4]) for r in body]
        if got != exp:
            probs.append(f"{fn}: 값 다름")

h, body, foot, fc = table("표3_검정결과.csv")
FOOT["표3_검정결과.csv"] = (foot, fc)
exp = []
for tn, b in (("유지", 125), ("평균±3SD 제외", 343)):
    for dn, s, k in (("발행년", b, 18), ("주제", b + 11, 10)):
        exp.append([tn, dn, "웰치 분산분석", v(s), f"{k-1}, {v(s+1)}", v(s+2), "η²", v(s+3), v(s+4), v(s+5)])
        exp.append([tn, dn, "크러스컬-월리스", v(s+6), f"{k-1}", v(s+7), "ε²", v(s+8), v(s+9), v(s+10)])
if body != exp:
    probs.append("표3 값 다름")

h, body, foot, fc = table("표4_평균미만_비교.csv")
FOOT["표4_평균미만_비교.csv"] = (foot, fc)
exp = []
for tn, b, NT in (("유지", 147, 2), ("평균±3SD 제외", 365, 8)):
    for lab, s in (("A", b), ("B", b + 42)):
        g = lambda m: v(s + m - 1)
        exp.append([tn, lab, "고른 책", g(1), g(2), g(3), g(4), g(33), g(35), g(37), g(39), g(41)])
        exp.append([tn, lab, "나머지", str(int(v(NT)) - int(g(1))), "", "", "", g(34), g(36), g(38), g(40), g(42)])
if body != exp:
    probs.append("표4 값 다름")

h, body, foot, fc = table("표5_평균미만_집단별비율.csv")
FOOT["표5_평균미만_집단별비율.csv"] = (foot, fc)
starts = [147, 189, 365, 407]
exp = [["발행년" if i < 18 else "주제", str(lab)] + [v(s + 4 + i) for s in starts]
       for i, lab in enumerate(YEARS + SUBJ)] + [["전체", "전체"] + [v(s + 1) for s in starts]]
if body != exp:
    probs.append("표5 값 다름")

h, body, foot, fc = table("표6_집단별분포.csv")
FOOT["표6_집단별분포.csv"] = (foot, fc)
exp = []
for tn, b, (dy, ds) in (("유지", 13, (449, 503)), ("평균±3SD 제외", 231, (533, 587))):
    for dn, labels, cs, ds_ in (("발행년", YEARS, b, dy), ("주제", SUBJ, b + 72, ds)):
        for i, lab in enumerate(labels):
            exp.append([tn, dn, str(lab), v(cs + 4 * i), v(ds_ + 3 * i), v(ds_ + 3 * i + 1), v(ds_ + 3 * i + 2)])
if body != exp:
    probs.append("표6 값 다름")
print("표1~6 대조:", probs if probs else "모두 일치")
for fn, (foot, fc) in FOOT.items():
    print(f"각주 {fn}: {len(foot)}줄, csv로 읽으면 칸 수 {fc}")

# ---------- 3. 그림 숫자 (Read로 본 그림 막대 값을 옮겨 적음) ----------
FIG1 = [("2010", "2.31", "3125"), ("2006", "2.45", "3293"), ("2005", "2.47", "3108"), ("2019", "2.57", "3563"),
        ("2007", "2.59", "3483"), ("2017", "2.69", "3705"), ("2008", "2.73", "3829"), ("2013", "2.73", "3703"),
        ("2016", "2.85", "3856"), ("2012", "2.94", "3903"), ("2009", "2.95", "3936"), ("2011", "2.96", "3852"),
        ("2021", "3.06", "2774"), ("2015", "3.08", "3943"), ("2018", "3.19", "4157"), ("2020", "3.51", "4581"),
        ("2014", "3.61", "4872"), ("2022", "3.64", "1514")]
FIG2 = [("총류", "1.61", "2763"), ("기술과학", "1.87", "6335"), ("철학", "2.57", "3167"), ("사회과학", "2.59", "7915"),
        ("자연과학", "2.83", "3934"), ("종교", "2.85", "1887"), ("언어", "2.89", "3259"), ("예술", "2.99", "5267"),
        ("역사", "3.25", "9038"), ("문학", "3.88", "21632")]
for name, fig, labels, start in (("그림1", FIG1, YEARS, 13), ("그림2", FIG2, SUBJ, 85)):
    exp = sorted(((int(v(start + 4 * i + 3)), str(lab), v(start + 4 * i + 2), v(start + 4 * i + 1))
                  for i, lab in enumerate(labels)))
    print(name, "막대 대조:", "일치" if [e[1:] for e in exp] == fig else "다름")
print("그림 각주 숫자: N2 =", v(2), "N77 =", v(77), "N81 =", v(81))

# ---------- 4. 결과.md 안의 'N번호와 함께 쓴 값' ----------
md = open(W + "분석/결과.md", encoding="utf-8").read()
pairs = re.findall(r"(-?\d[\d.]*)%?\s*\(N(\d+)\)", md) + [(b, a) for a, b in re.findall(r"N(\d+) = (-?\d[\d.]*)", md)]
bad_md = [(n, x) for x, n in pairs if 1 <= int(n) <= 616 and x != v(int(n)) and not (x.endswith(".") and x[:-1] == v(int(n)))]
# N 범위 표기(N13~N16 등), 순위·번호 표기('N124 = 1')는 위 식에 함께 걸린다
print("결과.md 값-번호 쌍", len(pairs), "개, 다른 것:", bad_md if bad_md else "없음")
# 결과.md 2-1~2-3·3·4절 표는 표1~6과 같은 값 (위 2에서 대조) — 아래는 결과.md 표 행을 직접 대조
tbl_bad = []
for line in md.splitlines():
    m = re.match(r"\| (\d+) \| (\S+) \| (\d+) \| (\d+) \| ([\d.]+) \| N(\d+)~N\d+ \|", line)
    if m:
        s = int(m.group(6))
        if [m.group(3), m.group(4), m.group(5), m.group(1)] != [v(s), v(s + 1), v(s + 2), v(s + 3)]:
            tbl_bad.append(line)
    m = re.match(r"\| (20\d\d) \| (\d+) \| (\d+) \| ([\d.]+) \| (\d+) \| (\d+) \| (\d+) \| ([\d.]+) \| (\d+) \|", line)
    if m:
        k = int(m.group(1)) - 2005
        if list(m.groups()[1:]) != [v(13 + 4 * k + f) for f in range(4)] + [v(231 + 4 * k + f) for f in range(4)]:
            tbl_bad.append(line)
print("결과.md 2절 표:", tbl_bad if tbl_bad else "일치")

# p값 문장 표기 (p ≥ 0.001 → 소수 셋째, p < 0.001 → '0.001 미만')
for n in (127, 132, 138, 143, 345, 350, 356, 361):
    p = float(v(n))
    print(f"N{n} csv {v(n)} → 문장 표기 기대 {'0.001 미만' if p < 0.001 else format(p, '.3f')}")

# 결과.md 맨 앞 3·4번의 순위 변화 개수 (검증값의 순위로 다시 셈)
for nm, kp, ex, labels in (("주제", 85, 303, SUBJ), ("발행년", 13, 231, YEARS)):
    ch = [(lab, int(v(kp + 4 * i + 3)), int(v(ex + 4 * i + 3))) for i, lab in enumerate(labels)]
    moved = [c for c in ch if c[1] != c[2]]
    mx = max(abs(a - b) for _, a, b in ch)
    print(f"{nm}: 순위 바뀐 집단 {len(moved)}개, 최대 이동 {mx}칸, 최대 이동 집단 {[c for c in ch if abs(c[1]-c[2]) == mx]}")

# ---------- 5. 경계 판정: 제외 발행년 η² 점추정과 하한 (N346·N347), 반올림 전 값 ----------
# 원자료에서 제외 처리 발행년 집단을 다시 만들어 명세 5-3과 같은 호출로 하한을 구한다 (판정 확인용, 핵심 수치 아님)
rec = []
with open("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        if r["구입일"].strip() <= "2022-12-31":
            rec.append((int(r["발행년"].strip()), int(r["대출횟수"].strip())))
x = np.array([b for _, b in rec], dtype=float)
mu, sd = x.sum() / len(x), x.std(ddof=1)
g = tuple(np.array([b for a, b in rec if a == y and mu - 3 * sd <= b <= mu + 3 * sd], dtype=np.int64) for y in YEARS)


def eta(*s):
    a = np.concatenate(s).astype(float)
    m = a.mean()
    return sum(len(t) * (t.mean() - m) ** 2 for t in s) / ((a - m) ** 2).sum()


lo = stats.bootstrap(g, eta, n_resamples=5000, batch=None, confidence_level=0.95, method="percentile",
                     paired=False, vectorized=False, rng=np.random.default_rng(20261117)).confidence_interval.low
print(f"제외 발행년 η² 반올림 전: 점추정 {eta(*g):.8f}, 하한 {lo:.8f} → 반올림 전 비교 {'안' if eta(*g) >= lo else '밖'}")

# ---------- 대조표.md 본문 표 ----------
with open(W + "검증/대조표_N표.tmp", "w", encoding="utf-8") as f:  # 대조표.md의 N 표 본문 (머리말과 합친 뒤 지움)
    f.write("\n".join(rows) + "\n")
print("항목 이름 다른 번호(표기만):", len(item_diff), item_diff[:3])

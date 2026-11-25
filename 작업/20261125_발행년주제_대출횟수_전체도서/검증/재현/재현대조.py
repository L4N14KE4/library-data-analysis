# 8.5단계 재현 대조: 다시 만든 분석/*.csv vs 검증/재현/분석_재현전/*.csv (칸 단위 문자열), 핵심수치.csv vs 검증/검증값.csv
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/검증/재현/재현대조.py
import csv, glob, os
os.chdir("작업/20261125_발행년주제_대출횟수_전체도서")
rd = lambda p: list(csv.reader(open(p, encoding="utf-8-sig")))
tot = same = 0
for p in sorted(glob.glob("분석/*.csv")):
    a, b = rd(p), rd("검증/재현/분석_재현전/" + os.path.basename(p))
    n = sum(len(r) for r in b)
    s = sum(x == y for ra, rb in zip(a, b) for x, y in zip(ra, rb)) if [len(r) for r in a] == [len(r) for r in b] else 0
    print(f"{os.path.basename(p)}: 행 {len(a)}/{len(b)}, 칸 일치 {s}/{n}")
    tot += n; same += s
print(f"CSV 전체 칸 일치 {same}/{tot}")
A = {r[0]: r[2] for r in rd("분석/핵심수치.csv")[1:]}
V = {r[0]: r[2] for r in rd("검증/검증값.csv")[1:]}
d = [k for k in V if A.get(k) != V[k]]
print(f"핵심수치.csv(재현) vs 검증값.csv: 일치 {len(V)-len(d)}/{len(V)}, 불일치 {d}")

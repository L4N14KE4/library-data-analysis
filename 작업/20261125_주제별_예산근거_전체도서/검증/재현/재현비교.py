# 8.5단계 재현 비교. 프로젝트 폴더에서: .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/검증/재현/재현비교.py
import csv, glob, os, sys, importlib.metadata as m
W = "작업/20261125_주제별_예산근거_전체도서/"
tot = same = 0
for f in sorted(glob.glob(W + "분석/*.csv")):
    n = os.path.basename(f)
    old = W + "검증/재현/분석_재현전/" + n
    A = list(csv.reader(open(f, encoding="utf-8-sig")))
    B = list(csv.reader(open(old, encoding="utf-8-sig")))
    assert len(A) == len(B) and A[0] == B[0], n
    if n == "핵심수치.csv":  # 번호·값으로 비교
        c, s = len(A) - 1, sum(a[0] == b[0] and a[2] == b[2] for a, b in zip(A[1:], B[1:]))
    else:
        c = sum(len(r) - 1 for r in A[1:])
        s = sum(x == y for a, b in zip(A[1:], B[1:]) for x, y in zip(a[1:], b[1:]))
    print(n, len(A) - 1, c, s, open(f, "rb").read() == open(old, "rb").read())
    tot += c; same += s
print("재현 일치", same, "/", tot)
a = {r["번호"]: r["값"] for r in csv.DictReader(open(W + "분석/핵심수치.csv", encoding="utf-8-sig"))}
b = {r["번호"]: r["값"] for r in csv.DictReader(open(W + "검증/검증값.csv", encoding="utf-8"))}
print("핵심수치 vs 검증값", sum(a.get(k) == v for k, v in b.items()), "/", len(b))
print("입력 행 수", sum(1 for _ in csv.DictReader(open("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig"))))
print("Python", sys.version)
for p in ["pandas", "numpy", "scipy", "matplotlib"]:
    print(p, m.version(p))

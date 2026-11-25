# 8.5단계 재현 비교. 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_무대출_주제분포/검증/재현/비교.py
import csv, sys, filecmp
W = "작업/20261125_무대출_주제분포/"
def rows(p):
    with open(p, encoding="utf-8-sig", newline="") as f: return list(csv.reader(f))
def cells(p):
    return {(i, j): v for i, r in enumerate(rows(p)) for j, v in enumerate(r)}
for name in ["핵심수치.csv", "주제별_무대출표.csv"]:
    a, b = cells(W+"검증/재현/분석_재현전/"+name), cells(W+"분석/"+name)
    diff = [(k, a.get(k), b.get(k)) for k in a.keys() | b.keys() if a.get(k) != b.get(k)]
    print(name, "rows", len(rows(W+"분석/"+name)), "cells", len(a), "diff", len(diff), diff[:5], "bytes_identical", filecmp.cmp(W+"검증/재현/분석_재현전/"+name, W+"분석/"+name, shallow=False))
print("보조값.txt bytes_identical", filecmp.cmp(W+"검증/재현/분석_재현전/보조값.txt", W+"분석/보조값.txt", shallow=False))
k = {r[0]: r for r in rows(W+"분석/핵심수치.csv")[1:]}
v = {r[0]: r for r in rows(W+"검증/검증값.csv")[1:]}
print("header k", rows(W+"분석/핵심수치.csv")[0], "header v", rows(W+"검증/검증값.csv")[0])
bad = [(n, k.get(n), v.get(n)) for n in sorted(k.keys() | v.keys(), key=lambda x: int(x[1:])) if (k.get(n) or [0,0,None])[2] != (v.get(n) or [0,0,None])[2]]
print("verify n", len(k), len(v), "mismatch", bad)

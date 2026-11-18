# 8.5단계 재현 비교 — 프로젝트 폴더에서 .venv/bin/python 작업/20261117_무대출_주제분포/검증/재현/비교.py
# 값은 이미 보고 자릿수 문자열로 저장돼 있으므로 칸 단위 문자열로 비교한다.
import csv
W = "작업/20261117_무대출_주제분포/"
def rd(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))
def cmp(a, b, label):
    A, B = rd(a), rd(b)
    n = m = 0
    bad = []
    if len(A) != len(B):
        bad.append(f"행 수 다름 {len(A)} vs {len(B)}")
    for i, (ra, rb) in enumerate(zip(A, B)):
        if len(ra) != len(rb):
            bad.append(f"{i+1}행 열 수 다름")
        for j, (x, y) in enumerate(zip(ra, rb)):
            m += 1
            if x == y: n += 1
            else: bad.append(f"{i+1}행 {j+1}열: {x!r} vs {y!r}")
    print(f"{label}: 칸 일치 {n}/{m}, 행 {len(A)}/{len(B)}", "불일치:" if bad else "불일치 없음", *bad)
for f in ["핵심수치.csv", "주제별_무대출표.csv"]:
    cmp(W + "검증/재현/분석_재현전/" + f, W + "분석/" + f, f"{f} 재실행 vs 재현 전 사본")
# 핵심수치 vs 검증값: 번호별 값 비교
K = {r[0]: r[2] for r in rd(W + "분석/핵심수치.csv")[1:]}
V = {r[0]: r[2] for r in rd(W + "검증/검증값.csv")[1:]}
same = [k for k in K if V.get(k) == K[k]]
print(f"핵심수치(재실행) vs 검증값: 번호 일치 {len(same)}/{len(set(K) | set(V))}",
      "다름:", [(k, K.get(k), V.get(k)) for k in sorted(set(K) | set(V)) if K.get(k) != V.get(k)])
with open("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", newline="") as f:
    r = list(csv.reader(f))
print("입력 파일 데이터 행 수(머리글 제외):", len(r) - 1, "열 수:", len(r[0]))

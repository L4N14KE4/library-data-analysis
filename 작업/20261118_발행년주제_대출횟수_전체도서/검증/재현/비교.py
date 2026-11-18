# 재현 비교: 다시 만들어진 분석/*.csv 를 검증/재현/분석_재현전/ 사본과 칸 단위로 비교하고,
# 핵심수치.csv 를 검증/검증값.csv 와 번호별로 다시 대조한다. 프로젝트 폴더에서 실행한다.
# 판정: 문자열이 같으면 일치. 다르면 두 값을 숫자로 읽어, 기준 쪽(사본·검증값) 문자열의 소수 자릿수로 반올림해 같으면 일치.
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import csv

W = Path("작업/20261118_발행년주제_대출횟수_전체도서")
NEW, OLD, VER = W / "분석", W / "검증/재현/분석_재현전", W / "검증/검증값.csv"


def read(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.reader(f))


def same(ref, new):
    if ref == new:
        return True
    try:
        a, b = Decimal(ref.replace(",", "")), Decimal(new.replace(",", ""))
    except InvalidOperation:
        return False
    q = Decimal(1).scaleb(a.as_tuple().exponent)
    return a == b.quantize(q, ROUND_HALF_UP)


print("== 분석 재실행 vs 재현전 사본 (CSV) ==")
tot_ok = tot = 0
for po in sorted(OLD.glob("*.csv")):
    pn = NEW / po.name
    if not pn.exists():
        print(f"{po.name}: 다시 만들어지지 않음")
        continue
    o, n = read(po), read(pn)
    if len(o) != len(n) or any(len(a) != len(b) for a, b in zip(o, n)):
        print(f"{po.name}: 모양 다름 {len(o)}행 vs {len(n)}행")
    cells = ok = 0
    for i, (ro, rn) in enumerate(zip(o, n)):
        for j, (a, b) in enumerate(zip(ro, rn)):
            cells += 1
            if same(a, b):
                ok += 1
            else:
                print(f"  불일치 {po.name} 행{i} 열{j} ({o[0][j]}): 사본={a!r} 재실행={b!r}")
    print(f"{po.name}: {ok}/{cells} 칸 일치, 행 {len(o)}")
    tot_ok += ok; tot += cells
print(f"CSV 합계: {tot_ok}/{tot} 칸 일치")

print("== 재실행 핵심수치.csv vs 검증값.csv ==")
k = {r[0]: r[2] for r in read(NEW / "핵심수치.csv")[1:]}
v = {r[0]: r[2] for r in read(VER)[1:]}
keys = sorted(set(k) | set(v), key=lambda s: int(s[1:]))
ok = 0
for key in keys:
    if key in k and key in v and same(v[key], k[key]):
        ok += 1
    else:
        print(f"  불일치 {key}: 분석={k.get(key)!r} 검증={v.get(key)!r}")
print(f"번호 {ok}/{len(keys)} 일치 (분석 {len(k)}개, 검증 {len(v)}개)")

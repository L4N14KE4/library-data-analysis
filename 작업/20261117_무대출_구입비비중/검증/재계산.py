# 독립 재계산 — 무대출 장서의 구입가격 비중 (N1~N9)
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261117_무대출_구입비비중/검증/재계산.py
# 읽는 것: 원자료 CSV (표준 라이브러리 csv). pandas 안 씀. 난수 없음.
import csv
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261117_무대출_구입비비중/검증/검증값.csv"
CUT = date(2022, 12, 31)


def stop(msg):
    sys.exit(f"[멈춤] {msg}")


def to_date(s, col, rid):
    try:
        return date.fromisoformat(s) if len(s) == 10 and s[4] == "-" and s[7] == "-" else stop(f"{col} 날짜 아님: {rid} {s!r}")
    except ValueError:
        stop(f"{col} 날짜 아님: {rid} {s!r}")


def to_int(s, col, rid):
    if not s.lstrip("-").isdigit():
        stop(f"{col} 정수 아님: {rid} {s!r}")
    return int(s)


def pct(a, b):
    # 정확한 분수 → 소수 셋째 자리에서 사사오입
    q = Fraction(a * 100, b)
    return (Decimal(q.numerator) / Decimal(q.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


n1 = n2 = n3 = n4 = n5 = n6 = n9 = 0
with open(SRC, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f):
        rid = r["자료ID"]
        buy = to_date(r["구입일"].strip(), "구입일", rid)
        loans = to_int(r["대출횟수"].strip(), "대출횟수", rid)
        price = to_int(r["구입가격"].strip(), "구입가격", rid)
        last = r["최근대출일"].strip()
        blank = last == ""
        if not blank:
            to_date(last, "최근대출일", rid)

        target = buy <= CUT
        noloan = target and loans == 0
        n1 += 1
        n6 += price
        if noloan:
            n2 += 1
            n4 += price
        else:
            n3 += 1
            n5 += price
        if target and (blank != (loans == 0)):
            n9 += 1

# 합 확인 (어긋나면 멈춤)
if n2 + n3 != n1:
    stop(f"N2+N3={n2 + n3} != N1={n1}")
if n4 + n5 != n6:
    stop(f"N4+N5={n4 + n5} != N6={n6}")
if n9 != 0:
    stop(f"N9={n9} (무대출 정의 어긋남)")

rows = [
    ("N1", "전체 권수", n1),
    ("N2", "무대출 권수", n2),
    ("N3", "나머지 권수", n3),
    ("N4", "무대출 구입가격 합계", n4),
    ("N5", "나머지 구입가격 합계", n5),
    ("N6", "구입가격 합계(현재 목록 28,000권)", n6),
    ("N7", "무대출 비중", pct(n4, n6)),
    ("N8", "나머지 비중", pct(n5, n6)),
    ("N9", "무대출 정의 어긋남 수", n9),
]
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)
for r in rows:
    print(*r, sep=",")

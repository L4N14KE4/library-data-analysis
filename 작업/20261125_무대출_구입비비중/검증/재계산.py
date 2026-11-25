# 질문 5 독립 재계산 (검증 담당, 6단계). 프로젝트 폴더에서 실행:
#   .venv/bin/python 작업/20261125_무대출_구입비비중/검증/재계산.py
# 근거: 이 폴더 계산명세.md 2절·6절. 난수 없음, 시드 없음.
import csv
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_무대출_구입비비중/검증/검증값.csv"
CUT = date(2022, 12, 31)

# ponytail: pandas 대신 csv 모듈 — 모든 칸이 문자열로 들어와 dtype=str, keep_default_na=False와 같다
with open(SRC, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))


def to_date(s):
    return datetime.strptime(s.strip(), "%Y-%m-%d").date()  # 실패하면 예외로 멈춘다


def to_int(s):
    s = s.strip()
    if not s.lstrip("-").isdigit():
        raise SystemExit(f"정수로 바뀌지 않는 값: {s!r} — 멈추고 진행 담당에게 보고")
    return int(s)


recs = []
for r in rows:
    last = r["최근대출일"].strip()
    if last:
        to_date(last)  # 날짜도 빈칸도 아니면 예외로 멈춘다
    recs.append((to_date(r["구입일"]), to_int(r["대출횟수"]), to_int(r["구입가격"]), last == ""))

target = [x for x in recs if x[0] <= CUT]
nolend = [x for x in recs if x[0] <= CUT and x[1] == 0]
rest = [x for x in recs if not (x[0] <= CUT and x[1] == 0)]

N1 = len(recs)
N2 = len(nolend)
N3 = len(rest)
N4 = sum(x[2] for x in nolend)
N5 = sum(x[2] for x in rest)
N6 = sum(x[2] for x in recs)
N9 = sum(1 for x in target if x[3] != (x[1] == 0))


def pct(a, b):
    v = Fraction(a, b) * 100
    return (Decimal(v.numerator) / Decimal(v.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


N7 = pct(N4, N6)
N8 = pct(N5, N6)

# 합 확인 (계산명세 6절): 어긋나면 멈춘다
assert N1 == 28000, N1
assert N2 + N3 == N1
assert N4 + N5 == N6
assert N9 == 0, N9
assert pct(12345, 100000) == Decimal("12.35")  # 사사오입 자체 확인 (12.345 -> 12.35)

vals = [
    ("N1", "전체 권수", N1),
    ("N2", "무대출 권수", N2),
    ("N3", "나머지 권수", N3),
    ("N4", "무대출 구입가격 합계", N4),
    ("N5", "나머지 구입가격 합계", N5),
    ("N6", "구입가격 합계(현재 목록 28,000권)", N6),
    ("N7", "무대출 비중", f"{N7:.2f}"),
    ("N8", "나머지 비중", f"{N8:.2f}"),
    ("N9", "무대출 정의 어긋남 수", N9),
]
with open(OUT, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(vals)
for v in vals:
    print(*v, sep=",")

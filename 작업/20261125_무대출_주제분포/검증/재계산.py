# 질문 1 독립 재계산 (검증 담당, 6단계). 분석/ 코드를 보지 않고 계산명세.md만 따라 새로 썼다.
# 실행: 프로젝트 폴더에서 .venv/bin/python "작업/20261125_무대출_주제분포/검증/재계산.py"
# 난수 없음, 시드 없음. pandas 대신 표준 라이브러리 csv로 읽는다 (분석 담당과 읽는 경로를 다르게 해 독립성을 높임).
import csv
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction
from pathlib import Path

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261125_무대출_주제분포/검증")
CUT = date(2022, 12, 31)
TOPICS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
USE = ["자료ID", "구입일", "대출횟수", "최근대출일", "주제분류명"]  # 삭제 7열·나머지 열은 읽지 않는다


def pct(num, den):
    """정확한 분수로 계산 후 소수 둘째 자리 사사오입 (계산명세 6절)."""
    f = Fraction(num, den) * 100
    return (Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


assert str(pct(40575, 100000)) == "40.58"  # 계산명세 예시: 40.575 -> 40.58 (사사오입)
assert str(pct(1, 8)) == "12.50"            # 12.5 -> 끝자리 0 유지

with open(SRC, encoding="utf-8-sig", newline="") as fh:
    rows = [{k: r[k] for k in USE} for r in csv.DictReader(fh)]

N1 = len(rows)
tgt = []
for r in rows:
    d = datetime.strptime(r["구입일"].strip(), "%Y-%m-%d").date()  # 형식이 어긋나면 여기서 멈춘다
    if d <= CUT:
        tgt.append(r)
loan0 = [int(r["대출횟수"]) == 0 for r in tgt]  # 정수로 읽는다; 정수 아니면 멈춘다
blank = [(r["최근대출일"] or "").strip() == "" for r in tgt]

N2 = len(tgt)
N3 = sum(loan0)
N5 = sum(a != b for a, b in zip(loan0, blank))

ga = {k: 0 for k in TOPICS}
na = {k: 0 for k in TOPICS}
for r, z in zip(tgt, loan0):
    k = r["주제분류명"]
    assert k in ga, f"코드북 밖 주제값: {k!r}"
    ga[k] += 1
    na[k] += z
assert sum(ga.values()) == N2 and sum(na.values()) == N3, "합 확인 실패"
assert sum(Fraction(na[k], N3) for k in TOPICS) == 1

counts = sorted(na.values())
tie = len(set(counts)) != len(counts)
rank = {k: 1 + sum(na[j] < na[k] for j in TOPICS) for k in TOPICS}  # 오름차순, 동률이면 같은 순위(아래에서 표시)

vals = [
    ("N1", "전체 권수", N1),
    ("N2", "대상 권수", N2),
    ("N3", "무대출 권수", N3),
    ("N4", "무대출 전체 대비 비율", pct(N3, N1)),
    ("N5", "무대출 정의 어긋남 수", N5),
]
n = 6
for k in TOPICS:
    vals += [
        (f"N{n}", f"{k} 대상 권수", ga[k]),
        (f"N{n+1}", f"{k} 무대출 권수", na[k]),
        (f"N{n+2}", f"{k} 주제 안 무대출 비율", pct(na[k], ga[k])),
        (f"N{n+3}", f"{k} 무대출 전체 중 비중", pct(na[k], N3)),
        (f"N{n+4}", f"{k} 순위", rank[k]),
    ]
    n += 5
vals.append(("N56", "대상 대비 무대출 비율", pct(N3, N2)))
assert len(vals) == 56

with open(OUT / "검증값.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    w.writerows((a, b, str(c)) for a, b, c in vals)

# 보조 값 S: 반올림한 N9…N54 문자열을 Decimal로 바로 더함
S = sum(Decimal(str(v)) for no, _, v in vals if no in {f"N{9 + 5 * i}" for i in range(10)})
note = [
    f"S = {S}",
    "정의: N9, N14, N19, N24, N29, N34, N39, N44, N49, N54 (반올림한 소수 둘째 자리 값)을 Decimal로 더한 값 (계산명세 6절).",
    f"합 확인: 주제 (가) 합 = {sum(ga.values())} (N2 = {N2}), (나) 합 = {sum(na.values())} (N3 = {N3}), (라) 반올림 전 합 = 1 (정확한 분수)",
    f"N5 (무대출 정의 어긋남) = {N5}",
    f"순위 동률: {'있음 - 멈추고 보고' if tie else '없음'}",
    f"입력 행 수 = {N1}, 시드 없음",
    "산출 코드: 작업/20261125_무대출_주제분포/검증/재계산.py",
]
(OUT / "보조값.txt").write_text("\n".join(note) + "\n", encoding="utf-8")
print("\n".join(note))
for v in vals:
    print(*v, sep=",")

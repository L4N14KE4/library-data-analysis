# 검증 담당 독립 재계산 — 3년 무대출 장서의 주제별 분포 (N1~N56)
# 실행: 프로젝트 폴더에서 `.venv/bin/python 작업/20261117_무대출_주제분포/검증/재계산.py`
# 읽는 것: 원자료 CSV만. 난수 없음, 시드 없음.
import csv
import sys
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from fractions import Fraction

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261117_무대출_주제분포/검증/검증값.csv"
TOPICS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
CUTOFF = date(2022, 12, 31)
# 코드북 1-1절 삭제 7열(서명·저자·출판사·자료구분·소장관·이용상태·장서연령)과 이 질문에 안 쓰는 열은 읽지 않는다.
USE = ["자료ID", "구입일", "대출횟수", "최근대출일", "주제분류명"]

stops = []


def pct(num, den):
    # 정확한 분수 → 소수 셋째 자리에서 사사오입 → 소수 둘째 자리 문자열
    f = Fraction(num * 100, den)
    return str((Decimal(f.numerator) / Decimal(f.denominator)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


with open(SRC, encoding="utf-8-sig", newline="") as fh:
    rows = [{k: r[k] for k in USE} for r in csv.DictReader(fh)]

N1 = len(rows)
target = [r for r in rows if datetime.strptime(r["구입일"], "%Y-%m-%d").date() <= CUTOFF]
for r in target:
    r["n"] = int(r["대출횟수"])  # 정수가 아니면 여기서 오류로 멈춘다
    r["blank"] = (r["최근대출일"] or "").strip() == ""
noloan = [r for r in target if r["n"] == 0]

N2, N3 = len(target), len(noloan)
N5 = sum(r["blank"] != (r["n"] == 0) for r in target)
if N5:
    stops.append(f"무대출 정의 어긋남 {N5}행 (N5 != 0)")

topic_vals = set(r["주제분류명"] for r in rows)
if topic_vals != set(TOPICS):
    stops.append(f"주제분류명 값이 코드북 10개와 다름: {sorted(topic_vals)}")

tgt_k = {k: sum(r["주제분류명"] == k for r in target) for k in TOPICS}
nol_k = {k: sum(r["주제분류명"] == k for r in noloan) for k in TOPICS}
if sum(tgt_k.values()) != N2 or sum(nol_k.values()) != N3:
    stops.append("주제별 합이 N2 또는 N3와 다름")
if len(set(nol_k.values())) != len(TOPICS):
    stops.append(f"무대출 권수 동률 있음: {nol_k}")
order = sorted(TOPICS, key=lambda k: nol_k[k])
rank = {k: i + 1 for i, k in enumerate(order)}

out = [
    ("N1", "전체 권수", N1),
    ("N2", "대상 권수", N2),
    ("N3", "무대출 권수", N3),
    ("N4", "무대출 전체 대비 비율", pct(N3, N1)),
    ("N5", "무대출 정의 어긋남 수", N5),
]
for i, k in enumerate(TOPICS):
    b = 6 + 5 * i
    out += [
        (f"N{b}", f"{k} 대상 권수", tgt_k[k]),
        (f"N{b+1}", f"{k} 무대출 권수", nol_k[k]),
        (f"N{b+2}", f"{k} 주제 안 무대출 비율", pct(nol_k[k], tgt_k[k])),
        (f"N{b+3}", f"{k} 무대출 전체 중 비중", pct(nol_k[k], N3)),
        (f"N{b+4}", f"{k} 순위", rank[k]),
    ]
out.append(("N56", "대상 대비 무대출 비율", pct(N3, N2)))

# 합 확인 (핵심 수치 아님): 비중 반올림 전 합 = 100
assert sum(Fraction(nol_k[k] * 100, N3) for k in TOPICS) == 100

with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["번호", "항목", "값"])
    w.writerows(out)

print("반올림한 비중 합:", sum(Decimal(pct(nol_k[k], N3)) for k in TOPICS))
print("멈춤 조건:", stops or "없음")
if stops:
    sys.exit(1)

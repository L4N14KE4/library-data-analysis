# 5단계 분석 — 3년 무대출 장서의 주제별 분포 (계산명세.md, 승인기록 10번)
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261117_무대출_주제분포/분석/분석.py
# 난수 없음. 원자료는 읽기만 한다.
import csv
import sys
from decimal import Decimal
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261117_무대출_주제분포/분석/"
COLS = ["자료ID", "구입일", "대출횟수", "최근대출일", "주제분류명"]  # 계산명세 3절 (삭제 7열 등은 읽지 않음)
SUBJECTS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절 순서


def pct(num, den):
    """num/den*100 을 정확한 정수 연산으로 소수 셋째 자리에서 사사오입(ROUND_HALF_UP), 소수 둘째 자리 문자열."""
    q = (2 * num * 10000 + den) // (2 * den)  # num, den >= 0
    return f"{q // 100}.{q % 100:02d}"


def stop(msg):
    print("멈춤:", msg)
    sys.exit(1)


assert pct(40575, 100000) == "40.58" and pct(1, 3) == "33.33" and pct(2, 3) == "66.67" and pct(1, 1) == "100.00"

# 읽기
df = pd.read_csv(SRC, encoding="utf-8-sig", usecols=COLS, dtype=str)
df["최근대출일"] = df["최근대출일"].fillna("").str.strip()
df["대출횟수"] = df["대출횟수"].astype(int)
df["구입일"] = pd.to_datetime(df["구입일"], format="%Y-%m-%d")

# 전체 수치
대상 = df["구입일"] <= pd.Timestamp("2022-12-31")
영 = df["대출횟수"] == 0
빈칸 = df["최근대출일"] == ""
무대출 = 대상 & 영

N1 = len(df)
N2 = int(대상.sum())
N3 = int(무대출.sum())
N4 = pct(N3, N1)
N5 = int((대상 & (빈칸 ^ 영)).sum())
if N5 != 0:
    stop(f"무대출 정의 어긋남 N5 = {N5}")

# 주제별 수치
if set(df["주제분류명"]) != set(SUBJECTS):
    stop(f"주제분류명 값이 코드북 10개와 다름: {sorted(set(df['주제분류명']))}")
가 = {k: int((대상 & (df["주제분류명"] == k)).sum()) for k in SUBJECTS}
나 = {k: int((무대출 & (df["주제분류명"] == k)).sum()) for k in SUBJECTS}
if sum(가.values()) != N2 or sum(나.values()) != N3:
    stop("주제별 합이 N2 또는 N3와 다름")
if len(set(나.values())) != len(SUBJECTS):
    stop(f"무대출 권수 동률: {나}")
순서 = sorted(SUBJECTS, key=lambda k: 나[k])
순위 = {k: i + 1 for i, k in enumerate(순서)}
N56 = pct(N3, N2)

# 핵심수치.csv
rows = [
    ("N1", "전체 권수", N1),
    ("N2", "대상 권수", N2),
    ("N3", "무대출 권수", N3),
    ("N4", "무대출 전체 대비 비율", N4),
    ("N5", "무대출 정의 어긋남 수", N5),
]
for i, k in enumerate(SUBJECTS):
    b = 6 + 5 * i
    rows += [
        (f"N{b}", f"{k} 대상 권수", 가[k]),
        (f"N{b + 1}", f"{k} 무대출 권수", 나[k]),
        (f"N{b + 2}", f"{k} 주제 안 무대출 비율", pct(나[k], 가[k])),
        (f"N{b + 3}", f"{k} 무대출 전체 중 비중", pct(나[k], N3)),
        (f"N{b + 4}", f"{k} 순위", 순위[k]),
    ]
rows.append(("N56", "대상 대비 무대출 비율", N56))
with open(OUT + "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)

# 주제별_무대출표.csv (표 1, 승인기록 9번: 대상 권수 열 + 합계 행)
with open(OUT + "주제별_무대출표.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["순위", "주제분류명", "대상 권수", "무대출 권수", "주제 안 무대출 비율(%)", "무대출 전체 중 비중(%)"])
    for k in 순서:
        w.writerow([순위[k], k, 가[k], 나[k], pct(나[k], 가[k]), pct(나[k], N3)])
    w.writerow(["", "합계", N2, N3, N56, pct(N3, N3)])
    # 표 아래 '주' 행 (승인기록 11·12번). 값 열은 건드리지 않는다
    비중합 = sum(Decimal(pct(나[k], N3)) for k in SUBJECTS)
    w.writerow(["주", f"무대출 전체 중 비중 열을 반올림한 값으로 더하면 {비중합}이며, 반올림 때문이다 (반올림 전 합은 100)", "", "", "", ""])
    w.writerow(["주", f"합계 행의 주제 안 무대출 비율 {N56}는 무대출 {N3:,} ÷ 대상 {N2:,}이며, 10개 주제 비율의 평균이 아니다", "", "", "", ""])

# 확인용 출력 (핵심 수치 아님)
print(f"N1={N1} N2={N2} N3={N3} N4={N4} N5={N5} N56={N56}")
print("비중(라) 반올림 값 합:", sum(float(pct(나[k], N3)) for k in SUBJECTS))
for k in 순서:
    print(순위[k], k, 가[k], 나[k], pct(나[k], 가[k]), pct(나[k], N3))

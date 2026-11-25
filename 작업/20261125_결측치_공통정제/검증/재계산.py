# 독립 재계산 — 결측치 공통 정제 (6단계, 검증 담당)
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_결측치_공통정제/검증/재계산.py
# 읽는 것: 원자료 CSV만 (코드북 삭제 7열은 코드에서 뺌). 난수 없음 -> 시드 없음.
import csv
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_결측치_공통정제/검증/검증값.csv"
DROP = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 '삭제'
SPECIAL = {"9999", "-", "N/A", "NA", "모름"}

# 모든 값을 글자 그대로 읽는다 (빈칸을 NaN으로 바꾸지 않음)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
df = raw.drop(columns=DROP)
USE = list(df.columns)
assert len(USE) == 8

blank = df["최근대출일"] == ""
loans = df["대출횟수"].astype(int)
has = df[~blank]
buy = pd.to_datetime(df["구입일"], format="%Y-%m-%d")
last = pd.to_datetime(has["최근대출일"], format="%Y-%m-%d")

others = [c for c in USE if c != "최근대출일"]
n8 = int(sum((df[c] == "").sum() for c in others))
n9 = int(sum(df[c].map(lambda v: (v != "" and v.strip() == "") or v in SPECIAL).sum() for c in USE))

n18 = len(df)  # 승인된 처리: 모든 문제 '유지' (승인기록 4~9번), 제거 행 없음
n19 = len(raw) - n18

vals = [
    ("N1", "원본 행 수", len(raw)),
    ("N2", "원본 열 수", raw.shape[1]),
    ("N3", "사용 열 수", len(USE)),
    ("N4", "최근대출일 빈칸 행 수", int(blank.sum())),
    ("N5", "최근대출일 빈칸 & 대출횟수=0", int((blank & (loans == 0)).sum())),
    ("N6", "최근대출일 빈칸 & 대출횟수>=1", int((blank & (loans >= 1)).sum())),
    ("N7", "최근대출일 있음 & 대출횟수=0", int((~blank & (loans == 0)).sum())),
    ("N8", "최근대출일 외 7개 변수 빈칸 수 합계", n8),
    ("N9", "8개 변수 공백·특수값 칸 수 합계", n9),
    ("N10", "최근대출일<구입일 행 수", int((last < buy[~blank]).sum())),
    ("N11", "구입일 연도<발행년 행 수", int((buy.dt.year < df["발행년"].astype(int)).sum())),
    ("N12", "최근대출일 2023-01-01~2025-12-30 밖 행 수",
     int(((last < "2023-01-01") | (last > "2025-12-30")).sum())),
    ("N13", "자료ID 중복 행 수(두 번째 이후)", int(df["자료ID"].duplicated().sum())),
    ("N14", "자료ID 외 7열이 같은 다른 행이 있는 행 수", int(df.duplicated(subset=[c for c in USE if c != "자료ID"], keep=False).sum())),
    ("N15", "최근대출일=구입일 행 수", int((has["최근대출일"] == has["구입일"]).sum())),
    ("N16", "KDC='000' 행 수", int((df["KDC"] == "000").sum())),
    ("N17", "최근대출일 최솟값", last.min().strftime("%Y-%m-%d")),
    ("N18", "처리 후 행 수", n18),
    ("N19", "제거한 행 수", n19),
    ("N20", "제거 비율(%)", f"{n19 / len(raw) * 100:.2f}"),
]

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(vals)
for v in vals:
    print(*v, sep=",")

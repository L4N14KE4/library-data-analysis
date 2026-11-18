# 독립 재계산 — 결측치 공통 정제 N1~N20
# 실행: 프로젝트 폴더에서  .venv/bin/python "작업/20261116_결측치_공통정제/검증/재계산.py"
# 입력: 원자료 CSV, 코드북(1-1절 삭제 7열), 승인기록 4~9번(모두 '유지')
# 난수 사용 없음 (시드 해당 없음)
import csv
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261116_결측치_공통정제/검증/검증값.csv"
DROP = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 '삭제'

raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw.drop(columns=DROP)
assert list(d.columns) == ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]

rows = []
def put(no, item, val):
    rows.append((no, item, val))

blank = d["최근대출일"] == ""                     # 정확히 빈 문자열
blank_ws = d["최근대출일"].str.strip() == ""       # 공백만 있는 칸까지 빈칸으로 볼 때
loans = pd.to_numeric(d["대출횟수"], errors="raise")
last = pd.to_datetime(d["최근대출일"].where(~blank_ws), format="%Y-%m-%d")
buy = pd.to_datetime(d["구입일"], format="%Y-%m-%d")
pubyear = pd.to_numeric(d["발행년"], errors="raise")

put("N1", "원본 행 수", len(raw))
put("N2", "원본 열 수", raw.shape[1])
put("N3", "사용 열 수", d.shape[1])
put("N4", "최근대출일 빈칸 행 수", int(blank.sum()))
put("N4(공백포함)", "최근대출일 빈칸 행 수 — 공백만 있는 칸도 빈칸으로 볼 때 (점검용)", int(blank_ws.sum()))
put("N5", "최근대출일 빈칸 & 대출횟수=0 행 수", int((blank & (loans == 0)).sum()))
put("N6", "최근대출일 빈칸 & 대출횟수>=1 행 수", int((blank & (loans >= 1)).sum()))
put("N7", "최근대출일 있음 & 대출횟수=0 행 수", int((~blank & (loans == 0)).sum()))

seven = [c for c in d.columns if c != "최근대출일"]
put("N8", "최근대출일 제외 7개 변수 빈칸 수 합계", int((d[seven] == "").sum().sum()))
put("N8(공백포함)", "N8 — 공백만 있는 칸도 빈칸으로 볼 때 (점검용)", int((d[seven].apply(lambda s: s.str.strip()) == "").sum().sum()))

TOKENS = {"9999", "-", "N/A", "NA", "모름"}
ws_only = d.apply(lambda s: (s != "") & (s.str.strip() == ""))   # 공백 문자 1개 이상, 다른 글자 없음
tok = d.isin(TOKENS)
empty = d == ""
# 계산명세 모호: '공백만 있는' 칸에 빈 문자열("")이 들어가는지 두 가지로 읽힘
put("N9a", "[계산명세 모호] 특수값 칸 수 — 빈 문자열 제외(공백 문자만 있는 칸 + 5개 표기)", int((ws_only | tok).sum().sum()))
put("N9b", "[계산명세 모호] 특수값 칸 수 — 빈 문자열 포함(빈칸·공백 문자만 있는 칸 + 5개 표기)", int((empty | ws_only | tok).sum().sum()))

put("N10", "최근대출일 < 구입일 행 수(빈칸 제외)", int((last.notna() & (last < buy)).sum()))
put("N11", "구입일 연도 < 발행년 행 수", int((buy.dt.year < pubyear).sum()))
lo, hi = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-30")
put("N12", "최근대출일 2023-01-01~2025-12-30 밖 행 수(빈칸 제외, 양 끝 포함 구간)", int((last.notna() & ((last < lo) | (last > hi))).sum()))
put("N13", "자료ID 중복 행 수(두 번째 이후)", int(d["자료ID"].duplicated(keep="first").sum()))
# 계산명세 모호: 최근대출일 빈칸끼리를 '같은 값'으로 볼지 두 가지로 읽힘
no_id = [c for c in d.columns if c != "자료ID"]  # 자료ID를 뺀 7개 사용 열
dup7 = d.duplicated(subset=no_id, keep=False)
put("N14a", "[계산명세 모호] 자료ID 제외 7개 열이 모두 같은 다른 행이 있는 행 수(묶음 전체) — 최근대출일 빈칸끼리 같다고 봄", int(dup7.sum()))
put("N14b", "[계산명세 모호] N14 — 최근대출일 빈칸끼리는 같다고 보지 않음(빈칸은 값이 아님)", int((dup7 & ~blank).sum()))
put("N15", "최근대출일 = 구입일 행 수", int((last.notna() & (last == buy)).sum()))
put("N16", "KDC = '000' 행 수", int((d["KDC"] == "000").sum()))
put("N17", "최근대출일 최솟값(빈칸 제외)", last.min().strftime("%Y-%m-%d"))

clean = d  # 승인기록 4~9번: 모든 문제 '유지' -> 행 변경 없음
put("N18", "승인된 처리 적용 후 행 수", len(clean))
put("N19", "제거한 행 수", len(raw) - len(clean))
put("N20", "제거 비율(%)", f"{(len(raw) - len(clean)) / len(raw) * 100:.2f}")

with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(rows)
for r in rows:
    print(*r, sep=" | ")

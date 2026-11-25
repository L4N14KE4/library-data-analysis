# 질문 1 (다시 하기) — 3년 무대출 장서의 주제별 분포. 계산명세.md 그대로.
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_무대출_주제분포/분석/분석.py
import csv
from decimal import Decimal
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_무대출_주제분포/분석/"
USE = ["자료ID", "구입일", "대출횟수", "최근대출일", "주제분류명"]  # 계산명세 3절 (삭제 7열 등 나머지는 읽지 않음)
SUBJECTS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절 순서


def pct(num, den):
    """num/den*100 을 정확한 정수 연산으로 소수 셋째 자리 사사오입(ROUND_HALF_UP), 소수 둘째 자리 문자열."""
    h = (num * 10000 * 2 + den) // (2 * den)  # 백분율의 1/100 단위, 음수 없음
    return f"{h // 100}.{h % 100:02d}"


df = pd.read_csv(SRC, encoding="utf-8-sig", usecols=USE, dtype=str, keep_default_na=False)
assert df["대출횟수"].str.fullmatch(r"\d+").all(), "대출횟수에 정수 아닌 값"
df["대출횟수"] = df["대출횟수"].astype(int)
df["구입일"] = pd.to_datetime(df["구입일"], format="%Y-%m-%d")
blank = df["최근대출일"].fillna("").str.strip() == ""
assert set(df["주제분류명"]) == set(SUBJECTS), "주제분류명 값이 코드북 10개와 다름"

target = df["구입일"] <= pd.Timestamp("2022-12-31")
zero = df["대출횟수"] == 0
noloan = target & zero

N1 = len(df)
N2 = int(target.sum())
N3 = int(noloan.sum())
N5 = int((target & (blank ^ zero)).sum())
if N5 != 0:
    raise SystemExit(f"무대출 정의 어긋남 {N5}행 — 멈추고 진행 담당에게 보고")

rows = []  # (주제, 대상, 무대출)
for s in SUBJECTS:
    m = df["주제분류명"] == s
    rows.append((s, int((m & target).sum()), int((m & noloan).sum())))
assert sum(r[1] for r in rows) == N2 and sum(r[2] for r in rows) == N3, "주제 합이 전체와 다름"
counts = [r[2] for r in rows]
if len(set(counts)) != len(counts):
    raise SystemExit("무대출 권수 동률 — 순서를 정하지 않고 멈춤")
rank = {s: i + 1 for i, (s, _, _) in enumerate(sorted(rows, key=lambda r: r[2]))}

key = [("N1", "전체 권수", N1), ("N2", "대상 권수", N2), ("N3", "무대출 권수", N3),
       ("N4", "무대출 전체 대비 비율", pct(N3, N1)), ("N5", "무대출 정의 어긋남 수", N5)]
n = 6
for s, a, b in rows:
    for name, v in [("대상 권수", a), ("무대출 권수", b), ("주제 안 무대출 비율", pct(b, a)),
                    ("무대출 전체 중 비중", pct(b, N3)), ("순위", rank[s])]:
        key.append((f"N{n}", f"{s} {name}", v))
        n += 1
key.append(("N56", "대상 대비 무대출 비율", pct(N3, N2)))
assert n == 56 and len(key) == 56

with open(OUT + "핵심수치.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    w.writerows(key)

# 보조 값 S: 반올림한 비중 10개를 문자열에서 Decimal로 더함 (핵심 수치 아님)
S = sum(Decimal(pct(b, N3)) for _, _, b in rows)

# 표 1: 무대출 권수 오름차순 + 합계 행 + 각주 '주' 행 (계산명세 7절 각주 ①~④, 승인 10·11번 '표가 가는 곳마다')
NOTES = [
    f"① 무대출 전체 중 비중 열의 주제 10개 값을 더하면 {S}%로 100%와 다르다. 각 값을 소수 둘째 자리로 반올림했기 때문이다.",
    f"② 합계 행의 주제 안 무대출 비율 {pct(N3, N2)}%는 대상 {N2:,}권 기준 전체 비율이며, 주제 비율의 평균이 아니다.",
    f"③ 주제 안 무대출 비율 = 주제 무대출 권수 ÷ 그 주제의 구입일 2022-12-31 이하 권수. 무대출 전체 중 비중 = 주제 무대출 권수 ÷ 무대출 전체 {N3:,}권.",
    "④ 무대출 = 구입일 2022-12-31 이하이면서 2023-01-01~2025-12-30 대출횟수 0 (최근대출일 빈칸).",
]
with open(OUT + "주제별_무대출표.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["순위", "주제분류명", "대상 권수", "무대출 권수", "주제 안 무대출 비율(%)", "무대출 전체 중 비중(%)"])
    for s, a, b in sorted(rows, key=lambda r: r[2]):
        w.writerow([rank[s], s, a, b, pct(b, a), pct(b, N3)])
    w.writerow(["", "합계", N2, N3, pct(N3, N2), pct(N3, N3)])
    for t in NOTES:
        w.writerow(["주", t, "", "", "", ""])

with open(OUT + "보조값.txt", "w", encoding="utf-8") as f:
    f.write(f"S (N9+N14+N19+N24+N29+N34+N39+N44+N49+N54, 반올림 값의 Decimal 합) = {S}\n")

for r in key:
    print(*r)
print("S =", S)

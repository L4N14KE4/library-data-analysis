# 5단계 분석 — 질문 5: 무대출 장서의 구입가격 비중 (계산명세.md 그대로, 핵심 수치 N1~N9)
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_무대출_구입비비중/분석/분석.py
# 원자료는 읽기만 한다. 지우거나 바꾸는 행 없음 (승인 4·5번). 난수 없음, 시드 없음.
import csv
import sys
from datetime import date, datetime
from fractions import Fraction
from pathlib import Path

import pandas as pd
from matplotlib import font_manager, pyplot as plt

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261117_무대출_구입비비중/분석")
PNG = OUT / "무대출_구입비비중_원그래프.png"
CSV = OUT / "핵심수치.csv"
CUT = date(2022, 12, 31)  # 승인 1·6번: 구입일 2022-12-31 이하
COLS = ["자료ID", "구입일", "대출횟수", "최근대출일", "구입가격"]  # 계산명세 3절 (삭제 7열 등은 읽은 뒤 쓰지 않음)


def stop(msg):  # 계산명세의 '멈추고 보고' 조건
    sys.exit(f"[멈춤] {msg}")


def parse(col, fn, allow_blank=False):
    out = []
    for i, v in enumerate(raw[col].str.strip()):
        if allow_blank and v == "":
            out.append(None)
            continue
        try:
            out.append(fn(v))
        except ValueError:
            stop(f"{col} 변환 실패: {i + 2}번째 줄 값 {v!r}")
    return out


to_date = lambda v: datetime.strptime(v, "%Y-%m-%d").date()  # noqa: E731

# ---------------------------------------------------------------- 읽기 (계산명세 2절)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)[COLS]
buy = parse("구입일", to_date)
loans = parse("대출횟수", int)
price = parse("구입가격", int)  # 정수(원), 합계는 파이썬 정수 덧셈
last = parse("최근대출일", to_date, allow_blank=True)  # None = 빈칸

# ---------------------------------------------------------------- 분류
target = [b <= CUT for b in buy]
noloan = [t and n == 0 for t, n in zip(target, loans)]  # 무대출
rest = [not t or n != 0 for t, n in zip(target, loans)]  # 나머지: 조건으로 직접 (무대출 아님)

N = {}
N["N1"] = len(raw)
N["N2"] = sum(noloan)
N["N3"] = sum(rest)
N["N4"] = sum(p for p, m in zip(price, noloan) if m)
N["N5"] = sum(p for p, m in zip(price, rest) if m)
N["N6"] = sum(price)


def pct(a, b):  # 정확한 분수 → 소수 셋째 자리 사사오입(ROUND_HALF_UP) → 소수 둘째 자리 문자열
    x = Fraction(a * 100, b) * 100 + Fraction(1, 2)
    h = x.numerator // x.denominator  # 양수라 floor = 사사오입
    return f"{h // 100}.{h % 100:02d}"


N["N7"] = pct(N["N4"], N["N6"])
N["N8"] = pct(N["N5"], N["N6"])  # 100 − N7로 구하지 않음
N["N9"] = sum(t and ((l is None) != (n == 0)) for t, l, n in zip(target, last, loans))

# ---------------------------------------------------------------- 합 확인 (어긋나면 멈춤)
if N["N2"] + N["N3"] != N["N1"]:
    stop(f"N2 + N3 ≠ N1 ({N['N2']} + {N['N3']} ≠ {N['N1']})")
if N["N4"] + N["N5"] != N["N6"]:
    stop(f"N4 + N5 ≠ N6 ({N['N4']} + {N['N5']} ≠ {N['N6']})")
if N["N9"] != 0:
    stop(f"N9 = {N['N9']} (무대출 정의 어긋남)")

# ---------------------------------------------------------------- 핵심수치.csv
NAMES = {
    "N1": "전체 권수", "N2": "무대출 권수", "N3": "나머지 권수",
    "N4": "무대출 구입가격 합계", "N5": "나머지 구입가격 합계",
    "N6": "구입가격 합계(현재 목록 28,000권)", "N7": "무대출 비중", "N8": "나머지 비중",
    "N9": "무대출 정의 어긋남 수",
}
with open(CSV, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["번호", "항목", "값"])
    for k in NAMES:
        w.writerow([k, NAMES[k], N[k]])
for k in NAMES:
    print(f"{k} {NAMES[k]}: {N[k]}")

# ---------------------------------------------------------------- 그림 1 (계산명세 7절)
FONT = "NanumGothic.ttf"  # 프로젝트 폴더에서 실행한다
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(8, 8))
labels = [f"무대출\n{N['N7']}%\n{N['N4']:,}원", f"나머지\n{N['N8']}%\n{N['N5']:,}원"]
ax.pie([N["N4"], N["N5"]], labels=labels, startangle=90, counterclock=False,  # 명세의 counterclockwise=False: 이 matplotlib 인자 이름은 counterclock
       colors=["#d9534f", "#9db4c0"], labeldistance=0.55, textprops={"fontsize": 13},
       wedgeprops={"edgecolor": "white"})
for t in ax.texts:  # 조각 라벨을 가운데 정렬 (보기만 바꿈)
    t.set_ha("center")
ax.set_title(f"3년 무대출 장서의 구입가격 비중\n구입가격 합계(현재 목록 {N['N1']:,}권) {N['N6']:,}원 기준",
             fontsize=15)
ax.set_aspect("equal")
fig.text(0.5, 0.04,
         "무대출 = 구입일 2022-12-31 이하이면서 2023-01-01~2025-12-30 대출횟수 0인 책. "
         "나머지 = 그 밖의 모든 책(2023년 이후 구입한 책 포함).\n"
         "구입가격은 구입 당시 단가이며, 현재 목록 28,000권의 합계로 도서관 예산 집행액이 아니다.",
         ha="center", fontsize=9, wrap=True)

# 그림에 찍힌 숫자 = 핵심수치.csv 값 확인 (csv를 다시 읽어 대조)
with open(CSV, encoding="utf-8-sig") as f:
    saved = {r["번호"]: r["값"] for r in csv.DictReader(f)}
shown = "\n".join(t.get_text() for t in ax.texts) + "\n" + ax.get_title()
expect = [f"{int(saved['N1']):,}권", f"{int(saved['N4']):,}원", f"{int(saved['N5']):,}원",
          f"{int(saved['N6']):,}원", f"{saved['N7']}%", f"{saved['N8']}%"]
missing = [e for e in expect if e not in shown]
assert not missing, f"그림 숫자가 핵심수치.csv와 다름: {missing}"
print("그림 숫자 확인: N1, N4, N5, N6, N7, N8 모두 핵심수치.csv와 같음")

fig.savefig(PNG, dpi=150, bbox_inches="tight")
print(f"저장: {PNG}, {CSV}")

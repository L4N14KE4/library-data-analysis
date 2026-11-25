# 4단계 ① 사전 자료 — 질문 4 다시 하기 (2026-11-25), 규칙 5 (가)(나). 검정은 하지 않는다.
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/점검/사전자료.py
# 적용한 처리 (이전 결정 적용, 승인기록 원래 폴더 4~7번 + 공통 정제):
#   공통 정제: 지운 행 없음, 삭제 7열 쓰지 않음 / 4번 대출 이상치(평균±3SD) 유지 = 주 결과, 제외 = 비교
#   5번 구입가격 이상치 후보 유지 / 6번 자료ID만 다른 16쌍 유지 / 7번 '2023년 이후 구입 비율' 열
# 원자료는 읽기만 한다. 난수 없음.
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import font_manager, pyplot as plt

FONT = "NanumGothic.ttf"
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261125_주제별_예산근거_전체도서/점검")
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
d = pd.read_csv(SRC, encoding="utf-8-sig", usecols=["자료ID", "주제분류명", "구입일", "구입가격", "대출횟수"])
d["구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d")
if len(d) != 28000 or d[["구입가격", "대출횟수"]].isna().any().any():
    sys.exit("멈춤: 대상 28,000권이 아니거나 결측 있음")
new = d["구입일"] > pd.Timestamp("2022-12-31")

# 대출 이상치 경계 (승인 2번 기준: 28,000권 평균±3×표본표준편차)
mu, sd = d["대출횟수"].mean(), d["대출횟수"].std(ddof=1)
out = (d["대출횟수"] < mu - 3 * sd) | (d["대출횟수"] > mu + 3 * sd)
TREAT = {"유지 (주 결과)": d, f"대출 이상치 제외 {int(out.sum())}권 (비교)": d[~out]}

# ---------- (가)(나) 분포 요약: 주제 × 변수 × 처리
rows = []
for tname, df in TREAT.items():
    for var in ["대출횟수", "구입가격"]:
        for s in SUBJ + ["대상 전체"]:
            x = df[var] if s == "대상 전체" else df.loc[df["주제분류명"] == s, var]
            rows.append({"처리": tname, "변수": var, "주제분류명": s, "표본 크기": len(x),
                         "평균": x.mean(), "표준편차(ddof=1)": x.std(ddof=1),
                         "왜도(pandas, 편향 보정)": x.skew(),
                         "최소": x.min(), "Q1": x.quantile(0.25), "중앙값": x.median(),
                         "Q3": x.quantile(0.75), "최대": x.max(), "0 비율%": (x == 0).mean() * 100})
dist = pd.DataFrame(rows)
dist.round(4).to_csv(OUT / "사전자료_분포요약.csv", index=False, encoding="utf-8-sig")

# ---------- 주제별 근거 지표 (원래 폴더 사전자료_주제별.csv와 같은 형식, 유지 기준) + 7번 비율 열은 따로
g = d.groupby("주제분류명")
t = pd.DataFrame({"권수": g.size(), "대출합": g["대출횟수"].sum(), "가격합": g["구입가격"].sum(),
                  "가격평균": g["구입가격"].mean(), "가격중앙값": g["구입가격"].median()}).reindex(SUBJ)
t["권수비중%"] = t["권수"] / t["권수"].sum() * 100
t["대출비중%"] = t["대출합"] / t["대출합"].sum() * 100
t["가격합비중%"] = t["가격합"] / t["가격합"].sum() * 100
for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균", "가격중앙값"]:
    t[c + "_순위"] = t[c].rank(ascending=False, method="min")
pre = t[["권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위", "가격합", "가격합비중%",
         "가격합비중%_순위", "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]]
tot = pd.DataFrame([{"권수": len(d), "권수비중%": 100.0, "대출합": d["대출횟수"].sum(), "대출비중%": 100.0,
                     "가격합": d["구입가격"].sum(), "가격합비중%": 100.0,
                     "가격평균": d["구입가격"].mean(), "가격중앙값": d["구입가격"].median()}], index=["대상 합계"])
pre = pd.concat([pre, tot]).rename_axis("주제분류명")
pre.round(4).to_csv(OUT / "사전자료_주제별.csv", encoding="utf-8-sig")
r7 = pd.DataFrame({"권수": t["권수"], "2023년 이후 구입 권수": new.groupby(d["주제분류명"]).sum().reindex(SUBJ)})
r7["2023년 이후 구입 비율%"] = r7["2023년 이후 구입 권수"] / r7["권수"] * 100
r7.loc["대상 합계"] = [len(d), int(new.sum()), new.mean() * 100]
r7.rename_axis("주제분류명").round(4).to_csv(OUT / "사전자료_2023이후구입비율.csv", encoding="utf-8-sig")

# ---------- 그림: 주제별 히스토그램 (2×5), 박스플롯
def hists(var, df, bins, logy, title, fname, xlabel):
    fig, axs = plt.subplots(2, 5, figsize=(18, 7), sharex=True, sharey=True)
    for ax, s in zip(axs.flat, SUBJ):
        x = df.loc[df["주제분류명"] == s, var]
        ax.hist(x, bins=bins, color="#4C72B0", edgecolor="white")
        if logy:
            ax.set_yscale("log")
        ax.set_title(f"{s} (n={len(x):,})")
    for ax in axs[1]:
        ax.set_xlabel(xlabel)
    for ax in axs[:, 0]:
        ax.set_ylabel("권수" + (" (로그 눈금)" if logy else ""))
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(OUT / fname, dpi=120)
    plt.close(fig)


hists("대출횟수", d, np.arange(0, 535, 5), True,
      "주제별 대출횟수 분포 — 유지 (28,000권, 구간 5회, 세로축 로그)", "히스토그램_대출횟수_유지.png", "대출횟수 (2023~2025년, 회)")
hists("대출횟수", d[~out], np.arange(0, 35, 1), True,
      f"주제별 대출횟수 분포 — 이상치 {int(out.sum())}권 제외 비교 ({int((~out).sum()):,}권, 구간 1회, 세로축 로그)",
      "히스토그램_대출횟수_제외.png", "대출횟수 (2023~2025년, 회)")
hists("구입가격", d, np.arange(6000, 39000, 1000), False,
      "주제별 구입가격 분포 (28,000권, 구간 1,000원)", "히스토그램_구입가격.png", "구입가격 (원)")

fig, axs = plt.subplots(1, 2, figsize=(16, 6))
for ax, (tname, df) in zip(axs, TREAT.items()):
    ax.boxplot([df.loc[df["주제분류명"] == s, "대출횟수"] for s in SUBJ], tick_labels=SUBJ)
    ax.set_title(tname)
    ax.set_xlabel("주제분류명")
    ax.set_ylabel("대출횟수 (2023~2025년, 회)")
    ax.tick_params(axis="x", rotation=45)
fig.suptitle("주제별 대출횟수 박스플롯 (상자 = Q1~Q3, 수염 = 상자 길이 1.5배 안, 점 = 그 밖)")
fig.tight_layout()
fig.savefig(OUT / "박스플롯_대출횟수.png", dpi=120)
plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 6))
ax.boxplot([d.loc[d["주제분류명"] == s, "구입가격"] for s in SUBJ], tick_labels=SUBJ)
ax.set_title("주제별 구입가격 박스플롯 (28,000권, 유지)")
ax.set_xlabel("주제분류명")
ax.set_ylabel("구입가격 (원)")
ax.tick_params(axis="x", rotation=45)
fig.tight_layout()
fig.savefig(OUT / "박스플롯_구입가격.png", dpi=120)
plt.close(fig)

# 점검: 주제 합 = 대상 합
for c in ["권수", "대출합", "가격합"]:
    if pre.loc[SUBJ, c].sum() != pre.loc["대상 합계", c]:
        sys.exit(f"멈춤: {c} 주제 합 ≠ 대상 합")
print(dist.round(3).to_string())
print(pre.round(2).to_string())
print(r7.round(2).to_string())

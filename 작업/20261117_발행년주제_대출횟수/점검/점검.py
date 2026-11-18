# 2~3단계 점검 + 4단계 사전 자료(규칙 5 (가)(나)) — 질문 3 발행년·주제분류별 대출횟수
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_발행년주제_대출횟수/점검/점검.py
# 원자료는 읽기만 한다. 아무 행도 지우거나 바꾸지 않는다. 선택지별 결과만 계산한다. 검정 없음. 난수 없음.
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd
from matplotlib import font_manager, pyplot as plt

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261117_발행년주제_대출횟수/점검")
# 코드북 1-1절 '삭제' 7열은 쓰지 않는다. 아래 8열만 고른다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
CUTOFF = pd.Timestamp("2022-12-31")  # 대상: 구입일 <= 2022-12-31 (승인기록 1번)
KDC_NAME = {"000": "총류", "100": "철학", "200": "종교", "300": "사회과학", "400": "자연과학",
            "500": "기술과학", "600": "예술", "700": "언어", "800": "문학", "900": "역사"}  # 한국십진분류 주류

FONT = "NanumGothic.ttf"  # 규칙 10
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

V = []  # (항목, 값) -> 점검값.csv


def put(k, v):
    V.append((k, v))
    print(f"{k}: {v}")


# ---------------------------------------------------------------- 0. 읽기 (변환 실패 시 예외로 멈춤)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[COLS].copy()
for c in ["발행년", "구입가격", "대출횟수"]:
    d[c] = d[c].astype(int)  # 정수가 아닌 값이 있으면 ValueError로 멈춘다
d["구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="raise")
d["최근대출일"] = pd.to_datetime(d["최근대출일"].replace("", None), format="%Y-%m-%d", errors="raise")
put("원본 행 수", len(raw))
put("원본 열 수", raw.shape[1])
t = d[d["구입일"] <= CUTOFF].copy()  # 대상
t["구입연도"] = t["구입일"].dt.year
put("대상 권수 (구입일<=2022-12-31)", len(t))
put("구입일 = 2022-12-31 당일 권수", int((d["구입일"] == CUTOFF).sum()))

# ---------------------------------------------------------------- 1. 대상 구성·기간·논리
put("대상 구입일 범위", f"{t['구입일'].min().date()} ~ {t['구입일'].max().date()}")
put("대상 발행년 범위", f"{t['발행년'].min()} ~ {t['발행년'].max()}")
put("대상 발행년 고유값 수", t["발행년"].nunique())
put("대상 발행년 2005~2025 밖 권수", int((~t["발행년"].between(2005, 2025)).sum()))
put("대상 대출횟수 범위", f"{t['대출횟수'].min()} ~ {t['대출횟수'].max()}")
put("대상 구입가격 범위", f"{t['구입가격'].min()} ~ {t['구입가격'].max()}")
put("발행년 > 구입연도 권수 (대상)", int((t["발행년"] > t["구입연도"]).sum()))
put("발행년 > 구입연도 권수 (전체)", int((d["발행년"] > d["구입일"].dt.year).sum()))
put("발행년 = 구입연도 권수 (대상)", int((t["발행년"] == t["구입연도"]).sum()))
put("구입연도-발행년 차이별 권수 (대상)", (t["구입연도"] - t["발행년"]).value_counts().sort_index().to_dict())
put("최근대출일 < 구입일 권수 (대상)", int((t["최근대출일"] < t["구입일"]).sum()))
put("KDC-주제분류명 대응 어긋남 (대상)", int((t["KDC"].map(KDC_NAME) != t["주제분류명"]).sum()))
put("코드북 주제분류명 목록 밖 값 (대상)", sorted(set(t["주제분류명"]) - set(KDC_NAME.values())))
put("대상 대출횟수 0 권수", int((t["대출횟수"] == 0).sum()))
put("대상 최근대출일 빈칸 권수", int(t["최근대출일"].isna().sum()))

# 발행년 > 구입연도가 있으면 행 목록 저장 (0이면 빈 표)
t[t["발행년"] > t["구입연도"]].to_csv(OUT / "논리위반_발행년gt구입연도.csv", index=False, encoding="utf-8-sig")

# 발행년별·주제별 권수, 발행년×주제 교차표
t.groupby("발행년").size().rename("권수").to_csv(OUT / "발행년별_권수.csv", encoding="utf-8-sig")
t.groupby("주제분류명").size().rename("권수").to_csv(OUT / "주제별_권수.csv", encoding="utf-8-sig")
pd.crosstab(t["발행년"], t["주제분류명"], margins=True, margins_name="합계").to_csv(
    OUT / "발행년x주제_권수.csv", encoding="utf-8-sig")
pd.crosstab(t["발행년"], t["구입연도"]).to_csv(OUT / "발행년x구입연도_권수.csv", encoding="utf-8-sig")
put("발행년×주제 칸 중 권수 30 미만 칸 수 (210칸 중)",
    int((pd.crosstab(t["발행년"], t["주제분류명"]) < 30).sum().sum()))

# ---------------------------------------------------------------- 2(a). 대출횟수 이상치 후보 (판정 안 함)
y = t["대출횟수"]
q1, q3 = y.quantile(0.25), y.quantile(0.75)  # pandas 기본(선형 보간)
iqr = q3 - q1
mu, sd = y.mean(), y.std()  # 표본 표준편차(ddof=1)
put("대상 대출횟수 Q1", q1)
put("대상 대출횟수 Q3", q3)
put("대상 대출횟수 IQR", iqr)
put("대상 대출횟수 평균", round(mu, 4))
put("대상 대출횟수 표준편차", round(sd, 4))
CRIT = {  # 이름: (아래 경계, 위 경계) — 경계 밖을 후보로 본다
    "IQR1.5": (q1 - 1.5 * iqr, q3 + 1.5 * iqr),
    "IQR3": (q1 - 3 * iqr, q3 + 3 * iqr),
    "평균±3SD": (mu - 3 * sd, mu + 3 * sd),
}
crit_rows = []
for k, (lo, hi) in CRIT.items():
    m = (y < lo) | (y > hi)
    crit_rows.append({"기준": k, "아래경계": round(lo, 4), "위경계": round(hi, 4),
                      "아래쪽권수": int((y < lo).sum()), "위쪽권수": int((y > hi).sum()), "권수": int(m.sum()),
                      "대상중비율%": round(100 * m.mean(), 2),
                      "후보최솟값": int(y[m].min()) if m.any() else None,
                      "후보최댓값": int(y[m].max()) if m.any() else None,
                      "후보대출횟수합": int(y[m].sum()), "대상대출횟수합중비율%": round(100 * y[m].sum() / y.sum(), 2)})
    t["후보_" + k] = m
crit = pd.DataFrame(crit_rows)
crit.to_csv(OUT / "이상치_후보기준.csv", index=False, encoding="utf-8-sig")
print(crit.to_string())
# 후보 권수 발행년별·주제별 분포
pd.DataFrame({k: t.groupby("발행년")["후보_" + k].sum() for k in CRIT}).to_csv(
    OUT / "이상치후보_발행년별권수.csv", encoding="utf-8-sig")
pd.DataFrame({k: t.groupby("주제분류명")["후보_" + k].sum() for k in CRIT}).to_csv(
    OUT / "이상치후보_주제별권수.csv", encoding="utf-8-sig")

# ---------------------------------------------------------------- 2(b). 자료ID만 다른 행 (자료ID 제외 7개 사용 열이 모두 같음)
KEY = COLS[1:]
dupmask = t.duplicated(KEY, keep=False)
put("대상 안 자료ID만 다른 행 수", int(dupmask.sum()))
put("대상 안 자료ID만 다른 묶음 수", int(t[dupmask].groupby(KEY, dropna=False).ngroups))
put("그 행들의 대출횟수 고유값", sorted(t.loc[dupmask, "대출횟수"].unique().tolist()))
t[dupmask].sort_values(KEY).drop(columns=[c for c in t if c.startswith("후보_")]).to_csv(
    OUT / "자료ID만다른행_대상.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 선택지별 집단 평균·순위
OPTS = {"유지(기준)": t}
for k, (lo, hi) in CRIT.items():
    OPTS[f"{k} 제외"] = t[~t["후보_" + k]]
    OPTS[f"{k} 대체(경계값으로)"] = t.assign(대출횟수=t["대출횟수"].clip(upper=hi))  # 아래쪽 후보는 0권
OPTS["자료ID만다른행 모두 제외"] = t[~dupmask]
OPTS["자료ID만다른행 한 권만 남김"] = t[~t.duplicated(KEY, keep="first")]


def table(df, g):
    s = df.groupby(g)["대출횟수"].agg(권수="size", 총합="sum", 평균="mean")
    s["평균순위(오름차순)"] = s["평균"].rank(method="min").astype(int)
    return s


opt_rows, rank_rows = [], []
for g in ["발행년", "주제분류명"]:
    base = table(t, g)
    for name, df in OPTS.items():
        s = table(df, g)
        ch = (s["평균순위(오름차순)"] != base["평균순위(오름차순)"])
        opt_rows.append({"집단": g, "선택지": name, "권수": len(df), "전체평균": round(df["대출횟수"].mean(), 4),
                         "전체중앙값": df["대출횟수"].median(),
                         "집단평균최소": round(s["평균"].min(), 4), "최소집단": s["평균"].idxmin(),
                         "집단평균최대": round(s["평균"].max(), 4), "최대집단": s["평균"].idxmax(),
                         "최대-최소": round(s["평균"].max() - s["평균"].min(), 4),
                         "순위바뀐집단수": int(ch.sum()), "순위바뀐집단": ",".join(map(str, s.index[ch])),
                         "평균순서(오름차순)": ",".join(map(str, s.sort_values(["평균"]).index))})
        for grp, r in s.iterrows():
            rank_rows.append({"집단": g, "값": grp, "선택지": name, "권수": int(r["권수"]), "총합": int(r["총합"]),
                              "평균": round(r["평균"], 4), "평균순위": int(r["평균순위(오름차순)"]),
                              "기준대비평균차": round(r["평균"] - base.loc[grp, "평균"], 4),
                              "기준대비순위차": int(r["평균순위(오름차순)"] - base.loc[grp, "평균순위(오름차순)"])})
opt = pd.DataFrame(opt_rows)
opt.to_csv(OUT / "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
pd.DataFrame(rank_rows).to_csv(OUT / "선택지별_집단평균순위.csv", index=False, encoding="utf-8-sig")
print(opt.drop(columns=["평균순서(오름차순)"]).to_string())

# ---------------------------------------------------------------- 3. 규칙 5 (가)(나) 집단별 기술통계 (유지 기준)
def desc(g):
    gb = t.groupby(g)["대출횟수"]
    s = pd.DataFrame({"n": gb.size(), "평균": gb.mean(), "중앙값": gb.median(), "표준편차": gb.std(),
                      "왜도": gb.skew(), "최솟값": gb.min(), "Q1": gb.quantile(0.25), "Q3": gb.quantile(0.75),
                      "최댓값": gb.max(), "0비율%": gb.apply(lambda x: 100 * (x == 0).mean()),
                      "최댓값1권이평균에더한몫": gb.max() / gb.size(),  # 그 1권이 평균을 얼마나 올리는가
                      "상위1%권수의대출합비율%": gb.apply(lambda x: 100 * x.nlargest(max(1, round(len(x) * 0.01))).sum() / x.sum())})
    return s.round(4)


desc_y, desc_s = desc("발행년"), desc("주제분류명")
desc_y.to_csv(OUT / "기술통계_발행년별.csv", encoding="utf-8-sig")
desc_s.to_csv(OUT / "기술통계_주제별.csv", encoding="utf-8-sig")
print(desc_y.to_string()); print(desc_s.to_string())
put("대상 전체 대출횟수 중앙값", y.median())
put("대상 전체 대출횟수 왜도", round(y.skew(), 4))
put("대상 전체 0비율%", round(100 * (y == 0).mean(), 2))
put("발행년 집단 표준편차 최대/최소 비", round(desc_y["표준편차"].max() / desc_y["표준편차"].min(), 4))
put("주제 집단 표준편차 최대/최소 비", round(desc_s["표준편차"].max() / desc_s["표준편차"].min(), 4))


def figs(g, name, ncol):
    groups = sorted(t[g].unique())
    # 히스토그램: 집단마다 작은 그림, 가로축 공통 (0 ~ 대상 최댓값), 세로축은 집단마다 따로
    nrow = -(-len(groups) // ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(3.2 * ncol, 2.4 * nrow), sharex=True)
    bins = range(0, int(y.max()) + 11, 10)
    for ax, k in zip(axes.flat, groups):
        x = t.loc[t[g] == k, "대출횟수"]
        ax.hist(x, bins=bins, color="#4C72B0")
        ax.set_title(f"{k} (n={len(x):,})", fontsize=9)
        ax.set_yscale("symlog")
    for ax in list(axes.flat)[len(groups):]:
        ax.axis("off")
    fig.suptitle(f"{name}별 대출횟수(2023~2025년) 분포 — 히스토그램 (구간 10회, 세로축 로그)")
    fig.supxlabel("대출횟수 (회)"); fig.supylabel("권수")
    fig.tight_layout()
    fig.savefig(OUT / f"히스토그램_{name}별.png", dpi=120); plt.close(fig)
    # 박스플롯 두 장: 전체 범위, 0~50 확대
    for tag, ylim in [("", None), ("_0to50확대", (-1, 50))]:
        fig, ax = plt.subplots(figsize=(max(8, 0.55 * len(groups)), 5))
        ax.boxplot([t.loc[t[g] == k, "대출횟수"] for k in groups], tick_labels=[str(k) for k in groups],
                   whis=1.5, flierprops={"markersize": 2})
        if ylim: ax.set_ylim(*ylim)
        ax.set_title(f"{name}별 대출횟수(2023~2025년) 박스플롯" + (" — 0~50회 확대" if ylim else ""))
        ax.set_xlabel(name); ax.set_ylabel("대출횟수 (회)")
        plt.setp(ax.get_xticklabels(), rotation=45 if g == "발행년" else 0)
        fig.tight_layout()
        fig.savefig(OUT / f"박스플롯_{name}별{tag}.png", dpi=120); plt.close(fig)


figs("발행년", "발행년", 5)
figs("주제분류명", "주제분류명", 5)

# ---------------------------------------------------------------- 4. 산출물 ③ 정의 확인: 자기 집단 평균보다 적은 책
below_rows = []
for name, df in OPTS.items():
    r = {"선택지": name, "권수": len(df)}
    for g in ["발행년", "주제분류명"]:
        b = df["대출횟수"] < df.groupby(g)["대출횟수"].transform("mean")
        r[f"{g}평균미만 권수"] = int(b.sum()); r[f"{g}평균미만 %"] = round(100 * b.mean(), 2)
    b2 = (df["대출횟수"] < df.groupby("발행년")["대출횟수"].transform("mean")) & \
         (df["대출횟수"] < df.groupby("주제분류명")["대출횟수"].transform("mean"))
    r["둘다미만 권수"] = int(b2.sum()); r["둘다미만 %"] = round(100 * b2.mean(), 2)
    r["전체평균미만 %"] = round(100 * (df["대출횟수"] < df["대출횟수"].mean()).mean(), 2)
    below_rows.append(r)
below = pd.DataFrame(below_rows)
below.to_csv(OUT / "평균미만_권수.csv", index=False, encoding="utf-8-sig")
print(below.to_string())
# 집단별 평균 미만 비율 (유지 기준)
for g in ["발행년", "주제분류명"]:
    b = t["대출횟수"] < t.groupby(g)["대출횟수"].transform("mean")
    b.groupby(t[g]).agg(["size", "sum", "mean"]).rename(
        columns={"size": "n", "sum": "평균미만권수", "mean": "평균미만비율"}).assign(
        평균미만비율=lambda x: (100 * x["평균미만비율"]).round(2)).to_csv(
        OUT / f"평균미만_{g}별.csv", encoding="utf-8-sig")

for g in ["발행년", "주제분류명"]:  # 평균 미만 책의 대출횟수 구성 (유지 기준)
    b = t["대출횟수"] < t.groupby(g)["대출횟수"].transform("mean")
    put(f"{g}평균 미만 책의 대출횟수 값별 권수", t.loc[b, "대출횟수"].value_counts().sort_index().to_dict())

pd.DataFrame(V, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")

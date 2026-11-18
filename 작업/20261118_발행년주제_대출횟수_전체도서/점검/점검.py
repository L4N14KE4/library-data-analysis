# 2~3단계 점검 + 4단계 사전 자료(규칙 5 (가)(나)) — 질문 3 다시, 전체 도서 28,000권
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261118_발행년주제_대출횟수_전체도서/점검/점검.py
# 원자료는 읽기만 한다. 아무 행도 지우거나 바꾸지 않는다. 선택지별 결과만 계산한다. 검정 없음. 난수 없음.
# 이전 판(작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/점검/점검.py)의 틀을 따르고, 대상만 28,000권 전부로 바꿨다.
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import pandas as pd
from matplotlib import font_manager, pyplot as plt

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261118_발행년주제_대출횟수_전체도서/점검")
OUT.mkdir(parents=True, exist_ok=True)
# 코드북 1-1절 '삭제' 7열은 쓰지 않는다. 아래 8열만 고른다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
CUT = pd.Timestamp("2022-12-31")  # (d) 비교용: 이전 판 대상 범위 (구입일 <= 2022-12-31). 대상 자체는 28,000권 전부 (승인기록 1번)
KDC_NAME = {"000": "총류", "100": "철학", "200": "종교", "300": "사회과학", "400": "자연과학",
            "500": "기술과학", "600": "예술", "700": "언어", "800": "문학", "900": "역사"}  # 코드북 2절 주제분류명 10개

FONT = "NanumGothic.ttf"  # 규칙 10
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

V = []  # (항목, 값) -> 점검값.csv


def put(k, v):
    V.append((k, v))
    print(f"{k}: {v}")


def csv(df, name, index=True):
    df.to_csv(OUT / name, index=index, encoding="utf-8-sig")


# ---------------------------------------------------------------- 0. 읽기 (변환 실패 시 예외로 멈춤)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
t = raw[COLS].copy()
for c in ["발행년", "구입가격", "대출횟수"]:
    t[c] = t[c].astype(int)  # 정수가 아닌 값이 있으면 ValueError로 멈춘다
t["구입일"] = pd.to_datetime(t["구입일"], format="%Y-%m-%d", errors="raise")
t["최근대출일"] = pd.to_datetime(t["최근대출일"].replace("", None), format="%Y-%m-%d", errors="raise")
t["구입연도"] = t["구입일"].dt.year
put("원본 행 수", len(raw))
put("원본 열 수", raw.shape[1])
put("대상 권수 (전체)", len(t))

# ---------------------------------------------------------------- 1. 구성·기간·논리
put("구입일 범위", f"{t['구입일'].min().date()} ~ {t['구입일'].max().date()}")
put("최근대출일 범위 (빈칸 제외)", f"{t['최근대출일'].min().date()} ~ {t['최근대출일'].max().date()}")
put("발행년 범위", f"{t['발행년'].min()} ~ {t['발행년'].max()}")
put("발행년 값 목록", sorted(t["발행년"].unique().tolist()))
put("발행년 2005~2025 밖 권수", int((~t["발행년"].between(2005, 2025)).sum()))
put("대출횟수 범위", f"{t['대출횟수'].min()} ~ {t['대출횟수'].max()}")
put("구입가격 범위", f"{t['구입가격'].min()} ~ {t['구입가격'].max()}")
put("자료ID 중복 수", int(t["자료ID"].duplicated().sum()))
put("발행년 > 구입연도 권수", int((t["발행년"] > t["구입연도"]).sum()))
put("구입연도-발행년 차이별 권수", (t["구입연도"] - t["발행년"]).value_counts().sort_index().to_dict())
put("최근대출일 < 구입일 권수", int((t["최근대출일"] < t["구입일"]).sum()))
put("최근대출일 > 2025-12-30 권수", int((t["최근대출일"] > pd.Timestamp("2025-12-30")).sum()))
put("최근대출일 < 2023-01-01 권수 (대출 기간 밖)", int((t["최근대출일"] < pd.Timestamp("2023-01-01")).sum()))
put("대출횟수 0 인데 최근대출일 있음", int(((t["대출횟수"] == 0) & t["최근대출일"].notna()).sum()))
put("대출횟수 >0 인데 최근대출일 빈칸", int(((t["대출횟수"] > 0) & t["최근대출일"].isna()).sum()))
put("KDC-주제분류명 대응 어긋남", int((t["KDC"].map(KDC_NAME) != t["주제분류명"]).sum()))
put("KDC 값 목록", sorted(t["KDC"].unique().tolist()))
put("코드북 주제분류명 목록 밖 값", sorted(set(t["주제분류명"]) - set(KDC_NAME.values())))
put("대출횟수 0 권수", int((t["대출횟수"] == 0).sum()))
put("대출횟수 0 비율%", round(100 * (t["대출횟수"] == 0).mean(), 2))
put("최근대출일 빈칸 권수 (코드북 결측 수 14036)", int(t["최근대출일"].isna().sum()))
csv(t[t["발행년"] > t["구입연도"]], "논리위반_발행년gt구입연도.csv", index=False)  # 0이면 빈 표

# 발행년별·주제별·구입연도별 권수, 교차표
y_cnt = t.groupby("발행년")["대출횟수"].agg(권수="size", 총합="sum", 평균="mean", 대출0권수=lambda x: int((x == 0).sum()))
y_cnt["대출0비율%"] = 100 * y_cnt["대출0권수"] / y_cnt["권수"]
csv(y_cnt.round(4), "발행년별_권수.csv")
csv(t.groupby("주제분류명").size().rename("권수"), "주제별_권수.csv")
b_cnt = t.groupby("구입연도")["대출횟수"].agg(권수="size", 평균="mean", 중앙값="median", 대출0권수=lambda x: int((x == 0).sum()))
b_cnt["대출0비율%"] = 100 * b_cnt["대출0권수"] / b_cnt["권수"]
csv(b_cnt.round(4), "구입연도별_권수.csv")
csv(pd.crosstab(t["발행년"], t["주제분류명"], margins=True, margins_name="합계"), "발행년x주제_권수.csv")
csv(pd.crosstab(t["발행년"], t["구입연도"], margins=True, margins_name="합계"), "발행년x구입연도_권수.csv")
put("발행년×주제 칸 중 권수 30 미만 칸 수 (210칸 중)", int((pd.crosstab(t["발행년"], t["주제분류명"]) < 30).sum().sum()))

# 2023년 이후 구입분
new = t["구입일"] > CUT
put("2023-01-01 이후 구입 권수", int(new.sum()))
put("2023-01-01 이후 구입 비율%", round(100 * new.mean(), 2))
put("2023 이후 구입분 대출0 비율%", round(100 * (t.loc[new, "대출횟수"] == 0).mean(), 2))
put("2022 이하 구입분 대출0 비율%", round(100 * (t.loc[~new, "대출횟수"] == 0).mean(), 2))
put("2023 이후 구입분 평균", round(t.loc[new, "대출횟수"].mean(), 4))
put("2022 이하 구입분 평균", round(t.loc[~new, "대출횟수"].mean(), 4))
put("2023 이후 구입분 중앙값", t.loc[new, "대출횟수"].median())
put("2022 이하 구입분 중앙값", t.loc[~new, "대출횟수"].median())
put("2023~2025년 발행 책 중 2023 이후 구입 비율%",
    round(100 * new[t["발행년"] >= 2023].mean(), 2))

# ---------------------------------------------------------------- 2(a). 대출횟수 이상치 후보 (판정 안 함, 28,000권 기준)
y = t["대출횟수"]
q1, q3 = y.quantile(0.25), y.quantile(0.75)  # pandas 기본(선형 보간)
iqr = q3 - q1
mu, sd = y.mean(), y.std()  # 표본 표준편차(ddof=1)
put("대출횟수 Q1", q1); put("대출횟수 Q3", q3); put("대출횟수 IQR", iqr)
put("대출횟수 평균", round(mu, 4)); put("대출횟수 표준편차", round(sd, 4))
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
                      "후보최솟값": int(y[m].min()), "후보최댓값": int(y[m].max()),
                      "후보대출횟수합": int(y[m].sum()), "대상대출횟수합중비율%": round(100 * y[m].sum() / y.sum(), 2),
                      "후보중2023이후구입권수": int((m & new).sum())})
    t["후보_" + k] = m
crit = pd.DataFrame(crit_rows)
csv(crit, "이상치_후보기준.csv", index=False)
print(crit.to_string())
csv(pd.DataFrame({k: t.groupby("발행년")["후보_" + k].sum() for k in CRIT}), "이상치후보_발행년별권수.csv")
csv(pd.DataFrame({k: t.groupby("주제분류명")["후보_" + k].sum() for k in CRIT}), "이상치후보_주제별권수.csv")

# ---------------------------------------------------------------- 2(b). 자료ID만 다른 행 (자료ID 제외 7개 사용 열이 모두 같음)
KEY = COLS[1:]
dupmask = t.duplicated(KEY, keep=False)
put("자료ID만 다른 행 수", int(dupmask.sum()))
put("자료ID만 다른 묶음 수", int(t[dupmask].groupby(KEY, dropna=False).ngroups))
put("묶음 크기별 묶음 수", t[dupmask].groupby(KEY, dropna=False).size().value_counts().to_dict())
put("그 행들의 대출횟수 고유값", sorted(t.loc[dupmask, "대출횟수"].unique().tolist()))
put("그 행들 중 2023 이후 구입", int((dupmask & new).sum()))
csv(t[dupmask].sort_values(KEY)[COLS], "자료ID만다른행.csv", index=False)

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
        ch = s["평균순위(오름차순)"] != base["평균순위(오름차순)"]
        srt = s.sort_values("평균")
        opt_rows.append({"집단": g, "선택지": name, "권수": len(df), "전체평균": round(df["대출횟수"].mean(), 4),
                         "전체중앙값": df["대출횟수"].median(),
                         "집단평균최소": round(srt["평균"].iloc[0], 4), "최소집단": srt.index[0],
                         "둘째최소": round(srt["평균"].iloc[1], 4), "둘째집단": srt.index[1],
                         "집단평균최대": round(srt["평균"].iloc[-1], 4), "최대집단": srt.index[-1],
                         "최대-최소": round(srt["평균"].iloc[-1] - srt["평균"].iloc[0], 4),
                         "순위바뀐집단수": int(ch.sum()),
                         "최대순위이동": int((s["평균순위(오름차순)"] - base["평균순위(오름차순)"]).abs().max()),
                         "순위바뀐집단": ",".join(map(str, s.index[ch])),
                         "평균순서(오름차순)": ",".join(map(str, srt.index))})
        for grp, r in s.iterrows():
            rank_rows.append({"집단": g, "값": grp, "선택지": name, "권수": int(r["권수"]), "총합": int(r["총합"]),
                              "평균": round(r["평균"], 4), "평균순위": int(r["평균순위(오름차순)"]),
                              "기준대비평균차": round(r["평균"] - base.loc[grp, "평균"], 4),
                              "기준대비순위차": int(r["평균순위(오름차순)"] - base.loc[grp, "평균순위(오름차순)"])})
opt = pd.DataFrame(opt_rows)
csv(opt, "선택지별_핵심수치.csv", index=False)
csv(pd.DataFrame(rank_rows), "선택지별_집단평균순위.csv", index=False)
print(opt.drop(columns=["평균순서(오름차순)", "순위바뀐집단"]).to_string())
# 2005~2022년 발행 18개 해만 놓고 본 순위 변화 (2023~2025년이 맨 아래 3칸을 차지하는지 따로 보려고)
r18 = pd.DataFrame(rank_rows).query("집단 == '발행년'").copy()
r18 = r18[r18["값"].astype(int) <= 2022]
r18["순위18"] = r18.groupby("선택지")["평균"].rank(method="min").astype(int)
b18 = r18[r18["선택지"] == "유지(기준)"].set_index("값")["순위18"]
r18["순위18차"] = r18["순위18"] - r18["값"].map(b18)
csv(r18.groupby("선택지", sort=False).agg(바뀐해수=("순위18차", lambda x: int((x != 0).sum())),
                                        최대이동=("순위18차", lambda x: int(x.abs().max()))),
    "선택지별_2005to2022순위변화.csv")

# ---------------------------------------------------------------- 2(d). 2023년 이후 구입분의 영향 (계산만, 판단 안 함)
def side(g):
    a = t.groupby(g)["대출횟수"].agg(전체_권수="size", 전체_평균="mean")
    b = t[~new].groupby(g)["대출횟수"].agg(구입2022이하_권수="size", 구입2022이하_평균="mean")
    c = t[new].groupby(g)["대출횟수"].agg(구입2023이후_권수="size", 구입2023이후_평균="mean")
    s = a.join(b).join(c)
    s["2023이후구입비율%"] = 100 * s["구입2023이후_권수"].fillna(0) / s["전체_권수"]
    s["평균차(전체-2022이하)"] = s["전체_평균"] - s["구입2022이하_평균"]
    s["전체_순위"] = s["전체_평균"].rank(method="min")
    s["구입2022이하_순위"] = s["구입2022이하_평균"].rank(method="min")
    return s.round(4)


sd_y, sd_s = side("발행년"), side("주제분류명")
csv(sd_y, "구입2023이후_영향_발행년별.csv"); csv(sd_s, "구입2023이후_영향_주제별.csv")
print(sd_y.to_string()); print(sd_s.to_string())
put("주제 순위: 전체 vs 구입2022이하 바뀐 주제 수",
    int((sd_s["전체_순위"] != sd_s["구입2022이하_순위"]).sum()))
put("주제 평균 오름차순 (전체)", ",".join(sd_s.sort_values("전체_평균").index))
put("주제 평균 오름차순 (구입2022이하)", ",".join(sd_s.sort_values("구입2022이하_평균").index))

# 이전 판 대상 범위로 다시 낸 값이 이전 판 점검 CSV와 같은지 (읽기만)
PREV = Path("작업/20261117_발행년주제_대출횟수_보관_구입일2022이하/점검")
pv = pd.read_csv(PREV / "기술통계_발행년별.csv", encoding="utf-8-sig", index_col=0)
put("구입2022이하 발행년 평균 = 이전 판 점검값 (소수 4자리)",
    bool((sd_y["구입2022이하_평균"].dropna().round(4) == pv["평균"].round(4)).all()))

# ---------------------------------------------------------------- 3. 규칙 5 (가)(나) 집단별 기술통계 (유지 기준)
def desc(g, df=t):
    gb = df.groupby(g)["대출횟수"]
    s = pd.DataFrame({"n": gb.size(), "평균": gb.mean(), "중앙값": gb.median(), "표준편차": gb.std(),
                      "왜도": gb.skew(), "최솟값": gb.min(), "Q1": gb.quantile(0.25), "Q3": gb.quantile(0.75),
                      "최댓값": gb.max(), "0비율%": gb.apply(lambda x: 100 * (x == 0).mean()),
                      "최댓값1권이평균에더한몫": gb.max() / gb.size(),  # 그 1권이 평균을 얼마나 올리는가
                      "상위1%권수의대출합비율%": gb.apply(lambda x: 100 * x.nlargest(max(1, round(len(x) * 0.01))).sum() / x.sum())})
    return s.round(4)


desc_y, desc_s, desc_b = desc("발행년"), desc("주제분류명"), desc("구입연도")
csv(desc_y, "기술통계_발행년별.csv"); csv(desc_s, "기술통계_주제별.csv"); csv(desc_b, "기술통계_구입연도별.csv")
print(desc_y.to_string()); print(desc_s.to_string())
put("전체 대출횟수 중앙값", y.median())
put("전체 대출횟수 왜도", round(y.skew(), 4))
put("발행년 집단 표준편차 최대/최소 비", round(desc_y["표준편차"].max() / desc_y["표준편차"].min(), 4))
put("주제 집단 표준편차 최대/최소 비", round(desc_s["표준편차"].max() / desc_s["표준편차"].min(), 4))
put("발행년 집단 n 최소/최대", f"{desc_y['n'].min()} / {desc_y['n'].max()}")
put("주제 집단 n 최소/최대", f"{desc_s['n'].min()} / {desc_s['n'].max()}")


def figs(g, name, ncol):
    groups = sorted(t[g].unique())
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
    fig.suptitle(f"{name}별 대출횟수(2023~2025년) 분포 — 전체 28,000권, 히스토그램 (구간 10회, 세로축 로그)")
    fig.supxlabel("대출횟수 (회)"); fig.supylabel("권수")
    fig.tight_layout(rect=(0.02, 0, 1, 1))  # 세로축 이름이 눈금과 겹치지 않게
    fig.savefig(OUT / f"히스토그램_{name}별.png", dpi=120); plt.close(fig)
    for tag, ylim in [("", None), ("_0to50확대", (-1, 50))]:
        fig, ax = plt.subplots(figsize=(max(8, 0.55 * len(groups)), 5))
        ax.boxplot([t.loc[t[g] == k, "대출횟수"] for k in groups], tick_labels=[str(k) for k in groups],
                   whis=1.5, flierprops={"markersize": 2})
        if ylim: ax.set_ylim(*ylim)
        ax.set_title(f"{name}별 대출횟수(2023~2025년) 박스플롯 — 전체 28,000권" + (", 0~50회 확대" if ylim else ""))
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
        r[f"{g}평균미만 대출횟수범위"] = f"{df.loc[b, '대출횟수'].min():g}~{df.loc[b, '대출횟수'].max():g}"
    b2 = (df["대출횟수"] < df.groupby("발행년")["대출횟수"].transform("mean")) & \
         (df["대출횟수"] < df.groupby("주제분류명")["대출횟수"].transform("mean"))
    r["둘다미만 권수"] = int(b2.sum()); r["둘다미만 %"] = round(100 * b2.mean(), 2)
    r["전체평균미만 %"] = round(100 * (df["대출횟수"] < df["대출횟수"].mean()).mean(), 2)
    below_rows.append(r)
below = pd.DataFrame(below_rows)
csv(below, "평균미만_권수.csv", index=False)
print(below.to_string())
for g in ["발행년", "주제분류명"]:  # 집단별 평균 미만 비율·대출횟수 범위 (유지 기준)
    mean_g = t.groupby(g)["대출횟수"].transform("mean")
    b = t["대출횟수"] < mean_g
    s = t.assign(b=b).groupby(g).agg(n=("b", "size"), 집단평균=("대출횟수", "mean"), 평균미만권수=("b", "sum"))
    s["평균미만비율%"] = 100 * s["평균미만권수"] / s["n"]
    s["평균미만_대출횟수최댓값"] = t[b].groupby(g)["대출횟수"].max()
    csv(s.round(4), f"평균미만_{g}별.csv")
    put(f"{g}평균 미만 책의 대출횟수 값별 권수", t.loc[b, "대출횟수"].value_counts().sort_index().to_dict())
    put(f"{g}평균 미만 책 중 2023 이후 구입 권수", int((b & new).sum()))
    put(f"2023 이후 구입분 중 {g}평균 미만 비율%", round(100 * b[new].mean(), 2))

pd.DataFrame(V, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")

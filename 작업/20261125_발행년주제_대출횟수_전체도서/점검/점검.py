# 2~3단계 점검 + 4단계 사전 자료(규칙 5 (가)(나)) — 질문 3 다시 하기 (2026-11-25), 전체 도서 28,000권
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/점검/점검.py
# 원자료는 읽기만 한다. 행을 지우거나 바꾸지 않는다 — 선택지별 결과는 메모리 안에서만 계산한다. 검정 없음. 난수 없음.
# 원래 폴더(작업/20261118_...)의 코드를 옮기지 않고 새로 썼다. 원래 점검값.csv는 끝에서 비교용으로만 읽는다.
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np
import pandas as pd
from matplotlib import font_manager, pyplot as plt

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261125_발행년주제_대출횟수_전체도서/점검")
OLD = Path("작업/20261118_발행년주제_대출횟수_전체도서/점검/점검값.csv")
# 코드북 1-1절 '삭제' 7열(서명·저자·출판사·자료구분·소장관·이용상태·장서연령)은 쓰지 않는다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절
CUT = pd.Timestamp("2022-12-31")  # 2023년 이후 구입분 구분 (승인 7번 '2023년 이후 구입 비율')

FONT = "NanumGothic.ttf"  # 규칙 10
font_manager.fontManager.addfont(FONT)
plt.rcParams["font.family"] = font_manager.FontProperties(fname=FONT).get_name()
plt.rcParams["axes.unicode_minus"] = False

V = []


def put(k, v):
    V.append((k, v))
    print(f"{k}: {v}")


def save(df, name, index=True):
    df.to_csv(OUT / name, index=index, encoding="utf-8-sig")


# ============================================================ 1. 읽기와 형식 점검
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[COLS].copy()
put("원본 행 수", len(raw))
put("원본 열 수", raw.shape[1])
put("대상 권수 (전체)", len(d))
# 새 점검: 쓰는 8열의 빈칸·앞뒤 공백
put("[새] 빈칸 수 (8열별)", {c: int((d[c] == "").sum()) for c in COLS})
put("[새] 앞뒤 공백이 있는 값 수 (8열 합)", int(sum((d[c] != d[c].str.strip()).sum() for c in COLS)))
put("[새] 자료ID 형식 B+6자리 아닌 수", int((~d["자료ID"].str.fullmatch(r"B\d{6}")).sum()))
put("[새] 자료ID 범위", f"{d['자료ID'].min()} ~ {d['자료ID'].max()}")
for c in ["발행년", "구입가격", "대출횟수"]:
    put(f"[새] {c} 정수 아닌 값 수", int((~d[c].str.fullmatch(r"\d+")).sum()))
put("[새] 구입일 YYYY-MM-DD 아닌 값 수", int((~d["구입일"].str.fullmatch(r"\d{4}-\d{2}-\d{2}")).sum()))
nb = d["최근대출일"] != ""
put("[새] 최근대출일(빈칸 제외) YYYY-MM-DD 아닌 값 수", int((~d.loc[nb, "최근대출일"].str.fullmatch(r"\d{4}-\d{2}-\d{2}")).sum()))

d["발행년"] = d["발행년"].astype(int)
d["구입가격"] = d["구입가격"].astype(int)
d["대출횟수"] = d["대출횟수"].astype(int)
d["구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d")  # 없는 날짜면 여기서 멈춘다
d["최근대출일"] = pd.to_datetime(d["최근대출일"].replace("", None), format="%Y-%m-%d")
d["구입연도"] = d["구입일"].dt.year
d["후구입"] = d["구입일"] > CUT
y = d["대출횟수"]

put("구입일 범위", f"{d['구입일'].min():%Y-%m-%d} ~ {d['구입일'].max():%Y-%m-%d}")
put("최근대출일 범위 (빈칸 제외)", f"{d['최근대출일'].min():%Y-%m-%d} ~ {d['최근대출일'].max():%Y-%m-%d}")
put("발행년 범위", f"{d['발행년'].min()} ~ {d['발행년'].max()}")
put("발행년 값 목록", sorted(d["발행년"].unique().tolist()))
put("발행년 2005~2025 밖 권수", int((~d["발행년"].between(2005, 2025)).sum()))
put("대출횟수 범위", f"{y.min()} ~ {y.max()}")
put("구입가격 범위", f"{d['구입가격'].min()} ~ {d['구입가격'].max()}")
put("[새] 구입가격 500원 배수 아닌 수", int((d["구입가격"] % 500 != 0).sum()))
put("자료ID 중복 수", int(d["자료ID"].duplicated().sum()))

# 논리 점검
put("발행년 > 구입연도 권수", int((d["발행년"] > d["구입연도"]).sum()))
save(d.loc[d["발행년"] > d["구입연도"], COLS], "논리위반_발행년gt구입연도.csv", index=False)
put("구입연도-발행년 차이별 권수", (d["구입연도"] - d["발행년"]).value_counts().sort_index().to_dict())
put("최근대출일 < 구입일 권수", int((d["최근대출일"] < d["구입일"]).sum()))
put("최근대출일 > 2025-12-30 권수", int((d["최근대출일"] > "2025-12-30").sum()))
put("최근대출일 < 2023-01-01 권수 (대출 기간 밖)", int((d["최근대출일"] < "2023-01-01").sum()))
put("대출횟수 0 인데 최근대출일 있음", int(((y == 0) & d["최근대출일"].notna()).sum()))
put("대출횟수 >0 인데 최근대출일 빈칸", int(((y > 0) & d["최근대출일"].isna()).sum()))
put("[새] 구입일 > 2025-12-30 권수 (대출 기간 끝 뒤)", int((d["구입일"] > "2025-12-30").sum()))
# KDC↔주제분류명: 대응표는 코드북에 없으므로 이름을 가정하지 않고 1:1 대응인지만 본다
kp = d.groupby("KDC")["주제분류명"].nunique()
pk = d.groupby("주제분류명")["KDC"].nunique()
put("KDC-주제분류명 대응 어긋남", int((kp > 1).sum() + (pk > 1).sum()))
put("[새] KDC-주제분류명 대응", d.drop_duplicates("KDC").set_index("KDC")["주제분류명"].sort_index().to_dict())
put("KDC 값 목록", sorted(d["KDC"].unique().tolist()))
put("코드북 주제분류명 목록 밖 값", sorted(set(d["주제분류명"]) - set(SUBJ)))
put("대출횟수 0 권수", int((y == 0).sum()))
put("대출횟수 0 비율%", round((y == 0).mean() * 100, 2))
put("최근대출일 빈칸 권수 (코드북 결측 수 14036)", int(d["최근대출일"].isna().sum()))

# ============================================================ 2. 집단별 권수
def tab(by):
    g = d.groupby(by)["대출횟수"]
    t = pd.DataFrame({"권수": g.size(), "총합": g.sum(), "평균": g.mean().round(4),
                      "대출0권수": g.apply(lambda s: int((s == 0).sum()))})
    t["대출0비율%"] = (t["대출0권수"] / t["권수"] * 100).round(4)
    return t


save(tab("발행년"), "발행년별_권수.csv")
save(tab("주제분류명"), "주제별_권수.csv")
by_buy = tab("구입연도")
by_buy.insert(2, "중앙값", d.groupby("구입연도")["대출횟수"].median())
save(by_buy, "구입연도별_권수.csv")
xt = pd.crosstab(d["발행년"], d["주제분류명"])
save(xt, "발행년x주제_권수.csv")
save(pd.crosstab(d["발행년"], d["구입연도"]), "발행년x구입연도_권수.csv")
put("발행년×주제 칸 중 권수 30 미만 칸 수 (210칸 중)", int((xt < 30).sum().sum()))

# ============================================================ 3. 2023년 이후 구입분
a, b = d[d["후구입"]], d[~d["후구입"]]
put("2023-01-01 이후 구입 권수", len(a))
put("2023-01-01 이후 구입 비율%", round(len(a) / len(d) * 100, 2))
put("2023 이후 구입분 대출0 비율%", round((a["대출횟수"] == 0).mean() * 100, 2))
put("2022 이하 구입분 대출0 비율%", round((b["대출횟수"] == 0).mean() * 100, 2))
put("2023 이후 구입분 평균", round(a["대출횟수"].mean(), 4))
put("2022 이하 구입분 평균", round(b["대출횟수"].mean(), 4))
put("2023 이후 구입분 중앙값", a["대출횟수"].median())
put("2022 이하 구입분 중앙값", b["대출횟수"].median())
put("2023~2025년 발행 책 중 2023 이후 구입 비율%", round(d.loc[d["발행년"] >= 2023, "후구입"].mean() * 100, 2))

# ============================================================ 4. 대출횟수 이상치 후보 (코드북 기준 없음 -> 세 후보 기준을 나란히)
q1, q3 = y.quantile(0.25), y.quantile(0.75)
iqr, mu, sd = q3 - q1, y.mean(), y.std(ddof=1)
put("대출횟수 Q1", q1)
put("대출횟수 Q3", q3)
put("대출횟수 IQR", iqr)
put("대출횟수 평균", round(mu, 4))
put("대출횟수 표준편차", round(sd, 4))
BOUND = {"IQR1.5": (q1 - 1.5 * iqr, q3 + 1.5 * iqr), "IQR3": (q1 - 3 * iqr, q3 + 3 * iqr),
         "평균±3SD": (mu - 3 * sd, mu + 3 * sd)}
rows, flag = [], {}
for k, (lo, hi) in BOUND.items():
    m = (y < lo) | (y > hi)
    flag[k] = m
    rows.append({"기준": k, "아래경계": round(lo, 4), "위경계": round(hi, 4), "아래쪽권수": int((y < lo).sum()),
                 "위쪽권수": int((y > hi).sum()), "권수": int(m.sum()), "대상중비율%": round(m.mean() * 100, 2),
                 "후보최솟값": int(y[m].min()), "후보최댓값": int(y[m].max()), "후보대출횟수합": int(y[m].sum()),
                 "대상대출횟수합중비율%": round(y[m].sum() / y.sum() * 100, 2),
                 "후보중2023이후구입권수": int((m & d["후구입"]).sum())})
save(pd.DataFrame(rows), "이상치_후보기준.csv", index=False)
for g, f in [("발행년", "이상치후보_발행년별권수.csv"), ("주제분류명", "이상치후보_주제별권수.csv")]:
    save(pd.DataFrame({k: m.groupby(d[g]).sum() for k, m in flag.items()}), f)

# 구입가격 이상치 후보 (승인 8번 ③ '유지'가 다루는 범위를 이번 자료로 다시 셈)
p = d["구입가격"]
pq1, pq3 = p.quantile(0.25), p.quantile(0.75)
pi_, pm, ps = pq3 - pq1, p.mean(), p.std(ddof=1)
put("[새] 구입가격 IQR1.5 후보 권수", int(((p < pq1 - 1.5 * pi_) | (p > pq3 + 1.5 * pi_)).sum()))
put("[새] 구입가격 IQR3 후보 권수", int(((p < pq1 - 3 * pi_) | (p > pq3 + 3 * pi_)).sum()))
put("[새] 구입가격 평균±3SD 후보 권수", int(((p < pm - 3 * ps) | (p > pm + 3 * ps)).sum()))

# ============================================================ 5. 자료ID만 다른 행 (중복 기준: 자료ID를 뺀 쓰는 7열)
K7 = COLS[1:]
dup = d.duplicated(K7, keep=False)
grp = d[dup].groupby(K7, dropna=False).ngroup()
put("[새] 8열 모두 같은 행 수 (자료ID 포함)", int(d.duplicated(COLS, keep=False).sum()))
put("자료ID만 다른 행 수", int(dup.sum()))
put("자료ID만 다른 묶음 수", int(grp.nunique()))
put("묶음 크기별 묶음 수", grp.value_counts().value_counts().to_dict())
put("그 행들의 대출횟수 고유값", sorted(d.loc[dup, "대출횟수"].unique().tolist()))
put("그 행들 중 2023 이후 구입", int((dup & d["후구입"]).sum()))
dd = d.loc[dup, COLS].assign(묶음=grp.values).sort_values(["묶음", "자료ID"])
save(dd, "자료ID만다른행.csv", index=False)

# ============================================================ 6. 선택지별 집단 평균과 순위 (처리하지 않고 계산만)
def treat(name):
    """선택지 이름 -> 대출횟수 Series (제외는 행을 뺀 것, 대체는 위 경계값으로 바꾼 것)."""
    if name == "유지(기준)":
        return y
    if name == "자료ID만다른행 모두 제외":
        return y[~dup]
    if name == "자료ID만다른행 한 권만 남김":
        return y[~d.duplicated(K7, keep="first")]
    k, how = name.split(" ")
    lo, hi = BOUND[k]
    return y[~flag[k]] if how == "제외" else y.clip(lower=lo, upper=hi)  # 대체 = 경계값으로 (아래쪽 후보 0권)


CHOICES = ["유지(기준)", "IQR1.5 제외", "IQR1.5 대체(경계값으로)", "IQR3 제외", "IQR3 대체(경계값으로)",
           "평균±3SD 제외", "평균±3SD 대체(경계값으로)", "자료ID만다른행 모두 제외", "자료ID만다른행 한 권만 남김"]
TR = {c: treat(c) for c in CHOICES}
long, summ, r18 = [], [], []
for g in ["발행년", "주제분류명"]:
    base = None
    for c in CHOICES:
        s = TR[c]
        gg = s.groupby(d.loc[s.index, g])
        t = pd.DataFrame({"권수": gg.size(), "총합": gg.sum(), "평균": gg.mean()})
        t["평균순위"] = t["평균"].rank(method="min").astype(int)  # 1 = 평균 가장 낮음
        if base is None:
            base = t
        t["기준대비평균차"] = (t["평균"] - base["평균"]).round(4)
        t["기준대비순위차"] = t["평균순위"] - base["평균순위"]
        long.append(t.assign(평균=t["평균"].round(4)).reset_index().rename(columns={g: "값"}).assign(집단=g, 선택지=c))
        o = t.sort_values("평균")
        ch = t.index[t["기준대비순위차"] != 0]
        summ.append({"집단": g, "선택지": c, "권수": len(s), "전체평균": round(s.mean(), 4), "전체중앙값": s.median(),
                     "집단평균최소": round(o["평균"].iloc[0], 4), "최소집단": o.index[0], "둘째최소": round(o["평균"].iloc[1], 4),
                     "둘째집단": o.index[1], "집단평균최대": round(o["평균"].iloc[-1], 4), "최대집단": o.index[-1],
                     "최대-최소": round(o["평균"].iloc[-1] - o["평균"].iloc[0], 4), "순위바뀐집단수": len(ch),
                     "최대순위이동": int(t["기준대비순위차"].abs().max()), "순위바뀐집단": ",".join(map(str, ch)),
                     "평균순서(오름차순)": ",".join(map(str, o.index))})
        if g == "발행년":  # 2005~2022년 18개 해만으로 순위를 다시 매긴 변화
            u = t.loc[t.index <= 2022, "평균"].rank(method="min")
            ub = base.loc[base.index <= 2022, "평균"].rank(method="min")
            r18.append({"선택지": c, "바뀐해수": int((u != ub).sum()), "최대이동": int((u - ub).abs().max())})
save(pd.concat(long)[["집단", "값", "선택지", "권수", "총합", "평균", "평균순위", "기준대비평균차", "기준대비순위차"]],
     "선택지별_집단평균순위.csv", index=False)
S = pd.DataFrame(summ)
save(S, "선택지별_핵심수치.csv", index=False)
save(pd.DataFrame(r18), "선택지별_2005to2022순위변화.csv", index=False)

# ============================================================ 7. 2023년 이후 구입분의 영향 (계산만)
def impact(g):
    t = pd.DataFrame({"전체_권수": d.groupby(g).size(), "전체_평균": d.groupby(g)["대출횟수"].mean(),
                      "구입2022이하_권수": b.groupby(g).size(), "구입2022이하_평균": b.groupby(g)["대출횟수"].mean(),
                      "구입2023이후_권수": a.groupby(g).size(), "구입2023이후_평균": a.groupby(g)["대출횟수"].mean()})
    t["2023이후구입비율%"] = t["구입2023이후_권수"].fillna(0) / t["전체_권수"] * 100
    t["평균차(전체-2022이하)"] = t["전체_평균"] - t["구입2022이하_평균"]
    t["전체_순위"] = t["전체_평균"].rank(method="min")
    t["구입2022이하_순위"] = t["구입2022이하_평균"].rank(method="min")
    return t.round(4)


save(impact("발행년"), "구입2023이후_영향_발행년별.csv")
ims = impact("주제분류명")
save(ims, "구입2023이후_영향_주제별.csv")
put("주제 순위: 전체 vs 구입2022이하 바뀐 주제 수", int((ims["전체_순위"] != ims["구입2022이하_순위"]).sum()))
put("주제 평균 오름차순 (전체)", ",".join(ims.sort_values("전체_평균").index))
put("주제 평균 오름차순 (구입2022이하)", ",".join(ims.sort_values("구입2022이하_평균").index))

# ============================================================ 8. 규칙 5 (가)(나) — 유지 / 평균±3SD 제외 두 처리 (승인 5번)
TREAT = {"유지": d, "3SD제외": d[~flag["평균±3SD"]]}


def desc(s):
    n = len(s)
    k = max(1, round(n * 0.01))  # 상위 1% 권수 = n×0.01 반올림 (최소 1권)
    return pd.Series({"n": n, "평균": round(s.mean(), 4), "중앙값": s.median(), "표준편차": round(s.std(ddof=1), 4),
                      "왜도": round(s.skew(), 4), "최솟값": s.min(), "Q1": s.quantile(0.25), "Q3": s.quantile(0.75),
                      "최댓값": s.max(), "0비율%": round((s == 0).mean() * 100, 4),
                      "최댓값1권이평균에더한몫": round(s.max() / n, 4),
                      "상위1%권수의대출합비율%": round(s.nlargest(k).sum() / s.sum() * 100, 4) if s.sum() else np.nan})


for tn, x in TREAT.items():
    sfx = "" if tn == "유지" else "_3SD제외"
    for g, f in [("발행년", "기술통계_발행년별"), ("주제분류명", "기술통계_주제별"), ("구입연도", "기술통계_구입연도별")]:
        t = x.groupby(g)["대출횟수"].apply(desc).unstack().astype({"n": int, "최솟값": int, "최댓값": int})
        save(t, f"{f}{sfx}.csv")
        if g != "구입연도":
            nm = "발행년" if g == "발행년" else "주제"
            put(f"{nm} 집단 표준편차 최대/최소 비{'' if tn == '유지' else ' (3SD제외)'}",
                round(t["표준편차"].max() / t["표준편차"].min(), 4))
            put(f"{nm} 집단 n 최소/최대{'' if tn == '유지' else ' (3SD제외)'}", f"{int(t['n'].min())} / {int(t['n'].max())}")
    tag = "" if tn == "유지" else " (3SD제외)"
    put(f"전체 대출횟수 중앙값{tag}", x["대출횟수"].median())
    put(f"전체 대출횟수 왜도{tag}", round(x["대출횟수"].skew(), 4))
    put(f"[새] 전체 대출횟수 표준편차{tag}", round(x["대출횟수"].std(ddof=1), 4))
put("[새] 2005~2022 발행년 표준편차 최대/최소 비 (유지)",
    round((lambda t: t.max() / t.min())(d[d["발행년"] <= 2022].groupby("발행년")["대출횟수"].std()), 4))

# 그림: 처리마다 히스토그램(집단별 작은 그림)·박스플롯(전체, 0~50 확대)
for tn, x in TREAT.items():
    sfx = "" if tn == "유지" else "_3SD제외"
    lab = "유지 28,000권" if tn == "유지" else f"평균±3SD 제외 {len(x):,}권"
    xmax = int(x["대출횟수"].max())
    for g, fn in [("발행년", "발행년별"), ("주제분류명", "주제분류명별")]:
        keys = sorted(x[g].unique())
        nc = 6 if g == "발행년" else 5
        nr = int(np.ceil(len(keys) / nc))
        fig, axs = plt.subplots(nr, nc, figsize=(3 * nc, 2.4 * nr), sharex=True, sharey=True)
        bins = np.arange(0, xmax + 11, 10) if tn == "유지" else np.arange(0, xmax + 2, 1)
        for ax, k in zip(axs.flat, keys):
            ax.hist(x.loc[x[g] == k, "대출횟수"], bins=bins, color="steelblue")
            ax.set_yscale("symlog")
            ax.set_title(f"{k} (n={int((x[g] == k).sum()):,})", fontsize=9)
        for ax in list(axs.flat)[len(keys):]:
            ax.axis("off")
        fig.suptitle(f"{g}별 대출횟수 히스토그램 — {lab} (구간 {int(bins[1] - bins[0])}회, 세로축 로그)")
        fig.supxlabel("대출횟수 (2023~2025년, 회)")
        fig.supylabel("권수")
        fig.tight_layout()
        fig.savefig(OUT / f"히스토그램_{fn}{sfx}.png", dpi=120)
        plt.close(fig)
        for zoom in [False, True]:
            fig, ax = plt.subplots(figsize=(13, 5))
            ax.boxplot([x.loc[x[g] == k, "대출횟수"] for k in keys], tick_labels=[str(k) for k in keys], flierprops={"markersize": 3})
            if zoom:
                ax.set_ylim(-1, 50)
            ax.set_title(f"{g}별 대출횟수 박스플롯 — {lab}{' (세로축 0~50회 확대)' if zoom else ''}")
            ax.set_xlabel(g)
            ax.set_ylabel("대출횟수 (회)")
            plt.setp(ax.get_xticklabels(), rotation=45)
            fig.tight_layout()
            fig.savefig(OUT / f"박스플롯_{fn}{'_0to50확대' if zoom else ''}{sfx}.png", dpi=120)
            plt.close(fig)

# ============================================================ 9. 산출물 ③ 정의 확인 — 자기 집단 평균 미만 (승인 8번 ①)
lt_rows = []
for c in CHOICES:
    s = TR[c]
    x = d.loc[s.index].assign(대출횟수=s)
    r = {"선택지": c, "권수": len(x)}
    both = None
    for g in ["발행년", "주제분류명"]:
        m = x["대출횟수"] < x.groupby(g)["대출횟수"].transform("mean")
        both = m if both is None else both & m
        r.update({f"{g}평균미만 권수": int(m.sum()), f"{g}평균미만 %": round(m.mean() * 100, 2),
                  f"{g}평균미만 대출횟수범위": f"{x.loc[m, '대출횟수'].min():g}~{x.loc[m, '대출횟수'].max():g}"})
        if c == "유지(기준)":
            save(pd.DataFrame({"n": x.groupby(g).size(), "집단평균": x.groupby(g)["대출횟수"].mean(),
                               "평균미만권수": m.groupby(x[g]).sum(), "평균미만비율%": m.groupby(x[g]).mean() * 100,
                               "평균미만_대출횟수최댓값": x[m].groupby(g)["대출횟수"].max()}).round(4),
                 f"평균미만_{'발행년' if g == '발행년' else '주제분류명'}별.csv")
            put(f"{g}평균 미만 책의 대출횟수 값별 권수", x.loc[m, "대출횟수"].value_counts().sort_index().to_dict())
            put(f"{g}평균 미만 책 중 2023 이후 구입 권수", int((m & x["후구입"]).sum()))
            put(f"2023 이후 구입분 중 {g}평균 미만 비율%", round(m[x["후구입"]].mean() * 100, 2))
    r.update({"둘다미만 권수": int(both.sum()), "둘다미만 %": round(both.mean() * 100, 2),
              "전체평균미만 %": round((x["대출횟수"] < x["대출횟수"].mean()).mean() * 100, 2)})
    lt_rows.append(r)
save(pd.DataFrame(lt_rows), "평균미만_권수.csv", index=False)

# ============================================================ 10. 점검값.csv 저장과 원래 값 비교
cur = pd.DataFrame(V, columns=["항목", "값"]).astype({"값": str})
save(cur, "점검값.csv", index=False)
old = pd.read_csv(OLD, encoding="utf-8-sig", dtype=str)
cmp_ = old.merge(cur, on="항목", how="outer", suffixes=("_원래", "_이번"), indicator=True)


def same(r):
    if r["_merge"] != "both":
        return "원래에 없음(새 항목)" if r["_merge"] == "right_only" else "이번에 없음"
    try:
        return "같음" if float(r["값_원래"]) == float(r["값_이번"]) else "다름"
    except ValueError:
        return "같음" if r["값_원래"].replace(" ", "") == r["값_이번"].replace(" ", "") else "다름"


cmp_["비교"] = cmp_.apply(same, axis=1)
save(cmp_.drop(columns="_merge"), "원래값_비교.csv", index=False)
print(cmp_["비교"].value_counts().to_dict())
print(cmp_.loc[cmp_["비교"].isin(["다름", "이번에 없음"]), ["항목", "값_원래", "값_이번", "비교"]].to_string())

# 그 밖의 CSV 비교 (같은 이름 파일을 숫자 오차 1e-9로 대조)
od = OLD.parent
for f in sorted(OUT.glob("*.csv")):
    if f.name in ("점검값.csv", "원래값_비교.csv") or not (od / f.name).exists():
        continue
    o, n = pd.read_csv(od / f.name, encoding="utf-8-sig"), pd.read_csv(f, encoding="utf-8-sig")
    o.columns, n.columns = [str(c) for c in o.columns], [str(c) for c in n.columns]
    if o.shape != n.shape or list(o.columns) != list(n.columns):
        print(f"[CSV] {f.name}: 모양/열 다름 원래 {o.shape} {list(o.columns)[:4]}.. / 이번 {n.shape} {list(n.columns)[:4]}..")
        continue
    diff = [c for c in o.columns if not (o[c].astype(str) == n[c].astype(str)).all()
            and not (pd.api.types.is_numeric_dtype(o[c]) and pd.api.types.is_numeric_dtype(n[c])
                     and np.allclose(o[c].fillna(-1e9), n[c].fillna(-1e9), atol=1e-9))]
    print(f"[CSV] {f.name}: {'같음' if not diff else '다른 열 ' + str(diff)}")

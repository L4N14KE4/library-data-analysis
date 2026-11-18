# 2~3단계 점검 — 질문 4: 주제별 대출횟수·이상치·구입가격과 예산 배분 근거
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_주제별_예산근거/점검/점검.py
# 원자료는 읽기만 한다. 아무것도 처리(삭제·대체)하지 않고, 선택지별 결과만 계산한다. 난수 없음.
import sys
from pathlib import Path

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261117_주제별_예산근거/점검")
# 코드북 1-1절 '삭제' 7열은 쓰지 않는다. 사용 8열만 고른다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
K7 = [c for c in COLS if c != "자료ID"]
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절
CUT = pd.Timestamp("2022-12-31")  # 승인기록 1번
V = []  # 점검값.csv (항목, 값)


def put(k, v):
    V.append((k, v))
    print(f"{k}: {v}")


def stop(msg):
    sys.exit(f"멈춤: {msg}")


# ---------------------------------------------------------------- 0. 읽기 (변환 실패는 멈춤)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[COLS].copy()
for c in ["발행년", "구입가격", "대출횟수"]:
    bad = ~d[c].str.fullmatch(r"\d+")
    if bad.any():
        stop(f"{c}: 숫자로만 된 값이 아닌 칸 {int(bad.sum())}개")
    d[c] = d[c].astype("int64")
d["구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
if d["구입일"].isna().any():
    stop("구입일 날짜 변환 실패")

# ---------------------------------------------------------------- 1. 대상·코드북 대조
put("1 원본 행 수", len(raw))
put("1 원본 열 수", raw.shape[1])
put("1 사용 열 수", len(COLS))
t = d[d["구입일"] <= CUT].copy()  # 대상 (공통 정제로 지운 행 없음)
put("1 대상(구입일<=2022-12-31) 권수", len(t))
put("1 구입일 = 2022-12-31 당일 권수", int((d["구입일"] == CUT).sum()))
put("1 대상 구입일 범위", f"{t['구입일'].min().date()} ~ {t['구입일'].max().date()}")

cb = []
for name, df in [("전체 28,000", d), ("대상", t)]:
    cb += [
        [name, "주제분류명", "값 목록", "10개: " + ", ".join(SUBJ),
         f"{df['주제분류명'].nunique()}개, 목록 밖 값 {sorted(set(df['주제분류명']) - set(SUBJ))}, 빈칸 {int((df['주제분류명'] == '').sum())}"],
        [name, "대출횟수", "0 ~ 527, 결측 0", "",
         f"{df['대출횟수'].min()} ~ {df['대출횟수'].max()}, 빈칸 0 (0단계에서 숫자 아닌 칸 0 확인)"],
        [name, "구입가격", "6000 ~ 38000, 결측 0", "",
         f"{df['구입가격'].min()} ~ {df['구입가격'].max()}, 0원 {int((df['구입가격'] == 0).sum())}, "
         f"9로만 된 값 {int(df['구입가격'].isin([9, 99, 999, 9999, 99999]).sum())}, 500원 단위 아닌 값 {int((df['구입가격'] % 500 != 0).sum())}"],
        [name, "구입일", "2005-01-01 ~ 2025-12-27, 결측 0", "",
         f"{df['구입일'].min().date()} ~ {df['구입일'].max().date()}, 변환 실패 0"],
    ]
cb = pd.DataFrame(cb, columns=["범위", "변수", "코드북 2절 표기", "코드북 값 목록", "데이터 실제"])
cb.to_csv(OUT / "코드북대조.csv", index=False, encoding="utf-8-sig")
print(cb.to_string(index=False))
# KDC와 주제분류명이 1:1로 짝지어지는지 (주제분류명의 뜻을 확인하는 보조 점검)
pair = d.groupby("주제분류명")["KDC"].unique().apply(lambda a: ",".join(sorted(a)))
put("1 주제분류명별 KDC 값", pair.to_dict())
put("1 KDC 하나에 주제분류명 여러 개인 KDC 수", int((d.groupby("KDC")["주제분류명"].nunique() > 1).sum()))

# ---------------------------------------------------------------- 공통 계산: 주제별 표


def subj_table(df, loan="대출횟수", price="구입가격"):
    """주제별 권수·대출·구입가격 요약. 모든 순위 열: 1 = 값이 가장 큼, 동률은 같은 순위(min)."""
    g = df.groupby("주제분류명")
    s = pd.DataFrame({
        "권수": g.size(),
        "대출합": g[loan].sum(),
        "대출평균": g[loan].mean(),
        "대출중앙값": g[loan].median(),
        "가격합": g[price].sum(),
        "가격평균": g[price].mean(),
        "가격중앙값": g[price].median(),
    }).reindex(SUBJ)
    s["권수비중%"] = s["권수"] / s["권수"].sum() * 100
    s["대출비중%"] = s["대출합"] / s["대출합"].sum() * 100
    s["가격합비중%"] = s["가격합"] / s["가격합"].sum() * 100
    for c in ["권수비중%", "대출비중%", "가격합비중%", "대출평균", "가격평균", "가격중앙값"]:
        s[f"{c}_순위"] = s[c].rank(ascending=False, method="min").astype(int)
    return s


def long(s, opt):
    return s.reset_index().assign(선택지=opt)


# ---------------------------------------------------------------- 2a. 대출횟수 평균±3SD (승인 2번 기준)
print("\n[2a] 대출횟수 평균±3SD")
x = t["대출횟수"].astype(float)
mu, sd = x.mean(), x.std(ddof=1)  # 질문 3과 같은 표본 표준편차
lo, hi = mu - 3 * sd, mu + 3 * sd
out = (x < lo) | (x > hi)
put("2a 대상 대출횟수 평균", round(mu, 4))
put("2a 대상 대출횟수 표준편차(ddof=1)", round(sd, 4))
put("2a 경계", f"{lo:.4f} ~ {hi:.4f}")
put("2a 경계 밖 권수 (아래/위)", f"{int(out.sum())} ({int((x < lo).sum())}/{int((x > hi).sum())})")
put("2a 경계 밖 최소 대출횟수", int(x[out].min()))
put("2a 경계 밖 대출 합 / 대상 대출 합", f"{int(x[out].sum())} / {int(x.sum())} ({x[out].sum() / x.sum() * 100:.2f}%)")
oc = pd.DataFrame({"대상 권수": t.groupby("주제분류명").size(),
                   "이상치 권수": t[out].groupby("주제분류명").size(),
                   "이상치 대출합": t[out].groupby("주제분류명")["대출횟수"].sum()}).reindex(SUBJ).fillna(0).astype(int)
oc["대상 권수 비중%"] = (oc["대상 권수"] / oc["대상 권수"].sum() * 100).round(2)
oc["이상치 중 비중%"] = (oc["이상치 권수"] / oc["이상치 권수"].sum() * 100).round(2)
oc["주제 안 이상치 비율%"] = (oc["이상치 권수"] / oc["대상 권수"] * 100).round(2)
oc.to_csv(OUT / "대출이상치_주제별.csv", encoding="utf-8-sig")
print(oc.to_string())

t["_대출_대체"] = x.clip(lo, hi)  # 대체: 경계 밖 값을 경계값(소수)으로 바꿈, 권수 그대로
LOAN_OPTS = {
    "유지": subj_table(t),
    f"제외 (평균±3SD 밖 {int(out.sum())}권 뺌)": subj_table(t[~out]),
    f"대체 (경계값 {hi:.4f}회로 바꿈)": subj_table(t, loan="_대출_대체"),
}
la = pd.concat([long(s, k) for k, s in LOAN_OPTS.items()])
la_cols = ["선택지", "주제분류명", "권수", "권수비중%", "대출합", "대출비중%", "대출비중%_순위",
           "대출평균", "대출평균_순위", "대출중앙값"]
la[la_cols].round(4).to_csv(OUT / "선택지별_대출비중.csv", index=False, encoding="utf-8-sig")
print(la[la_cols].round(2).to_string(index=False))
base = LOAN_OPTS["유지"]
for k, s in LOAN_OPTS.items():
    put(f"2a [{k}] 대출비중 순위가 유지와 다른 주제 수",
        int((s["대출비중%_순위"] != base["대출비중%_순위"]).sum()))
    put(f"2a [{k}] 대출평균 순위가 유지와 다른 주제 수",
        int((s["대출평균_순위"] != base["대출평균_순위"]).sum()))
    put(f"2a [{k}] 대출비중 최대 변화(%p)", round((s["대출비중%"] - base["대출비중%"]).abs().max(), 2))
    put(f"2a [{k}] 대출비중과 권수비중 순위가 다른 주제 수",
        int((s["대출비중%_순위"] != s["권수비중%_순위"]).sum()))

# ---------------------------------------------------------------- 2b. 구입가격 이상치 후보 (판정하지 않음)
print("\n[2b] 구입가격 이상치 후보")
CANDS = {}
for basis, df in [("28,000권 기준(질문 5와 같음)", d), ("대상 기준", t)]:
    p = df["구입가격"].astype(float)
    q1, q3 = p.quantile(0.25), p.quantile(0.75)  # pandas 기본(선형 보간)
    m, s_ = p.mean(), p.std(ddof=1)
    put(f"2b {basis} Q1/Q3/IQR", f"{q1}/{q3}/{q3 - q1}")
    put(f"2b {basis} 평균/표준편차", f"{m:.2f}/{s_:.2f}")
    CANDS[f"IQR 1.5배, {basis}"] = (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1))
    CANDS[f"IQR 3배, {basis}"] = (q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1))
    CANDS[f"평균±3SD, {basis}"] = (m - 3 * s_, m + 3 * s_)
pt = t["구입가격"].astype(float)
PRICE_OPTS = {"유지": base}
pc_rows = []
for name, (plo, phi) in CANDS.items():
    pm = (pt < plo) | (pt > phi)
    put(f"2b {name} 경계 / 대상 안 해당 권수", f"{plo:.2f} ~ {phi:.2f} / {int(pm.sum())}")
    pc_rows.append(t[pm].groupby("주제분류명").size().reindex(SUBJ).fillna(0).astype(int).rename(name))
    if pm.any():
        PRICE_OPTS[f"제외: {name} ({int(pm.sum())}권)"] = subj_table(t[~pm])
        PRICE_OPTS[f"대체: {name} 경계값 {phi:.2f}원"] = subj_table(t.assign(_p=pt.clip(plo, phi)), price="_p")
pd.concat(pc_rows, axis=1).to_csv(OUT / "구입가격이상치후보_주제별권수.csv", encoding="utf-8-sig")
pa = pd.concat([long(s, k) for k, s in PRICE_OPTS.items()])
pa_cols = ["선택지", "주제분류명", "권수", "가격합", "가격합비중%", "가격합비중%_순위",
           "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]
pa[pa_cols].round(4).to_csv(OUT / "선택지별_구입가격.csv", index=False, encoding="utf-8-sig")
print(pa[pa_cols].round(2).to_string(index=False))
for k, s in PRICE_OPTS.items():
    put(f"2b [{k}] 가격평균 최대 변화(원)", round((s["가격평균"] - base["가격평균"]).abs().max(), 2))
    put(f"2b [{k}] 가격중앙값 최대 변화(원)", round((s["가격중앙값"] - base["가격중앙값"]).abs().max(), 2))
    put(f"2b [{k}] 가격합비중 최대 변화(%p)", round((s["가격합비중%"] - base["가격합비중%"]).abs().max(), 2))
    put(f"2b [{k}] 가격평균 순위가 유지와 다른 주제 수", int((s["가격평균_순위"] != base["가격평균_순위"]).sum()))
    put(f"2b [{k}] 가격합비중 순위가 유지와 다른 주제 수", int((s["가격합비중%_순위"] != base["가격합비중%_순위"]).sum()))

# ---------------------------------------------------------------- 2c. 자료ID만 다른 쌍 (자료ID 뺀 7개 사용 열이 모두 같은 행)
print("\n[2c] 자료ID만 다른 쌍")
dup = t.duplicated(subset=K7, keep=False)  # 대상 안에서 본다 (짝이 대상 밖에 있을 수 없음: 구입일이 같은 열)
later = t.duplicated(subset=K7, keep="first")  # 묶음의 뒤 행 (원자료 자료ID 순)
put("2c 자료ID 자체 중복 행 수 (전체)", int(d["자료ID"].duplicated().sum()))
put("2c 대상 안 자료ID만 다른 행 수", int(dup.sum()))
put("2c 대상 안 묶음 수", t[dup].groupby(K7).ngroups)
put("2c 그중 대출횟수 합", int(t.loc[dup, "대출횟수"].sum()))
put("2c 그중 구입가격 합", int(t.loc[dup, "구입가격"].sum()))
put("2c 주제별 행 수", t[dup].groupby("주제분류명").size().to_dict())
t[dup].sort_values(K7 + ["자료ID"])[COLS].to_csv(OUT / "자료ID만다른행_대상.csv", index=False, encoding="utf-8-sig")
DUP_OPTS = {"유지": base, "한 권만 남김": subj_table(t[~later]), "모두 제외": subj_table(t[~dup])}
for k, s in DUP_OPTS.items():
    for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균", "가격중앙값"]:
        put(f"2c [{k}] {c} 최대 변화", round((s[c] - base[c]).abs().max(), 4))
    put(f"2c [{k}] 순위(권수·대출·가격합 비중, 가격평균)가 유지와 다른 주제 수",
        int(sum((s[f"{c}_순위"] != base[f"{c}_순위"]).sum() for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균"])))
pd.concat([long(s, k) for k, s in DUP_OPTS.items()]).round(4) \
    .to_csv(OUT / "선택지별_자료ID쌍.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 2d. 그 밖의 점검
print("\n[2d] 그 밖의 점검")
put("2d 대상 대출횟수 0 권수", int((t["대출횟수"] == 0).sum()))
z = (t.assign(_z=t["대출횟수"] == 0).groupby("주제분류명")["_z"].mean() * 100).reindex(SUBJ).round(2)
put("2d 주제별 대출 0 비율%", z.to_dict())
put("2d 주제별 대출중앙값 고유값", sorted(base["대출중앙값"].unique().tolist()))
put("2d 주제별 가격중앙값 고유값 수", base["가격중앙값"].nunique())
put("2d 주제별 가격 표준편차(ddof=1)", t.groupby("주제분류명")["구입가격"].std().round(2).to_dict())
# 순위 동률
for c in ["권수비중%", "대출비중%", "가격합비중%", "대출평균", "가격평균", "가격중앙값"]:
    put(f"2d [유지] {c} 순위 동률 주제 수", int(base[f"{c}_순위"].duplicated(keep=False).sum()))
# 구입가격은 구입 당시 단가: 구입연도별 평균(사실 확인만, 보정하지 않음)
py = t.groupby(t["구입일"].dt.year)["구입가격"].agg(["size", "mean", "median"]).round(1)
py.to_csv(OUT / "구입연도별_구입가격.csv", encoding="utf-8-sig")
put("2d 구입연도별 가격평균 최소~최대", f"{py['mean'].min()} ~ {py['mean'].max()}")

# ---------------------------------------------------------------- 3. 산출물 ⑤ 사전 자료 (유지 기준, 계산만)
print("\n[3] 사전 자료")
pre = base[["권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위",
            "가격합", "가격합비중%", "가격합비중%_순위", "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]]
tot = pd.DataFrame([{"권수": pre["권수"].sum(), "대출합": pre["대출합"].sum(), "가격합": pre["가격합"].sum(),
                     "가격평균": t["구입가격"].mean(), "가격중앙값": t["구입가격"].median()}], index=["대상 합계"])
pre = pd.concat([pre, tot])
pre.round(4).to_csv(OUT / "사전자료_주제별.csv", encoding="utf-8-sig")
print(pre.round(2).to_string())
for c in ["권수", "대출합", "가격합"]:
    if pre.loc[SUBJ, c].sum() != pre.loc["대상 합계", c]:
        stop(f"{c} 주제 합이 대상 합과 다름")

pd.DataFrame(V, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")
print("\n완료")

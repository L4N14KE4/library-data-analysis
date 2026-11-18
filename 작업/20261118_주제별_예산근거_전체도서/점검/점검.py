# 2~3단계 점검 — 질문 4 (전체 도서판): 주제별 대출횟수·이상치·구입가격과 예산 배분 근거
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261118_주제별_예산근거_전체도서/점검/점검.py
# 대상 = 원자료 28,000권 전부 (승인기록 1번). 원자료는 읽기만 한다.
# 아무것도 처리(삭제·대체)하지 않고, 선택지별 결과만 계산한다. 난수 없음.
# 이전 판(작업/20261117_주제별_예산근거_보관_구입일2022이하/점검/)과 같은 틀. 이전 판 파일은 읽기만 한다 (2d 대조).
import sys
from pathlib import Path

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261118_주제별_예산근거_전체도서/점검")
PREV = Path("작업/20261117_주제별_예산근거_보관_구입일2022이하/점검/사전자료_주제별.csv")  # 읽기만
# 코드북 1-1절 '삭제' 7열은 쓰지 않는다. 사용 8열만 고른다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
K7 = [c for c in COLS if c != "자료ID"]
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절
CUT = pd.Timestamp("2022-12-31")  # 2023년 이후 구입분을 가르는 날 (2d, 계산만)
V = []  # 점검값.csv (항목, 값)


def put(k, v):
    V.append((k, v))
    print(f"{k}: {v}")


def stop(msg):
    sys.exit(f"멈춤: {msg}")


def csv(df, name, index=True):
    df.to_csv(OUT / name, index=index, encoding="utf-8-sig")


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
d["_2023이후"] = d["구입일"] > CUT

# ---------------------------------------------------------------- 1. 대상·코드북 대조
put("1 원본 행 수", len(raw))
put("1 원본 열 수", raw.shape[1])
put("1 사용 열 수", len(COLS))
put("1 대상 권수 (28,000권 전부)", len(d))
put("1 대상 구입일 범위", f"{d['구입일'].min().date()} ~ {d['구입일'].max().date()}")
put("1 대상 발행년 범위", f"{d['발행년'].min()} ~ {d['발행년'].max()}")

cb = [
    ["주제분류명", "명목, 10개: " + ", ".join(SUBJ) + ", 결측 0",
     f"{d['주제분류명'].nunique()}개, 목록 밖 값 {sorted(set(d['주제분류명']) - set(SUBJ))}, 빈칸 {int((d['주제분류명'] == '').sum())}"],
    ["대출횟수", "비율, 0 ~ 527, 결측 0",
     f"{d['대출횟수'].min()} ~ {d['대출횟수'].max()}, 빈칸 0 (0단계에서 숫자 아닌 칸 0 확인)"],
    ["구입가격", "비율, 6000 ~ 38000, 결측 0",
     f"{d['구입가격'].min()} ~ {d['구입가격'].max()}, 0원 {int((d['구입가격'] == 0).sum())}, "
     f"9로만 된 값 {int(d['구입가격'].isin([9, 99, 999, 9999, 99999]).sum())}, 500원 단위 아닌 값 {int((d['구입가격'] % 500 != 0).sum())}"],
    ["구입일", "등간, 2005-01-01 ~ 2025-12-27, 결측 0",
     f"{d['구입일'].min().date()} ~ {d['구입일'].max().date()}, 변환 실패 0"],
]
cb = pd.DataFrame(cb, columns=["변수", "코드북 2절 표기", "데이터 실제 (28,000권)"])
csv(cb, "코드북대조.csv", index=False)
print(cb.to_string(index=False))
pair = d.groupby("주제분류명")["KDC"].unique().apply(lambda a: ",".join(sorted(a)))
put("1 주제분류명별 KDC 값", pair.to_dict())
put("1 KDC 하나에 주제분류명 여러 개인 KDC 수", int((d.groupby("KDC")["주제분류명"].nunique() > 1).sum()))

# ---------------------------------------------------------------- 공통 계산: 주제별 표


def subj_table(df, loan="대출횟수", price="구입가격"):
    """주제별 권수·대출·구입가격 요약. 모든 순위 열: 1 = 값이 가장 큼, 동률은 같은 순위(min).
    중앙값은 pandas 기본(짝수 개면 가운데 두 값 평균) — 점검용. 본 분석의 중앙값 규칙은 계산명세에서 정한다."""
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


base = subj_table(d)

# ---------------------------------------------------------------- 2a. 대출횟수 평균±3SD (승인 2번 기준, 28,000권)
print("\n[2a] 대출횟수 평균±3SD")
x = d["대출횟수"].astype(float)
mu, sd = x.mean(), x.std(ddof=1)  # 질문 3 전체 도서판과 같은 표본 표준편차
lo, hi = mu - 3 * sd, mu + 3 * sd
out = (x < lo) | (x > hi)
put("2a 대상 대출횟수 평균", round(mu, 4))
put("2a 대상 대출횟수 표준편차(ddof=1)", round(sd, 4))
put("2a 경계", f"{lo:.4f} ~ {hi:.4f}")
put("2a 경계 밖 권수 (아래/위)", f"{int(out.sum())} ({int((x < lo).sum())}/{int((x > hi).sum())})")
put("2a 경계 밖 최소 대출횟수", int(x[out].min()))
put("2a 경계 밖 대출 합 / 대상 대출 합", f"{int(x[out].sum())} / {int(x.sum())} ({x[out].sum() / x.sum() * 100:.2f}%)")
put("2a 경계 밖 중 2023년 이후 구입 권수", int((out & d["_2023이후"]).sum()))
oc = pd.DataFrame({"대상 권수": d.groupby("주제분류명").size(),
                   "이상치 권수": d[out].groupby("주제분류명").size(),
                   "이상치 대출합": d[out].groupby("주제분류명")["대출횟수"].sum(),
                   "주제 대출합": d.groupby("주제분류명")["대출횟수"].sum()}).reindex(SUBJ).fillna(0).astype(int)
oc["대상 권수 비중%"] = (oc["대상 권수"] / oc["대상 권수"].sum() * 100).round(2)
oc["이상치 중 비중%"] = (oc["이상치 권수"] / oc["이상치 권수"].sum() * 100).round(2)
oc["주제 안 이상치 비율%"] = (oc["이상치 권수"] / oc["대상 권수"] * 100).round(2)
oc["주제 대출합 중 이상치 몫%"] = (oc["이상치 대출합"] / oc["주제 대출합"] * 100).round(2)
csv(oc, "대출이상치_주제별.csv")
print(oc.to_string())

d["_대출_대체"] = x.clip(lo, hi)  # 대체: 경계 밖 값을 경계값(소수)으로 바꿈, 권수 그대로
LOAN_OPTS = {
    "유지": base,
    f"제외 (평균±3SD 밖 {int(out.sum())}권 뺌)": subj_table(d[~out]),
    f"대체 (경계값 {hi:.4f}회로 바꿈)": subj_table(d, loan="_대출_대체"),
}
la = pd.concat([long(s, k) for k, s in LOAN_OPTS.items()])
la_cols = ["선택지", "주제분류명", "권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위",
           "대출평균", "대출평균_순위", "대출중앙값"]
csv(la[la_cols].round(4), "선택지별_대출비중.csv", index=False)
print(la[la_cols].round(2).to_string(index=False))
for k, s in LOAN_OPTS.items():
    put(f"2a [{k}] 대출 합", round(s["대출합"].sum(), 4))
    put(f"2a [{k}] 대출비중 순위가 유지와 다른 주제 수",
        int((s["대출비중%_순위"] != base["대출비중%_순위"]).sum()))
    put(f"2a [{k}] 대출평균 순위가 유지와 다른 주제 수",
        int((s["대출평균_순위"] != base["대출평균_순위"]).sum()))
    put(f"2a [{k}] 대출비중 최대 변화(%p)", round((s["대출비중%"] - base["대출비중%"]).abs().max(), 2))
    put(f"2a [{k}] 대출비중 > 권수비중인 주제", [i for i in SUBJ if s.loc[i, "대출비중%"] > s.loc[i, "권수비중%"]])

# ---------------------------------------------------------------- 2b. 구입가격 이상치 후보 (판정하지 않음, 질문 5 '유지')
print("\n[2b] 구입가격 이상치 후보 (28,000권 기준 = 질문 5와 같음)")
p = d["구입가격"].astype(float)
q1, q3 = p.quantile(0.25), p.quantile(0.75)  # pandas 기본(선형 보간)
m, s_ = p.mean(), p.std(ddof=1)
put("2b Q1/Q3/IQR", f"{q1}/{q3}/{q3 - q1}")
put("2b 평균/표준편차", f"{m:.2f}/{s_:.2f}")
CANDS = {
    "IQR 1.5배": (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)),
    "IQR 3배": (q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1)),
    "평균±3SD": (m - 3 * s_, m + 3 * s_),
}
PRICE_OPTS = {"유지": base}
pc_rows = []
for name, (plo, phi) in CANDS.items():
    pm = (p < plo) | (p > phi)
    put(f"2b {name} 경계 / 해당 권수 (아래/위)", f"{plo:.2f} ~ {phi:.2f} / {int(pm.sum())} ({int((p < plo).sum())}/{int((p > phi).sum())})")
    put(f"2b {name} 해당 중 2023년 이후 구입 권수", int((pm & d["_2023이후"]).sum()))
    pc_rows.append(d[pm].groupby("주제분류명").size().reindex(SUBJ).fillna(0).astype(int).rename(name))
    if pm.any():
        PRICE_OPTS[f"제외: {name} ({int(pm.sum())}권)"] = subj_table(d[~pm])
        PRICE_OPTS[f"대체: {name} 경계값 {phi:.2f}원"] = subj_table(d.assign(_p=p.clip(plo, phi)), price="_p")
csv(pd.concat(pc_rows, axis=1), "구입가격이상치후보_주제별권수.csv")
pa = pd.concat([long(s, k) for k, s in PRICE_OPTS.items()])
pa_cols = ["선택지", "주제분류명", "권수", "가격합", "가격합비중%", "가격합비중%_순위",
           "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]
csv(pa[pa_cols].round(4), "선택지별_구입가격.csv", index=False)
print(pa[pa_cols].round(2).to_string(index=False))
for k, s in PRICE_OPTS.items():
    put(f"2b [{k}] 가격평균 최대 변화(원)", round((s["가격평균"] - base["가격평균"]).abs().max(), 2))
    put(f"2b [{k}] 가격중앙값 최대 변화(원)", round((s["가격중앙값"] - base["가격중앙값"]).abs().max(), 2))
    put(f"2b [{k}] 가격합비중 최대 변화(%p)", round((s["가격합비중%"] - base["가격합비중%"]).abs().max(), 2))
    put(f"2b [{k}] 가격평균 순위가 유지와 다른 주제 수", int((s["가격평균_순위"] != base["가격평균_순위"]).sum()))
    put(f"2b [{k}] 가격합비중 순위가 유지와 다른 주제 수", int((s["가격합비중%_순위"] != base["가격합비중%_순위"]).sum()))

# ---------------------------------------------------------------- 2c. 자료ID만 다른 쌍 (자료ID 뺀 7개 사용 열이 모두 같은 행)
print("\n[2c] 자료ID만 다른 쌍")
dup = d.duplicated(subset=K7, keep=False)
later = d.duplicated(subset=K7, keep="first")  # 묶음의 뒤 행 (원자료 자료ID 순)
put("2c 자료ID 자체 중복 행 수", int(d["자료ID"].duplicated().sum()))
put("2c 자료ID만 다른 행 수", int(dup.sum()))
put("2c 묶음 수", d[dup].groupby(K7).ngroups)
put("2c 묶음 크기 최대", int(d[dup].groupby(K7).size().max()))
put("2c 그중 대출횟수 합", int(d.loc[dup, "대출횟수"].sum()))
put("2c 그중 구입가격 합", int(d.loc[dup, "구입가격"].sum()))
put("2c 그중 2023년 이후 구입 행 수", int((dup & d["_2023이후"]).sum()))
put("2c 주제별 행 수", d[dup].groupby("주제분류명").size().to_dict())
csv(d[dup].sort_values(K7 + ["자료ID"])[COLS], "자료ID만다른행.csv", index=False)
DUP_OPTS = {"유지": base, "한 권만 남김": subj_table(d[~later]), "모두 제외": subj_table(d[~dup])}
for k, s in DUP_OPTS.items():
    put(f"2c [{k}] 권수", int(s["권수"].sum()))
    for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균", "가격중앙값"]:
        put(f"2c [{k}] {c} 최대 변화", round((s[c] - base[c]).abs().max(), 4))
    for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균"]:
        put(f"2c [{k}] {c} 순위가 유지와 다른 주제 수", int((s[f"{c}_순위"] != base[f"{c}_순위"]).sum()))
csv(pd.concat([long(s, k) for k, s in DUP_OPTS.items()]).round(4), "선택지별_자료ID쌍.csv", index=False)

# ---------------------------------------------------------------- 2d. 2023년 이후 구입분의 영향 (계산만, 판단 없음)
print("\n[2d] 2023년 이후 구입분")
old = d[~d["_2023이후"]]
put("2d 2023년 이후 구입 권수 / 비율%", f"{int(d['_2023이후'].sum())} / {d['_2023이후'].mean() * 100:.2f}")
put("2d 2023년 이후 구입분 대출 합 / 전체 대출 합 중 %",
    f"{int(d.loc[d['_2023이후'], '대출횟수'].sum())} / {d.loc[d['_2023이후'], '대출횟수'].sum() / d['대출횟수'].sum() * 100:.2f}")
put("2d 2023년 이후 / 2022 이하 구입분 대출 평균",
    f"{d.loc[d['_2023이후'], '대출횟수'].mean():.4f} / {old['대출횟수'].mean():.4f}")
put("2d 2023년 이후 / 2022 이하 구입분 대출 0 비율%",
    f"{(d.loc[d['_2023이후'], '대출횟수'] == 0).mean() * 100:.2f} / {(old['대출횟수'] == 0).mean() * 100:.2f}")
put("2d 구입연도별 권수 (2023·2024·2025)", d["구입일"].dt.year.value_counts().reindex([2023, 2024, 2025]).to_dict())
g = d.groupby("주제분류명")
old_s = subj_table(old)
im = pd.DataFrame({
    "권수": base["권수"],
    "2023이후 구입 권수": g["_2023이후"].sum().reindex(SUBJ).astype(int),
    "2023이후 구입 비율%": (g["_2023이후"].mean() * 100).reindex(SUBJ),
    "2023이후 구입분 대출합": d[d["_2023이후"]].groupby("주제분류명")["대출횟수"].sum().reindex(SUBJ).fillna(0).astype(int),
    "전체 권수비중%": base["권수비중%"], "2022이하 권수비중%": old_s["권수비중%"],
    "전체 권수비중 순위": base["권수비중%_순위"], "2022이하 권수비중 순위": old_s["권수비중%_순위"],
    "전체 대출비중%": base["대출비중%"], "2022이하 대출비중%": old_s["대출비중%"],
    "전체 대출비중 순위": base["대출비중%_순위"], "2022이하 대출비중 순위": old_s["대출비중%_순위"],
    "전체 가격합비중%": base["가격합비중%"], "2022이하 가격합비중%": old_s["가격합비중%"],
    "전체 가격평균": base["가격평균"], "2022이하 가격평균": old_s["가격평균"],
})
im["주제 대출합 중 2023이후 구입분 몫%"] = im["2023이후 구입분 대출합"] / base["대출합"] * 100
csv(im.round(4), "구입2023이후_영향_주제별.csv")
print(im.round(2).to_string())
put("2d 대출비중 순위가 전체와 2022이하에서 다른 주제 수", int((im["전체 대출비중 순위"] != im["2022이하 대출비중 순위"]).sum()))
put("2d 권수비중 순위가 전체와 2022이하에서 다른 주제 수", int((im["전체 권수비중 순위"] != im["2022이하 권수비중 순위"]).sum()))
put("2d 대출비중 차이 최대(%p, 전체 − 2022이하)", round((im["전체 대출비중%"] - im["2022이하 대출비중%"]).abs().max(), 2))
put("2d 권수비중 차이 최대(%p, 전체 − 2022이하)", round((im["전체 권수비중%"] - im["2022이하 권수비중%"]).abs().max(), 2))
# 2022 이하 값이 이전 판(별도 검증) 점검 값과 같은지 대조 (다르면 멈춤)
prev = pd.read_csv(PREV, encoding="utf-8-sig", index_col=0).reindex(SUBJ)
for c in ["권수", "대출합", "가격합"]:
    if not (prev[c].astype(int).values == old_s[c].astype(int).values).all():
        stop(f"2022 이하 {c}가 이전 판 점검 값과 다름")
put("2d 2022이하 권수·대출합·가격합이 이전 판 사전자료_주제별.csv와 같은가", "같음")

# ---------------------------------------------------------------- 2e. 그 밖의 점검
print("\n[2e] 그 밖의 점검")
put("2e 대출횟수 0 권수 / 비율%", f"{int((d['대출횟수'] == 0).sum())} / {(d['대출횟수'] == 0).mean() * 100:.2f}")
z = (d.assign(_z=d["대출횟수"] == 0).groupby("주제분류명")["_z"].mean() * 100).reindex(SUBJ).round(2)
put("2e 주제별 대출 0 비율%", z.to_dict())
put("2e 주제별 대출중앙값 고유값", sorted(base["대출중앙값"].unique().tolist()))
put("2e 주제별 가격중앙값 고유값", sorted(base["가격중앙값"].unique().tolist()))
put("2e 주제별 가격 표준편차(ddof=1)", g["구입가격"].std().reindex(SUBJ).round(2).to_dict())
put("2e 주제별 가격평균 최소~최대", f"{base['가격평균'].min():.2f} ~ {base['가격평균'].max():.2f}")
for c in ["권수비중%", "대출비중%", "가격합비중%", "대출평균", "가격평균", "가격중앙값"]:
    put(f"2e [유지] {c} 순위 동률 주제 수", int(base[f"{c}_순위"].duplicated(keep=False).sum()))
put("2e [유지] 대출비중과 권수비중 순위가 다른 주제 수", int((base["대출비중%_순위"] != base["권수비중%_순위"]).sum()))
put("2e [유지] 가격합비중과 권수비중 순위가 다른 주제 수", int((base["가격합비중%_순위"] != base["권수비중%_순위"]).sum()))
py = d.groupby(d["구입일"].dt.year)["구입가격"].agg(["size", "mean", "median"]).round(1)
py.index.name = "구입연도"
csv(py, "구입연도별_구입가격.csv")
put("2e 구입연도별 가격평균 최소~최대", f"{py['mean'].min()} ~ {py['mean'].max()}")
put("2e 발행년 > 구입연도 권수", int((d["발행년"] > d["구입일"].dt.year).sum()))

# ---------------------------------------------------------------- 3. 산출물 ⑤ 사전 자료 (유지 기준, 계산만)
# 시나리오 식(대출 비중대로 등)을 이 대상으로 계산한 값은 만들지 않는다 (진행 담당 지시).
print("\n[3] 사전 자료")
pre = base[["권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위",
            "가격합", "가격합비중%", "가격합비중%_순위", "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]]
tot = pd.DataFrame([{"권수": pre["권수"].sum(), "권수비중%": 100.0, "대출합": pre["대출합"].sum(), "대출비중%": 100.0,
                     "가격합": pre["가격합"].sum(), "가격합비중%": 100.0,
                     "가격평균": d["구입가격"].mean(), "가격중앙값": d["구입가격"].median()}], index=["대상 합계"])
pre = pd.concat([pre, tot])
pre.index.name = "주제분류명"
csv(pre.round(4), "사전자료_주제별.csv")
print(pre.round(2).to_string())
for c in ["권수", "대출합", "가격합"]:
    if pre.loc[SUBJ, c].sum() != pre.loc["대상 합계", c]:
        stop(f"{c} 주제 합이 대상 합과 다름")
if pre.loc["대상 합계", "권수"] != 28000:
    stop("대상 권수가 28,000이 아님")

pd.DataFrame(V, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")
# CSV 칸 수 점검: 머리줄과 모든 행의 칸 수가 같은지
import csv as _csv  # noqa: E402
for f in sorted(OUT.glob("*.csv")):
    with open(f, encoding="utf-8-sig", newline="") as fh:
        n = {len(r) for r in _csv.reader(fh)}
    if len(n) != 1:
        stop(f"{f.name} 칸 수가 행마다 다름 {n}")
print("\n완료")

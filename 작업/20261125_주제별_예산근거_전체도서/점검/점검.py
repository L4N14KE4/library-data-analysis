# 2~3단계 점검 — 질문 4 다시 하기 (2026-11-25): 주제별 대출횟수·이상치·구입가격, 28,000권 전부
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/점검/점검.py
# 처음부터 새로 쓴 코드. 원자료는 읽기만 하고, 행을 지우거나 값을 바꾸지 않는다 (선택지별 값은 계산만).
# 쓰는 열은 코드북 1-1절 '삭제' 7열을 뺀 8열. 난수 없음.
# 점검값.csv 항목 이름은 원래 폴더(작업/20261118_주제별_예산근거_전체도서/점검/점검값.csv)와 같게 둔다.
import csv as csvmod
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261125_주제별_예산근거_전체도서/점검")
USE = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
KEY = USE[1:]  # 중복 판정 열 = 자료ID를 뺀 사용 7열
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절 값 목록
CUT = pd.Timestamp("2022-12-31")  # 이 날 뒤에 구입한 책 = '2023년 이후 구입분'
ITEMS = []


def put(k, v):
    ITEMS.append((k, v))
    print(k, "=", v)


def halt(msg):
    sys.exit("멈춤: " + msg)


def save(df, name, index=True):
    df.to_csv(OUT / name, index=index, encoding="utf-8-sig")


# ---------- 0. 읽기: 머리줄로 원본 열 수만 세고, 사용 8열만 문자로 읽는다
with open(SRC, encoding="utf-8-sig", newline="") as fh:
    header = next(csvmod.reader(fh))
r = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False, usecols=USE)[USE]
d = r.copy()
for c in ["발행년", "구입가격", "대출횟수"]:
    nonnum = ~d[c].str.fullmatch(r"[0-9]+")
    if nonnum.any():
        halt(f"{c} 숫자 아닌 칸 {int(nonnum.sum())}")
    d[c] = d[c].astype(np.int64)
d["구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
if d["구입일"].isna().any():
    halt("구입일 변환 실패")
blank_last = d["최근대출일"] == ""
d["최근대출일"] = pd.to_datetime(d["최근대출일"].where(~blank_last), format="%Y-%m-%d", errors="coerce")
if d.loc[~blank_last, "최근대출일"].isna().any():
    halt("최근대출일 변환 실패 (빈칸 아닌 칸)")
new = d["구입일"] > CUT

# ---------- 1. 행 수·기간·코드북 대조
put("1 원본 행 수", len(r))
put("1 원본 열 수", len(header))
put("1 사용 열 수", len(USE))
put("1 대상 권수 (28,000권 전부)", len(d))
put("1 대상 구입일 범위", f"{d['구입일'].min().date()} ~ {d['구입일'].max().date()}")
put("1 대상 발행년 범위", f"{d['발행년'].min()} ~ {d['발행년'].max()}")

nines = d["구입가격"].isin([9, 99, 999, 9999, 99999])
cb = pd.DataFrame([
    ["주제분류명", "명목, 10개: " + ", ".join(SUBJ) + ", 결측 0",
     f"{d['주제분류명'].nunique()}개, 목록 밖 값 {sorted(set(d['주제분류명']) - set(SUBJ))}, 빈칸 {int((d['주제분류명'] == '').sum())}"],
    ["대출횟수", "비율, 0 ~ 527, 결측 0",
     f"{d['대출횟수'].min()} ~ {d['대출횟수'].max()}, 빈칸 0 (0단계에서 숫자 아닌 칸 0 확인)"],
    ["구입가격", "비율, 6000 ~ 38000, 결측 0",
     f"{d['구입가격'].min()} ~ {d['구입가격'].max()}, 0원 {int((d['구입가격'] == 0).sum())}, 9로만 된 값 {int(nines.sum())}, "
     f"500원 단위 아닌 값 {int((d['구입가격'] % 500 != 0).sum())}"],
    ["구입일", "등간, 2005-01-01 ~ 2025-12-27, 결측 0",
     f"{d['구입일'].min().date()} ~ {d['구입일'].max().date()}, 변환 실패 0"],
], columns=["변수", "코드북 2절 표기", "데이터 실제 (28,000권)"])
save(cb, "코드북대조.csv", index=False)
put("1 주제분류명별 KDC 값", d.groupby("주제분류명")["KDC"].apply(lambda s: ",".join(sorted(s.unique()))).to_dict())
put("1 KDC 하나에 주제분류명 여러 개인 KDC 수", int((d.groupby("KDC")["주제분류명"].nunique() > 1).sum()))
# 원래 항목에 없던 추가 대조 (코드북 2절 나머지 4열)
put("1+ 자료ID 범위·형식", f"{d['자료ID'].min()} ~ {d['자료ID'].max()}, 'B'+6자리 아닌 값 {int((~d['자료ID'].str.fullmatch(r'B[0-9]{6}')).sum())}")
put("1+ KDC 고유값", sorted(d["KDC"].unique()))
put("1+ 최근대출일 빈칸 / 범위", f"{int(blank_last.sum())} / {d['최근대출일'].min().date()} ~ {d['최근대출일'].max().date()}")
put("1+ 사용 8열 빈칸 수 (최근대출일 제외)", int((r[USE[:-1]] == "").sum().sum()))
put("1+ 앞뒤 공백이 있는 칸 수 (사용 8열)", int(sum((r[c] != r[c].str.strip()).sum() for c in USE)))


# ---------- 주제별 요약 함수
def table(df, loan="대출횟수", price="구입가격"):
    """주제별 권수·대출·가격. 순위 1 = 가장 큼, 동률 같은 순위(min).
    중앙값은 pandas 기본(짝수 개면 가운데 두 값 평균) — 점검용."""
    g = df.groupby("주제분류명")
    t = pd.DataFrame({"권수": g.size(), "대출합": g[loan].sum(), "대출평균": g[loan].mean(), "대출중앙값": g[loan].median(),
                      "가격합": g[price].sum(), "가격평균": g[price].mean(), "가격중앙값": g[price].median()}).reindex(SUBJ)
    for a, b in [("권수비중%", "권수"), ("대출비중%", "대출합"), ("가격합비중%", "가격합")]:
        t[a] = t[b] / t[b].sum() * 100
    for c in ["권수비중%", "대출비중%", "가격합비중%", "대출평균", "가격평균", "가격중앙값"]:
        t[c + "_순위"] = t[c].rank(ascending=False, method="min").astype(int)
    return t


def maxdiff(a, b, c):
    return (a[c] - b[c]).abs().max()


def rankdiff(a, b, c):
    return int((a[c + "_순위"] != b[c + "_순위"]).sum())


base = table(d)

# ---------- 2a. 대출횟수 평균±3SD (승인 2번 기준)
L = d["대출횟수"].astype(float)
mu, sd = L.mean(), L.std(ddof=1)
lo, hi = mu - 3 * sd, mu + 3 * sd
out = (L < lo) | (L > hi)
put("2a 대상 대출횟수 평균", round(mu, 4))
put("2a 대상 대출횟수 표준편차(ddof=1)", round(sd, 4))
put("2a 경계", f"{lo:.4f} ~ {hi:.4f}")
put("2a 경계 밖 권수 (아래/위)", f"{int(out.sum())} ({int((L < lo).sum())}/{int((L > hi).sum())})")
put("2a 경계 밖 최소 대출횟수", int(L[out].min()))
put("2a 경계 밖 대출 합 / 대상 대출 합", f"{int(L[out].sum())} / {int(L.sum())} ({L[out].sum() / L.sum() * 100:.2f}%)")
put("2a 경계 밖 중 2023년 이후 구입 권수", int((out & new).sum()))
og = d[out].groupby("주제분류명")
oc = pd.DataFrame({"대상 권수": base["권수"], "이상치 권수": og.size(), "이상치 대출합": og["대출횟수"].sum(),
                   "주제 대출합": base["대출합"]}).reindex(SUBJ).fillna(0).astype(int)
oc["대상 권수 비중%"] = (oc["대상 권수"] / oc["대상 권수"].sum() * 100).round(2)
oc["이상치 중 비중%"] = (oc["이상치 권수"] / oc["이상치 권수"].sum() * 100).round(2)
oc["주제 안 이상치 비율%"] = (oc["이상치 권수"] / oc["대상 권수"] * 100).round(2)
oc["주제 대출합 중 이상치 몫%"] = (oc["이상치 대출합"] / oc["주제 대출합"] * 100).round(2)
save(oc, "대출이상치_주제별.csv")

loan_opts = {"유지": base,
             f"제외 (평균±3SD 밖 {int(out.sum())}권 뺌)": table(d[~out]),
             f"대체 (경계값 {hi:.4f}회로 바꿈)": table(d.assign(_L=L.clip(lo, hi)), loan="_L")}
cols = ["선택지", "주제분류명", "권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위",
        "대출평균", "대출평균_순위", "대출중앙값"]
save(pd.concat([t.reset_index().assign(선택지=k) for k, t in loan_opts.items()])[cols].round(4), "선택지별_대출비중.csv", index=False)
for k, t in loan_opts.items():
    put(f"2a [{k}] 대출 합", round(t["대출합"].sum(), 4))
    put(f"2a [{k}] 대출비중 순위가 유지와 다른 주제 수", rankdiff(t, base, "대출비중%"))
    put(f"2a [{k}] 대출평균 순위가 유지와 다른 주제 수", rankdiff(t, base, "대출평균"))
    put(f"2a [{k}] 대출비중 최대 변화(%p)", round(maxdiff(t, base, "대출비중%"), 2))
    put(f"2a [{k}] 대출비중 > 권수비중인 주제", [s for s in SUBJ if t.loc[s, "대출비중%"] > t.loc[s, "권수비중%"]])

# ---------- 2b. 구입가격 이상치 후보 (코드북 기준 없음: 후보 기준별 계산만)
P = d["구입가격"].astype(float)
q1, q3 = P.quantile(0.25), P.quantile(0.75)
pm_, ps_ = P.mean(), P.std(ddof=1)
put("2b Q1/Q3/IQR", f"{q1}/{q3}/{q3 - q1}")
put("2b 평균/표준편차", f"{pm_:.2f}/{ps_:.2f}")
bounds = {"IQR 1.5배": (q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)),
          "IQR 3배": (q1 - 3 * (q3 - q1), q3 + 3 * (q3 - q1)),
          "평균±3SD": (pm_ - 3 * ps_, pm_ + 3 * ps_)}
price_opts = {"유지": base}
cand = {}
for nm, (a, b) in bounds.items():
    m = (P < a) | (P > b)
    put(f"2b {nm} 경계 / 해당 권수 (아래/위)", f"{a:.2f} ~ {b:.2f} / {int(m.sum())} ({int((P < a).sum())}/{int((P > b).sum())})")
    put(f"2b {nm} 해당 중 2023년 이후 구입 권수", int((m & new).sum()))
    cand[nm] = d[m].groupby("주제분류명").size().reindex(SUBJ).fillna(0).astype(int)
    if m.any():
        price_opts[f"제외: {nm} ({int(m.sum())}권)"] = table(d[~m])
        price_opts[f"대체: {nm} 경계값 {b:.2f}원"] = table(d.assign(_P=P.clip(a, b)), price="_P")
save(pd.DataFrame(cand).rename_axis("주제분류명"), "구입가격이상치후보_주제별권수.csv")
cols = ["선택지", "주제분류명", "권수", "가격합", "가격합비중%", "가격합비중%_순위", "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]
save(pd.concat([t.reset_index().assign(선택지=k) for k, t in price_opts.items()])[cols].round(4), "선택지별_구입가격.csv", index=False)
for k, t in price_opts.items():
    put(f"2b [{k}] 가격평균 최대 변화(원)", round(maxdiff(t, base, "가격평균"), 2))
    put(f"2b [{k}] 가격중앙값 최대 변화(원)", round(maxdiff(t, base, "가격중앙값"), 2))
    put(f"2b [{k}] 가격합비중 최대 변화(%p)", round(maxdiff(t, base, "가격합비중%"), 2))
    put(f"2b [{k}] 가격평균 순위가 유지와 다른 주제 수", rankdiff(t, base, "가격평균"))
    put(f"2b [{k}] 가격합비중 순위가 유지와 다른 주제 수", rankdiff(t, base, "가격합비중%"))

# ---------- 2c. 중복: 자료ID 기준, 그리고 자료ID를 뺀 사용 7열 기준
same = d.duplicated(KEY, keep=False)
second = d.duplicated(KEY, keep="first")
put("2c 자료ID 자체 중복 행 수", int(d["자료ID"].duplicated().sum()))
put("2c 자료ID만 다른 행 수", int(same.sum()))
put("2c 묶음 수", int(d[same].groupby(KEY, dropna=False).ngroups))
put("2c 묶음 크기 최대", int(d[same].groupby(KEY, dropna=False).size().max()))
put("2c 그중 대출횟수 합", int(d.loc[same, "대출횟수"].sum()))
put("2c 그중 구입가격 합", int(d.loc[same, "구입가격"].sum()))
put("2c 그중 2023년 이후 구입 행 수", int((same & new).sum()))
put("2c 주제별 행 수", d[same].groupby("주제분류명").size().to_dict())
save(r[same.values].sort_values(KEY + ["자료ID"]), "자료ID만다른행.csv", index=False)
dup_opts = {"유지": base, "한 권만 남김": table(d[~second]), "모두 제외": table(d[~same])}
for k, t in dup_opts.items():
    put(f"2c [{k}] 권수", int(t["권수"].sum()))
    for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균", "가격중앙값"]:
        put(f"2c [{k}] {c} 최대 변화", round(maxdiff(t, base, c), 4))
    for c in ["권수비중%", "대출비중%", "가격합비중%", "가격평균"]:
        put(f"2c [{k}] {c} 순위가 유지와 다른 주제 수", rankdiff(t, base, c))
save(pd.concat([t.reset_index().assign(선택지=k) for k, t in dup_opts.items()]).round(4), "선택지별_자료ID쌍.csv", index=False)

# ---------- 2d. 2023년 이후 구입분 (계산만)
old = d[~new]
put("2d 2023년 이후 구입 권수 / 비율%", f"{int(new.sum())} / {new.mean() * 100:.2f}")
put("2d 2023년 이후 구입분 대출 합 / 전체 대출 합 중 %",
    f"{int(d.loc[new, '대출횟수'].sum())} / {d.loc[new, '대출횟수'].sum() / d['대출횟수'].sum() * 100:.2f}")
put("2d 2023년 이후 / 2022 이하 구입분 대출 평균", f"{d.loc[new, '대출횟수'].mean():.4f} / {old['대출횟수'].mean():.4f}")
put("2d 2023년 이후 / 2022 이하 구입분 대출 0 비율%",
    f"{(d.loc[new, '대출횟수'] == 0).mean() * 100:.2f} / {(old['대출횟수'] == 0).mean() * 100:.2f}")
put("2d 구입연도별 권수 (2023·2024·2025)", d["구입일"].dt.year.value_counts().reindex([2023, 2024, 2025]).to_dict())
ot = table(old)
ng = d[new].groupby("주제분류명")
im = pd.DataFrame({
    "권수": base["권수"],
    "2023이후 구입 권수": ng.size().reindex(SUBJ).fillna(0).astype(int),
    "2023이후 구입 비율%": ng.size().reindex(SUBJ) / base["권수"] * 100,
    "2023이후 구입분 대출합": ng["대출횟수"].sum().reindex(SUBJ).fillna(0).astype(int),
    "전체 권수비중%": base["권수비중%"], "2022이하 권수비중%": ot["권수비중%"],
    "전체 권수비중 순위": base["권수비중%_순위"], "2022이하 권수비중 순위": ot["권수비중%_순위"],
    "전체 대출비중%": base["대출비중%"], "2022이하 대출비중%": ot["대출비중%"],
    "전체 대출비중 순위": base["대출비중%_순위"], "2022이하 대출비중 순위": ot["대출비중%_순위"],
    "전체 가격합비중%": base["가격합비중%"], "2022이하 가격합비중%": ot["가격합비중%"],
    "전체 가격평균": base["가격평균"], "2022이하 가격평균": ot["가격평균"],
})
im["주제 대출합 중 2023이후 구입분 몫%"] = im["2023이후 구입분 대출합"] / base["대출합"] * 100
save(im.round(4), "구입2023이후_영향_주제별.csv")
put("2d 대출비중 순위가 전체와 2022이하에서 다른 주제 수", int((im["전체 대출비중 순위"] != im["2022이하 대출비중 순위"]).sum()))
put("2d 권수비중 순위가 전체와 2022이하에서 다른 주제 수", int((im["전체 권수비중 순위"] != im["2022이하 권수비중 순위"]).sum()))
put("2d 대출비중 차이 최대(%p, 전체 − 2022이하)", round((im["전체 대출비중%"] - im["2022이하 대출비중%"]).abs().max(), 2))
put("2d 권수비중 차이 최대(%p, 전체 − 2022이하)", round((im["전체 권수비중%"] - im["2022이하 권수비중%"]).abs().max(), 2))
# 원래 항목 '2d 2022이하 ... 이전 판 사전자료_주제별.csv와 같은가'는 만들지 않는다 (보관판 폴더를 쓰지 않음, 진행 담당 지시)
put("2d+ 2022이하 권수 / 대출합 / 가격합", f"{len(old)} / {int(old['대출횟수'].sum())} / {int(old['구입가격'].sum())}")

# ---------- 2e. 그 밖의 점검
z = d["대출횟수"] == 0
put("2e 대출횟수 0 권수 / 비율%", f"{int(z.sum())} / {z.mean() * 100:.2f}")
put("2e 주제별 대출 0 비율%", (z.groupby(d["주제분류명"]).mean() * 100).reindex(SUBJ).round(2).to_dict())
put("2e 주제별 대출중앙값 고유값", sorted(base["대출중앙값"].unique().tolist()))
put("2e 주제별 가격중앙값 고유값", sorted(base["가격중앙값"].unique().tolist()))
put("2e 주제별 가격 표준편차(ddof=1)", d.groupby("주제분류명")["구입가격"].std(ddof=1).reindex(SUBJ).round(2).to_dict())
put("2e 주제별 가격평균 최소~최대", f"{base['가격평균'].min():.2f} ~ {base['가격평균'].max():.2f}")
for c in ["권수비중%", "대출비중%", "가격합비중%", "대출평균", "가격평균", "가격중앙값"]:
    put(f"2e [유지] {c} 순위 동률 주제 수", int(base[c + "_순위"].duplicated(keep=False).sum()))
put("2e [유지] 대출비중과 권수비중 순위가 다른 주제 수", int((base["대출비중%_순위"] != base["권수비중%_순위"]).sum()))
put("2e [유지] 가격합비중과 권수비중 순위가 다른 주제 수", int((base["가격합비중%_순위"] != base["권수비중%_순위"]).sum()))
py = d.groupby(d["구입일"].dt.year.rename("구입연도"))["구입가격"].agg(["size", "mean", "median"]).round(1)
save(py, "구입연도별_구입가격.csv")
put("2e 구입연도별 가격평균 최소~최대", f"{py['mean'].min()} ~ {py['mean'].max()}")
put("2e 발행년 > 구입연도 권수", int((d["발행년"] > d["구입일"].dt.year).sum()))
# 원래 항목에 없던 논리 점검 (공통 정제 P4·P5와 같은 종류; 최근대출일은 이 질문에서 쓰지 않음)
has = ~blank_last
put("2e+ 대출횟수 0인데 최근대출일 있음 / 대출횟수 ≥1인데 최근대출일 빈칸",
    f"{int((z & has).sum())} / {int((~z & blank_last).sum())}")
put("2e+ 최근대출일 < 구입일 권수", int((d["최근대출일"] < d["구입일"]).sum()))
put("2e+ 최근대출일이 2023-01-01 이전 권수", int((d["최근대출일"] < pd.Timestamp("2023-01-01")).sum()))
put("2e+ 최근대출일 = 구입일 권수", int((d["최근대출일"] == d["구입일"]).sum()))
put("2e+ 2025년 구입분 중 대출 ≥1 권수 / 최대 대출횟수",
    f"{int(((d['구입일'].dt.year == 2025) & ~z).sum())} / {int(d.loc[d['구입일'].dt.year == 2025, '대출횟수'].max())}")

# ---------- 3. 주제별 근거 지표 (유지, 처리 전 값 — 4단계 ① 사전자료.py와 같은 형식)
pre = base[["권수", "권수비중%", "권수비중%_순위", "대출합", "대출비중%", "대출비중%_순위", "가격합", "가격합비중%",
            "가격합비중%_순위", "가격평균", "가격평균_순위", "가격중앙값", "가격중앙값_순위"]]
tot = pd.DataFrame([{"권수": len(d), "권수비중%": 100.0, "대출합": d["대출횟수"].sum(), "대출비중%": 100.0,
                     "가격합": d["구입가격"].sum(), "가격합비중%": 100.0,
                     "가격평균": d["구입가격"].mean(), "가격중앙값": d["구입가격"].median()}], index=["대상 합계"])
pre = pd.concat([pre, tot]).rename_axis("주제분류명")
for c in ["권수", "대출합", "가격합"]:
    if pre.loc[SUBJ, c].sum() != pre.loc["대상 합계", c]:
        halt(c + " 주제 합 ≠ 대상 합")
if len(d) != 28000:
    halt("대상 권수 ≠ 28,000")

pd.DataFrame(ITEMS, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")
for f in sorted(OUT.glob("*.csv")):
    with open(f, encoding="utf-8-sig", newline="") as fh:
        widths = {len(row) for row in csvmod.reader(fh)}
    if len(widths) != 1:
        halt(f"{f.name} 칸 수가 행마다 다름 {widths}")
print("완료")

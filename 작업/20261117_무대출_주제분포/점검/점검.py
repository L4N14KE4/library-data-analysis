# 2~3단계 점검 — 질문 1: 3년 무대출 장서의 주제별 분포
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_무대출_주제분포/점검/점검.py
# 원자료는 읽기만 한다. 아무것도 처리(삭제·대체)하지 않고, 선택지별 결과만 계산해 보고한다. 난수 없음.
from pathlib import Path

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261117_무대출_주제분포/점검")
# 코드북 1-1절 '삭제' 7열(서명·저자·출판사·자료구분·소장관·이용상태·장서연령)은 읽은 뒤 바로 뺀다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
K7 = [c for c in COLS if c != "자료ID"]
SUBJECTS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절
CUT = pd.Timestamp("2022-12-31")  # 승인기록 3번: 구입일 2022-12-31 이하
TOTAL = 28000                     # 질문.md: 전체 28,000권 대비

raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[COLS].copy()
d["_대출횟수"] = pd.to_numeric(d["대출횟수"], errors="coerce")
d["_구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
d["_최근대출일"] = pd.to_datetime(d["최근대출일"].replace("", None), format="%Y-%m-%d", errors="coerce")
rows = []  # 점검값.csv (항목, 값)


def put(k, v):
    rows.append((k, v))
    print(f"{k}: {v}")


# ---------------------------------------------------------------- 1. 공통 정제 적용 후 행 수
print("[1] 공통 정제 적용")
# 공통 정제 승인(20261116 승인기록 4·6~9·19번)은 모두 유지/처리 안 함이라 지우는 행이 없다.
put("1 원본 행 수", len(raw))
put("1 원본 열 수", raw.shape[1])
put("1 공통 정제 적용 후 행 수", len(d))
put("1 사용 열 수", len(COLS))

# ---------------------------------------------------------------- 2. 코드북 2절·5절 대조 (4개 변수 + KDC)
print("\n[2] 코드북 대조")
put("2 구입일 빈칸 수", int((d["구입일"] == "").sum()))
put("2 구입일 YYYY-MM-DD 형식 아님(날짜 변환 실패) 수", int(d["_구입일"].isna().sum()))
put("2 구입일 최솟값", d["_구입일"].min().date())
put("2 구입일 최댓값", d["_구입일"].max().date())
put("2 대출횟수 정수 변환 실패 수", int(d["_대출횟수"].isna().sum()))
put("2 대출횟수 소수점 있는 값 수", int((d["_대출횟수"] % 1 != 0).sum()))
put("2 대출횟수 최솟값", int(d["_대출횟수"].min()))
put("2 대출횟수 최댓값", int(d["_대출횟수"].max()))
put("2 최근대출일 빈칸 수", int((d["최근대출일"] == "").sum()))
put("2 최근대출일 값이 있는데 날짜 변환 실패 수", int(((d["최근대출일"] != "") & d["_최근대출일"].isna()).sum()))
put("2 최근대출일 최솟값(빈칸 제외)", d["_최근대출일"].min().date())
put("2 최근대출일 최댓값(빈칸 제외)", d["_최근대출일"].max().date())
put("2 주제분류명 빈칸 수", int((d["주제분류명"] == "").sum()))
put("2 주제분류명 고유값 수", d["주제분류명"].nunique())
put("2 주제분류명 코드북 10개 밖 값 수", int((~d["주제분류명"].isin(SUBJECTS)).sum()))
put("2 주제분류명 앞뒤 공백 있는 값 수", int((d["주제분류명"] != d["주제분류명"].str.strip()).sum()))
cb = pd.DataFrame([
    ["주제분류명", "값/범위", "기술과학, 문학, 사회과학, 언어, 역사, 예술, 자연과학, 종교, 철학, 총류",
     ", ".join(sorted(d["주제분류명"].unique()))],
    ["주제분류명", "결측 수", "0", str(int((d["주제분류명"] == "").sum()))],
    ["구입일", "값/범위", "2005-01-01 ~ 2025-12-27", f"{d['_구입일'].min().date()} ~ {d['_구입일'].max().date()}"],
    ["구입일", "결측 수", "0", str(int((d["구입일"] == "").sum()))],
    ["대출횟수", "값/범위", "0 ~ 527", f"{int(d['_대출횟수'].min())} ~ {int(d['_대출횟수'].max())}"],
    ["대출횟수", "결측 수", "0", str(int((d["대출횟수"] == "").sum()))],
    ["최근대출일", "값/범위", "(필드 값 없음) ~ 2025-12-30",
     f"{d['_최근대출일'].min().date()} ~ {d['_최근대출일'].max().date()} (빈칸 제외)"],
    ["최근대출일", "결측 표기·수", "빈칸, 14036", f"빈칸, {int((d['최근대출일'] == '').sum())}"],
    ["KDC", "값/범위", "0 ~ 900", ", ".join(sorted(d["KDC"].unique()))],
], columns=["변수", "코드북 칸", "코드북 표기", "데이터 실제"])
cb["같은가"] = [a == b for a, b in zip(cb["코드북 표기"], cb["데이터 실제"])]
cb.to_csv(OUT / "코드북대조_4변수.csv", index=False, encoding="utf-8-sig")
print(cb.to_string(index=False))

# ---------------------------------------------------------------- 3a. 구입일 경계
print("\n[3a] 구입일 경계")
put("3a 구입일 2022-12-31 이하 (대상 권수)", int((d["_구입일"] <= CUT).sum()))
put("3a 구입일 = 2022-12-31 당일", int((d["_구입일"] == CUT).sum()))
put("3a 구입일 = 2023-01-01 당일", int((d["_구입일"] == pd.Timestamp("2023-01-01")).sum()))
put("3a 구입일 2022-12-01 ~ 2022-12-31", int(d["_구입일"].between("2022-12-01", CUT).sum()))
put("3a 구입일 2022-12-31 당일 중 무대출", int(((d["_구입일"] == CUT) & (d["_대출횟수"] == 0)).sum()))
put("3a 구입일 2023-01-01 이후", int((d["_구입일"] > CUT).sum()))
put("3a 구입일 2023-01-01 이후 중 무대출 (대상 밖)", int(((d["_구입일"] > CUT) & (d["_대출횟수"] == 0)).sum()))
put("3a 구입일 2021-12-31 이하 (참고: 승인 3번에서 고르지 않은 기준)", int((d["_구입일"] <= "2021-12-31").sum()))

# ---------------------------------------------------------------- 3b. 대상 안 빈칸 = 대출횟수 0
print("\n[3b] 대상 안 최근대출일 빈칸 vs 대출횟수 0")
t = d[d["_구입일"] <= CUT]
blank, zero = t["최근대출일"] == "", t["_대출횟수"] == 0
put("3b 대상 안 빈칸이면서 0", int((blank & zero).sum()))
put("3b 대상 안 빈칸이면서 1 이상", int((blank & ~zero).sum()))
put("3b 대상 안 값 있으면서 0", int((~blank & zero).sum()))

# ---------------------------------------------------------------- 3c. 자료ID만 다른 16쌍
print("\n[3c] 자료ID만 다른 행")
dup_all = d.duplicated(subset=K7, keep=False)
put("3c 전체 자료ID만 다른 행 수", int(dup_all.sum()))
put("3c 전체 묶음 수", d[dup_all].groupby(K7).ngroups)
dup = d[dup_all].copy()
dup["_대상"] = dup["_구입일"] <= CUT
g = dup.groupby(K7)["_대상"].agg(["size", "all", "any"])
put("3c 묶음 크기 분포", g["size"].value_counts().to_dict())
put("3c 대상 안 묶음 수 (두 행 모두 구입일 2022-12-31 이하)", int(g["all"].sum()))
put("3c 대상 걸침 묶음 수 (한 행만 대상)", int((g["any"] & ~g["all"]).sum()))
put("3c 대상 안 행 수", int(dup["_대상"].sum()))
put("3c 대상 안 행 중 무대출", int((dup["_대상"] & (dup["_대출횟수"] == 0)).sum()))
dup.sort_values(K7 + ["자료ID"])[COLS + ["_대상"]].rename(columns={"_대상": "대상(구입일<=2022-12-31)"}) \
    .to_csv(OUT / "자료ID만다른행_대상표시.csv", index=False, encoding="utf-8-sig")
print(dup.groupby("주제분류명")["_대상"].sum().to_string())

# ---------------------------------------------------------------- 3d. 주제분류명 ↔ KDC
print("\n[3d] 주제분류명 x KDC")
ct = pd.crosstab(d["KDC"], d["주제분류명"])
ct.to_csv(OUT / "주제분류명_KDC_교차표.csv", encoding="utf-8-sig")
print(ct.to_string())
put("3d KDC 고유값 수", d["KDC"].nunique())
put("3d KDC마다 주제분류명 1개뿐인가", bool((d.groupby("KDC")["주제분류명"].nunique() == 1).all()))
put("3d 주제분류명마다 KDC 1개뿐인가", bool((d.groupby("주제분류명")["KDC"].nunique() == 1).all()))
put("3d 교차표에서 0이 아닌 칸 수", int((ct > 0).sum().sum()))

# ---------------------------------------------------------------- 4. 선택지별 핵심 수치
print("\n[4] 선택지별 핵심 수치")
first_of_pair = d.duplicated(subset=K7, keep="first")  # 쌍의 두 번째 행(자료ID 큰 쪽)만 True


def core(df, name):
    tg = df[df["_구입일"] <= CUT]
    nl = tg[tg["_대출횟수"] == 0]  # 무대출 = 대출횟수 0 (= 최근대출일 빈칸, 3b)
    s = nl["주제분류명"].value_counts().reindex(SUBJECTS, fill_value=0)
    rank = s.rank(method="min").astype(int)  # 무대출 권수 오름차순 순위 (같으면 같은 순위)
    order = " < ".join(s.sort_values(kind="stable").index)
    return {"선택지": name, "전체 행": len(df), "대상 권수": len(tg), "무대출 권수": len(nl),
            "무대출 ÷ 28,000 (%)": round(len(nl) / TOTAL * 100, 2), "(참고) 무대출 ÷ 대상 (%)": round(len(nl) / len(tg) * 100, 2),
            "주제 오름차순": order, **{f"{k} 무대출": int(v) for k, v in s.items()},
            **{f"{k} 순위": int(v) for k, v in rank.items()}}


opts = [
    core(d, "P6 유지 (공통 정제 결정 그대로)"),
    core(d[~dup_all], "P6 제외 (16쌍 32행 모두 뺌)"),
    core(d[~first_of_pair], "P6 한 권만 남김 (쌍마다 자료ID 앞쪽 1행)"),
    core(d[d["_구입일"] != CUT], "(참고) 경계: 2022-12-31 당일 구입 제외"),
]
res = pd.DataFrame(opts)
res.to_csv(OUT / "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
print(res.T.to_string())
base = res.iloc[0]
for i in range(1, len(res)):
    same = all(res.iloc[i][f"{k} 순위"] == base[f"{k} 순위"] for k in SUBJECTS)
    put(f"4 순위가 유지와 같은가: {res.iloc[i]['선택지']}", same)
# 순위 동률 확인 (유지 기준)
s0 = pd.Series({k: base[f"{k} 무대출"] for k in SUBJECTS}).sort_values()
put("4 유지 기준 무대출 권수 동률 있음", bool(s0.duplicated().any()))
put("4 유지 기준 이웃 순위 간 최소 차이(권)", int(s0.diff().min()))

pd.DataFrame(rows, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")

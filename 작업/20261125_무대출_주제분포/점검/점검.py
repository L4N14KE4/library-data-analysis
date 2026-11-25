# 질문 1 다시 하기 (2026-11-25) — 2~3단계 점검. 아무 행도 지우거나 바꾸지 않는다. 난수 없음.
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_무대출_주제분포/점검/점검.py
import html, re, zipfile
import pandas as pd

OUT = "작업/20261125_무대출_주제분포/점검/"
SRC = "P02_장서목록_대출횟수 original.csv"
DROP7 = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 '삭제'
CUT = pd.Timestamp("2022-12-31")  # 승인 3번: 구입일 2022-12-31 이하
TOTAL = 28000  # 질문.md: 전체 비율 분모
vals = []
def put(k, v): vals.append((k, v))

# ---- 1. 행·열 (원자료는 문자 그대로 읽어 빈칸을 빈칸으로 본다)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
put("1 원본 행 수", len(raw)); put("1 원본 열 수", raw.shape[1])
d = raw.drop(columns=DROP7)  # 공통 정제: 지운 행 없음
put("1 공통 정제 적용 후 행 수", len(d)); put("1 사용 열 수", d.shape[1])

# ---- 2. 변수별 값 점검 (질문에 쓰는 4변수)
buy = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
put("2 구입일 빈칸 수", (d["구입일"] == "").sum())
put("2 구입일 YYYY-MM-DD 형식 아님(날짜 변환 실패) 수", buy.isna().sum())
put("2 구입일 최솟값", buy.min().date()); put("2 구입일 최댓값", buy.max().date())
loan = pd.to_numeric(d["대출횟수"], errors="coerce")
put("2 대출횟수 정수 변환 실패 수", (~d["대출횟수"].str.fullmatch(r"-?\d+")).sum())
put("2 대출횟수 소수점 있는 값 수", d["대출횟수"].str.contains(r"\.").sum())
put("2 대출횟수 최솟값", int(loan.min())); put("2 대출횟수 최댓값", int(loan.max()))
blank = d["최근대출일"] == ""
rec = pd.to_datetime(d["최근대출일"].where(~blank), format="%Y-%m-%d", errors="coerce")
put("2 최근대출일 빈칸 수", blank.sum())
put("2 최근대출일 값이 있는데 날짜 변환 실패 수", (rec.isna() & ~blank).sum())
put("2 최근대출일 최솟값(빈칸 제외)", rec.min().date()); put("2 최근대출일 최댓값(빈칸 제외)", rec.max().date())
SUBJ10 = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]  # 코드북 2절
put("2 주제분류명 빈칸 수", (d["주제분류명"] == "").sum())
put("2 주제분류명 고유값 수", d["주제분류명"].nunique())
put("2 주제분류명 코드북 10개 밖 값 수", (~d["주제분류명"].isin(SUBJ10)).sum())
put("2 주제분류명 앞뒤 공백 있는 값 수", (d["주제분류명"] != d["주제분류명"].str.strip()).sum())

# ---- 2b. 나머지 4변수 + 결측 후보 표기 (이번에 더 본 것)
put("2b 자료ID 고유한가", d["자료ID"].is_unique)
put("2b 자료ID 형식 B+6자리 아닌 수", (~d["자료ID"].str.fullmatch(r"B\d{6}")).sum())
put("2b 자료ID 범위", f'{d["자료ID"].min()} ~ {d["자료ID"].max()}')
put("2b 발행년 4자리 정수 아닌 수", (~d["발행년"].str.fullmatch(r"\d{4}")).sum())
put("2b 발행년 범위", f'{d["발행년"].min()} ~ {d["발행년"].max()}')
put("2b KDC 값 목록", ",".join(sorted(d["KDC"].unique())))
price = pd.to_numeric(d["구입가격"], errors="coerce")
put("2b 구입가격 정수 아닌 수", (~d["구입가격"].str.fullmatch(r"\d+")).sum())
put("2b 구입가격 범위", f"{int(price.min())} ~ {int(price.max())}")
put("2b 8열 빈칸 합계(최근대출일 제외)", int((d.drop(columns="최근대출일") == "").sum().sum()))
SPECIAL = ["NA", "N/A", "-", "9999", "NULL", "모름", "NAN"]
put("2b 8열 특수값 표기(NA,N/A,-,9999,NULL,모름,NaN) 수", int(d.apply(lambda s: s.str.strip().str.upper().isin(SPECIAL)).sum().sum()))
put("2b 8열 앞뒤 공백 있는 칸 수", int(d.apply(lambda s: s != s.str.strip()).sum().sum()))
put("2b 최근대출일 < 구입일 (불가능한 값)", (rec < buy).sum())
put("2b 최근대출일 = 구입일", (rec == buy).sum())
put("2b 구입연도 < 발행년", (buy.dt.year < d["발행년"].astype(int)).sum())

# ---- 2c. 코드북 2절 표 대조 (코드북 본문은 파일로 저장하지 않는다)
x = zipfile.ZipFile("데이터코드북.docx").read("word/document.xml").decode("utf-8")
x = re.sub(r"</w:tc>", " | ", x); x = re.sub(r"</w:p>", "\n", x)
cb = html.unescape(re.sub(r"<[^>]+>", "", x))
sec2 = cb[cb.index("2. 변수 정의"):cb.index("작성 규칙")]
cells = [c.strip() for c in sec2.split("|")]
cbrow = {}
for i, c in enumerate(cells):
    if c in d.columns and i >= 1 and cells[i - 1].isdigit():
        cbrow[c] = cells[i + 2:i + 7]  # 척도, 타입, 값/범위, 결측 표기, 결측 수
actual = {
    "자료ID": f'{d["자료ID"].min()} ~ {d["자료ID"].max()}',
    "발행년": f'{d["발행년"].min()} ~ {d["발행년"].max()} (4자리 정수 문자)',
    "KDC": ", ".join(sorted(d["KDC"].unique())) + " (3자리 문자)",
    "주제분류명": ", ".join(sorted(d["주제분류명"].unique())),
    "구입일": f"{buy.min().date()} ~ {buy.max().date()}",
    "구입가격": f"{int(price.min())} ~ {int(price.max())}",
    "대출횟수": f"{int(loan.min())} ~ {int(loan.max())}",
    "최근대출일": f"{rec.min().date()} ~ {rec.max().date()} (빈칸 제외)",
}
rows = []
for c in d.columns:
    sc, ty, rng, mk, mn = cbrow.get(c, [""] * 5)
    nb = int((d[c] == "").sum())
    rows.append(dict(변수=c, 코드북_척도=sc, 코드북_타입=ty, 코드북_값범위=rng, 데이터_값범위=actual[c],
                     코드북_결측표기=mk, 코드북_결측수=mn, 데이터_빈칸수=nb,
                     결측수_같은가=str(nb) == mn.replace(",", "")))
pd.DataFrame(rows).to_csv(OUT + "코드북대조_8변수.csv", index=False, encoding="utf-8-sig")
put("2c 코드북 2절에 없는 사용 열 수", sum(c not in cbrow for c in d.columns))
put("2c 코드북 결측 수와 데이터 빈칸 수가 다른 변수 수", sum(not r["결측수_같은가"] for r in rows))

# ---- 3a. 구입일 경계
tgt = buy <= CUT
nol = loan == 0  # 무대출 정의: 대출횟수 0 (= 최근대출일 빈칸, 3b에서 확인)
put("3a 구입일 2022-12-31 이하 (대상 권수)", tgt.sum())
put("3a 구입일 = 2022-12-31 당일", (buy == CUT).sum())
put("3a 구입일 = 2023-01-01 당일", (buy == pd.Timestamp("2023-01-01")).sum())
put("3a 구입일 2022-12-01 ~ 2022-12-31", buy.between("2022-12-01", "2022-12-31").sum())
put("3a 구입일 2022-12-31 당일 중 무대출", ((buy == CUT) & nol).sum())
put("3a 구입일 2023-01-01 이후", (~tgt).sum())
put("3a 구입일 2023-01-01 이후 중 무대출 (대상 밖)", (~tgt & nol).sum())
put("3a 구입일 2021-12-31 이하 (참고: 승인 3번에서 고르지 않은 기준)", (buy <= "2021-12-31").sum())

# ---- 3b. 대상 안 최근대출일 빈칸과 대출횟수 0의 일치
put("3b 대상 안 빈칸이면서 0", (tgt & blank & nol).sum())
put("3b 대상 안 빈칸이면서 1 이상", (tgt & blank & ~nol).sum())
put("3b 대상 안 값 있으면서 0", (tgt & ~blank & nol).sum())

# ---- 3c. 중복: (가) 15열 전체 같은 행, (나) 자료ID 뺀 14열, (다) 자료ID 뺀 사용 7열
put("3c 15열 전체 같은 행 수", raw.duplicated(keep=False).sum())
put("3c 자료ID 뺀 14열(삭제 7열 포함) 같은 행 수", raw.drop(columns="자료ID").duplicated(keep=False).sum())
key7 = [c for c in d.columns if c != "자료ID"]
dup = d[d.duplicated(key7, keep=False)].copy()
dup["묶음"] = dup.groupby(key7).ngroup()
dup["대상"] = tgt[dup.index]
dup["무대출"] = nol[dup.index]
g = dup.groupby("묶음")["대상"].agg(["size", "sum"])
put("3c 전체 자료ID만 다른 행 수", len(dup))
put("3c 전체 묶음 수", len(g))
put("3c 묶음 크기 분포", str(g["size"].value_counts().to_dict()))
put("3c 대상 안 묶음 수 (두 행 모두 구입일 2022-12-31 이하)", (g["sum"] == g["size"]).sum())
put("3c 대상 걸침 묶음 수 (한 행만 대상)", ((g["sum"] > 0) & (g["sum"] < g["size"])).sum())
put("3c 대상 안 행 수", dup["대상"].sum())
put("3c 대상 안 행 중 무대출", (dup["대상"] & dup["무대출"]).sum())
put("3c 대상 안 행 주제별", str(dup[dup["대상"]]["주제분류명"].value_counts().to_dict()))
dup.sort_values(["묶음", "자료ID"]).to_csv(OUT + "자료ID만다른행_대상표시.csv", index=False, encoding="utf-8-sig")

# ---- 3d. 주제분류명 × KDC
ct = pd.crosstab(d["KDC"], d["주제분류명"])
ct.to_csv(OUT + "주제분류명_KDC_교차표.csv", encoding="utf-8-sig")
put("3d KDC 고유값 수", d["KDC"].nunique())
put("3d KDC마다 주제분류명 1개뿐인가", bool(((ct > 0).sum(axis=1) == 1).all()))
put("3d 주제분류명마다 KDC 1개뿐인가", bool(((ct > 0).sum(axis=0) == 1).all()))
put("3d 교차표에서 0이 아닌 칸 수", int((ct > 0).sum().sum()))

# ---- 3e. 대출횟수 큰 값: 코드북에 이상치 기준 없음 → 판정하지 않고 분포만
put("3e 대출횟수 0 행 수 (전체)", nol.sum())
put("3e 대출횟수 1 이상 중앙값", loan[~nol].median())

# ---- 4. 선택지별 핵심 수치 (P6 12쌍 처리, 참고: 경계)
def core(mask):
    t = tgt & mask; n = t & nol
    by = d[n]["주제분류명"].value_counts().reindex(SUBJ10, fill_value=0)
    return dict(대상권수=int(t.sum()), 무대출권수=int(n.sum()),
                무대출_28000_pct=round(n.sum() / TOTAL * 100, 2),
                무대출_대상_pct=round(n.sum() / t.sum() * 100, 2), by=by)
all_ = pd.Series(True, index=d.index)
first = dup.sort_values("자료ID").groupby("묶음").head(1).index
opts = {
    "유지 (공통 정제·승인 8번)": all_,
    "P6 제외 (16쌍 32행 모두 뺌)": ~d.index.isin(dup.index),
    "P6 한 권만 남김 (쌍마다 자료ID 앞쪽 1행)": ~d.index.isin(dup.index.difference(first)),
    "(참고) 경계: 2022-12-31 당일 구입 제외": buy != CUT,
}
res = {k: core(m) for k, m in opts.items()}
base_rank = list(res["유지 (공통 정제·승인 8번)"]["by"].sort_values(kind="stable").index)
tab = []
for k, r in res.items():
    rank = list(r["by"].sort_values(kind="stable").index)
    row = {"선택지": k, **{c: v for c, v in r.items() if c != "by"}, **r["by"].to_dict(),
           "순위(오름차순)": " < ".join(rank)}
    tab.append(row)
    if k != "유지 (공통 정제·승인 8번)":
        put(f"4 순위가 유지와 같은가: {k}", rank == base_rank)
pd.DataFrame(tab).to_csv(OUT + "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
s = res["유지 (공통 정제·승인 8번)"]["by"].sort_values()
put("4 유지 기준 무대출 권수 동률 있음", bool(s.duplicated().any()))
put("4 유지 기준 이웃 순위 간 최소 차이(권)", int(s.diff().min()))

pd.DataFrame(vals, columns=["항목", "값"]).to_csv(OUT + "점검값.csv", index=False, encoding="utf-8-sig")
for k, v in vals: print(k, "=", v)
print(pd.DataFrame(tab).T.to_string())
print(pd.DataFrame(rows).to_string())

# ---- 5. 원래 점검값(작업/20261117_무대출_주제분포/점검/점검값.csv)과 항목별 비교 → 점검결과.md 끝 표
old = pd.read_csv("작업/20261117_무대출_주제분포/점검/점검값.csv", encoding="utf-8-sig", dtype=str)
new = pd.read_csv(OUT + "점검값.csv", encoding="utf-8-sig", dtype=str)
cmp_ = old.merge(new, on="항목", how="outer", suffixes=("_원래", "_이번"), indicator=True)
cmp_["같은가"] = cmp_["_merge"].astype(str).map({"both": "", "left_only": "원래에만", "right_only": "이번에 새로 봄"})
both = cmp_["_merge"] == "both"
cmp_.loc[both, "같은가"] = (cmp_.loc[both, "값_원래"] == cmp_.loc[both, "값_이번"]).map({True: "같음", False: "다름"})
order = {k: i for i, k in enumerate(new["항목"])}
cmp_ = cmp_.assign(o=cmp_["항목"].map(order)).sort_values("o")
print("\n| 항목 | 원래 값 | 이번 값 | 같은가 |\n|---|---|---|---|")
for _, r in cmp_.iterrows():
    print(f'| {r["항목"]} | {"" if pd.isna(r["값_원래"]) else r["값_원래"]} | {"" if pd.isna(r["값_이번"]) else r["값_이번"]} | {r["같은가"]} |')
print(cmp_["같은가"].value_counts().to_dict())

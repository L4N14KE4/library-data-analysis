# 2~3단계 점검 (다시 하기 2026-11-25) — P02_장서목록_대출횟수, 사용 열 8개
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_결측치_공통정제/점검/점검.py
# 원자료는 읽기만 한다. 행을 지우거나 값을 바꾼 사본을 만들지 않는다. 난수는 쓰지 않는다.
# 선택지별 수치(제외/대체)는 "그렇게 하면 이렇게 된다"를 메모리에서 계산만 한 것이다.
import re
import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = "작업/20261125_결측치_공통정제/점검/"
DROP7 = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 '삭제'
USE = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
SUBJ = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
P_START, P_END = pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-30")  # 코드북 1절 대상 기간


def save(df, name):
    df.to_csv(OUT + name, index=False, encoding="utf-8-sig")


# ---- 읽기: 모든 칸을 글자 그대로 읽는다 (빈칸을 NaN으로 바꾸지 않음) ----
raw_bytes = open(SRC, "rb").read(3)
raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
assert set(DROP7) <= set(raw.columns) and set(USE) <= set(raw.columns)
s = raw[USE]                                                  # 문자열 원본 (8열)
d = pd.DataFrame({
    "자료ID": s["자료ID"], "KDC": s["KDC"], "주제분류명": s["주제분류명"],
    "발행년": pd.to_numeric(s["발행년"], errors="coerce"),
    "구입가격": pd.to_numeric(s["구입가격"], errors="coerce"),
    "대출횟수": pd.to_numeric(s["대출횟수"], errors="coerce"),
    "구입일": pd.to_datetime(s["구입일"], format="%Y-%m-%d", errors="coerce"),
    "최근대출일": pd.to_datetime(s["최근대출일"].replace("", None), format="%Y-%m-%d", errors="coerce"),
})
blank = s["최근대출일"] == ""
n = len(d)

# ---- 1. 개요와 코드북 대조 ----
FMT = {  # 변수별 형식 (정규식, 이름)
    "자료ID": (r"B\d{6}", "문자(B+6자리)"), "발행년": (r"\d+", "정수(숫자만)"),
    "KDC": (r"\d{3}", "숫자 3자리 문자"), "주제분류명": (None, "문자"),
    "구입일": (r"\d{4}-\d{2}-\d{2}", "날짜(YYYY-MM-DD)"), "구입가격": (r"\d+", "정수(숫자만)"),
    "대출횟수": (r"\d+", "정수(숫자만)"), "최근대출일": (r"\d{4}-\d{2}-\d{2}", "날짜(YYYY-MM-DD)"),
}
CB = {  # 코드북 2절 (타입, 값/범위, 결측 표기, 결측 수) — 데이터코드북.docx에서 옮김
    "자료ID": ("문자", "B000001 ~ B028000", "N", 0), "발행년": ("날짜", "2005 ~ 2025", "N", 0),
    "KDC": ("문자", "0 ~ 900", "N", 0), "주제분류명": ("문자", ", ".join(SUBJ), "N", 0),
    "구입일": ("날짜", "2005-01-01 ~ 2025-12-27", "N", 0), "구입가격": ("숫자", "6000 ~ 38000", "N", 0),
    "대출횟수": ("숫자", "0 ~ 527", "N", 0), "최근대출일": ("날짜", "(필드 값 없음) ~ 2025-12-30", "빈칸", 14036),
}


def fmt_bad(c):
    pat = FMT[c][0]
    v = s[c][s[c] != ""]
    if pat is None:
        return int((~v.isin(SUBJ)).sum())
    return int((~v.str.fullmatch(pat)).sum())


rows = []
for c in USE:
    v = s[c][s[c] != ""]
    if c in ("KDC", "주제분류명"):
        rng = ", ".join(sorted(v.unique()))
    elif c in ("발행년", "구입가격", "대출횟수"):
        rng = f"{int(d[c].min())} ~ {int(d[c].max())}"
    else:
        rng = f"{v.min()} ~ {v.max()}"
    rows.append([c, CB[c][0], FMT[c][1], CB[c][1], rng, s[c].nunique(), CB[c][2], CB[c][3], int((s[c] == "").sum())])
save(pd.DataFrame(rows, columns=["변수", "코드북_타입", "실제_형태", "코드북_값범위", "실제_값범위",
                                 "고유값수", "코드북_결측표기", "코드북_결측수", "실제_빈칸수"]), "코드북대조.csv")
kdc_map = pd.crosstab(s["KDC"], s["주제분류명"])
kdc_pairs = int((kdc_map > 0).sum().sum())                     # 1:1이면 10

# ---- 2. 결측·특수값 ----
SPECIAL = ["9999", "-", "N/A", "NA", "n/a", "null", "NULL", "None", "nan", "NaN", "모름", "없음", "?", "."]
rows = []
for c in USE:
    v = s[c]
    nonblank = v != ""
    st = v.str.strip()
    r = [c, int((~nonblank).sum()), int((nonblank & (st == "")).sum()), int((nonblank & (st != "") & (v != st)).sum())]
    r += [int((st == x).sum()) for x in SPECIAL]                 # 앞뒤 공백을 지운 뒤 비교
    r.append(fmt_bad(c))
    rows.append(r)
special = pd.DataFrame(rows, columns=["변수", "빈칸", "공백문자만", "앞뒤공백"] + SPECIAL + ["형식벗어남"])
save(special, "특수값검색.csv")
cross = pd.crosstab(blank, d["대출횟수"] == 0)                  # 2-2절: 빈칸 x 대출횟수 0

# ---- 3. 이상치: 논리 검사 ----
gap = (d["최근대출일"] - d["구입일"]).dt.days
logic = [
    ("구입일 날짜 변환 실패", int(d["구입일"].isna().sum())),
    ("최근대출일 날짜 변환 실패(빈칸 제외)", int((d["최근대출일"].isna() & ~blank).sum())),
    ("구입일 연도 < 발행년", int((d["구입일"].dt.year < d["발행년"]).sum())),
    ("최근대출일 < 구입일", int((gap < 0).sum())),
    ("최근대출일이 대상기간(2023-01-01~2025-12-30) 밖", int(((d["최근대출일"] < P_START) | (d["최근대출일"] > P_END)).sum())),
    ("구입일 > 대상기간 끝(2025-12-30)", int((d["구입일"] > P_END).sum())),
    ("구입가격 <= 0", int((d["구입가격"] <= 0).sum())),
    ("대출횟수 < 0", int((d["대출횟수"] < 0).sum())),
    ("대출횟수 > 0 인데 최근대출일 빈칸", int(((d["대출횟수"] > 0) & blank).sum())),
    ("대출횟수 = 0 인데 최근대출일 있음", int(((d["대출횟수"] == 0) & ~blank).sum())),
    ("발행년이 코드북 범위(2005~2025) 밖", int((~d["발행년"].between(2005, 2025)).sum())),
    ("구입일이 코드북 범위(2005-01-01~2025-12-27) 밖", int((~d["구입일"].between("2005-01-01", "2025-12-27")).sum())),
    ("구입가격이 코드북 범위(6000~38000) 밖", int((~d["구입가격"].between(6000, 38000)).sum())),
    ("대출횟수가 코드북 범위(0~527) 밖", int((~d["대출횟수"].between(0, 527)).sum())),
    ("(참고) 최근대출일 = 구입일", int((gap == 0).sum())),
]
save(pd.DataFrame(logic, columns=["검사", "해당 행 수"]), "논리검사.csv")
buy_gap = (d["구입일"].dt.year - d["발행년"]).value_counts().sort_index()   # 3-1절 참고
gap_0_7 = gap[gap.between(0, 7)].value_counts().sort_index()                  # 3-2절

# ---- 3-3. 통계적 이상치 후보 기준 (코드북에 기준 없음 — 고르지 않고 행 수만 센다) ----
def bounds(x):
    q1, q3 = x.quantile(0.25), x.quantile(0.75)
    iqr, m, sd = q3 - q1, x.mean(), x.std(ddof=1)
    return {"IQR 1.5배": (q1 - 1.5 * iqr, q3 + 1.5 * iqr), "IQR 3배": (q1 - 3 * iqr, q3 + 3 * iqr),
            "평균±3표준편차": (m - 3 * sd, m + 3 * sd)}


B = {c: bounds(d[c]) for c in ("발행년", "구입가격", "대출횟수")}
rows = []
for c, bb in B.items():
    for k, (lo, hi) in bb.items():
        a, b = int((d[c] < lo).sum()), int((d[c] > hi).sum())
        rows.append([c, k, round(lo, 2), round(hi, 2), a, b, a + b])
save(pd.DataFrame(rows, columns=["변수", "후보 기준", "하한", "상한", "하한 미만", "상한 초과", "합계"]), "이상치_후보기준.csv")
desc = {c: d[c].describe() for c in ("대출횟수", "구입가격")}

# ---- 4. 중복 ----
COL7 = USE[1:]
dup_id = int(s["자료ID"].duplicated().sum())
dup_all = int(s.duplicated().sum())
dup7_second = int(s.duplicated(COL7).sum())
dup7_rows = s[s.duplicated(COL7, keep=False)].sort_values(COL7 + ["자료ID"])
save(dup7_rows, "중복_자료ID제외7열.csv")

# ---- 5. 선택지별 핵심 수치 ----
def core(x, label):
    k, base = len(x), n
    z = int((x["대출횟수"] == 0).sum())
    cnt = x["주제분류명"].value_counts().reindex(SUBJ, fill_value=0)
    return [label, k, base - k, round((base - k) / base * 100, 2), round(x["대출횟수"].mean(), 4),
            float(x["대출횟수"].median()), z, round(z / k * 100, 2), int(round(x["구입가격"].sum()))] + cnt.tolist()


opts = [core(d, "기준: 원자료 그대로(모든 문제 '유지')"),
        core(d[~blank], "A. 최근대출일 빈칸 — 제외"),
        core(d[s["KDC"] != "000"], "B. KDC '000' 행 — 제외"),
        core(d[~s.duplicated(COL7)], "C. 자료ID 제외 7열 중복 — 제외(묶음의 첫 행만 남김)"),
        core(d[gap != 0], "D. (참고) 최근대출일=구입일 — 제외")]
for c, tag in (("대출횟수", "E"), ("구입가격", "F")):
    for k, (lo, hi) in B[c].items():
        out = (d[c] < lo) | (d[c] > hi)
        name = f"{tag}. {c} 이상치({k})"
        if out.sum() == 0:
            opts.append(core(d, f"{name} — 해당 0행, 변화 없음"))
            continue
        opts.append(core(d[~out], f"{name} — 제외"))
        opts.append(core(d.assign(**{c: d[c].clip(lo, hi)}), f"{name} — 대체(경계값 {round(hi, 2)}로 바꿈)"))
opt = pd.DataFrame(opts, columns=["선택지", "행 수", "제거 행 수", "제거 비율(%)", "대출횟수 평균", "대출횟수 중앙값",
                                  "대출횟수 0 권수", "대출횟수 0 비율(%)", "구입가격 합계"] + SUBJ)
save(opt, "선택지별_핵심수치.csv")
pct = opt[["선택지"]].join((opt[SUBJ].div(opt["행 수"], axis=0) * 100).round(2))
save(pct, "선택지별_주제분류구성비.csv")

# ---- P1 대체 시 생기는 문제 ----
med = d["최근대출일"].median().normalize()


def fill_check(r, label, filled):
    g = (r - d["구입일"]).dt.days
    return [label, filled, int(((d["대출횟수"] == 0) & r.notna()).sum()),
            int(((r < P_START) | (r > P_END)).sum()), int((g < 0).sum()),
            r.median().strftime("%Y-%m-%d"), int(r.value_counts().max())]


rf = [fill_check(d["최근대출일"], "유지(빈칸 그대로)", 0),
      fill_check(d["최근대출일"].fillna(d["구입일"]), "대체: 구입일로 채움", int(blank.sum())),
      fill_check(d["최근대출일"].fillna(med), f"대체: 최근대출일 중앙값({med:%Y-%m-%d})으로 채움", int(blank.sum()))]
save(pd.DataFrame(rf, columns=["방법", "채운 행 수", "대출횟수=0인데 최근대출일 있음", "최근대출일이 대상기간 밖",
                               "최근대출일 < 구입일", "최근대출일 중앙값", "가장 많은 날짜의 행 수"]), "최근대출일_대체시_문제.csv")

# ---- 승인된 처리 적용 (원래 승인 4·6~9·19번: 유지 / 처리 안 함 / 처리할 것 없음 / 판정하지 않음) ----
# ponytail: 승인된 처리가 모두 행·값을 바꾸지 않으므로 그대로 둔다. 바꾸는 처리가 승인되면 여기에 넣는다.
clean = s.copy()
assert clean.equals(s)

# ---- 핵심 수치 N1~N20 (원래 폴더 점검/핵심수치.csv와 같은 번호·항목) ----
ws_or_exact = sum(int(((s[c] != "") & (s[c].str.strip() == "")).sum() + s[c].isin(["9999", "-", "N/A", "NA", "모름"]).sum())
                  for c in USE)                                 # 앞뒤 공백을 지우지 않고 비교
key = [
    ("N1", "원본 행 수", len(raw)),
    ("N2", "원본 열 수", raw.shape[1]),
    ("N3", "사용 열 수 (코드북 1-1절 '삭제' 열 제외)", len([c for c in raw.columns if c not in DROP7])),
    ("N4", "최근대출일이 빈칸인 행 수", int(blank.sum())),
    ("N5", "최근대출일 빈칸이면서 대출횟수 = 0인 행 수", int((blank & (d["대출횟수"] == 0)).sum())),
    ("N6", "최근대출일 빈칸이면서 대출횟수 >= 1인 행 수", int((blank & (d["대출횟수"] >= 1)).sum())),
    ("N7", "최근대출일이 있으면서 대출횟수 = 0인 행 수", int((~blank & (d["대출횟수"] == 0)).sum())),
    ("N8", "최근대출일을 뺀 7개 사용 변수의 빈칸 수 합계", int((s[USE[:-1]] == "").sum().sum())),
    ("N9", "8개 사용 변수에서 공백만 있거나 정확히 9999/-/N/A/NA/모름인 칸 수 합계", ws_or_exact),
    ("N10", "최근대출일 < 구입일인 행 수 (최근대출일 빈칸 제외)", int((gap < 0).sum())),
    ("N11", "구입일의 연도 < 발행년인 행 수", int((d["구입일"].dt.year < d["발행년"]).sum())),
    ("N12", "최근대출일이 2023-01-01 ~ 2025-12-30 밖인 행 수 (빈칸 제외)",
     int(((d["최근대출일"] < P_START) | (d["최근대출일"] > P_END)).sum())),
    ("N13", "자료ID가 앞 행과 겹치는 행 수 (같은 값의 두 번째 이후)", dup_id),
    ("N14", "자료ID를 뺀 7개 사용 열의 값이 모두 같은 다른 행이 있는 행 수", len(dup7_rows)),
    ("N15", "최근대출일 = 구입일인 행 수", int((gap == 0).sum())),
    ("N16", "KDC 값이 문자 '000'인 행 수", int((s["KDC"] == "000").sum())),
    ("N17", "최근대출일 최솟값 (빈칸 제외, YYYY-MM-DD)", d["최근대출일"].min().strftime("%Y-%m-%d")),
    ("N18", "승인된 처리 적용 후 행 수", len(clean)),
    ("N19", "제거한 행 수", len(raw) - len(clean)),
    ("N20", "제거 비율(%, 소수 둘째 자리)", f"{(len(raw) - len(clean)) / len(raw) * 100:.2f}"),
]
save(pd.DataFrame(key, columns=["번호", "항목", "값"]), "핵심수치.csv")

# ---- 화면 출력 (점검결과.md 본문 수치의 출처) ----
print("UTF-8 BOM 있음:", raw_bytes == b"\xef\xbb\xbf", "| 행x열:", raw.shape, "| 사용 열:", USE)
print("구입일 범위:", s["구입일"].min(), "~", s["구입일"].max(), "| 최근대출일(빈칸 제외):", d["최근대출일"].min().date(), "~", d["최근대출일"].max().date())
print("KDC-주제분류명 값이 있는 칸 수:", kdc_pairs, dict(s.groupby("KDC")["주제분류명"].first()))
print("빈칸 x 대출횟수0 교차표:\n", cross)
print("구입연도-발행년:", dict(buy_gap), "| 최근대출일-구입일 0~7일:", dict(gap_0_7))
for c, x in desc.items():
    print(c, x.round(4).to_dict())
print("중복: 자료ID", dup_id, "| 8열 전체", dup_all, "| 7열(두 번째 이후)", dup7_second, "| 7열 해당 행", len(dup7_rows),
      "| 그중 대출0·빈칸", int(((dup7_rows["대출횟수"] == "0") & (dup7_rows["최근대출일"] == "")).sum()))
print("최근대출일 중앙값:", med.date())
for r in key:
    print(*r, sep=" | ")

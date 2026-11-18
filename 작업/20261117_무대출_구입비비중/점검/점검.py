# 2~3단계 점검 — 질문 5: 무대출 장서의 구입가격 비중
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261117_무대출_구입비비중/점검/점검.py
# 원자료는 읽기만 한다. 아무것도 처리(삭제·대체)하지 않고, 선택지별 결과만 계산해 보고한다. 난수 없음.
from pathlib import Path

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261117_무대출_구입비비중/점검")
# 코드북 1-1절 '삭제' 7열(서명·저자·출판사·자료구분·소장관·이용상태·장서연령)은 읽은 뒤 바로 뺀다.
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
K7 = [c for c in COLS if c != "자료ID"]
CUT = pd.Timestamp("2022-12-31")  # 승인기록 1번: 질문 1과 같게, 구입일 2022-12-31 이하

raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[COLS].copy()
d["_가격"] = pd.to_numeric(d["구입가격"], errors="coerce")
d["_대출횟수"] = pd.to_numeric(d["대출횟수"], errors="coerce")
d["_구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
d["_최근대출일"] = pd.to_datetime(d["최근대출일"].replace("", None), format="%Y-%m-%d", errors="coerce")
d["_무대출"] = (d["_구입일"] <= CUT) & (d["_대출횟수"] == 0)  # 질문 1과 같은 정의
rows = []  # 점검값.csv (항목, 값)


def put(k, v):
    rows.append((k, v))
    print(f"{k}: {v}")


# ---------------------------------------------------------------- 1. 공통 정제 적용 후 행 수
print("[1] 공통 정제 적용")
# 공통 정제 승인(20261116 승인기록)은 모두 유지/처리 안 함이라 지우는 행이 없다.
put("1 원본 행 수", len(raw))
put("1 원본 열 수", raw.shape[1])
put("1 공통 정제 적용 후 행 수", len(d))
put("1 사용 열 수", len(COLS))

# ---------------------------------------------------------------- 2. 코드북 2절·5절 대조 (4개 변수)
print("\n[2] 코드북 대조")
p = d["구입가격"]
put("2 구입가격 빈칸 수", int((p == "").sum()))
put("2 구입가격 숫자만으로 된 값 아님(쉼표·소수점·문자·음수 부호 등) 수", int((~p.str.fullmatch(r"\d+")).sum()))
put("2 구입가격 숫자 변환 실패 수", int(d["_가격"].isna().sum()))
put("2 구입가격 정수 아닌 값 수", int((d["_가격"] % 1 != 0).sum()))
put("2 구입가격 최솟값", int(d["_가격"].min()))
put("2 구입가격 최댓값", int(d["_가격"].max()))
put("2 구입가격 0 수", int((d["_가격"] == 0).sum()))
put("2 구입가격 음수 수", int((d["_가격"] < 0).sum()))
put("2 구입가격 9로만 된 값(9, 99, 999, 9999, ...) 수", int(p.str.fullmatch(r"9+").sum()))
put("2 구입가격 코드북 범위 6000~38000 밖 수", int((~d["_가격"].between(6000, 38000)).sum()))
put("2 구입가격 고유값 수", d["_가격"].nunique())
put("2 구입가격 500원 단위 아닌 값 수", int((d["_가격"] % 500 != 0).sum()))
put("2 구입일 빈칸 수", int((d["구입일"] == "").sum()))
put("2 구입일 날짜 변환 실패 수", int(d["_구입일"].isna().sum()))
put("2 대출횟수 빈칸 수", int((d["대출횟수"] == "").sum()))
put("2 대출횟수 정수 아닌 값 수", int((d["_대출횟수"].isna() | (d["_대출횟수"] % 1 != 0)).sum()))
put("2 최근대출일 빈칸 수", int((d["최근대출일"] == "").sum()))
put("2 최근대출일 값 있는데 날짜 변환 실패 수", int(((d["최근대출일"] != "") & d["_최근대출일"].isna()).sum()))
cb = pd.DataFrame([
    ["구입가격", "값/범위", "6000 ~ 38000", f"{int(d['_가격'].min())} ~ {int(d['_가격'].max())}"],
    ["구입가격", "결측 표기·수", "N, 0", f"빈칸 {int((p == '').sum())}, 0 {int((d['_가격'] == 0).sum())}, "
                                       f"음수 {int((d['_가격'] < 0).sum())}, 9로만 된 값 {int(p.str.fullmatch(r'9+').sum())}"],
    ["구입일", "값/범위", "2005-01-01 ~ 2025-12-27", f"{d['_구입일'].min().date()} ~ {d['_구입일'].max().date()}"],
    ["구입일", "결측 수", "0", str(int((d["구입일"] == "").sum()))],
    ["대출횟수", "값/범위", "0 ~ 527", f"{int(d['_대출횟수'].min())} ~ {int(d['_대출횟수'].max())}"],
    ["대출횟수", "결측 수", "0", str(int((d["대출횟수"] == "").sum()))],
    ["최근대출일", "값/범위", "(필드 값 없음) ~ 2025-12-30",
     f"{d['_최근대출일'].min().date()} ~ {d['_최근대출일'].max().date()} (빈칸 제외)"],
    ["최근대출일", "결측 표기·수", "빈칸, 14036", f"빈칸, {int((d['최근대출일'] == '').sum())}"],
], columns=["변수", "코드북 칸", "코드북 표기", "데이터 실제"])
cb.to_csv(OUT / "코드북대조_4변수.csv", index=False, encoding="utf-8-sig")
print(cb.to_string(index=False))

# ---------------------------------------------------------------- 3c. 그 밖의 문제 (정의 경계)
print("\n[3c] 무대출 정의 경계")
t = d[d["_구입일"] <= CUT]
blank, zero = t["최근대출일"] == "", t["_대출횟수"] == 0
put("3c 대상(구입일<=2022-12-31) 권수", len(t))
put("3c 대상 안 빈칸이면서 대출횟수 1 이상", int((blank & ~zero).sum()))
put("3c 대상 안 최근대출일 있으면서 대출횟수 0", int((~blank & zero).sum()))
put("3c 구입일 = 2022-12-31 당일", int((d["_구입일"] == CUT).sum()))
put("3c 구입일 2023-01-01 이후 권수 ('나머지'에 들어감)", int((d["_구입일"] > CUT).sum()))
put("3c 구입일 2023-01-01 이후 중 대출횟수 0 ('나머지'에 들어감)", int(((d["_구입일"] > CUT) & (d["_대출횟수"] == 0)).sum()))

# ---------------------------------------------------------------- 3a. 구입가격 이상치 후보 (판정하지 않음)
print("\n[3a] 구입가격 이상치 후보 — 기준 후보별 해당 권수만 센다")
x = d["_가격"]
q1, q3 = x.quantile(0.25), x.quantile(0.75)  # pandas 기본(선형 보간), 전체 28,000권 기준
iqr = q3 - q1
mu, sd = x.mean(), x.std()  # 표본 표준편차(ddof=1)
put("3a Q1", q1)
put("3a Q3", q3)
put("3a IQR", iqr)
put("3a 평균", round(mu, 2))
put("3a 표준편차(ddof=1)", round(sd, 2))
CANDS = {  # 이름: (아래 경계, 위 경계)
    "IQR 1.5배": (q1 - 1.5 * iqr, q3 + 1.5 * iqr),
    "IQR 3배": (q1 - 3 * iqr, q3 + 3 * iqr),
    "평균±3표준편차": (mu - 3 * sd, mu + 3 * sd),
}
out_rows = []
for name, (lo, hi) in CANDS.items():
    m = (x < lo) | (x > hi)
    put(f"3a {name} 경계", f"{lo:.2f} ~ {hi:.2f}")
    put(f"3a {name} 해당 권수 (아래/위)", f"{int(m.sum())} ({int((x < lo).sum())}/{int((x > hi).sum())})")
    put(f"3a {name} 해당 중 무대출", int((m & d["_무대출"]).sum()))
    if m.any():
        put(f"3a {name} 해당 값별 권수", x[m].value_counts().sort_index().to_dict())
    out_rows.append(d[m].assign(기준=name))
pd.concat(out_rows)[["기준"] + COLS + ["_무대출"]].rename(columns={"_무대출": "무대출"}) \
    .to_csv(OUT / "구입가격_이상치후보행.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 3b. 자료ID만 다른 쌍
print("\n[3b] 자료ID만 다른 행")
dup_all = d.duplicated(subset=K7, keep=False)
later = d.duplicated(subset=K7, keep="first")  # 쌍의 뒤 행(자료ID 큰 쪽, 원자료가 자료ID 순)
put("3b 자료ID만 다른 행 수", int(dup_all.sum()))
put("3b 묶음 수", d[dup_all].groupby(K7).ngroups)
put("3b 그중 무대출 행 수", int((dup_all & d["_무대출"]).sum()))
put("3b 구입가격 합계(32행)", int(x[dup_all].sum()))
put("3b 그중 무대출 구입가격 합계", int(x[dup_all & d["_무대출"]].sum()))
d[dup_all].sort_values(K7 + ["자료ID"])[COLS + ["_무대출"]].rename(columns={"_무대출": "무대출"}) \
    .to_csv(OUT / "자료ID만다른행.csv", index=False, encoding="utf-8-sig")

# ---------------------------------------------------------------- 4. 선택지별 핵심 수치
print("\n[4] 선택지별 핵심 수치")


def core(df, name, price="_가격"):
    nl = df[df["_무대출"]]
    tot, s_nl = round(df[price].sum()), round(nl[price].sum())  # 대체(평균±3SD)는 소수 경계값이라 원 단위 반올림
    return {"선택지": name, "전체 권수": len(df), "무대출 권수": len(nl),
            "무대출 구입가격 합계(원)": s_nl, "전체 구입가격 합계(원)": tot,
            "나머지 구입가격 합계(원)": tot - s_nl,
            "비중(%)": round(s_nl / tot * 100, 2),
            "(점검용) 권수 비중(%)": round(len(nl) / len(df) * 100, 2),
            "(점검용) 금액 비중 - 권수 비중(%p)": round(s_nl / tot * 100 - len(nl) / len(df) * 100, 2)}


opts = [core(d, "유지 (아무것도 하지 않음, 기준값)")]
for name, (lo, hi) in CANDS.items():
    m = (x < lo) | (x > hi)
    opts.append(core(d[~m], f"이상치 제외: {name} ({int(m.sum())}권 뺌)"))
    d[f"_대체_{name}"] = x.clip(lo, hi)  # 대체: 경계 밖 값을 경계값으로 바꿈 (권수는 그대로)
    opts.append(core(d, f"이상치 대체: {name} 경계값으로 ({int(m.sum())}권 값 바꿈)", f"_대체_{name}"))
opts += [
    core(d[~dup_all], "자료ID만 다른 쌍 제외 (16쌍 32행 모두 뺌)"),
    core(d[~later], "자료ID만 다른 쌍 한 권만 남김 (16행 뺌)"),
    core(d.assign(_무대출=d["_대출횟수"] == 0), "(참고) 무대출을 '대출횟수 0 전부'로 (승인 1번에서 고르지 않은 정의)"),
]
res = pd.DataFrame(opts)
res.to_csv(OUT / "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
print(res.T.to_string())
base = res.iloc[0]
put("4 비중(%) 최솟값 (참고 행 제외)", res.iloc[:-1]["비중(%)"].min())
put("4 비중(%) 최댓값 (참고 행 제외)", res.iloc[:-1]["비중(%)"].max())
put("4 '금액 비중 < 권수 비중' 방향이 모든 선택지에서 같은가",
    bool((res["(점검용) 금액 비중 - 권수 비중(%p)"].lt(0) == (base["(점검용) 금액 비중 - 권수 비중(%p)"] < 0)).all()))

pd.DataFrame(rows, columns=["항목", "값"]).to_csv(OUT / "점검값.csv", index=False, encoding="utf-8-sig")

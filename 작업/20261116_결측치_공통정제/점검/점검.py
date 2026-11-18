# 2~3단계 점검 — P02_장서목록_대출횟수 결측·이상치·중복·코드북 대조
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261116_결측치_공통정제/점검/점검.py
# 원자료는 읽기만 한다. 아무것도 처리(삭제·대체)하지 않고, 선택지별 결과만 계산해 보고한다.
from pathlib import Path

import pandas as pd

SRC = "P02_장서목록_대출횟수 original.csv"
OUT = Path("작업/20261116_결측치_공통정제/점검")
# 코드북 1-1절 '삭제' 7열(서명·저자·출판사·자료구분·소장관·이용상태·장서연령)은 쓰지 않는다
# (원본 열 수 확인에만 전체 헤더를 읽고, 바로 아래 8열만 남긴다).
COLS = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]
SUBJECTS = ["기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"]
PERIOD = (pd.Timestamp("2023-01-01"), pd.Timestamp("2025-12-30"))  # 코드북 1절 대상 기간

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 30)


def load():
    # 모든 열을 문자열로 읽어 원래 표기(KDC 000 등)와 빈칸을 그대로 둔다.
    raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    d = raw[COLS].copy()
    d["_발행년"] = d["발행년"].astype(int)
    d["_구입가격"] = d["구입가격"].astype(int)
    d["_대출횟수"] = d["대출횟수"].astype(int)
    d["_구입일"] = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
    d["_최근대출일"] = pd.to_datetime(d["최근대출일"].replace("", None), format="%Y-%m-%d", errors="coerce")
    return raw, d


# ---------------------------------------------------------------- 1. 개요·코드북 대조
def overview(raw, d):
    print("\n[1] 개요")
    print("원본 행×열:", raw.shape, "/ 사용 열:", len(COLS))
    print("인코딩: UTF-8 BOM (utf-8-sig로 읽음)")
    print("구입일 범위:", d["구입일"].min(), "~", d["구입일"].max())
    ld = d.loc[d["최근대출일"] != "", "최근대출일"]
    print("최근대출일 범위(빈칸 제외):", ld.min(), "~", ld.max())

    # 코드북 2절: 타입, 값/범위, 결측 표기, 결측 수
    book = {
        "자료ID": ("문자", "B000001 ~ B028000", "N", 0),
        "발행년": ("날짜", "2005 ~ 2025", "N", 0),
        "KDC": ("문자", "0 ~ 900", "N", 0),
        "주제분류명": ("문자", ", ".join(SUBJECTS), "N", 0),
        "구입일": ("날짜", "2005-01-01 ~ 2025-12-27", "N", 0),
        "구입가격": ("숫자", "6000 ~ 38000", "N", 0),
        "대출횟수": ("숫자", "0 ~ 527", "N", 0),
        "최근대출일": ("날짜", "(필드 값 없음) ~ 2025-12-30", "빈칸", 14036),
    }
    rows = []
    for c in COLS:
        s = d[c]
        ne = s[s != ""]
        if c in ("발행년", "구입가격", "대출횟수"):
            rng = f"{d['_' + c].min()} ~ {d['_' + c].max()}"
            kind = "정수(숫자만)"
        elif c in ("구입일", "최근대출일"):
            rng = f"{ne.min()} ~ {ne.max()}"
            kind = "날짜(YYYY-MM-DD)"
        elif c == "KDC":
            rng = ", ".join(sorted(ne.unique()))
            kind = "숫자 3자리 문자"
        elif c == "주제분류명":
            rng = ", ".join(sorted(ne.unique()))
            kind = "문자"
        else:
            rng = f"{ne.min()} ~ {ne.max()}"
            kind = "문자(B+6자리)"
        rows.append({
            "변수": c, "코드북_타입": book[c][0], "실제_형태": kind,
            "코드북_값범위": book[c][1], "실제_값범위": rng, "고유값수": s.nunique(),
            "코드북_결측표기": book[c][2], "코드북_결측수": book[c][3], "실제_빈칸수": int((s == "").sum()),
        })
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    t.to_csv(OUT / "코드북대조.csv", index=False, encoding="utf-8-sig")

    # KDC와 주제분류명이 1:1로 대응하는지
    ct = pd.crosstab(d["KDC"], d["주제분류명"])
    print("KDC × 주제분류명 (0이 아닌 칸 수 =", int((ct > 0).sum().sum()), ")")
    print(ct.to_string())
    return t


# ---------------------------------------------------------------- 2. 결측·특수값
SPECIAL = ["9999", "-", "N/A", "NA", "n/a", "null", "NULL", "None", "nan", "NaN", "모름", "없음", "?", "."]
PATTERN = {
    "자료ID": r"B\d{6}", "발행년": r"\d{4}", "KDC": r"\d{3}", "구입가격": r"\d+", "대출횟수": r"\d+",
    "구입일": r"\d{4}-\d{2}-\d{2}", "최근대출일": r"\d{4}-\d{2}-\d{2}",
}


def missing(d):
    print("\n[2] 결측·특수값")
    rows = []
    for c in COLS:
        s = d[c]
        r = {"변수": c, "빈칸": int((s == "").sum()),
             "공백문자만": int(((s != "") & (s.str.strip() == "")).sum()),
             "앞뒤공백": int((s != s.str.strip()).sum())}
        for v in SPECIAL:
            r[v] = int((s.str.strip() == v).sum())
        # 형식 벗어남: 빈칸이 아닌데 정해진 형식(PATTERN)·목록(SUBJECTS)에 맞지 않는 값
        ne = s[s != ""]
        if c == "주제분류명":
            r["형식벗어남"] = int((~ne.isin(SUBJECTS)).sum())
        else:
            r["형식벗어남"] = int((~ne.str.fullmatch(PATTERN[c])).sum())
        rows.append(r)
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    t.to_csv(OUT / "특수값검색.csv", index=False, encoding="utf-8-sig")

    # 코드북 5절: 빈칸이 '값이 없는 것이 정상'인지 다른 열과 대조
    ct = pd.crosstab(d["최근대출일"] == "", d["_대출횟수"] == 0,
                     rownames=["최근대출일 빈칸"], colnames=["대출횟수=0"])
    print("최근대출일 빈칸 × 대출횟수=0\n", ct.to_string())
    blank = d["최근대출일"] == ""
    print("빈칸 행의 대출횟수 값:", d.loc[blank, "_대출횟수"].value_counts().to_dict())
    print("빈칸 아닌 행의 대출횟수 최솟값:", d.loc[~blank, "_대출횟수"].min())
    return t, ct


# ---------------------------------------------------------------- 3. 이상치
def logic(d):
    print("\n[3-1] 논리적으로 불가능한 값")
    checks = {
        "구입일 날짜 변환 실패": d["_구입일"].isna(),
        "최근대출일 날짜 변환 실패(빈칸 제외)": d["_최근대출일"].isna() & (d["최근대출일"] != ""),
        "구입일 연도 < 발행년": d["_구입일"].dt.year < d["_발행년"],
        "최근대출일 < 구입일": d["_최근대출일"] < d["_구입일"],
        "최근대출일이 대상기간(2023-01-01~2025-12-30) 밖": (d["_최근대출일"] < PERIOD[0]) | (d["_최근대출일"] > PERIOD[1]),
        "구입일 > 대상기간 끝(2025-12-30)": d["_구입일"] > PERIOD[1],
        "구입가격 <= 0": d["_구입가격"] <= 0,
        "대출횟수 < 0": d["_대출횟수"] < 0,
        "대출횟수 > 0 인데 최근대출일 빈칸": (d["_대출횟수"] > 0) & (d["최근대출일"] == ""),
        "대출횟수 = 0 인데 최근대출일 있음": (d["_대출횟수"] == 0) & (d["최근대출일"] != ""),
        "발행년이 코드북 범위(2005~2025) 밖": ~d["_발행년"].between(2005, 2025),
        "구입일이 코드북 범위(2005-01-01~2025-12-27) 밖": ~d["_구입일"].between("2005-01-01", "2025-12-27"),
        "구입가격이 코드북 범위(6000~38000) 밖": ~d["_구입가격"].between(6000, 38000),
        "대출횟수가 코드북 범위(0~527) 밖": ~d["_대출횟수"].between(0, 527),
        # 논리 위반은 아님 — 참고용
        "(참고) 최근대출일 = 구입일": d["_최근대출일"] == d["_구입일"],
    }
    t = pd.DataFrame({"검사": list(checks), "해당 행 수": [int(m.sum()) for m in checks.values()]})
    print(t.to_string(index=False))
    t.to_csv(OUT / "논리검사.csv", index=False, encoding="utf-8-sig")

    gap_y = (d["_구입일"].dt.year - d["_발행년"]).value_counts().sort_index()
    print("구입연도 - 발행년 분포:", gap_y.to_dict())
    gap_d = (d["_최근대출일"] - d["_구입일"]).dt.days.value_counts().sort_index()
    print("최근대출일 - 구입일(일) 0~7일 분포:", gap_d.loc[0:7].to_dict())
    return t, checks


def fences(s):
    # 통계적 이상치 후보 기준 — 코드북에 기준이 없어 고르지 않고 세 가지 모두 계산만 한다.
    # IQR: pandas 기본 분위수(선형 보간), 표준편차: 표본표준편차(ddof=1)
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    m, sd = s.mean(), s.std()
    return {
        "IQR 1.5배": (q1 - 1.5 * iqr, q3 + 1.5 * iqr),
        "IQR 3배": (q1 - 3 * iqr, q3 + 3 * iqr),
        "평균±3표준편차": (m - 3 * sd, m + 3 * sd),
    }


def stat_outliers(d):
    print("\n[3-2] 통계적 이상치 후보 기준별 행 수 (기준 필요 — 코드북에 기준 없음)")
    rows = []
    for c in ("발행년", "구입가격", "대출횟수"):
        s = d["_" + c]
        for name, (lo, hi) in fences(s).items():
            rows.append({"변수": c, "후보 기준": name, "하한": round(lo, 2), "상한": round(hi, 2),
                         "하한 미만": int((s < lo).sum()), "상한 초과": int((s > hi).sum()),
                         "합계": int(((s < lo) | (s > hi)).sum())})
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    t.to_csv(OUT / "이상치_후보기준.csv", index=False, encoding="utf-8-sig")
    for c in ("구입가격", "대출횟수"):
        print(c, "분위수:", d["_" + c].quantile([0, .25, .5, .75, 1]).to_dict(),
              "평균:", round(d["_" + c].mean(), 4), "표준편차:", round(d["_" + c].std(), 4))
    return t


# ---------------------------------------------------------------- 4. 중복
def duplicates(d):
    print("\n[4] 중복")
    k7 = [c for c in COLS if c != "자료ID"]
    res = {
        "자료ID 기준": int(d.duplicated(subset=["자료ID"]).sum()),
        "8개 열 전체 기준": int(d.duplicated(subset=COLS).sum()),
        "(보충) 자료ID 제외 7개 열 기준": int(d.duplicated(subset=k7).sum()),
    }
    for k, v in res.items():
        print(f"{k}: 두 번째 이후 행 {v}개")
    grp = d[d.duplicated(subset=k7, keep=False)].sort_values(k7 + ["자료ID"])
    print("7개 열 중복에 걸린 행:", len(grp), "/ 묶음 수:", grp.groupby(k7).ngroups,
          "/ 묶음 크기:", grp.groupby(k7).size().value_counts().to_dict())
    print("이 행들의 대출횟수 값:", grp["_대출횟수"].value_counts().to_dict(),
          "/ 최근대출일 빈칸:", int((grp["최근대출일"] == "").sum()))
    grp[COLS].to_csv(OUT / "중복_자료ID제외7열.csv", index=False, encoding="utf-8-sig")
    return res, k7


# ---------------------------------------------------------------- 5. 선택지별 핵심 수치
def core(df, n_col="_대출횟수"):
    n = df[n_col]
    r = {"행 수": len(df), "대출횟수 평균": round(n.mean(), 4), "대출횟수 중앙값": n.median(),
         "대출횟수 0 권수": int((n == 0).sum()), "대출횟수 0 비율(%)": round((n == 0).mean() * 100, 2),
         "구입가격 합계": int(round(df["_구입가격"].sum()))}
    vc = df["주제분류명"].value_counts()
    for s in SUBJECTS:
        r[s] = int(vc.get(s, 0))
    assert sum(r[s] for s in SUBJECTS) == r["행 수"]
    return r


def scenarios(d, checks, k7):
    print("\n[5] 선택지별 핵심 수치")
    blank = d["최근대출일"] == ""
    sc = [("기준: 원자료 그대로(모든 문제 '유지')", d)]
    sc.append(("A. 최근대출일 빈칸 — 제외", d[~blank]))
    sc.append(("B. KDC '000' 행 — 제외", d[d["KDC"] != "000"]))
    sc.append(("C. 자료ID 제외 7열 중복 — 제외(묶음의 첫 행만 남김)", d[~d.duplicated(subset=k7)]))
    sc.append(("D. (참고) 최근대출일=구입일 — 제외", d[~checks["(참고) 최근대출일 = 구입일"]]))
    rows = [{"선택지": name, **core(df)} for name, df in sc]

    # E·F. 통계적 이상치 — 후보 기준마다 제외 / 대체(경계값으로 바꿈)
    for tag, c in (("E", "대출횟수"), ("F", "구입가격")):
        s = d["_" + c]
        for name, (lo, hi) in fences(s).items():
            out = (s < lo) | (s > hi)
            if not out.any():
                rows.append({"선택지": f"{tag}. {c} 이상치({name}) — 해당 0행, 변화 없음", **core(d)})
                continue
            rows.append({"선택지": f"{tag}. {c} 이상치({name}) — 제외", **core(d[~out])})
            cl = d.copy()
            # 대체: 경계 밖 값을 경계값으로 바꾼다. 경계값이 소수(예: 33.02)면 소수 그대로 넣는다(반올림 안 함).
            cl["_" + c] = s.clip(lower=lo, upper=hi)
            rows.append({"선택지": f"{tag}. {c} 이상치({name}) — 대체(경계값 {round(hi, 2)}로 바꿈)", **core(cl)})
    t = pd.DataFrame(rows)
    t.insert(2, "제거 행 수", len(d) - t["행 수"])
    t.insert(3, "제거 비율(%)", ((len(d) - t["행 수"]) / len(d) * 100).round(2))
    print(t.to_string(index=False))
    t.to_csv(OUT / "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
    share = t[["선택지"]].join((t[SUBJECTS].div(t["행 수"], axis=0) * 100).round(2))
    print("주제분류 구성비(%)\n", share.to_string(index=False))
    share.to_csv(OUT / "선택지별_주제분류구성비.csv", index=False, encoding="utf-8-sig")
    return t


def fill_dates(d):
    # A의 '대체' 선택지: 최근대출일 빈칸을 날짜로 채우면 무엇이 생기는지 (대출횟수 열은 바뀌지 않으므로
    # 핵심 수치는 기준과 같다. 대신 최근대출일 자체에 생기는 문제를 센다.)
    print("\n[5-A] 최근대출일 빈칸 '대체' 시 생기는 문제")
    blank = d["최근대출일"] == ""
    ld = d["_최근대출일"]
    med = ld.dropna().sort_values().iloc[(ld.notna().sum() - 1) // 2]  # 날짜 중앙값(아래쪽 중앙)
    ways = {
        "유지(빈칸 그대로)": ld,
        "대체: 구입일로 채움": ld.fillna(d["_구입일"]),
        f"대체: 최근대출일 중앙값({med.date()})으로 채움": ld.fillna(med),
    }
    rows = []
    for name, x in ways.items():
        has = x.notna()
        rows.append({
            "방법": name, "채운 행 수": int((blank & has).sum()),
            "대출횟수=0인데 최근대출일 있음": int(((d["_대출횟수"] == 0) & has).sum()),
            "최근대출일이 대상기간 밖": int(((x < PERIOD[0]) | (x > PERIOD[1])).sum()),
            "최근대출일 < 구입일": int((x < d["_구입일"]).sum()),
            "최근대출일 중앙값": str(x.dropna().sort_values().iloc[(has.sum() - 1) // 2].date()),
            "가장 많은 날짜의 행 수": int(x.value_counts().iloc[0]),
        })
    t = pd.DataFrame(rows)
    print(t.to_string(index=False))
    t.to_csv(OUT / "최근대출일_대체시_문제.csv", index=False, encoding="utf-8-sig")
    return t


def kdc_notation(d):
    # B의 '대체' 선택지: '000'을 코드북 표기 '0'으로 바꾸는 경우와, 숫자로 읽으면 생기는 일
    print("\n[5-B] KDC 표기")
    print("KDC가 '000'인 행:", int((d["KDC"] == "000").sum()))
    as_num = pd.read_csv(SRC, encoding="utf-8-sig", usecols=["KDC"])["KDC"]
    print("숫자로 읽었을 때 dtype:", as_num.dtype, "/ 고유값:", sorted(as_num.unique().tolist()))


if __name__ == "__main__":
    raw, d = load()
    assert len(d) == 28000 and list(d.columns[:8]) == COLS
    overview(raw, d)
    missing(d)
    _, checks = logic(d)
    stat_outliers(d)
    _, k7 = duplicates(d)
    scenarios(d, checks, k7)
    fill_dates(d)
    kdc_notation(d)

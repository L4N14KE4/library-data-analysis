# 질문 5 다시 하기 (2026-11-25) — 2~3단계 점검. 아무 행도 지우거나 바꾸지 않는다. 난수 없음.
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_무대출_구입비비중/점검/점검.py
import pandas as pd

OUT = "작업/20261125_무대출_구입비비중/점검/"
raw = pd.read_csv("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
DROP = ["서명", "저자", "출판사", "자료구분", "소장관", "이용상태", "장서연령"]  # 코드북 1-1절 '삭제'
USE = [c for c in raw.columns if c not in DROP]
d = raw[USE].copy()  # 공통 정제: 지운 행 없음 (20261116 승인 4·8·9번)

V = []  # (항목, 값)
def put(k, v): V.append((k, v))

# ---- 1 행 수 ----
put("1 원본 행 수", len(raw)); put("1 원본 열 수", raw.shape[1])
put("1 공통 정제 적용 후 행 수", len(d)); put("1 사용 열 수", len(USE))

# ---- 2 코드북 대조: 구입가격·구입일·대출횟수·최근대출일 ----
p = d["구입가격"]
put("2 구입가격 빈칸 수", int((p.str.strip() == "").sum()))
put("2 구입가격 숫자만으로 된 값 아님(쉼표·소수점·문자·음수 부호 등) 수", int((~p.str.fullmatch(r"\d+")).sum()))
pn = pd.to_numeric(p, errors="coerce")
put("2 구입가격 숫자 변환 실패 수", int(pn.isna().sum()))
put("2 구입가격 정수 아닌 값 수", int((pn % 1 != 0).sum()))
put("2 구입가격 최솟값", int(pn.min())); put("2 구입가격 최댓값", int(pn.max()))
put("2 구입가격 0 수", int((pn == 0).sum())); put("2 구입가격 음수 수", int((pn < 0).sum()))
put("2 구입가격 9로만 된 값(9, 99, 999, 9999, ...) 수", int(p.str.fullmatch(r"9+").sum()))
put("2 구입가격 코드북 범위 6000~38000 밖 수", int(((pn < 6000) | (pn > 38000)).sum()))
put("2 구입가격 고유값 수", int(pn.nunique()))
put("2 구입가격 500원 단위 아닌 값 수", int((pn % 500 != 0).sum()))
buy = pd.to_datetime(d["구입일"], format="%Y-%m-%d", errors="coerce")
put("2 구입일 빈칸 수", int((d["구입일"].str.strip() == "").sum()))
put("2 구입일 날짜 변환 실패 수", int(buy.isna().sum()))
cnt = pd.to_numeric(d["대출횟수"], errors="coerce")
put("2 대출횟수 빈칸 수", int((d["대출횟수"].str.strip() == "").sum()))
put("2 대출횟수 정수 아닌 값 수", int((~d["대출횟수"].str.fullmatch(r"\d+")).sum()))
blank = d["최근대출일"].str.strip() == ""
last = pd.to_datetime(d["최근대출일"].where(~blank), format="%Y-%m-%d", errors="coerce")
put("2 최근대출일 빈칸 수", int(blank.sum()))
put("2 최근대출일 값 있는데 날짜 변환 실패 수", int((~blank & last.isna()).sum()))

# ---- 2 추가: 코드북 2절 나머지 범위·값 (이번에 새로 본 항목) ----
put("2+ 구입일 최솟값", buy.min().date().isoformat()); put("2+ 구입일 최댓값", buy.max().date().isoformat())
put("2+ 대출횟수 최솟값", int(cnt.min())); put("2+ 대출횟수 최댓값", int(cnt.max()))
put("2+ 최근대출일 최솟값", last.min().date().isoformat()); put("2+ 최근대출일 최댓값", last.max().date().isoformat())
put("2+ 최근대출일 대상 기간 2023-01-01~2025-12-30 밖 수", int(((last < "2023-01-01") | (last > "2025-12-30")).sum()))
put("2+ 최근대출일 < 구입일 수 (논리적으로 불가능)", int((last < buy).sum()))
put("2+ 최근대출일 = 구입일 수", int((last == buy).sum()))
put("2+ 자료ID 형식 B+6자리 아님 수", int((~d["자료ID"].str.fullmatch(r"B\d{6}")).sum()))
put("2+ 자료ID 코드북 범위 B000001~B028000 밖 수", int((~d["자료ID"].between("B000001", "B028000")).sum()))
put("2+ 발행년 최솟값~최댓값 (코드북 2005 ~ 2025)", f"{d['발행년'].astype(int).min()} ~ {d['발행년'].astype(int).max()}")
put("2+ KDC 고유값 (코드북 0 ~ 900)", ", ".join(sorted(d["KDC"].unique())))
CB_SUBJ = {"기술과학", "문학", "사회과학", "언어", "역사", "예술", "자연과학", "종교", "철학", "총류"}  # 코드북 2절
put("2+ 주제분류명 코드북 목록에 없는 값", ", ".join(sorted(set(d["주제분류명"]) - CB_SUBJ)) or "없음")
put("2+ KDC 하나에 주제분류명 둘 이상인 KDC 수", int((d.groupby("KDC")["주제분류명"].nunique() > 1).sum()))
put("2+ 전체 열 빈칸 수 (사용 8열 합계)", int((d.apply(lambda s: s.str.strip() == "")).sum().sum()))

# ---- 3c 무대출 정의 경계 ----
target = buy <= "2022-12-31"
put("3c 대상(구입일<=2022-12-31) 권수", int(target.sum()))
put("3c 대상 안 빈칸이면서 대출횟수 1 이상", int((target & blank & (cnt >= 1)).sum()))
put("3c 대상 안 최근대출일 있으면서 대출횟수 0", int((target & ~blank & (cnt == 0)).sum()))
put("3c 구입일 = 2022-12-31 당일", int((buy == "2022-12-31").sum()))
put("3c 구입일 2023-01-01 이후 권수 ('나머지'에 들어감)", int((~target).sum()))
put("3c 구입일 2023-01-01 이후 중 대출횟수 0 ('나머지'에 들어감)", int((~target & (cnt == 0)).sum()))
put("3c+ 전체 빈칸이면서 대출횟수 1 이상 / 값 있으면서 대출횟수 0", f"{int((blank & (cnt >= 1)).sum())} / {int((~blank & (cnt == 0)).sum())}")
nb1 = target & (cnt == 0)   # 정의 1: 질문 1과 같게 (승인 1·6번)
nb2 = cnt == 0              # 정의 2: 대출횟수 0 전부 (구입일 조건 없음)

# ---- 3a 구입가격 이상치 후보 (코드북 기준 없음: 판정하지 않고 후보별 영향만) ----
q1, q3 = pn.quantile(.25), pn.quantile(.75); iqr = q3 - q1
mu, sd = pn.mean(), pn.std(ddof=1)
put("3a Q1", q1); put("3a Q3", q3); put("3a IQR", iqr)
put("3a 사분위수 방식 5가지(linear/lower/higher/midpoint/nearest)에서 Q1·Q3 같은가",
    all(pn.quantile([.25, .75], interpolation=m).tolist() == [q1, q3] for m in ["linear", "lower", "higher", "midpoint", "nearest"]))
put("3a 평균", round(mu, 2)); put("3a 표준편차(ddof=1)", round(sd, 2))
BOUNDS = {"IQR 1.5배": (q1 - 1.5 * iqr, q3 + 1.5 * iqr), "IQR 3배": (q1 - 3 * iqr, q3 + 3 * iqr),
          "평균±3표준편차": (mu - 3 * sd, mu + 3 * sd)}
flags = {}
for name, (lo, hi) in BOUNDS.items():
    f = (pn < lo) | (pn > hi); flags[name] = f
    put(f"3a {name} 경계", f"{lo:.2f} ~ {hi:.2f}")
    put(f"3a {name} 해당 권수 (아래/위)", f"{int(f.sum())} ({int((pn < lo).sum())}/{int((pn > hi).sum())})")
    put(f"3a {name} 해당 중 무대출", int((f & nb1).sum()))
    put(f"3a+ {name} 해당 중 무대출 (정의 2: 대출횟수 0 전부)", int((f & nb2).sum()))
    if name != "IQR 3배":
        put(f"3a {name} 해당 값별 권수", str({int(k): int(v) for k, v in pn[f].value_counts().sort_index().items()}))
cand = d[flags["IQR 1.5배"]].assign(평균3SD해당=flags["평균±3표준편차"][flags["IQR 1.5배"]], 무대출_정의1=nb1, 무대출_정의2=nb2)
cand.to_csv(OUT + "구입가격_이상치후보행.csv", index=False, encoding="utf-8-sig")

# ---- 3b 중복 ----
put("3b+ 15열 전체가 같은 행 수", int(raw.duplicated(keep=False).sum()))
put("3b+ 자료ID 중복 행 수", int(d["자료ID"].duplicated(keep=False).sum()))
KEY = [c for c in USE if c != "자료ID"]  # 사용 8열 중 자료ID 뺀 7열 (삭제 열은 쓰지 않음, 20261116 승인 8번)
dup = d.duplicated(KEY, keep=False)
put("3b 자료ID만 다른 행 수", int(dup.sum()))
put("3b 묶음 수", int(d[dup].groupby(KEY).ngroups))
put("3b+ 묶음 크기 최댓값", int(d[dup].groupby(KEY).size().max()))
put("3b 그중 무대출 행 수", int((dup & nb1).sum()))
put("3b+ 그중 무대출 행 수 (정의 2)", int((dup & nb2).sum()))
put("3b 구입가격 합계(32행)", int(pn[dup].sum()))
put("3b 그중 무대출 구입가격 합계", int(pn[dup & nb1].sum()))
d[dup].sort_values(KEY + ["자료ID"]).assign(무대출_정의1=nb1, 무대출_정의2=nb2).to_csv(
    OUT + "자료ID만다른행.csv", index=False, encoding="utf-8-sig")
first_only = dup & d.duplicated(KEY, keep="first")  # 쌍마다 자료ID 앞쪽만 남기면 빠지는 행 (원자료가 자료ID 순)
assert d["자료ID"].is_monotonic_increasing

# ---- 4 선택지별 핵심 수치 (두 정의 모두) ----
def row(name, keep, price):
    out = {"선택지": name, "전체 권수": int(keep.sum())}
    tot = price[keep].sum()
    for tag, nb in [("", nb1), ("[정의2] ", nb2)]:
        m = keep & nb
        out[f"{tag}무대출 권수"] = int(m.sum())
        out[f"{tag}무대출 구입가격 합계(원)"] = int(round(price[m].sum()))
        if tag == "":
            out["전체 구입가격 합계(원)"] = int(round(tot))
            out["나머지 구입가격 합계(원)"] = int(round(tot)) - int(round(price[m].sum()))
        out[f"{tag}비중(%)"] = round(price[m].sum() / tot * 100, 2)
        out[f"{tag}(점검용) 권수 비중(%)"] = round(m.sum() / keep.sum() * 100, 2)
        out[f"{tag}(점검용) 금액 비중 - 권수 비중(%p)"] = round((price[m].sum() / tot - m.sum() / keep.sum()) * 100, 2)  # 반올림 전 값끼리
    return out
ALL = pd.Series(True, index=d.index)
R = [row("유지 (아무것도 하지 않음, 기준값)", ALL, pn)]
for name, (lo, hi) in BOUNDS.items():
    R.append(row(f"이상치 제외: {name} ({int(flags[name].sum())}권 뺌)", ~flags[name], pn))
    R.append(row(f"이상치 대체: {name} 경계값으로 ({int(flags[name].sum())}권 값 바꿈)", ALL, pn.clip(lo, hi)))
R.append(row(f"자료ID만 다른 쌍 제외 ({int(dup.sum())}행 모두 뺌)", ~dup, pn))
R.append(row(f"자료ID만 다른 쌍 한 권만 남김 ({int(first_only.sum())}행 뺌)", ~first_only, pn))
T = pd.DataFrame(R)
for tag in ["", "[정의2] "]:
    T[f"{tag}기준값과 차이(%p)"] = (T[f"{tag}비중(%)"] - T.loc[0, f"{tag}비중(%)"]).round(2)  # 반올림 값끼리
T.to_csv(OUT + "선택지별_핵심수치.csv", index=False, encoding="utf-8-sig")
put("4 비중(%) 최솟값 (참고 행 제외)", T["비중(%)"].min()); put("4 비중(%) 최댓값 (참고 행 제외)", T["비중(%)"].max())
put("4 '금액 비중 < 권수 비중' 방향이 모든 선택지에서 같은가", bool((T["(점검용) 금액 비중 - 권수 비중(%p)"] < 0).all()))
put("4+ [정의2] 비중(%) 최솟값", T["[정의2] 비중(%)"].min()); put("4+ [정의2] 비중(%) 최댓값", T["[정의2] 비중(%)"].max())
put("4+ [정의2] '금액 비중 < 권수 비중' 방향이 모든 선택지에서 같은가", bool((T["[정의2] (점검용) 금액 비중 - 권수 비중(%p)"] < 0).all()))

pd.DataFrame(V, columns=["항목", "값"]).to_csv(OUT + "점검값.csv", index=False, encoding="utf-8-sig")

# ---- 5 원래 점검 값과 비교 (같은 항목 이름끼리) ----
old = pd.read_csv("작업/20261117_무대출_구입비비중/점검/점검값.csv", encoding="utf-8-sig", dtype=str)
new = pd.DataFrame(V, columns=["항목", "값"]).astype(str)
cmp = old.merge(new, on="항목", how="outer", suffixes=("_원래", "_이번"), indicator=True)
def same(a, b):
    try: return float(a) == float(b)
    except (ValueError, TypeError): return a == b
cmp["같은가"] = [("원래에만" if m == "left_only" else "이번에만" if m == "right_only" else ("같음" if same(a, b) else "다름"))
               for a, b, m in zip(cmp["값_원래"], cmp["값_이번"], cmp["_merge"])]
cmp.drop(columns="_merge").to_csv("/private/tmp/claude-501/-Users-laniakea-dev-data-litaracy/53a72bce-b309-4d63-b050-c3b23fa7c6d2/scratchpad/analyst_q5/비교.csv", index=False, encoding="utf-8-sig")
oldT = pd.read_csv("작업/20261117_무대출_구입비비중/점검/선택지별_핵심수치.csv", encoding="utf-8-sig")
print(cmp["같은가"].value_counts().to_string())
print(cmp[cmp["같은가"] != "같음"].to_string())
print(T.to_string())
for c in ["전체 권수", "무대출 권수", "무대출 구입가격 합계(원)", "전체 구입가격 합계(원)", "나머지 구입가격 합계(원)", "비중(%)"]:
    print(c, "원래 1~9행과 같은가:", (oldT[c].iloc[:9].values == T[c].values).all())
print("정의2 기준값 vs 원래 참고행:", T.loc[0, ["[정의2] 무대출 권수", "[정의2] 무대출 구입가격 합계(원)", "[정의2] 비중(%)"]].tolist(), oldT.iloc[9, [2, 3, 6]].tolist())

# 2~3단계 점검 — 최근대출일의 월별 분포 (팀 추가 질문)
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_월별_최근대출일/점검/점검.py
# 아무것도 처리하지 않는다. 원자료는 읽기만 하고, 난수는 쓰지 않는다.
import pandas as pd

OUT = "작업/20261125_월별_최근대출일/점검/"
SRC = "P02_장서목록_대출횟수 original.csv"
USE = ["자료ID", "발행년", "KDC", "주제분류명", "구입일", "구입가격", "대출횟수", "최근대출일"]  # 코드북 1-1절 '삭제' 7열 제외
START, END = "2023-01-01", "2025-12-30"  # 코드북 1절 대상 기간

raw = pd.read_csv(SRC, encoding="utf-8-sig", dtype=str, keep_default_na=False)
d = raw[USE].copy()
vals = []  # (번호, 항목, 값)
def put(no, item, v):
    vals.append((no, item, v))
    print(no, item, v)

# 1. 규모와 기간
put("C1", "원본 행 수", len(raw))
put("C2", "원본 열 수", raw.shape[1])
put("C3", "사용 열 수", len(USE))
d["대출횟수"] = d["대출횟수"].astype(int)
buy = pd.to_datetime(d["구입일"], format="%Y-%m-%d")
put("C4", "구입일 최솟값", buy.min().date())
put("C5", "구입일 최댓값", buy.max().date())

# 2. 최근대출일 형식·범위
s = d["최근대출일"]
blank = s == ""
put("C6", "최근대출일 빈칸 행 수", int(blank.sum()))
put("C7", "최근대출일 값이 있는 행 수", int((~blank).sum()))
fmt_ok = s[~blank].str.fullmatch(r"\d{4}-\d{2}-\d{2}")
put("C8", "값이 있는데 YYYY-MM-DD 형식이 아닌 행 수", int((~fmt_ok).sum()))
last = pd.to_datetime(s.where(~blank), format="%Y-%m-%d", errors="coerce")
put("C9", "형식은 맞으나 없는 날짜(예: 02-30)인 행 수", int(last[~blank].isna().sum()))
put("C10", "최근대출일 최솟값", last.min().date())
put("C11", "최근대출일 최댓값", last.max().date())
out_rng = (last < START) | (last > END)
put("C12", f"최근대출일이 {START}~{END} 밖인 행 수", int(out_rng.sum()))

# 3. 빈칸과 대출횟수 0의 일치
zero = d["대출횟수"] == 0
put("C13", "빈칸이면서 대출횟수 0", int((blank & zero).sum()))
put("C14", "빈칸이면서 대출횟수 1 이상", int((blank & ~zero).sum()))
put("C15", "값이 있으면서 대출횟수 0", int((~blank & zero).sum()))

# 4. 연-월 36개 권수 (유지 기준)
months = pd.period_range("2023-01", "2025-12", freq="M").astype(str)
ym = last.dt.strftime("%Y-%m")
cnt = ym.value_counts().reindex(months, fill_value=0)
days = last.groupby(ym).apply(lambda x: x.dt.day.nunique()).reindex(months, fill_value=0)
mon = pd.DataFrame({"연월": months, "권수": cnt.values, "날짜가있는일수": days.values,
                    "그달일수": [pd.Period(m).days_in_month for m in months]})
mon["날짜가없는날"] = [" ".join(str(x) for x in sorted(set(range(1, pd.Period(m).days_in_month + 1)) - set(last[ym == m].dt.day))) for m in months]
mon["2025-12_30일보정권수"] = mon["권수"].astype(float)
mon.loc[mon["연월"] == "2025-12", "2025-12_30일보정권수"] = mon.loc[mon["연월"] == "2025-12", "권수"] * 31 / 30
mon.to_csv(OUT + "월별권수.csv", index=False, encoding="utf-8-sig")
put("C16", "연-월 36개 권수 합계", int(cnt.sum()))
put("C17", "권수 0인 달 수", int((cnt == 0).sum()))
put("C18", "날짜가 하루도 빠지지 않은 달 수 (날짜가있는일수 = 그달일수)", int((mon["날짜가있는일수"] == mon["그달일수"]).sum()))
put("C19", "2025-12 권수", int(cnt["2025-12"]))
put("C20", "2025-12-31 날짜가 있는 행 수", int((last == "2025-12-31").sum()))
put("C21", "2025-12 날짜가 있는 일수", int(days["2025-12"]))
dup_cnt = cnt[cnt.duplicated(keep=False)]
put("C22", "권수가 다른 달과 같은(동점) 달 수", len(dup_cnt))

# 5. 논리 위반
put("C23", "최근대출일 < 구입일 행 수", int((last < buy).sum()))
put("C24", "최근대출일 = 구입일 행 수", int((last == buy).sum()))

# 6. 자료ID만 다른 16쌍 (자료ID 제외 7열이 같은 행)
key = USE[1:]
dupe = d[d.duplicated(key, keep=False)]
put("C25", "자료ID 제외 7열이 같은 행 수", len(dupe))
put("C26", "그 쌍 수", dupe.groupby(key).ngroups)
put("C27", "그 가운데 최근대출일이 있는 행 수", int((dupe["최근대출일"] != "").sum()))

# 7. 구입연도 x 최근대출연도 교차표 (빈칸 제외)
has = ~blank
ct = pd.crosstab(buy[has].dt.year.rename("구입연도"), last[has].dt.year.rename("최근대출연도"))
ct.to_csv(OUT + "구입연도x최근대출연도.csv", encoding="utf-8-sig")
print(ct)
late = has & (buy >= "2023-01-01")
put("C28", "최근대출일이 있는 책 중 구입일 2023-01-01 이후", int(late.sum()))
put("C29", "최근대출일이 있는 책 중 구입일 2022-12-31 이하", int((has & ~late).sum()))
# 최근대출일이 구입일보다 앞설 수 없으므로, 구입월 이후 달에만 들어갈 수 있다
put("C30", "구입일 2025년이면서 최근대출일 있는 책", int((has & (buy.dt.year == 2025)).sum()))

# 8. 선택지별 수치 — 순위 상위 5와 하위 3, 2025-12 순위
def rank_view(c, tag):
    r = c.sort_values(ascending=False, kind="mergesort")  # 동점은 달 순서
    top = "; ".join(f"{m} {v:g}" for m, v in r.head(5).items())
    bot = "; ".join(f"{m} {v:g}" for m, v in r.tail(3).items())
    pos = list(r.index).index("2025-12") + 1 if "2025-12" in r.index else "제외"
    yr = c.groupby(c.index.str[:4]).sum()
    put(tag + "a", "포함 권수", f"{c.sum():g}")
    put(tag + "b", "상위 5", top)
    put(tag + "c", "하위 3", bot)
    put(tag + "d", "2025-12 순위", pos)
    put(tag + "e", "연도별 합 2023/2024/2025", "/".join(f"{v:g}" for v in yr.values))
    put(tag + "f", "최다 달 / 최소 달 권수 비", f"{r.iloc[0] / r.iloc[-1]:.2f}")

rank_view(cnt, "O1")  # 유지: 그대로
rank_view(cnt.drop("2025-12"), "O2")  # 2025-12 제외
rank_view(mon.set_index("연월")["2025-12_30일보정권수"], "O3")  # 2025-12 31/30 보정
old = has & ~late
cnt_old = ym[old].value_counts().reindex(months, fill_value=0)
rank_view(cnt_old, "O4")  # 구입일 2022-12-31 이하만
pd.DataFrame({"연월": months, "전체": cnt.values, "구입일2022이하": cnt_old.values,
              "구입일2023이후": (cnt - cnt_old).values}).to_csv(OUT + "월별권수_구입시기별.csv", index=False, encoding="utf-8-sig")

pd.DataFrame(vals, columns=["번호", "항목", "값"]).to_csv(OUT + "점검값.csv", index=False, encoding="utf-8-sig")

# 자체 점검: 처리하지 않았음을 확인
assert raw[USE]["최근대출일"].equals(s) and len(d) == len(raw) == 28000
assert int(cnt.sum()) == int(has.sum())  # 36개 달 밖으로 새는 행 없음

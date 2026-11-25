# 이번 점검 값과 원래 폴더(작업/20261118_주제별_예산근거_전체도서/점검/) 값의 항목별 비교. 원래 폴더 파일은 읽기만 한다.
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261125_주제별_예산근거_전체도서/점검/비교.py
from pathlib import Path

import pandas as pd

NEW = Path("작업/20261125_주제별_예산근거_전체도서/점검")
OLD = Path("작업/20261118_주제별_예산근거_전체도서/점검")

a = pd.read_csv(OLD / "점검값.csv", encoding="utf-8-sig", dtype=str)
b = pd.read_csv(NEW / "점검값.csv", encoding="utf-8-sig", dtype=str)
m = a.merge(b, on="항목", how="outer", suffixes=("_원래", "_이번"), indicator=True, sort=False)
m["판정"] = m.apply(lambda r: "원래에만 있음" if r["_merge"] == "left_only" else "이번에 추가" if r["_merge"] == "right_only"
                    else "같음" if r["값_원래"] == r["값_이번"] else "다름", axis=1)
m.drop(columns="_merge").to_csv(NEW / "원래대비_점검값비교.csv", index=False, encoding="utf-8-sig")
print(m["판정"].value_counts().to_string())

rows = []
for f in sorted(OLD.glob("*.csv")):
    if f.name == "점검값.csv":
        continue
    n = NEW / f.name
    rows.append({"파일": f.name, "판정": "이번에 없음" if not n.exists() else "바이트까지 같음" if f.read_bytes() == n.read_bytes() else "다름"})
fc = pd.DataFrame(rows)
fc.to_csv(NEW / "원래대비_파일비교.csv", index=False, encoding="utf-8-sig")
print(fc.to_string(index=False))

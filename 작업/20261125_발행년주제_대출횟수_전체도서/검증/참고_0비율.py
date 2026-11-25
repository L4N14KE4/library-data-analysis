# 참고 확인 (핵심 수치 아님): 결과.md 170줄 '대상의 약 절반이 대출 0회'
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/검증/참고_0비율.py
import numpy as np, pandas as pd
d = pd.read_csv("P02_장서목록_대출횟수 original.csv", encoding="utf-8-sig", dtype=str, keep_default_na=False)
x = d["대출횟수"].str.strip().astype(np.int64).to_numpy()
mu, sd = x.sum() / len(x), float(np.std(x.astype(np.float64), ddof=1))
keep = (x <= mu + 3 * sd) & (x >= mu - 3 * sd)
for name, v in [("유지", x), ("평균±3SD 제외", x[keep])]:
    print(f"{name}: 0회 {(v == 0).sum()}/{len(v)} = {(v == 0).mean() * 100:.2f}%")

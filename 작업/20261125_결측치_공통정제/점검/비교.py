# 이번 점검(20261125) 산출 CSV를 원래 점검(20261116) 산출 CSV와 칸마다 비교한다.
# 실행: 점검.py를 먼저 돌린 뒤, 프로젝트 폴더에서  .venv/bin/python 작업/20261125_결측치_공통정제/점검/비교.py
import pandas as pd

OLD, NEW = "작업/20261116_결측치_공통정제/점검/", "작업/20261125_결측치_공통정제/점검/"
FILES = ["핵심수치.csv", "코드북대조.csv", "특수값검색.csv", "논리검사.csv", "이상치_후보기준.csv",
         "중복_자료ID제외7열.csv", "선택지별_핵심수치.csv", "선택지별_주제분류구성비.csv", "최근대출일_대체시_문제.csv"]
rows = []
for f in FILES:
    a = pd.read_csv(OLD + f, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    b = pd.read_csv(NEW + f, encoding="utf-8-sig", dtype=str, keep_default_na=False)
    same_shape = a.shape == b.shape and list(a.columns) == list(b.columns)
    diff = 0 if not same_shape else int((a != b).sum().sum())
    rows.append([f, f"{a.shape[0]}x{a.shape[1]}", f"{b.shape[0]}x{b.shape[1]}", same_shape,
                 a.size if same_shape else "-", diff, "일치" if same_shape and diff == 0 else "다름"])
    if same_shape and diff:
        for (i, c) in zip(*((a != b).values.nonzero())):
            print(f, a.iloc[i, 0], a.columns[c], "원래:", a.iat[i, c], "이번:", b.iat[i, c])
out = pd.DataFrame(rows, columns=["파일", "원래 행x열", "이번 행x열", "열 이름·크기 같음", "비교한 칸 수", "다른 칸 수", "결과"])
out.to_csv(NEW + "비교표.csv", index=False, encoding="utf-8-sig")
print(out.to_string(index=False))

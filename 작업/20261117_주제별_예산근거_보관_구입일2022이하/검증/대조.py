# 핵심수치.csv(분석) vs 검증값.csv(검증) 번호별 대조 -> 대조표.md 의 표 부분을 출력. 프로젝트 폴더에서 실행.
import csv
P = "작업/20261117_주제별_예산근거_보관_구입일2022이하/"
a = {r["번호"]: r for r in csv.DictReader(open(P + "분석/핵심수치.csv", encoding="utf-8-sig"))}
v = {r["번호"]: r for r in csv.DictReader(open(P + "검증/검증값.csv", encoding="utf-8"))}
assert set(a) == set(v) and len(v) == 357
n_ok = 0
print("| 번호 | 항목 | 분석 값 | 검증 값 | 일치 여부 | 불일치 원인 |\n|---|---|---|---|---|---|")
for n in range(1, 358):
    k = f"N{n}"
    ok = a[k]["값"] == v[k]["값"]  # 두 값 모두 명세 보고 자릿수 문자열이라 문자열 비교 = 보고 자릿수 비교
    n_ok += ok
    print(f"| {k} | {v[k]['항목']} | {a[k]['값']} | {v[k]['값']} | {'일치' if ok else '불일치'} | |")
print(f"\n일치 {n_ok}/357")

# 2~3단계 마무리 — 승인된 품질 처리 적용과 정제 핵심 수치 N1~N20
# 실행: 프로젝트 폴더에서  .venv/bin/python 작업/20261116_결측치_공통정제/점검/정제.py
# 원자료는 읽기만 하고, 정제된 CSV 사본은 만들지 않는다. 난수는 쓰지 않는다.
import pandas as pd

from 점검 import COLS, OUT, PERIOD, SRC, load  # 같은 폴더의 점검.py (읽기·8열 선택·날짜 변환을 그대로 쓴다)

SPECIAL = ["9999", "-", "N/A", "NA", "모름"]  # N9 정의에 적힌 값만


def apply_approved(d):
    # 승인기록 4·6~9·12~17·19번 (19번이 11번을, 11번이 5번을 대체) — 행을 지우거나 값을 바꾸는 처리 없음.
    #   4 P1 최근대출일 빈칸 14,036행: 행 유지
    #   19 최근대출일 빈칸: 처리 안 함 (빈칸 유지), 행·값 변화 없음
    #   6·14 P7 통계적 이상치: 공통 정제에서는 판정하지 않음
    #   7 M1~M4 코드북 표기 차이: 데이터 유지, 코드북 표기를 고침 (코드북은 사용자가 고친다)
    #   8 P6 자료ID만 다른 16쌍(32행): 확인 없이 유지
    #   9 P5 최근대출일 = 구입일 712행: 정상으로 보고 유지
    #   15 P4 논리적으로 불가능한 값: 0행, 처리할 것 없음 (N10~N12로 확인)
    return d


def main():
    raw, d = load()                       # 점검.py 20~29행: utf-8-sig, 모든 열 문자열, 8열 선택
    blank = d["최근대출일"] == ""
    zero = d["_대출횟수"] == 0
    k7 = [c for c in COLS if c != "자료ID"]
    others = [c for c in COLS if c != "최근대출일"]
    ws_only = sum(int(((d[c] != "") & (d[c].str.strip() == "")).sum()) for c in COLS)
    special = sum(int(d[c].isin(SPECIAL).sum()) for c in COLS)
    ld = d.loc[~blank, "_최근대출일"]

    clean = apply_approved(d)
    removed = len(d) - len(clean)

    n = [
        ("N1", "원본 행 수", raw.shape[0]),
        ("N2", "원본 열 수", raw.shape[1]),
        ("N3", "사용 열 수 (코드북 1-1절 '삭제' 열 제외)", len(COLS)),
        ("N4", "최근대출일이 빈칸인 행 수", int(blank.sum())),
        ("N5", "최근대출일 빈칸이면서 대출횟수 = 0인 행 수", int((blank & zero).sum())),
        ("N6", "최근대출일 빈칸이면서 대출횟수 >= 1인 행 수", int((blank & (d["_대출횟수"] >= 1)).sum())),
        ("N7", "최근대출일이 있으면서 대출횟수 = 0인 행 수", int((~blank & zero).sum())),
        ("N8", "최근대출일을 뺀 7개 사용 변수의 빈칸 수 합계", sum(int((d[c] == "").sum()) for c in others)),
        ("N9", "8개 사용 변수에서 공백만 있거나 정확히 9999/-/N/A/NA/모름인 칸 수 합계", ws_only + special),
        ("N10", "최근대출일 < 구입일인 행 수 (최근대출일 빈칸 제외)", int((ld < d.loc[~blank, "_구입일"]).sum())),
        ("N11", "구입일의 연도 < 발행년인 행 수", int((d["_구입일"].dt.year < d["_발행년"]).sum())),
        ("N12", "최근대출일이 2023-01-01 ~ 2025-12-30 밖인 행 수 (빈칸 제외)",
         int(((ld < PERIOD[0]) | (ld > PERIOD[1])).sum())),
        ("N13", "자료ID가 앞 행과 겹치는 행 수 (같은 값의 두 번째 이후)", int(d.duplicated(subset=["자료ID"]).sum())),
        ("N14", "자료ID를 뺀 7개 사용 열의 값이 모두 같은 다른 행이 있는 행 수",
         int(d.duplicated(subset=k7, keep=False).sum())),
        ("N15", "최근대출일 = 구입일인 행 수", int((d["_최근대출일"] == d["_구입일"]).sum())),
        ("N16", "KDC 값이 문자 '000'인 행 수", int((d["KDC"] == "000").sum())),
        ("N17", "최근대출일 최솟값 (빈칸 제외, YYYY-MM-DD)", ld.min().strftime("%Y-%m-%d")),
        ("N18", "승인된 처리 적용 후 행 수", len(clean)),
        ("N19", "제거한 행 수", removed),
        ("N20", "제거 비율(%, 소수 둘째 자리)", f"{removed / len(d) * 100:.2f}"),
    ]
    t = pd.DataFrame(n, columns=["번호", "항목", "값"])
    print(t.to_string(index=False))
    print("N9 내역: 공백만 있는 칸", ws_only, "/ 지정 특수값 칸", special)
    t.to_csv(OUT / "핵심수치.csv", index=False, encoding="utf-8-sig")

    # 자체 확인: 승인대로라면 행·값이 원자료와 완전히 같아야 한다
    assert clean.equals(d) and len(clean) == raw.shape[0]
    # 코드북 M4(인코딩) 근거: 파일 첫 3바이트가 UTF-8 BOM(EF BB BF)인지
    with open(SRC, "rb") as f:
        print("UTF-8 BOM 있음:", f.read(3) == b"\xef\xbb\xbf")


if __name__ == "__main__":
    main()

# 6단계 대조: 핵심수치.csv vs 검증값.csv (값 문자열), 표 CSV 칸 vs 검증값.csv
# 실행: 프로젝트 폴더에서 .venv/bin/python 작업/20261125_발행년주제_대출횟수_전체도서/검증/대조.py
import os; os.chdir("작업/20261125_발행년주제_대출횟수_전체도서")
import csv
V={r['번호']:r['값'] for r in csv.DictReader(open('검증/검증값.csv',encoding='utf-8-sig'))}
g=lambda n:V[f"N{n}"]
Y=list(range(2005,2026)); S=["기술과학","문학","사회과학","언어","역사","예술","자연과학","종교","철학","총류"]
rd=lambda f:list(csv.reader(open('분석/'+f,encoding='utf-8-sig')))[1:]
bad=[];cnt=0
def chk(a,b,where):
    global cnt; cnt+=1
    if str(a)!=str(b): bad.append((where,a,b))
for T,s0,suf in [("유지",13,"유지"),("제외",284,"3SD제외")]:
    rows=rd(f"표1_발행년별_대출횟수_{suf}.csv")
    for i,r in enumerate(rows):
        k=Y.index(int(r[1])); b=s0+5*k
        chk(r[0],g(b+3),(suf,'t1',r[1])); chk(int(r[0]),i+1,'order')
        for c,o in zip(r[2:],[0,1,2,4]): chk(c,g(b+o),(suf,'t1',r[1],o))
    rows=rd(f"표2_주제별_대출횟수_{suf}.csv")
    for i,r in enumerate(rows):
        j=S.index(r[1]); b=s0+105+4*j
        chk(r[0],g(b+3),(suf,'t2',r[1])); chk(int(r[0]),i+1,'order')
        for c,o in zip(r[2:],[0,1,2]): chk(c,g(b+o),(suf,'t2',r[1],o))
rows=rd("표3_검정결과.csv"); it=iter(rows)
for s0 in (13,284):
  for base in (s0+146,s0+157):
    w=next(it);k=next(it)
    for c,o in zip([w[3],w[5],w[7],w[8],w[9]],[1,3,4,5,6]): chk(c,g(base+o),('t3',base,o))
    chk(w[4].split(", ")[1],g(base+2),('t3df',base))
    for c,o in zip([k[3],k[5],k[7],k[8],k[9]],[7,8,9,10,11]): chk(c,g(base+o),('t3',base,o))
rows=rd("표4_평균미만_비교.csv"); it=iter(rows)
for s0,NT,nr in [(13,28000,741),(284,27790,743)]:
  for ab,base in [("A",s0+168),("B",s0+219)]:
    p=next(it);r=next(it)
    for c,m in zip(p[3:15],[1,2,3,4,36,38,40,42,44,46,47,48]): chk(c,g(base+m),('t4',base,m))
    chk(p[15]," / ".join(g(base+m) for m in (49,50,51)),'t4max')
    for c,m in zip([r[7],r[8],r[9],r[10],r[11]],[37,39,41,43,45]): chk(c,g(base+m),('t4r',base,m))
    chk(r[13],g(nr+(ab=="B")),'t4rest'); chk(int(r[3]),NT-int(g(base+1)),'t4nr')
rows=rd("표5_평균미만_집단별비율.csv")
bases=[181,232,452,503]
for i,r in enumerate(rows):
    for c,b in zip(r[2:],bases): chk(c,g(b+(2 if i==31 else 5+i)),('t5',i))
rows=rd("표6_집단별분포.csv")
for i,r in enumerate(rows):
    T=i//31; q=i%31
    base=[555,648][T]+3*q if q<21 else [618,711][T]+3*(q-21)
    s0=[13,284][T]; nb=s0+5*q if q<21 else s0+105+4*(q-21)
    chk(r[3],g(nb),('t6n',i))
    for c,o in zip(r[4:],[0,1,2]): chk(c,g(base+o),('t6',i,o))
print("표 칸 대조:", cnt, "개 중 다름", len(bad), bad[:20])
A={r['번호']:r['값'] for r in csv.DictReader(open('분석/핵심수치.csv',encoding='utf-8-sig'))}
diff=[k for k in V if A.get(k)!=V[k]]
print("핵심 수치 대조: 일치", len(V)-len(diff), "/", len(V), "불일치", diff)

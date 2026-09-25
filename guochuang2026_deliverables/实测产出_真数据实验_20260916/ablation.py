# -*- coding: utf-8 -*-
"""Ablation：移除 en_sd 后 R² 掉多少？验证其主导性是真实贡献还是共线性伪像。
对照 9/14 鲶鱼 C2：当时 en_sd 占 61.4%，ablation 后 R² 只掉 0.0003 → 判为伪像。
"""
import pandas as pd, numpy as np, re, json, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
exec(open("run_real.py").read().split("print(\"=\"*70)")[0].split("# -*- coding")[1].replace(":utf-8-","",1)) if False else None

# 复用 run_real.py 的元素表与解析
src=open("run_real.py").read()
ns={"re":re,"np":np}
exec(src[src.index("R = 8.314"):src.index("print(\"=\"*70)")],ns)
ELEM=ns["ELEM"]; parse=ns["parse"]

df=pd.read_csv("/workspace/HEA_data.csv")
recs=[]
for _,row in df.iterrows():
    d=parse(row["formula"])
    if d is None: continue
    tot=sum(d.values()); fr={k:v/tot for k,v in d.items()}
    S=-8.314462618*sum(x*np.log(x) for x in fr.values() if x>0)
    recs.append(dict(n_elements=len(fr),S_mix=S,
        mass_w=np.mean([ELEM[e][0]*x for e,x in fr.items()]),
        en_w=np.mean([ELEM[e][1]*x for e,x in fr.items()]),
        rad_w=np.mean([ELEM[e][2]*x for e,x in fr.items()]),
        en_sd=np.std([ELEM[e][1] for e in fr]),
        rad_sd=np.std([ELEM[e][2] for e in fr]),
        Ef=row["formation_energy_peratom"]))
m=pd.DataFrame(recs).dropna(subset=["Ef"])
y=m["Ef"].values

def cv(cols):
    X=m[cols].values
    kf=KFold(5,shuffle=True,random_state=42)
    R2,MAE=[],[]
    for tr,te in kf.split(X):
        mdl=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1)
        mdl.fit(X[tr],y[tr]); p=mdl.predict(X[te])
        R2.append(r2_score(y[te],p)); MAE.append(mean_absolute_error(y[te],p))
    return float(np.mean(R2)),float(np.std(R2)),float(np.mean(MAE))

ALL=["n_elements","S_mix","mass_w","en_w","rad_w","en_sd","rad_sd"]
print("="*72)
print("Ablation 检验（RandomForest，5折CV，真数据 n=%d）"%len(m))
print("="*72)
base,bsd,bmae=cv(ALL)
print(f"  全特征                 R²={base:.4f}±{bsd:.4f}  MAE={bmae:.4f}")
rows=[("全特征（基线）",base,bsd,bmae,0.0)]
for drop in ["en_sd","rad_w","en_w","S_mix","rad_sd","n_elements","mass_w"]:
    cols=[c for c in ALL if c!=drop]
    r,s,ma=cv(cols)
    d=base-r
    rows.append((f"移除 {drop}",r,s,ma,d))
    flag="🔴 几乎不掉→疑似伪像" if d<0.01 else ("🟡 小幅下降" if d<0.05 else "🟢 真实贡献")
    print(f"  移除 {drop:12s}  R²={r:.4f}±{s:.4f}  MAE={ma:.4f}  ΔR²={d:+.4f}  {flag}")

json.dump(dict(n=int(len(m)),baseline=dict(R2=base,std=bsd,mae=bmae),
    ablation=[dict(removed=a,R2=b,std=c,mae=d,delta_R2=e) for a,b,c,d,e in rows]),
    open("ablation.json","w"),ensure_ascii=False,indent=2)
print("\nablation.json 已写入")

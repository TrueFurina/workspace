# -*- coding: utf-8 -*-
"""真数据实验：成分熵 vs 形成能 + 形成能预测 5 折 CV
数据源：JARVIS-DFT formation_energy_hea_subset.csv（15,783 行，真实公开数据）
严禁合成数据。
"""
import pandas as pd, numpy as np, re, json, os, warnings
warnings.filterwarnings("ignore")
from sklearn.model_selection import KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/workspace/实测产出_真数据实验_20260916"
SRC = "/workspace/实测产出_H档全链路_20260914/data/formation_energy_hea_subset.csv"
R = 8.314462618  # J/(mol*K)

# 元素属性：质量 / Pauling电负性 / 原子半径(pm)
ELEM = {
"H":(1.008,2.20,25),"Li":(6.94,0.98,145),"Be":(9.0122,1.57,105),"B":(10.81,2.04,85),
"C":(12.011,2.55,70),"N":(14.007,3.04,65),"O":(15.999,3.44,60),"F":(18.998,3.98,50),
"Na":(22.990,0.93,180),"Mg":(24.305,1.31,150),"Al":(26.982,1.61,125),"Si":(28.085,1.90,110),
"P":(30.974,2.19,100),"S":(32.06,2.58,100),"Cl":(35.45,3.16,100),"K":(39.098,0.82,220),
"Ca":(40.078,1.00,180),"Sc":(44.956,1.36,160),"Ti":(47.867,1.54,140),"V":(50.942,1.63,135),
"Cr":(51.996,1.66,140),"Mn":(54.938,1.55,140),"Fe":(55.845,1.83,140),"Co":(58.933,1.88,135),
"Ni":(58.693,1.91,135),"Cu":(63.546,1.90,135),"Zn":(65.38,1.65,135),"Ga":(69.723,1.81,130),
"Ge":(72.630,2.01,125),"As":(74.922,2.18,115),"Se":(78.971,2.55,115),"Br":(79.904,2.96,115),
"Rb":(85.468,0.82,235),"Sr":(87.62,0.95,200),"Y":(88.906,1.22,180),"Zr":(91.224,1.33,155),
"Nb":(92.906,1.60,145),"Mo":(95.95,2.16,145),"Tc":(98.0,1.90,135),"Ru":(101.07,2.20,130),
"Rh":(102.91,2.28,135),"Pd":(106.42,2.20,140),"Ag":(107.87,1.93,160),"Cd":(112.41,1.69,155),
"In":(114.82,1.78,155),"Sn":(118.71,1.96,145),"Sb":(121.76,2.05,145),"Te":(127.60,2.10,140),
"I":(126.90,2.66,140),"Cs":(132.91,0.79,260),"Ba":(137.33,0.89,215),"La":(138.91,1.10,195),
"Ce":(140.12,1.12,185),"Pr":(140.91,1.13,185),"Nd":(144.24,1.14,185),"Pm":(145.0,1.13,185),
"Sm":(150.36,1.17,185),"Eu":(151.96,1.20,185),"Gd":(157.25,1.20,180),"Tb":(158.93,1.10,175),
"Dy":(162.50,1.22,175),"Ho":(164.93,1.23,175),"Er":(167.26,1.24,175),"Tm":(168.93,1.25,175),
"Yb":(173.05,1.10,175),"Lu":(174.97,1.27,175),"Hf":(178.49,1.30,155),"Ta":(180.95,1.50,145),
"W":(183.84,2.36,135),"Re":(186.21,1.90,135),"Os":(190.23,2.20,130),"Ir":(192.22,2.20,135),
"Pt":(195.08,2.28,135),"Au":(196.97,2.54,135),"Hg":(200.59,2.00,150),"Tl":(204.38,1.62,190),
"Pb":(207.2,2.33,180),"Bi":(208.98,2.02,160),"Th":(232.04,1.30,180),"U":(238.03,1.38,175),
}

def parse(f):
    """解析化学式 -> {元素: 计数}"""
    d={}
    for el,num in re.findall(r"([A-Z][a-z]?)([0-9]*\.?[0-9]*)", str(f)):
        if not el or el not in ELEM: 
            if el: return None
            continue
        d[el]=d.get(el,0)+(float(num) if num else 1.0)
    return d if d else None

print("="*70)
print("真数据实验  JARVIS-DFT  formation_energy_hea_subset.csv")
print("="*70)
df=pd.read_csv(SRC)
print(f"原始行数: {len(df)}")

# ---- 解析成分 ----
recs=[]
for _,row in df.iterrows():
    d=parse(row["formula"])
    if d is None: continue
    tot=sum(d.values())
    fr={k:v/tot for k,v in d.items()}
    # 成分熵 S = -R * Σ x ln x   (J/(mol·K))
    S=-R*sum(x*np.log(x) for x in fr.values() if x>0)
    mass=np.mean([ELEM[e][0]*x for e,x in fr.items()])
    en_w=np.mean([ELEM[e][1]*x for e,x in fr.items()])
    rad_w=np.mean([ELEM[e][2]*x for e,x in fr.items()])
    en_sd=np.std([ELEM[e][1] for e in fr])
    rad_sd=np.std([ELEM[e][2] for e in fr])
    recs.append(dict(jid=row["jid"],formula=row["formula"],
        n_elements=len(fr),S_mix=S,mass_w=mass,en_w=en_w,rad_w=rad_w,
        en_sd=en_sd,rad_sd=rad_sd,
        Ef=row["formation_energy_peratom"]))
m=pd.DataFrame(recs).dropna(subset=["Ef"])
print(f"成分解析成功: {len(m)} 条  (解析失败/元素缺属性已丢弃: {len(df)-len(m)})")

# ---- ① 成分熵 vs 形成能 ----
from scipy.stats import pearsonr, spearmanr
pr,pp=pearsonr(m["S_mix"],m["Ef"])
sr,sp=spearmanr(m["S_mix"],m["Ef"])
print(f"\n【① 成分熵 vs 形成能】 n={len(m)}")
print(f"  Pearson  r={pr:+.4f}  p={pp:.3e}")
print(f"  Spearman rho={sr:+.4f}  p={sp:.3e}")
print(f"  → R²={pr**2:.4f}  解释方差仅 {pr**2*100:.2f}%")

plt.figure(figsize=(7,5))
plt.scatter(m["S_mix"],m["Ef"],s=4,alpha=.15,c="#2b6cb0",edgecolors="none")
z=np.polyfit(m["S_mix"],m["Ef"],1); xs=np.linspace(m["S_mix"].min(),m["S_mix"].max(),50)
plt.plot(xs,np.polyval(z,xs),"r--",lw=2,label=f"线性拟合 r={pr:+.3f}")
plt.xlabel("成分熵 S_mix  (J/(mol·K))"); plt.ylabel("形成能 (eV/atom)")
plt.title(f"成分熵 vs 形成能｜真数据 n={len(m)}｜Pearson r={pr:+.3f} R²={pr**2:.4f}")
plt.legend(); plt.tight_layout()
plt.savefig(f"{OUT}/成分熵vs形成能.png",dpi=140); plt.close()

# ---- ② 形成能预测 5 折 CV ----
FEATS=["n_elements","S_mix","mass_w","en_w","rad_w","en_sd","rad_sd"]
X=m[FEATS].values; y=m["Ef"].values
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
try:
    from xgboost import XGBRegressor
    models={"XGBoost":XGBRegressor(n_estimators=300,max_depth=8,learning_rate=0.08,
              random_state=42,n_jobs=-1,verbosity=0)}
    has_xgb=True
except Exception:
    models={}; has_xgb=False
models["RandomForest"]=RandomForestRegressor(n_estimators=300,random_state=42,n_jobs=-1)
models["Ridge"]=make_pipeline(StandardScaler(),Ridge(alpha=1.0))

kf=KFold(n_splits=5,shuffle=True,random_state=42)
res={}
print(f"\n【② 形成能预测 5 折 CV】特征={FEATS}")
for name,mdl in models.items():
    R2,MAE,RMSE=[],[],[]
    ytrue_all,ypred_all=[],[]
    for tr,te in kf.split(X):
        mdl.fit(X[tr],y[tr]); p=mdl.predict(X[te])
        R2.append(r2_score(y[te],p)); MAE.append(mean_absolute_error(y[te],p))
        RMSE.append(np.sqrt(mean_squared_error(y[te],p)))
        ytrue_all.append(y[te]); ypred_all.append(p)
    res[name]=dict(R2_mean=float(np.mean(R2)),R2_std=float(np.std(R2)),
        MAE_mean=float(np.mean(MAE)),RMSE_mean=float(np.mean(RMSE)),
        per_fold=[float(v) for v in R2])
    print(f"  {name:14s} R²={np.mean(R2):.4f}±{np.std(R2):.4f}  MAE={np.mean(MAE):.4f}  RMSE={np.mean(RMSE):.4f}")
    if name=="XGBoost" or (not has_xgb and name=="RandomForest"):
        yt=np.concatenate(ytrue_all); yp=np.concatenate(ypred_all)
        plt.figure(figsize=(5.5,5))
        plt.scatter(yt,yp,s=5,alpha=.15,c="#c53030",edgecolors="none")
        lo,hi=yt.min(),yt.max(); plt.plot([lo,hi],[lo,hi],"k--",lw=1.5)
        plt.xlabel("真实形成能 (eV/atom)"); plt.ylabel("预测形成能 (eV/atom)")
        plt.title(f"{name} 5折CV 预测vs真实｜R²={np.mean(R2):.4f}")
        plt.tight_layout(); plt.savefig(f"{OUT}/预测vs真实_{name}.png",dpi=140); plt.close()

# ---- ③ 特征重要性（XGBoost 或 RF）----
best="XGBoost" if has_xgb else "RandomForest"
mdl=models[best]; mdl.fit(X,y)
imp=getattr(mdl,"feature_importances_",None)
if imp is not None:
    order=np.argsort(imp)[::-1]
    print(f"\n【③ 特征重要性 · {best}】")
    for i in order: print(f"  {FEATS[i]:12s} {imp[i]:.4f}")
    plt.figure(figsize=(7,4))
    plt.bar([FEATS[i] for i in order],[imp[i] for i in order],color="#2f855a")
    plt.xticks(rotation=30,ha="right"); plt.ylabel("重要性")
    plt.title(f"特征重要性 · {best}（真数据 n={len(m)}）")
    plt.tight_layout(); plt.savefig(f"{OUT}/特征重要性_{best}.png",dpi=140); plt.close()

json.dump(dict(
    data_source=dict(name="JARVIS-DFT dft_3d",doi="10.6084/m9.figshare.6815699",
        license="CC BY 4.0",rows_raw=int(len(df)),rows_used=int(len(m)),
        dropped=int(len(df)-len(m))),
    mixing_entropy_vs_Ef=dict(n=int(len(m)),pearson_r=float(pr),pearson_p=float(pp),
        spearman_rho=float(sr),r_squared=float(pr**2)),
    cv5=res, best_model=best, features=FEATS),
    open(f"{OUT}/metrics.json","w"),ensure_ascii=False,indent=2)
print(f"\n产物已写入 {OUT}")
print("="*70)

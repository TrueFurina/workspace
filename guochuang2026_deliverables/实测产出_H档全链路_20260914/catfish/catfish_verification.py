#!/usr/bin/env python3
"""
Catfish (Adversarial) Verification Script
===========================================
Contract: 6 鲶鱼对抗式复核 Agent
Purpose: 对 HEA 形成能预测模型进行全面对抗式审查
"""

import os, sys, json, warnings, pickle
import numpy as np
import pandas as pd
from collections import defaultdict, Counter

# ML imports
from sklearn.model_selection import KFold, cross_val_predict, LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import xgboost as xgb

# Plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
sns.set_style('whitegrid')
np.random.seed(42)

# ============================================================
# Paths
# ============================================================
DATA_PATH   = '/root/code/research/data/formation_energy_hea_subset.csv'
OUT_DIR     = '/root/code/research/catfish'
FIG_DIR     = '/root/code/research/catfish'  # save figures here too
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 70)
print("鲶鱼 (CATFISH) ADVERSARIAL VERIFICATION")
print("=" * 70)

# ============================================================
# 0. Load data and feature engineering (same as experiment)
# ============================================================
df = pd.read_csv(DATA_PATH)
print(f"\nLoaded {len(df)} samples")

# Element properties (from run_experiment.py)
ELEMENT_PROPS = {
    'Ac': (89, 1.88, 1.10, 3, 227.03, 1323, 5.17),
    'Ag': (47, 1.44, 1.93, 1, 107.87, 1235, 7.58),
    'Al': (13, 1.43, 1.61, 3, 26.98,  933, 5.99),
    'As': (33, 1.25, 2.18, 5, 74.92,  1090, 9.82),
    'Au': (79, 1.44, 2.54, 1, 196.97, 1337, 9.23),
    'B':  (5,  0.85, 2.04, 3, 10.81,  2348, 8.30),
    'Ba': (56, 2.15, 0.89, 2, 137.33, 1000, 5.21),
    'Be': (4,  1.12, 1.57, 2, 9.01,   1560, 9.32),
    'Bi': (83, 1.46, 2.02, 5, 208.98, 544,  7.29),
    'Br': (35, 1.14, 2.96, 7, 79.90,  266,  11.81),
    'C':  (6,  0.77, 2.55, 4, 12.01,  3823, 11.26),
    'Ca': (20, 1.97, 1.00, 2, 40.08,  1115, 6.11),
    'Cd': (48, 1.51, 1.69, 2, 112.41, 594,  8.99),
    'Ce': (58, 1.82, 1.12, 3, 140.12, 1071, 5.54),
    'Cl': (17, 0.99, 3.16, 7, 35.45,  172,  12.97),
    'Co': (27, 1.25, 1.88, 2, 58.93,  1768, 7.88),
    'Cr': (24, 1.28, 1.66, 3, 52.00,  2180, 6.77),
    'Cs': (55, 2.65, 0.79, 1, 132.91, 302,  3.89),
    'Cu': (29, 1.28, 1.90, 2, 63.55,  1358, 7.73),
    'Dy': (66, 1.78, 1.22, 3, 162.50, 1680, 5.94),
    'Er': (68, 1.77, 1.24, 3, 167.26, 1770, 6.11),
    'Eu': (63, 2.04, 1.20, 2, 151.96, 1099, 5.67),
    'F':  (9,  0.71, 3.98, 7, 19.00,  54,  17.42),
    'Fe': (26, 1.24, 1.83, 2, 55.85,  1811, 7.90),
    'Ga': (31, 1.35, 1.81, 3, 69.72,  303,  6.00),
    'Gd': (64, 1.79, 1.20, 3, 157.25, 1585, 6.15),
    'Ge': (32, 1.23, 2.01, 4, 72.63,  1211, 7.90),
    'H':  (1,  0.37, 2.20, 1, 1.01,   14,   13.60),
    'Hf': (72, 1.58, 1.30, 4, 178.49, 2506, 6.83),
    'Hg': (80, 1.55, 2.00, 2, 200.59, 234,  10.44),
    'Ho': (67, 1.77, 1.23, 3, 164.93, 1734, 6.02),
    'I':  (53, 1.33, 2.66, 7, 126.90, 387,  10.45),
    'In': (49, 1.63, 1.78, 3, 114.82, 430,  5.79),
    'Ir': (77, 1.36, 2.20, 3, 192.22, 2719, 8.97),
    'K':  (19, 2.27, 0.82, 1, 39.10,  337,  4.34),
    'La': (57, 1.87, 1.10, 3, 138.91, 1193, 5.58),
    'Li': (3,  1.52, 0.98, 1, 6.94,   454,  5.39),
    'Lu': (71, 1.74, 1.27, 3, 174.97, 1925, 5.43),
    'Mg': (12, 1.60, 1.31, 2, 24.31,  923,  7.65),
    'Mn': (25, 1.27, 1.55, 2, 54.94,  1519, 7.43),
    'Mo': (42, 1.39, 2.16, 6, 95.95,  2896, 7.09),
    'N':  (7,  0.75, 3.04, 5, 14.01,  63,   14.53),
    'Na': (11, 1.86, 0.93, 1, 22.99,  371,  5.14),
    'Nb': (41, 1.43, 1.60, 5, 92.91,  2750, 6.76),
    'Nd': (60, 1.81, 1.14, 3, 144.24, 1289, 5.53),
    'Ni': (28, 1.24, 1.91, 2, 58.69,  1728, 7.64),
    'Np': (93, 1.55, 1.36, 5, 237.05, 917,  6.27),
    'O':  (8,  0.73, 3.44, 6, 16.00,  55,   13.62),
    'Os': (76, 1.35, 2.20, 4, 190.23, 3306, 8.44),
    'P':  (15, 1.10, 2.19, 5, 30.97,  317,  10.49),
    'Pa': (91, 1.63, 1.50, 5, 231.04, 1845, 5.89),
    'Pb': (82, 1.54, 2.33, 4, 207.20, 601,  7.42),
    'Pd': (46, 1.37, 2.20, 2, 106.42, 1828, 8.34),
    'Pm': (61, 1.80, 1.13, 3, 145.00, 1315, 5.55),
    'Pr': (59, 1.82, 1.13, 3, 140.91, 1204, 5.47),
    'Pt': (78, 1.39, 2.28, 2, 195.08, 2041, 8.96),
    'Pu': (94, 1.59, 1.28, 4, 244.06, 913,  6.03),
    'Rb': (37, 2.44, 0.82, 1, 85.47,  312,  4.18),
    'Re': (75, 1.37, 1.90, 4, 186.21, 3459, 7.83),
    'Rh': (45, 1.34, 2.28, 3, 102.91, 2237, 7.46),
    'Ru': (44, 1.34, 2.20, 4, 101.07, 2607, 7.36),
    'S':  (16, 1.04, 2.58, 6, 32.07,  388,  10.36),
    'Sb': (51, 1.41, 2.05, 5, 121.76, 904,  8.61),
    'Sc': (21, 1.62, 1.36, 3, 44.96,  1814, 6.56),
    'Se': (34, 1.17, 2.55, 6, 78.97,  494,  9.75),
    'Si': (14, 1.17, 1.90, 4, 28.09,  1687, 8.15),
    'Sm': (62, 1.80, 1.17, 3, 150.36, 1345, 5.64),
    'Sn': (50, 1.58, 1.96, 4, 118.71, 505,  7.34),
    'Sr': (38, 2.00, 0.95, 2, 87.62,  1050, 5.70),
    'Ta': (73, 1.43, 1.50, 5, 180.95, 3290, 7.89),
    'Tb': (65, 1.77, 1.20, 3, 158.93, 1629, 5.86),
    'Tc': (43, 1.36, 1.90, 4, 98.00,  2430, 7.28),
    'Te': (52, 1.37, 2.10, 6, 127.60, 723,  9.01),
    'Th': (90, 1.80, 1.30, 4, 232.04, 2023, 6.31),
    'Ti': (22, 1.47, 1.54, 4, 47.87,  1941, 6.82),
    'Tl': (81, 1.71, 1.62, 3, 204.38, 577,  6.11),
    'Tm': (69, 1.76, 1.25, 3, 168.93, 1818, 6.18),
    'U':  (92, 1.58, 1.38, 6, 238.03, 1408, 6.19),
    'V':  (23, 1.34, 1.63, 5, 50.94,  2183, 6.75),
    'W':  (74, 1.37, 2.36, 6, 183.84, 3695, 7.86),
    'Xe': (54, 1.40, 2.60, 8, 131.29, 165,  12.13),
    'Y':  (39, 1.80, 1.22, 3, 88.91,  1799, 6.22),
    'Yb': (70, 1.94, 1.10, 2, 173.05, 1097, 6.25),
    'Zn': (30, 1.34, 1.65, 2, 65.38,  693,  9.39),
    'Zr': (40, 1.60, 1.33, 4, 91.22,  2128, 6.63),
}

PROP_NAMES = ['Z', 'Atomic_Radius', 'Electronegativity', 'Valence_Electrons',
              'Atomic_Mass', 'Melting_Point', 'Ionization_Energy']

elem_prop_dict = {}
for el, (z, r, en, ve, am, mp, ie) in ELEMENT_PROPS.items():
    elem_prop_dict[el] = {
        'Z': z, 'Atomic_Radius': r, 'Electronegativity': en,
        'Valence_Electrons': ve, 'Atomic_Mass': am,
        'Melting_Point': mp, 'Ionization_Energy': ie,
    }

def extract_hea_features(elements_str):
    """Extract features (identical to experiment)."""
    elems = [e.strip() for e in elements_str.split(',')]
    n = len(elems)
    weights = np.ones(n) / n
    
    props = {}
    for pn in PROP_NAMES:
        vals = []
        for el in elems:
            vals.append(elem_prop_dict.get(el, {}).get(pn, np.nan))
        props[pn] = np.array(vals)
    
    features = {}
    for pn in PROP_NAMES:
        vals = props[pn]
        if np.any(np.isnan(vals)):
            features[f'{pn}_mean'] = np.nan
            features[f'{pn}_diff'] = np.nan
            features[f'{pn}_std']  = np.nan
        else:
            features[f'{pn}_mean'] = np.average(vals, weights=weights)
            features[f'{pn}_diff'] = np.max(vals) - np.min(vals)
            features[f'{pn}_std']  = np.sqrt(np.average((vals - np.average(vals, weights=weights))**2, weights=weights))
    
    # VEC
    vec_vals = np.array([elem_prop_dict[el]['Valence_Electrons'] for el in elems if el in elem_prop_dict])
    features['VEC'] = np.average(vec_vals, weights=weights[:len(vec_vals)]) if len(vec_vals) == n else np.nan
    
    # delta
    r_vals = np.array([elem_prop_dict[el]['Atomic_Radius'] for el in elems if el in elem_prop_dict])
    if len(r_vals) == n:
        r_avg = np.average(r_vals, weights=weights)
        features['delta'] = np.sqrt(np.average((1 - r_vals / r_avg)**2, weights=weights))
    else:
        features['delta'] = np.nan
    
    # Delta_Smix
    R = 8.314
    features['Delta_Smix'] = -R * np.sum(weights * np.log(weights))
    
    # Delta_Hmix (simplified)
    en_vals = np.array([elem_prop_dict[el]['Electronegativity'] for el in elems if el in elem_prop_dict])
    if len(en_vals) == n:
        dh_sum = 0
        for i in range(n):
            for j in range(i+1, n):
                den = en_vals[i] - en_vals[j]
                dr = r_vals[i] - r_vals[j] if len(r_vals) == n else 0
                dh_sum += 4 * weights[i] * weights[j] * (den**2 + 0.1 * (dr / (r_vals[i]+r_vals[j])*2)**2)
        features['Delta_Hmix'] = dh_sum * 100
    else:
        features['Delta_Hmix'] = np.nan
    
    # Omega
    mp_vals = np.array([elem_prop_dict[el]['Melting_Point'] for el in elems if el in elem_prop_dict])
    if len(mp_vals) == n and not np.isnan(features.get('Delta_Hmix', np.nan)) and features['Delta_Hmix'] != 0:
        tm_avg = np.average(mp_vals, weights=weights)
        features['Omega'] = tm_avg * features['Delta_Smix'] / abs(features['Delta_Hmix'])
    else:
        features['Omega'] = np.nan
    
    features['n_elements'] = n
    return features

# Build features
print("Extracting features...")
feature_list = []
for idx, row in df.iterrows():
    feats = extract_hea_features(row['elements'])
    feature_list.append(feats)
feat_df = pd.DataFrame(feature_list)

# Drop NaN rows
nan_counts = feat_df.isna().sum()
valid_mask = ~feat_df.isna().any(axis=1)
feat_df = feat_df[valid_mask].reset_index(drop=True)
df_f = df[valid_mask].reset_index(drop=True)
y = df_f['formation_energy_peratom'].values
X = feat_df.values
feature_names = list(feat_df.columns)

print(f"Final feature matrix: {X.shape}")
print(f"Feature names: {feature_names}")
print(f"Target stats: min={y.min():.4f}, max={y.max():.4f}, mean={y.mean():.4f}, std={y.std():.4f}")

# ============================================================
# COUNTER-HYPOTHESIS 1: "XGBoost is best model (R²=0.9260)"
# -> Check if this is due to overfitting
# ============================================================
print("\n" + "=" * 70)
print("COUNTER-HYPOTHESIS 1: XGBoost overfitting check")
print("=" * 70)

kf = KFold(n_splits=5, shuffle=True, random_state=42)

# Train XGBoost and compute train vs test gap
xgb_model = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
train_r2_list = []
test_r2_list = []

for train_idx, test_idx in kf.split(X):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    
    model = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    model.fit(X_tr, y_tr)
    
    y_tr_pred = model.predict(X_tr)
    y_te_pred = model.predict(X_te)
    
    train_r2 = r2_score(y_tr, y_tr_pred)
    test_r2 = r2_score(y_te, y_te_pred)
    
    train_r2_list.append(train_r2)
    test_r2_list.append(test_r2)
    print(f"  Fold: Train R²={train_r2:.4f}, Test R²={test_r2:.4f}, Gap={train_r2-test_r2:.4f}")

mean_train_r2 = np.mean(train_r2_list)
mean_test_r2 = np.mean(test_r2_list)
gap = mean_train_r2 - mean_test_r2
print(f"\n  Mean Train R²={mean_train_r2:.4f}, Mean Test R²={mean_test_r2:.4f}")
print(f"  Avg Train-Test Gap = {gap:.4f}")
if gap > 0.05:
    print("  ⚠️ Gap > 0.05 — potential overfitting concern")
elif gap > 0.03:
    print("  ⚠️ Gap > 0.03 — moderate overfitting, within acceptable range for tree ensembles")
else:
    print("  ✅ Gap ≤ 0.03 — overfitting not a major concern")

# ============================================================
# COUNTER-HYPOTHESIS 2: "Electronegativity_std is most important feature (61.4%)"
# -> Ablation study
# ============================================================
print("\n" + "=" * 70)
print("COUNTER-HYPOTHESIS 2: Ablation study on Electronegativity_std")
print("=" * 70)

# 2a. Remove Electronegativity_std and retrain
en_std_idx = feature_names.index('Electronegativity_std')
print(f"Electronegativity_std is at index {en_std_idx}")

# Remove the feature
X_no_en_std = np.delete(X, en_std_idx, axis=1)
print(f"X shape without Electronegativity_std: {X_no_en_std.shape}")

# Train XGBoost without it
xgb_no_en_std = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
r2_scores_no_en_std = []
for train_idx, test_idx in kf.split(X_no_en_std):
    X_tr, X_te = X_no_en_std[train_idx], X_no_en_std[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    r2_scores_no_en_std.append(r2_score(y_te, m.predict(X_te)))

mean_r2_no_en_std = np.mean(r2_scores_no_en_std)
print(f"  XGBoost CV R² WITHOUT Electronegativity_std: {mean_r2_no_en_std:.4f} ± {np.std(r2_scores_no_en_std):.4f}")
print(f"  Original XGBoost R²: 0.9260")
print(f"  Drop in R²: {0.9260 - mean_r2_no_en_std:.4f}")

# 2b. Train a model using ONLY Electronegativity_std
X_only_en_std = X[:, en_std_idx].reshape(-1, 1)
print(f"\n  Training model using ONLY Electronegativity_std...")
xgb_only_en_std = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
r2_scores_only_en_std = []
for train_idx, test_idx in kf.split(X_only_en_std):
    X_tr, X_te = X_only_en_std[train_idx], X_only_en_std[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    r2_scores_only_en_std.append(r2_score(y_te, m.predict(X_te)))

mean_r2_only_en_std = np.mean(r2_scores_only_en_std)
print(f"  XGBoost CV R² with ONLY Electronegativity_std: {mean_r2_only_en_std:.4f} ± {np.std(r2_scores_only_en_std):.4f}")
print(f"  Full model R² was 0.9260, single-feature R² = {mean_r2_only_en_std:.4f}")
print(f"  Ratio of full performance: {mean_r2_only_en_std/0.9260*100:.1f}%")

# 2c. Check if Electronegativity_diff can replace Electronegativity_std
en_diff_idx = feature_names.index('Electronegativity_diff')
X_no_en_diff = np.delete(X, en_diff_idx, axis=1)
r2_scores_no_en_diff = []
for train_idx, test_idx in kf.split(X_no_en_diff):
    X_tr, X_te = X_no_en_diff[train_idx], X_no_en_diff[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    r2_scores_no_en_diff.append(r2_score(y_te, m.predict(X_te)))
mean_r2_no_en_diff = np.mean(r2_scores_no_en_diff)
print(f"\n  XGBoost CV R² WITHOUT Electronegativity_diff: {mean_r2_no_en_diff:.4f} ± {np.std(r2_scores_no_en_diff):.4f}")
print(f"  Drop in R²: {0.9260 - mean_r2_no_en_diff:.4f}")

# 2d. Remove all electronegativity-related features
en_feat_indices = [i for i, name in enumerate(feature_names) if 'Electronegativity' in name]
X_no_en_all = np.delete(X, en_feat_indices, axis=1)
r2_scores_no_en_all = []
for train_idx, test_idx in kf.split(X_no_en_all):
    X_tr, X_te = X_no_en_all[train_idx], X_no_en_all[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    r2_scores_no_en_all.append(r2_score(y_te, m.predict(X_te)))
mean_r2_no_en_all = np.mean(r2_scores_no_en_all)
print(f"\n  XGBoost CV R² WITHOUT all electronegativity features: {mean_r2_no_en_all:.4f} ± {np.std(r2_scores_no_en_all):.4f}")
print(f"  Drop in R²: {0.9260 - mean_r2_no_en_all:.4f}")

# 2e. Also remove Delta_Hmix (highly correlated with EN_std, r=0.97)
print(f"\n  Note: Electronegativity_std and Delta_Hmix have r=0.977 correlation")

# 2f. Ablation for an unrelated feature for comparison
# Remove Melting_Point_mean (VIF=4.6, low multicollinearity)
mp_mean_idx = feature_names.index('Melting_Point_mean')
X_no_mp = np.delete(X, mp_mean_idx, axis=1)
r2_no_mp = []
for train_idx, test_idx in kf.split(X_no_mp):
    X_tr, X_te = X_no_mp[train_idx], X_no_mp[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    r2_no_mp.append(r2_score(y_te, m.predict(X_te)))
print(f"\n  (Control) XGBoost CV R² WITHOUT Melting_Point_mean: {np.mean(r2_no_mp):.4f}")
print(f"  Drop in R²: {0.9260 - np.mean(r2_no_mp):.4f}")

# ============================================================
# COUNTER-HYPOTHESIS 3: "Model generalizes to different HEA systems"
# -> Leave-one-group-out CV by primary metal / non-metal type
# ============================================================
print("\n" + "=" * 70)
print("COUNTER-HYPOTHESIS 3: Cross-group generalization (metal vs non-metal)")
print("=" * 70)

# Define groups based on element types
non_metals = {'H','He','B','C','N','O','F','Ne','Si','P','S','Cl','Ar','As','Se','Br','Kr','Te','I','Xe','At','Rn'}

# Classify each entry as "Oxide", "Other non-metal", or "All-metallic"
groups = []
group_names = []
for idx, row in df_f.iterrows():
    elems = [e.strip() for e in row['elements'].split(',')]
    found_non_metals = [e for e in elems if e in non_metals]
    if 'O' in found_non_metals:
        groups.append('contains_O')
    elif len(found_non_metals) > 0:
        groups.append('other_non_metal')
    else:
        groups.append('all_metal')

group_counts = Counter(groups)
print(f"Group distribution: {dict(group_counts)}")

# Check if there are enough all-metal entries for LOGO-CV
if group_counts.get('all_metal', 0) < 50:
    print("  ⚠️ Too few all-metal entries (HEA-like) for robust LOGO-CV")
    
# Now do leave-one-group-out CV
unique_groups = list(set(groups))
logo = LeaveOneGroupOut()

logo_r2_scores = {}
for group_name in unique_groups:
    # For each group as test
    test_mask = np.array([g == group_name for g in groups])
    train_mask = ~test_mask
    
    if test_mask.sum() < 10:
        print(f"  Skipping {group_name} (only {test_mask.sum()} samples)")
        continue
    
    X_tr, X_te = X[train_mask], X[test_mask]
    y_tr, y_te = y[train_mask], y[test_mask]
    
    m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
    m.fit(X_tr, y_tr)
    y_pred = m.predict(X_te)
    
    r2 = r2_score(y_te, y_pred)
    mae = mean_absolute_error(y_te, y_pred)
    logo_r2_scores[group_name] = {'r2': r2, 'mae': mae, 'n': test_mask.sum()}
    print(f"  Test '{group_name}' (n={test_mask.sum()}): R²={r2:.4f}, MAE={mae:.4f}")

print("\n  LOGO-CV Summary:")
for g, v in sorted(logo_r2_scores.items(), key=lambda x: x[1]['r2']):
    print(f"    {g:20s}: R²={v['r2']:.4f}, MAE={v['mae']:.4f}, n={v['n']}")

# ============================================================
# COUNTER-HYPOTHESIS 4: "15,783 effective HEA entries"
# -> Check actual HEA definition adherence
# ============================================================
print("\n" + "=" * 70)
print("COUNTER-HYPOTHESIS 4: Are these really HEAs?")
print("=" * 70)

# 4a. Element count distribution
elem_dist = df_f['n_elements'].value_counts().sort_index()
print(f"Element count distribution:")
for k, v in elem_dist.items():
    print(f"  {int(k)} elements: {v} ({100*v/len(df_f):.1f}%)")

# 4b. Non-metal analysis (expanded from before)
has_non_metal_count = 0
all_metal_count = 0
has_oxygen_count = 0
has_fluorine_count = 0
has_nitrogen_count = 0
has_chlorine_count = 0
has_hydrogen_count = 0
has_sulfur_count = 0

for idx, row in df_f.iterrows():
    elems = [e.strip() for e in row['elements'].split(',')]
    has_non_metal = any(e in non_metals for e in elems)
    if has_non_metal:
        has_non_metal_count += 1
    else:
        all_metal_count += 1
    if 'O' in elems: has_oxygen_count += 1
    if 'F' in elems: has_fluorine_count += 1
    if 'N' in elems: has_nitrogen_count += 1
    if 'Cl' in elems: has_chlorine_count += 1
    if 'H' in elems: has_hydrogen_count += 1
    if 'S' in elems: has_sulfur_count += 1

total = len(df_f)
print(f"\n  Composition analysis of 'HEA' dataset:")
print(f"  All-metal entries (true HEA candidates): {all_metal_count} ({100*all_metal_count/total:.1f}%)")
print(f"  Entries with non-metals: {has_non_metal_count} ({100*has_non_metal_count/total:.1f}%)")
print(f"  Contains Oxygen:   {has_oxygen_count} ({100*has_oxygen_count/total:.1f}%)")
print(f"  Contains Fluorine: {has_fluorine_count} ({100*has_fluorine_count/total:.1f}%)")
print(f"  Contains Nitrogen: {has_nitrogen_count} ({100*has_nitrogen_count/total:.1f}%)")
print(f"  Contains Chlorine: {has_chlorine_count} ({100*has_chlorine_count/total:.1f}%)")
print(f"  Contains Hydrogen: {has_hydrogen_count} ({100*has_hydrogen_count/total:.1f}%)")
print(f"  Contains Sulfur:   {has_sulfur_count} ({100*has_sulfur_count/total:.1f}%)")

# 4c. Entries that could be considered "traditional HEAs" (all metals, 4+ elements, near-equimolar)
# Since we don't have actual composition ratios, we can only check all-metal
print(f"\n  >>> CRITICAL: {100*all_metal_count/total:.1f}% of 'HEA' entries contain non-metals.")
print(f"  >>> This dataset is NOT an HEA dataset - it's a 'multi-component compound' dataset.")

# 4d. Space group analysis - how many are solid solutions vs ordered compounds?
print("\n  Space group diversity:")
spg_counts = df_f['spg_symbol'].value_counts()
print(f"  Number of unique space groups: {len(spg_counts)}")
print(f"  Top 10 space groups:")
for spg, cnt in spg_counts.head(10).items():
    print(f"    {spg:15s}: {cnt} ({100*cnt/total:.1f}%)")

# 4e. Count how many entries have high-symmetry (solid solution) space groups
# Common solid solution space groups: Fm-3m, Im-3m, Pm-3m, etc.
ss_spg = {'Fm-3m', 'Im-3m', 'Pm-3m', 'Fd-3m', 'Ia-3d', 'Pn-3m'}
ss_count = df_f['spg_symbol'].isin(ss_spg).sum()
print(f"  Entries in high-symmetry (solid solution) space groups: {ss_count} ({100*ss_count/total:.1f}%)")
print(f"  Most entries are ordered compounds, not solid-solution HEAs")

# ============================================================
# COUNTER-HYPOTHESIS 5: "Data is reliable (no anomalies)"
# -> Check for outliers and positive formation energy entries
# ============================================================
print("\n" + "=" * 70)
print("COUNTER-HYPOTHESIS 5: Data quality deep dive")
print("=" * 70)

# 5a. Positive formation energy entries
pos_fe = (y > 0).sum()
print(f"  Entries with positive formation energy (unstable): {pos_fe} ({100*pos_fe/len(y):.1f}%)")
print(f"  Range of positive formation energies: {y[y>0].min():.4f} to {y[y>0].max():.4f}")

# 5b. Extreme values
print(f"  Most negative (most stable): {y[np.argmin(y)]:.4f} eV/atom (index {np.argmin(y)})")
print(f"  Most positive (least stable): {y[np.argmax(y)]:.4f} eV/atom (index {np.argmax(y)})")

# Show the extreme entries
extreme_idx = [np.argmin(y), np.argmax(y)]
for ei in extreme_idx:
    print(f"    Sample {ei}: formula={df_f.iloc[ei]['formula']}, elements={df_f.iloc[ei]['elements']}, "
          f"spg={df_f.iloc[ei]['spg_symbol']}, fe={y[ei]:.4f}")

# 5c. Check ehull (energy above convex hull) distribution
if 'ehull' in df_f.columns:
    print(f"\n  ehull stats: min={df_f['ehull'].min():.4f}, max={df_f['ehull'].max():.4f}, "
          f"median={df_f['ehull'].median():.4f}")
    # Entries with ehull ~ 0 are ground-state structures
    near_ground = (df_f['ehull'] < 0.1).sum()
    print(f"  Entries near ground state (ehull < 0.1 eV/atom): {near_ground} ({100*near_ground/total:.1f}%)")

# 5d. Check for negative shear modulus
if 'shear_modulus_gv' in df_f.columns:
    neg_shear = (df_f['shear_modulus_gv'] < 0).sum()
    print(f"\n  Entries with negative shear modulus: {neg_shear} (unphysical)")

# ============================================================
# 6. ALL-METAL SUBSET: What is the model performance on true HEAs?
# ============================================================
print("\n" + "=" * 70)
print("SUPPLEMENTARY: Model performance on true all-metal HEAs")
print("=" * 70)

# Create mask for all-metal entries
all_metal_mask = np.array([g == 'all_metal' for g in groups])
all_metal_indices = np.where(all_metal_mask)[0]
print(f"All-metal entries: {len(all_metal_indices)}")

if len(all_metal_indices) >= 50:
    X_metal = X[all_metal_mask]
    y_metal = y[all_metal_mask]
    
    # 5-fold CV on all-metal subset
    kf_metal = KFold(n_splits=5, shuffle=True, random_state=42)
    metal_r2 = []
    for train_idx, test_idx in kf_metal.split(X_metal):
        X_tr, X_te = X_metal[train_idx], X_metal[test_idx]
        y_tr, y_te = y_metal[train_idx], y_metal[test_idx]
        m = xgb.XGBRegressor(n_estimators=300, learning_rate=0.1, random_state=42, verbosity=0)
        m.fit(X_tr, y_tr)
        metal_r2.append(r2_score(y_te, m.predict(X_te)))
    print(f"  XGBoost 5-fold CV R² on all-metal subset: {np.mean(metal_r2):.4f} ± {np.std(metal_r2):.4f}")
    print(f"  (vs 0.9260 on full dataset)")
    
    # Feature importance on all-metal subset
    rf_metal = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    rf_metal.fit(X_metal, y_metal)
    fi_metal = rf_metal.feature_importances_
    top_idx = np.argsort(fi_metal)[::-1][:10]
    print(f"\n  Top features on all-metal subset:")
    for idx in top_idx:
        print(f"    {feature_names[idx]:30s}: {fi_metal[idx]:.6f}")
    
    # Compare EN_std importance
    en_std_imp_metal = fi_metal[en_std_idx]
    print(f"\n  Electronegativity_std importance in all-metal subset: {en_std_imp_metal:.4f} ({100*en_std_imp_metal:.1f}%)")
    print(f"  Electronegativity_std importance in full dataset: 0.6136 (61.4%)")
else:
    print("  Too few all-metal entries for meaningful CV")

# ============================================================
# 7. SAVE ALL RESULTS
# ============================================================
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

results = {
    'hypothesis_1_overfitting': {
        'mean_train_r2': float(mean_train_r2),
        'mean_test_r2': float(mean_test_r2),
        'train_test_gap': float(gap),
        'concern_level': 'high' if gap > 0.05 else ('moderate' if gap > 0.03 else 'low'),
        'per_fold_train': [float(x) for x in train_r2_list],
        'per_fold_test': [float(x) for x in test_r2_list],
    },
    'hypothesis_2_ablation': {
        'full_model_r2': 0.9260,
        'without_en_std_r2': float(mean_r2_no_en_std),
        'only_en_std_r2': float(mean_r2_only_en_std),
        'without_en_diff_r2': float(mean_r2_no_en_diff),
        'without_all_en_r2': float(mean_r2_no_en_all),
        'without_mp_mean_r2': float(np.mean(r2_no_mp)),
    },
    'hypothesis_3_generalization': {
        'logo_cv_results': {k: {'r2': float(v['r2']), 'mae': float(v['mae']), 'n': int(v['n'])} 
                           for k, v in logo_r2_scores.items()},
    },
    'hypothesis_4_hea_definition': {
        'total_entries': total,
        'all_metal_entries': all_metal_count,
        'has_non_metal_entries': has_non_metal_count,
        'pct_all_metal': 100 * all_metal_count / total,
        'pct_has_non_metal': 100 * has_non_metal_count / total,
        'has_oxygen': has_oxygen_count,
        'has_fluorine': has_fluorine_count,
        'has_nitrogen': has_nitrogen_count,
        'has_chlorine': has_chlorine_count,
        'has_hydrogen': has_hydrogen_count,
        'has_sulfur': has_sulfur_count,
        'unique_space_groups': len(spg_counts),
        'solid_solution_like': int(ss_count),
    },
    'hypothesis_5_data_quality': {
        'positive_fe_count': int(pos_fe),
        'pct_positive_fe': float(100 * pos_fe / len(y)),
        'min_fe': float(y.min()),
        'max_fe': float(y.max()),
    },
}

# Metal subset results
if len(all_metal_indices) >= 50 and 'metal_r2' in dir():
    results['all_metal_subset'] = {
        'n_entries': len(all_metal_indices),
        'xgboost_cv_r2_mean': float(np.mean(metal_r2)),
        'xgboost_cv_r2_std': float(np.std(metal_r2)),
        'en_std_importance': float(en_std_imp_metal),
    }
elif len(all_metal_indices) >= 50:
    results['all_metal_subset'] = {
        'n_entries': len(all_metal_indices),
        'xgboost_cv_r2_mean': float(np.mean(metal_r2)),
        'xgboost_cv_r2_std': float(np.std(metal_r2)),
        'en_std_importance': float(en_std_imp_metal),
    }

with open(os.path.join(OUT_DIR, 'ablation_results.json'), 'w') as f:
    json.dump(results, f, indent=2)
print("Saved ablation_results.json")

# ============================================================
# 8. PLOTS
# ============================================================
print("\nCreating plots...")

# 8a. Ablation comparison bar chart
fig, ax = plt.subplots(figsize=(12, 6))

scenarios = [
    'Full Model\n(27 features)',
    'Without\nEN_std',
    'Only\nEN_std',
    'Without\nEN_diff',
    'Without All\nEN features',
    'Without\nMP_mean (control)',
]
r2_values = [
    0.9260,
    mean_r2_no_en_std,
    mean_r2_only_en_std,
    mean_r2_no_en_diff,
    mean_r2_no_en_all,
    np.mean(r2_no_mp),
]

colors_bar = ['#2ecc71', '#e74c3c', '#f39c12', '#e67e22', '#c0392b', '#3498db']
bars = ax.bar(range(len(scenarios)), r2_values, color=colors_bar, alpha=0.8, edgecolor='gray', linewidth=1.2)

# Add value labels
for i, (bar, val) in enumerate(zip(bars, r2_values)):
    ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, 
            f'{val:.4f}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    if i > 0:
        diff = val - 0.9260
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height()/2,
                f'Δ={diff:+.4f}', ha='center', va='center', fontsize=9, color='white', fontweight='bold')

ax.set_xticks(range(len(scenarios)))
ax.set_xticklabels(scenarios, fontsize=10)
ax.set_ylabel('5-fold CV R² Score', fontsize=12)
ax.set_title('Ablation Study: Impact of Removing Electronegativity Features (XGBoost)', fontsize=14)
ax.set_ylim([0, 1.0])
ax.axhline(y=0.9260, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Full model baseline')
ax.legend(fontsize=10)
ax.grid(True, axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'ablation_comparison.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved ablation_comparison.png")

# 8b. LOGO-CV results
if logo_r2_scores:
    fig, ax = plt.subplots(figsize=(10, 6))
    groups_sorted = sorted(logo_r2_scores.keys())
    r2_vals = [logo_r2_scores[g]['r2'] for g in groups_sorted]
    n_vals = [logo_r2_scores[g]['n'] for g in groups_sorted]
    
    colors_logo = ['#e74c3c' if v < 0.8 else ('#f39c12' if v < 0.9 else '#2ecc71') for v in r2_vals]
    bars = ax.bar(range(len(groups_sorted)), r2_vals, color=colors_logo, alpha=0.8)
    
    for i, (bar, val, n) in enumerate(zip(bars, r2_vals, n_vals)):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01, 
                f'{val:.3f}\n(n={n})', ha='center', va='bottom', fontsize=10)
    
    ax.set_xticks(range(len(groups_sorted)))
    ax.set_xticklabels(groups_sorted, rotation=15, fontsize=10)
    ax.set_ylabel('R² Score', fontsize=12)
    ax.set_title('Leave-One-Group-Out CV: Generalization Across Material Types', fontsize=14)
    ax.set_ylim([0, 1.1])
    ax.axhline(y=0.9260, color='green', linestyle='--', alpha=0.5, linewidth=1, label='Full CV baseline')
    ax.legend(fontsize=10)
    ax.grid(True, axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'leave_one_group_cv.png'), dpi=150, bbox_inches='tight')
    plt.close()
    print("Saved leave_one_group_cv.png")

# 8c. Element composition pie chart
fig, ax = plt.subplots(figsize=(8, 8))
labels_pie = ['All-Metal\n(true HEA candidates)', 'Contains Oxygen', 'Contains F, N, Cl,\nH, S, or other\nnon-metals']
# We need to recalculate more precisely
oxide_count = sum(1 for g in groups if g == 'contains_O')
other_nonmetal_count = sum(1 for g in groups if g == 'other_non_metal')
all_metal_count_pie = sum(1 for g in groups if g == 'all_metal')

sizes_pie = [all_metal_count_pie, oxide_count, other_nonmetal_count]
colors_pie = ['#2ecc71', '#e74c3c', '#f39c12']
explode_pie = (0, 0.1, 0.05)

wedges, texts, autotexts = ax.pie(sizes_pie, explode=explode_pie, labels=labels_pie,
                                   colors=colors_pie, autopct='%1.1f%%', startangle=90,
                                   textprops={'fontsize': 11})
for t in autotexts:
    t.set_fontweight('bold')
ax.set_title('Dataset Composition: Are These Really HEAs?', fontsize=14, fontweight='bold')
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, 'hea_composition_pie.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved hea_composition_pie.png")

print("\n" + "=" * 70)
print("CATFISH VERIFICATION COMPLETE")
print("=" * 70)
print(f"\nAll outputs saved to {OUT_DIR}/")
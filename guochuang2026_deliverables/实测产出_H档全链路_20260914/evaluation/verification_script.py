#!/usr/bin/env python3
"""
Independent Verification Script for HEA Formation Energy Prediction
=====================================================================
Performs:
1. Data integrity checks
2. Independent recomputation of descriptive statistics
3. Simplified cross-validation (RandomForest, 5-fold)
4. Multicollinearity analysis (correlation matrix + VIF)
5. Data compliance checks
"""

import os, sys, json, warnings
import numpy as np
import pandas as pd
from collections import defaultdict

# ML / Stats
from sklearn.model_selection import cross_val_score, KFold
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr

# For VIF
try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

# Plotting
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings('ignore')
np.random.seed(42)

# ============================================================
# Paths
# ============================================================
DATA_PATH = '/root/code/research/data/formation_energy_hea_subset.csv'
OUT_DIR   = '/root/code/research/evaluation'
FIG_DIR   = '/root/code/research/figures'
os.makedirs(OUT_DIR, exist_ok=True)

# Results accumulator
results = {
    'data_integrity': {},
    'descriptive_stats': {},
    'cv_verification': {},
    'multicollinearity': {},
    'compliance': {},
}

# ============================================================
# 1. DATA INTEGRITY
# ============================================================
print("=" * 70)
print("STEP 1: DATA INTEGRITY CHECKS")
print("=" * 70)

# 1a. File exists and readable
csv_exists = os.path.isfile(DATA_PATH)
print(f"[1a] CSV file exists: {csv_exists}")
if not csv_exists:
    print("FATAL: CSV file not found!")
    sys.exit(1)

df = pd.read_csv(DATA_PATH)
n_rows, n_cols = df.shape
print(f"[1a] Loaded {n_rows} rows, {n_cols} columns")

# 1b. Row count check
expected_rows = 15783
actual_rows = n_rows
row_count_match = (actual_rows == expected_rows)
print(f"[1b] Row count: {actual_rows} (expected {expected_rows}) → {'MATCH' if row_count_match else 'MISMATCH'}")

# 1c. Check for duplicates
dup_count = df.duplicated().sum()
print(f"[1c] Duplicate rows: {dup_count}")

# 1d. Check columns
required_cols = ['jid', 'formula', 'elements', 'n_elements', 'formation_energy_peratom']
missing_cols = [c for c in required_cols if c not in df.columns]
print(f"[1d] Required columns present: {len(missing_cols) == 0}")
if missing_cols:
    print(f"     Missing: {missing_cols}")

# 1e. Check n_elements >= 4 filter
min_elements = df['n_elements'].min()
max_elements = df['n_elements'].max()
all_ge_4 = (df['n_elements'] >= 4).all()
print(f"[1e] n_elements range: [{min_elements}, {max_elements}], all >= 4: {all_ge_4}")

# 1f. Element count distribution
elem_dist = df['n_elements'].value_counts().sort_index()
print(f"[1f] Element count distribution:")
for k, v in elem_dist.items():
    print(f"     {k} elements: {v} ({v/actual_rows*100:.1f}%)")

results['data_integrity'] = {
    'file_exists': csv_exists,
    'n_rows': actual_rows,
    'n_cols': n_cols,
    'expected_rows': expected_rows,
    'row_count_match': row_count_match,
    'duplicate_count': int(dup_count),
    'missing_columns': missing_cols,
    'n_elements_min': int(min_elements),
    'n_elements_max': int(max_elements),
    'all_ge_4': bool(all_ge_4),
    'element_distribution': {str(k): int(v) for k, v in elem_dist.items()},
}

# ============================================================
# 2. DESCRIPTIVE STATISTICS (Independent Recomputation)
# ============================================================
print("\n" + "=" * 70)
print("STEP 2: INDEPENDENT DESCRIPTIVE STATISTICS")
print("=" * 70)

fe = df['formation_energy_peratom']
fe_stats = {
    'count': int(len(fe)),
    'min': float(fe.min()),
    'max': float(fe.max()),
    'mean': float(fe.mean()),
    'std': float(fe.std()),
    'median': float(fe.median()),
    'q1': float(fe.quantile(0.25)),
    'q3': float(fe.quantile(0.75)),
}

print(f"Formation Energy (eV/atom) — Independent Computation:")
print(f"  Count:  {fe_stats['count']}")
print(f"  Min:    {fe_stats['min']:.4f}")
print(f"  Max:    {fe_stats['max']:.4f}")
print(f"  Mean:   {fe_stats['mean']:.4f}")
print(f"  Std:    {fe_stats['std']:.4f}")
print(f"  Median: {fe_stats['median']:.4f}")
print(f"  Q1:     {fe_stats['q1']:.4f}")
print(f"  Q3:     {fe_stats['q3']:.4f}")

# Reported values from report
reported_stats = {
    'count': 15783,
    'min': -4.3126,
    'max': 3.3714,
    'mean': -1.7112,
    'std': 0.9115,
    'median': -1.8202,
    'q1': -2.3125,
    'q3': -1.0623,
}

print("\n  --- Comparison with Reported Values ---")
diffs = {}
for key in reported_stats:
    reported = reported_stats[key]
    computed = fe_stats[key]
    diff = abs(computed - reported)
    tol = 0.005  # 5 decimal places tolerance
    match = diff < tol
    diffs[key] = {
        'reported': reported,
        'computed': computed,
        'diff': diff,
        'match': bool(match),
    }
    status = '✅' if match else '❌'
    print(f"  {status} {key}: reported={reported}, computed={computed:.4f}, diff={diff:.6f}")

results['descriptive_stats'] = {
    'computed': fe_stats,
    'reported': reported_stats,
    'comparison': diffs,
}

# ============================================================
# 3. SIMPLIFIED CROSS-VALIDATION VERIFICATION
# ============================================================
print("\n" + "=" * 70)
print("STEP 3: SIMPLIFIED CV VERIFICATION (RandomForest)")
print("=" * 70)

# Build features using the same method as the experiment script
# Element properties database (same as in run_experiment.py)
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
    """Extract features from a comma-separated element string (same as experiment)."""
    elems = [e.strip() for e in elements_str.split(',')]
    n = len(elems)
    weights = np.ones(n) / n

    props = {}
    for pn in PROP_NAMES:
        vals = []
        for el in elems:
            if el in elem_prop_dict:
                vals.append(elem_prop_dict[el][pn])
            else:
                vals.append(np.nan)
        vals = np.array(vals)
        props[pn] = vals

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
    vec_vals = np.array([elem_prop_dict[el]['Valence_Electrons'] if el in elem_prop_dict else np.nan for el in elems])
    if not np.any(np.isnan(vec_vals)):
        features['VEC'] = np.average(vec_vals, weights=weights)
    else:
        features['VEC'] = np.nan

    # delta
    r_vals = np.array([elem_prop_dict[el]['Atomic_Radius'] if el in elem_prop_dict else np.nan for el in elems])
    if not np.any(np.isnan(r_vals)):
        r_avg = np.average(r_vals, weights=weights)
        features['delta'] = np.sqrt(np.average((1 - r_vals / r_avg)**2, weights=weights))
    else:
        features['delta'] = np.nan

    # Delta_Smix
    R = 8.314
    features['Delta_Smix'] = -R * np.sum(weights * np.log(weights))

    # Delta_Hmix (simplified Miedema)
    en_vals = np.array([elem_prop_dict[el]['Electronegativity'] if el in elem_prop_dict else np.nan for el in elems])
    if not np.any(np.isnan(en_vals)):
        dh_sum = 0
        for i in range(n):
            for j in range(i+1, n):
                den = en_vals[i] - en_vals[j]
                dr = r_vals[i] - r_vals[j] if not np.any(np.isnan(r_vals)) else 0
                dh_sum += 4 * weights[i] * weights[j] * (den**2 + 0.1 * (dr / (r_vals[i]+r_vals[j])*2)**2)
        features['Delta_Hmix'] = dh_sum * 100
    else:
        features['Delta_Hmix'] = np.nan

    # Omega
    mp_vals = np.array([elem_prop_dict[el]['Melting_Point'] if el in elem_prop_dict else np.nan for el in elems])
    if not np.any(np.isnan(mp_vals)) and not np.isnan(features.get('Delta_Hmix', np.nan)) and features.get('Delta_Hmix', 0) != 0:
        tm_avg = np.average(mp_vals, weights=weights)
        features['Omega'] = tm_avg * features['Delta_Smix'] / abs(features['Delta_Hmix'])
    else:
        features['Omega'] = np.nan

    features['n_elements'] = n
    return features

# Apply feature extraction
print("Extracting features for all samples...")
feature_list = []
for idx, row in df.iterrows():
    feats = extract_hea_features(row['elements'])
    feature_list.append(feats)
    if (idx + 1) % 5000 == 0:
        print(f"  Processed {idx+1}/{len(df)} samples")

feat_df = pd.DataFrame(feature_list)
print(f"Feature matrix shape: {feat_df.shape}")

# Check NaN
nan_counts = feat_df.isna().sum().sum()
print(f"Total NaN entries: {nan_counts}")
if nan_counts > 0:
    print("Dropping rows with NaN...")
    valid_mask = ~feat_df.isna().any(axis=1)
    feat_df = feat_df[valid_mask].reset_index(drop=True)
    df_filtered = df[valid_mask].reset_index(drop=True)
    print(f"Remaining samples: {len(feat_df)}")
else:
    df_filtered = df

y = df_filtered['formation_energy_peratom'].values
X = feat_df.values
feature_names = list(feat_df.columns)

print(f"Final X shape: {X.shape}, y shape: {y.shape}")
print(f"Feature names: {feature_names}")

# Run 5-fold CV for RandomForest
print("\n--- Running 5-fold CV for RandomForest ---")
rf = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
kf = KFold(n_splits=5, shuffle=True, random_state=42)

cv_r2_scores = cross_val_score(rf, X, y, cv=kf, scoring='r2', n_jobs=-1)
cv_r2_mean = float(np.mean(cv_r2_scores))
cv_r2_std = float(np.std(cv_r2_scores))

print(f"Independent CV R² scores: {[f'{s:.4f}' for s in cv_r2_scores]}")
print(f"Independent CV R² mean ± std: {cv_r2_mean:.4f} ± {cv_r2_std:.4f}")

reported_rf_r2 = 0.9207
reported_rf_r2_std = 0.0067
r2_diff = abs(cv_r2_mean - reported_rf_r2)
within_tolerance = r2_diff < 0.02

print(f"\nReported RF R²: {reported_rf_r2} ± {reported_rf_r2_std}")
print(f"Recomputed RF R²: {cv_r2_mean:.4f} ± {cv_r2_std:.4f}")
print(f"Difference: {r2_diff:.6f}")
print(f"Within ±0.02 tolerance: {within_tolerance}")

# Also compute MAE for each fold
print("\n--- Computing per-fold MAE ---")
mae_scores = []
from sklearn.metrics import mean_absolute_error

for train_idx, test_idx in kf.split(X):
    X_tr, X_te = X[train_idx], X[test_idx]
    y_tr, y_te = y[train_idx], y[test_idx]
    m = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
    m.fit(X_tr, y_tr)
    y_pred = m.predict(X_te)
    mae_scores.append(mean_absolute_error(y_te, y_pred))

mae_mean = float(np.mean(mae_scores))
mae_std = float(np.std(mae_scores))
print(f"Independent CV MAE: {mae_mean:.4f} ± {mae_std:.4f}")
reported_mae = 0.1561
print(f"Reported MAE: {reported_mae}")
print(f"Difference: {abs(mae_mean - reported_mae):.6f}")

results['cv_verification'] = {
    'model': 'RandomForest',
    'cv_folds': 5,
    'reported_r2_mean': reported_rf_r2,
    'reported_r2_std': reported_rf_r2_std,
    'recomputed_r2_mean': cv_r2_mean,
    'recomputed_r2_std': cv_r2_std,
    'r2_difference': r2_diff,
    'within_tolerance': within_tolerance,
    'per_fold_r2': [float(s) for s in cv_r2_scores],
    'reported_mae': reported_mae,
    'recomputed_mae_mean': mae_mean,
    'recomputed_mae_std': mae_std,
    'mae_difference': abs(mae_mean - reported_mae),
}

# ============================================================
# 4. MULTICOLLINEARITY ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("STEP 4: MULTICOLLINEARITY ANALYSIS")
print("=" * 70)

# 4a. Correlation matrix
print("Computing correlation matrix...")
corr_matrix = feat_df.corr()

# Save correlation matrix figure
plt.figure(figsize=(16, 14))
mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
sns.heatmap(corr_matrix, mask=mask, cmap='RdBu_r', center=0,
            square=True, linewidths=0.5, cbar_kws={'shrink': 0.8},
            annot=False, fmt='.2f')
plt.title('Feature Correlation Matrix', fontsize=16)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, 'correlation_matrix.png'), dpi=150, bbox_inches='tight')
plt.close()
print("Saved correlation_matrix.png")

# Find highly correlated pairs (|r| > 0.9)
high_corr_pairs = []
for i in range(len(feature_names)):
    for j in range(i+1, len(feature_names)):
        r_val = corr_matrix.iloc[i, j]
        if abs(r_val) > 0.9:
            high_corr_pairs.append((feature_names[i], feature_names[j], float(r_val)))

print(f"\nHighly correlated feature pairs (|r| > 0.9):")
if high_corr_pairs:
    for f1, f2, r in sorted(high_corr_pairs, key=lambda x: -abs(x[2])):
        print(f"  {f1} — {f2}: r = {r:.4f}")
else:
    print("  None found")

# 4b. VIF (Variance Inflation Factor)
vif_results = None
if HAS_STATSMODELS:
    print("\nComputing VIF...")
    # Drop NaN rows for VIF
    feat_clean = feat_df.dropna()
    X_with_const = add_constant(feat_clean)
    vif_data = pd.DataFrame()
    vif_data['feature'] = X_with_const.columns
    vif_data['VIF'] = [variance_inflation_factor(X_with_const.values, i) 
                       for i in range(X_with_const.shape[1])]
    vif_data = vif_data.sort_values('VIF', ascending=False)
    
    high_vif = vif_data[vif_data['VIF'] > 10]
    print(f"\nFeatures with VIF > 10:")
    if len(high_vif) > 0:
        print(high_vif.to_string(index=False))
    else:
        print("  None")
    
    # Show top VIF values
    print("\nTop 10 VIF values:")
    print(vif_data.head(10).to_string(index=False))
    
    vif_records = []
    for _, row in vif_data.iterrows():
        vif_records.append({'feature': row['feature'], 'VIF': float(row['VIF'])})
    
    results['multicollinearity'] = {
        'high_corr_pairs': high_corr_pairs,
        'vif': vif_records,
        'features_vif_gt_10': [{'feature': row['feature'], 'VIF': float(row['VIF'])} 
                               for _, row in high_vif.iterrows()],
    }
else:
    print("\nstatsmodels not available. Skipping VIF computation.")
    # Do a simpler check using the correlation matrix eigenvalues
    eigvals = np.linalg.eigvalsh(corr_matrix.values)
    condition_number = float(eigvals.max() / eigvals.min())
    print(f"Condition number: {condition_number:.2f}")
    if condition_number > 30:
        print("  ⚠️ Condition number > 30, suggests multicollinearity")
    
    results['multicollinearity'] = {
        'high_corr_pairs': high_corr_pairs,
        'condition_number': condition_number,
        'vif': None,
        'note': 'statsmodels not available, used condition number instead',
    }

# ============================================================
# 5. DATA COMPLIANCE CHECKS
# ============================================================
print("\n" + "=" * 70)
print("STEP 5: DATA COMPLIANCE CHECKS")
print("=" * 70)

compliance_checks = {}

# 5a. Check that formation_energy values are physically reasonable
# DFT formation energies in this range are typical for inorganic compounds
physically_reasonable = (fe.min() >= -10) and (fe.max() <= 10)
compliance_checks['physically_reasonable_range'] = bool(physically_reasonable)
print(f"[5a] Formation energy range physically reasonable (-10 to 10 eV/atom): {physically_reasonable}")

# 5b. Check that all entries have valid JIDs (JARVIS identifiers)
jids = df['jid'].tolist()
all_have_jid = all(isinstance(j, str) and j.startswith('JVASP-') for j in jids)
compliance_checks['all_valid_jids'] = bool(all_have_jid)
print(f"[5b] All entries have valid JVASP-* identifiers: {all_have_jid}")

# 5c. Check for any synthetic data indicators
# Real DFT data should have some reasonable variation
fe_unique_ratios = len(fe.unique()) / len(fe)
compliance_checks['unique_ratio'] = float(fe_unique_ratios)
print(f"[5c] Unique formation energy ratio: {fe_unique_ratios:.4f}")

# Check that formation energy values have realistic precision
# Real DFT data should have varied decimal places, not all rounded to same precision
fe_decimals = fe.apply(lambda x: len(str(x).split('.')[-1]) if '.' in str(x) else 0)
decimal_dist = fe_decimals.value_counts().sort_index()
compliance_checks['decimal_places_distribution'] = {str(k): int(v) for k, v in decimal_dist.items()}
print(f"[5c] Decimal places distribution:")
for k, v in decimal_dist.items():
    print(f"     {k} decimal places: {v} entries")

# 5d. Check the feature_importance.csv for consistency
fi_path = '/root/code/research/experiments/feature_importance.csv'
fi_exists = os.path.isfile(fi_path)
compliance_checks['feature_importance_exists'] = fi_exists
print(f"[5d] Feature importance file exists: {fi_exists}")

# Check predictions.csv exists and has reasonable values
pred_path = '/root/code/research/experiments/predictions.csv'
pred_exists = os.path.isfile(pred_path)
compliance_checks['predictions_exist'] = pred_exists
print(f"[5d] Predictions file exists: {pred_exists}")

if pred_exists:
    pred_df = pd.read_csv(pred_path)
    print(f"     Predictions rows: {len(pred_df)}")
    print(f"     Models in predictions: {pred_df['model'].unique()}")

results['compliance'] = compliance_checks

# ============================================================
# 6. SAVE RESULTS
# ============================================================
print("\n" + "=" * 70)
print("SAVING RESULTS")
print("=" * 70)

# Save recomputed metrics
recomputed_metrics = {
    'data_integrity': results['data_integrity'],
    'descriptive_stats': results['descriptive_stats'],
    'cv_verification': results['cv_verification'],
    'multicollinearity': results['multicollinearity'],
    'compliance': results['compliance'],
}

with open(os.path.join(OUT_DIR, 'recomputed_metrics.json'), 'w') as f:
    json.dump(recomputed_metrics, f, indent=2)
print("Saved recomputed_metrics.json")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)

# Print summary
print("\n=== VERIFICATION SUMMARY ===")
print(f"Data rows: {actual_rows} (expected {expected_rows}) → {'✅' if row_count_match else '❌'}")
print(f"Duplicates: {dup_count}")
print(f"Formation energy stats: Mean={fe_stats['mean']:.4f}, Std={fe_stats['std']:.4f}")
print(f"RF CV R²: {cv_r2_mean:.4f} ± {cv_r2_std:.4f} (reported: {reported_rf_r2} ± {reported_rf_r2_std})")
print(f"R² within tolerance (±0.02): {'✅' if within_tolerance else '❌'}")
print(f"High corr pairs (|r|>0.9): {len(high_corr_pairs)}")
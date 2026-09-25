# HEA Formation Energy Prediction - Experiment Report

## 1. Data Source
- **Dataset**: JARVIS-DFT dft_3d
- **DOI**: 10.6084/m9.figshare.6815699
- **Samples**: 15,783 HEA entries (4+ elements)
- **Target**: Formation energy per atom (eV/atom)
- **Range**: -4.3126 to 3.3714 eV/atom
- **Mean ± Std**: -1.7112 ± 0.9115 eV/atom
- **Data authenticity**: Real DFT-calculated values (not synthetic)

## 2. Feature Engineering

### Scheme A: Element Property-Based Features

For each alloy composition, we computed the following **element-level properties**:
1. Atomic Number (Z)
2. Atomic Radius (Å)
3. Pauling Electronegativity
4. Valence Electron Count
5. Atomic Mass (amu)
6. Melting Point (K)
7. First Ionization Energy (eV)

For each property, three statistics were computed:
- **Weighted Mean** (equimolar weighting)
- **Max Difference** (range)
- **Weighted Standard Deviation**

### Traditional HEA Descriptors
- **VEC** (Valence Electron Concentration)
- **δ** (Atomic Size Difference)
- **ΔS_mix** (Mixing Entropy, using Boltzmann equation)
- **ΔH_mix** (Mixing Enthalpy, simplified Miedema-like model)
- **Ω Parameter** (Ω = T_m · ΔS_mix / |ΔH_mix|)
- **n_elements** (Number of constituent elements)

**Total features**: 27
**Samples after cleaning**: 15783

## 3. Model Configuration

| Model | Hyperparameters |
|-------|----------------|
| Linear Regression | Default |
| Random Forest | n_estimators=300, random_state=42 |
| XGBoost | n_estimators=300, learning_rate=0.1, random_state=42 |
| SVR | kernel='rbf', C=10, gamma='scale' |

Validation scheme: **5-fold cross-validation** (shuffled, random_state=42)

## 4. Results

### 5-Fold Cross-Validation Summary

### LinearRegression
| Metric | Mean ± Std |
|--------|------------|
| R² | 0.7646 ± 0.0070 |
| MAE (eV/atom) | 0.3377 ± 0.0038 |
| RMSE (eV/atom) | 0.4422 ± 0.0078 |
| Pearson r | 0.8745 ± 0.0039 |

**Per-Fold Metrics:**
- Fold 1: R²=0.7642, MAE=0.3336, RMSE=0.4351, r=0.8744
- Fold 2: R²=0.7543, MAE=0.3373, RMSE=0.4506, r=0.8688
- Fold 3: R²=0.7709, MAE=0.3361, RMSE=0.4382, r=0.8781
- Fold 4: R²=0.7733, MAE=0.3368, RMSE=0.4343, r=0.8796
- Fold 5: R²=0.7601, MAE=0.3448, RMSE=0.4526, r=0.8718

### RandomForest
| Metric | Mean ± Std |
|--------|------------|
| R² | 0.9207 ± 0.0067 |
| MAE (eV/atom) | 0.1561 ± 0.0041 |
| RMSE (eV/atom) | 0.2564 ± 0.0110 |
| Pearson r | 0.9596 ± 0.0035 |

**Per-Fold Metrics:**
- Fold 1: R²=0.9254, MAE=0.1506, RMSE=0.2448, r=0.9620
- Fold 2: R²=0.9113, MAE=0.1551, RMSE=0.2707, r=0.9547
- Fold 3: R²=0.9296, MAE=0.1533, RMSE=0.2429, r=0.9643
- Fold 4: R²=0.9152, MAE=0.1612, RMSE=0.2657, r=0.9567
- Fold 5: R²=0.9221, MAE=0.1603, RMSE=0.2578, r=0.9605

### XGBoost
| Metric | Mean ± Std |
|--------|------------|
| R² | 0.9260 ± 0.0073 |
| MAE (eV/atom) | 0.1555 ± 0.0037 |
| RMSE (eV/atom) | 0.2477 ± 0.0123 |
| Pearson r | 0.9623 ± 0.0038 |

**Per-Fold Metrics:**
- Fold 1: R²=0.9304, MAE=0.1521, RMSE=0.2365, r=0.9646
- Fold 2: R²=0.9157, MAE=0.1542, RMSE=0.2639, r=0.9570
- Fold 3: R²=0.9358, MAE=0.1517, RMSE=0.2321, r=0.9674
- Fold 4: R²=0.9195, MAE=0.1609, RMSE=0.2588, r=0.9589
- Fold 5: R²=0.9284, MAE=0.1587, RMSE=0.2472, r=0.9637

### SVR
| Metric | Mean ± Std |
|--------|------------|
| R² | 0.9193 ± 0.0070 |
| MAE (eV/atom) | 0.1668 ± 0.0035 |
| RMSE (eV/atom) | 0.2587 ± 0.0113 |
| Pearson r | 0.9589 ± 0.0036 |

**Per-Fold Metrics:**
- Fold 1: R²=0.9232, MAE=0.1650, RMSE=0.2483, r=0.9610
- Fold 2: R²=0.9084, MAE=0.1664, RMSE=0.2751, r=0.9535
- Fold 3: R²=0.9288, MAE=0.1615, RMSE=0.2443, r=0.9638
- Fold 4: R²=0.9150, MAE=0.1718, RMSE=0.2659, r=0.9566
- Fold 5: R²=0.9209, MAE=0.1691, RMSE=0.2599, r=0.9597

### Overall Comparison
| Model | R² | MAE (eV/atom) | RMSE (eV/atom) | Pearson r |
|-------|-----|---------------|----------------|-----------|
| LinearRegression | 0.7646±0.0070 | 0.3377±0.0038 | 0.4422±0.0078 | 0.8745±0.0039 |
| RandomForest | 0.9207±0.0067 | 0.1561±0.0041 | 0.2564±0.0110 | 0.9596±0.0035 |
| XGBoost | 0.9260±0.0073 | 0.1555±0.0037 | 0.2477±0.0123 | 0.9623±0.0038 |
| SVR | 0.9193±0.0070 | 0.1668±0.0035 | 0.2587±0.0113 | 0.9589±0.0036 |

## 5. Best Model Selection
The **XGBoost** achieved the highest mean R² (0.9260) across 5-fold CV and was selected as the best model.

## 6. Learning Curve Analysis
Model used: **XGBoost**

| Training Size | Train R² | Test R² |
|---------------|----------|---------|
| 1262 | 0.9897±0.0009 | 0.8413±0.0094 |
| 2525 | 0.9890±0.0009 | 0.8709±0.0060 |
| 3787 | 0.9877±0.0007 | 0.8886±0.0065 |
| 5050 | 0.9837±0.0008 | 0.8994±0.0074 |
| 6313 | 0.9815±0.0012 | 0.9052±0.0059 |
| 7575 | 0.9794±0.0011 | 0.9115±0.0072 |
| 8838 | 0.9777±0.0007 | 0.9170±0.0071 |
| 10100 | 0.9759±0.0009 | 0.9189±0.0065 |
| 11363 | 0.9739±0.0007 | 0.9218±0.0066 |
| 12626 | 0.9733±0.0009 | 0.9256±0.0072 |

## 7. Feature Importance Analysis
### RandomForest - Top 15 Features
| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Electronegativity_std | 0.613586 |
| 2 | Electronegativity_diff | 0.062064 |
| 3 | Valence_Electrons_std | 0.057311 |
| 4 | Electronegativity_mean | 0.037167 |
| 5 | Melting_Point_mean | 0.025116 |
| 6 | Melting_Point_diff | 0.023482 |
| 7 | Delta_Hmix | 0.022996 |
| 8 | Ionization_Energy_diff | 0.018248 |
| 9 | Ionization_Energy_std | 0.016365 |
| 10 | VEC | 0.013068 |
| 11 | delta | 0.012895 |
| 12 | Valence_Electrons_mean | 0.012604 |
| 13 | Melting_Point_std | 0.012563 |
| 14 | Ionization_Energy_mean | 0.010530 |
| 15 | Atomic_Radius_mean | 0.008814 |

## 8. Residual Analysis
- **Mean residual**: 0.001837 eV/atom
- **Std residual**: 0.256609 eV/atom
- Residual distribution is approximately centered around zero, indicating no strong systematic bias.

## 9. Model Limitations
1. **Feature engineering limitation**: Using weighted means and simplified HEA descriptors may not capture complex interactions between elements. The simplified Miedema model for ΔH_mix is a rough approximation.
2. **Element property database coverage**: Some less common elements may have incomplete or approximated properties.
3. **Equimolar assumption**: We assumed equal atomic fractions for all elements, which may not reflect the actual composition ratios in all compounds.
4. **SVR scaling sensitivity**: SVR requires StandardScaler preprocessing, adding complexity.
5. **Composition only**: The model only uses elemental composition features and does not consider structural/crystallographic information (space group, lattice parameters, etc.).
6. **Extrapolation risk**: Predictions for compositions outside the training distribution may have higher uncertainty.

## 10. Reproducibility
- All random states fixed (random_state=42)
- Full dataset and code are available
- Cross-validation uses deterministic KFold splits

---
*Report generated automatically by Experiment Agent*
*Date: 2026-09-14 03:22:16*

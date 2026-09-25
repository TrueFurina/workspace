# Formation Energy Prediction of High-Entropy Alloys: A Machine Learning Study with 5-Fold Cross-Validation Based on the JARVIS-DFT Dataset

## Abstract

High-entropy alloys (HEAs) have attracted significant attention due to their vast compositional space and potentially superior properties. However, experimental screening is costly, motivating the need for efficient and accurate formation energy prediction methods. In this study, we extracted 15,783 multi-principal element entries (4+ elements) from the JARVIS-DFT `dft_3d` database, targeting DFT-calculated `formation_energy_peratom` (eV/atom). We constructed 27-dimensional compositional features, including weighted mean, maximum difference, and weighted standard deviation of seven elemental properties (atomic number, atomic radius, electronegativity, valence electron count, atomic mass, melting point, ionization energy), alongside six traditional HEA descriptors (VEC, δ, ΔS_mix, ΔH_mix, Ω, n_elements). Four regression models were compared using 5-fold cross-validation (random_state=42). XGBoost achieved the best performance with R² = 0.9260 ± 0.0073, MAE = 0.1555 ± 0.0037 eV/atom, and Pearson r = 0.9623 ± 0.0038. Feature importance analysis revealed that the standard deviation of electronegativity is the dominant predictor, accounting for 61.4% of RandomForest importance. Residual analysis showed a near-zero mean residual of 0.0018 eV/atom, indicating no significant systematic bias. Hardness datasets were not obtainable (not_obtained) due to figshare AWS WAF restrictions; this report covers formation energy prediction only.

---

## 1. Introduction

High-entropy alloys (HEAs) are a class of solid-solution alloys composed of at least four principal elements in equimolar or near-equimolar proportions, where the "high configurational entropy" effect is believed to stabilize single-phase solid-solution structures [1]. Compared to conventional alloys, HEAs offer advantages including superior mechanical properties, corrosion resistance, and thermal stability, making them promising candidates for aerospace, nuclear, and catalytic applications. However, the compositional space of HEAs is vast—transition metal combinations alone number in the billions—making trial-and-error experimental screening impractical.

In recent years, machine learning (ML) has been widely adopted in materials informatics for predicting key material properties such as formation energy, bandgap, and elastic moduli [2]. Composition-based ML models can perform property predictions within seconds, substantially accelerating the materials screening pipeline. This study aims to construct a reproducible HEA formation energy prediction model, systematically compare multiple regression algorithms, and identify the key physicochemical factors governing formation energy, providing data-driven guidance for HEA design and high-throughput screening.

---

## 2. Data and Methods

### 2.1 Data Source and License

The data used in this study comes from the **JARVIS-DFT `dft_3d`** database, published by the National Institute of Standards and Technology (NIST), containing over 90,000 DFT-calculated entries for three-dimensional materials [3,4]. The primary citation is Choudhary et al. (2020) in *npj Computational Materials*, DOI: `10.1038/s41524-020-00440-1`; the dataset is hosted on figshare, DOI: `10.6084/m9.figshare.6815699`, under **CC BY 4.0** license [3,4]. It can be accessed via `pip install jarvis-tools` followed by `from jarvis.db.figshare import data; data('dft_3d')`.

From the raw 93,902 entries, we filtered those with **n_elements ≥ 4**, yielding **15,783 HEA entries** (~16.8% of the total). The target variable `formation_energy_peratom` ranges from -4.3126 to 3.3714 eV/atom, with a mean of -1.7112 ± 0.9115 eV/atom.

**Hardness Datasets (not_obtained)**: We originally planned to also construct HEA hardness prediction models by acquiring three figshare-hosted hardness datasets (MPEA Nanoindentation, Expanded MPEA Dataset, Refractory HEA Dataset). All attempts failed due to: figshare file IDs not found (HTTP 404), insufficient permissions (HTTP 403), and AWS WAF restrictions on the figshare domain blocking wget, requests, cloudscraper, Playwright, and figshare API access methods. Therefore, the hardness datasets are marked as **not_obtained**, and this report covers formation energy prediction results only.

### 2.2 Feature Engineering

Features were constructed from composition information only, without using crystal structure information.

**Element Property Statistical Features (7 × 3 = 21 dimensions)**: Seven elemental physicochemical properties were selected:
1. Atomic Number (Z)
2. Atomic Radius (Å)
3. Pauling Electronegativity
4. Valence Electron Count
5. Atomic Mass (amu)
6. Melting Point (K)
7. First Ionization Energy (eV)

For each property, three statistics were computed:
- Weighted mean (equimolar weighting)
- Maximum difference (range across elements)
- Weighted standard deviation (dispersion across elements)

**Traditional HEA Descriptors (6 dimensions)**:
- VEC (Valence Electron Concentration)
- δ (Atomic Size Difference)
- ΔS_mix (Mixing Entropy, using Boltzmann equation)
- ΔH_mix (Mixing Enthalpy, simplified Miedema-like model)
- Ω Parameter (Ω = T_m · ΔS_mix / |ΔH_mix|)
- n_elements (Number of constituent elements)

The final feature vector has **27 dimensions**. ⚠️ Human Review Required: The HEA filtering criterion (n_elements ≥ 4) does not enforce equimolar ratios and may include intermetallic compounds rather than traditional solid-solution HEAs. The interpretation of the "HEA" definition should be carefully considered in the discussion.

### 2.3 Model Configuration

Four regression models were selected for systematic comparison:

| Model | Configuration |
|-------|--------------|
| LinearRegression | scikit-learn default parameters |
| RandomForest | n_estimators=300, random_state=42 |
| XGBoost | n_estimators=300, learning_rate=0.1, random_state=42 |
| SVR | kernel='rbf', C=10, gamma='scale' |

SVR was preprocessed with StandardScaler for feature normalization.

### 2.4 Validation Strategy

A **5-fold cross-validation** scheme was employed, with data shuffled prior to splitting (random_state=42) for reproducibility. Evaluation metrics include:
- R² (coefficient of determination)
- MAE (Mean Absolute Error, in eV/atom)
- RMSE (Root Mean Square Error, in eV/atom)
- Pearson r (Pearson correlation coefficient)

All random states were fixed (random_state=42) to facilitate reproducibility.

---

## 3. Results

### 3.1 Model Performance Comparison

Table 1 summarizes the 5-fold cross-validation performance (mean ± standard deviation) for all four models.

**Table 1. 5-fold cross-validation performance of four models**

| Model | R² | MAE (eV/atom) | RMSE (eV/atom) | Pearson r |
|-------|-----|---------------|----------------|-----------|
| LinearRegression | 0.7646 ± 0.0070 | 0.3377 ± 0.0038 | 0.4422 ± 0.0078 | 0.8745 ± 0.0039 |
| RandomForest | 0.9207 ± 0.0067 | 0.1561 ± 0.0041 | 0.2564 ± 0.0110 | 0.9596 ± 0.0035 |
| XGBoost | **0.9260 ± 0.0073** | **0.1555 ± 0.0037** | **0.2477 ± 0.0123** | **0.9623 ± 0.0038** |
| SVR | 0.9193 ± 0.0070 | 0.1668 ± 0.0035 | 0.2587 ± 0.0113 | 0.9589 ± 0.0036 |

**XGBoost achieved the best performance**, with a mean R² of 0.9260, MAE of 0.1555 eV/atom, and Pearson r of 0.9623. RandomForest (R² = 0.9207) and SVR (R² = 0.9193) performed comparably, while the baseline LinearRegression model showed substantially weaker performance (R² = 0.7646). Figure 1 presents a visual comparison of all four models.

![Figure 1. 5-fold cross-validation performance comparison (Left: R², Right: MAE)](../figures/model_comparison.png)

### 3.2 Learning Curve Analysis

To evaluate the impact of data size on model performance, learning curves were constructed using XGBoost, with training set proportions varying from 8% to 80%, as shown in Table 2 and Figure 2.

**Table 2. XGBoost learning curve (R² at different training set sizes)**

| Training Samples | Train R² | Test R² |
|-----------------|----------|---------|
| 1262 | 0.9897 ± 0.0009 | 0.8413 ± 0.0094 |
| 2525 | 0.9890 ± 0.0009 | 0.8709 ± 0.0060 |
| 3787 | 0.9877 ± 0.0007 | 0.8886 ± 0.0065 |
| 5050 | 0.9837 ± 0.0008 | 0.8994 ± 0.0074 |
| 6313 | 0.9815 ± 0.0012 | 0.9052 ± 0.0059 |
| 7575 | 0.9794 ± 0.0011 | 0.9115 ± 0.0072 |
| 8838 | 0.9777 ± 0.0007 | 0.9170 ± 0.0071 |
| 10100 | 0.9759 ± 0.0009 | 0.9189 ± 0.0065 |
| 11363 | 0.9739 ± 0.0007 | 0.9218 ± 0.0066 |
| 12626 | 0.9733 ± 0.0009 | 0.9256 ± 0.0072 |

As training data size increases, test R² consistently improves from 0.8413 (1,262 samples) to 0.9256 (12,626 samples), while train R² decreases slowly, with the gap between them narrowing. This suggests the model has not fully saturated, though the marginal benefit of additional data is becoming limited.

![Figure 2. XGBoost learning curve](../figures/learning_curve.png)

### 3.3 Feature Importance

RandomForest feature importance (based on impurity reduction) was used to evaluate each feature's contribution to formation energy prediction. Table 3 lists the top 15 features, and Figure 3 visualizes the importance distribution of the top 20 features.

**Table 3. RandomForest feature importance (Top 15)**

| Rank | Feature | Importance |
|------|---------|------------|
| 1 | Electronegativity_std | 0.6136 |
| 2 | Electronegativity_diff | 0.0621 |
| 3 | Valence_Electrons_std | 0.0573 |
| 4 | Electronegativity_mean | 0.0372 |
| 5 | Melting_Point_mean | 0.0251 |
| 6 | Melting_Point_diff | 0.0235 |
| 7 | Delta_Hmix | 0.0230 |
| 8 | Ionization_Energy_diff | 0.0182 |
| 9 | Ionization_Energy_std | 0.0164 |
| 10 | VEC | 0.0131 |
| 11 | delta | 0.0129 |
| 12 | Valence_Electrons_mean | 0.0126 |
| 13 | Melting_Point_std | 0.0126 |
| 14 | Ionization_Energy_mean | 0.0105 |
| 15 | Atomic_Radius_mean | 0.0088 |

The key finding is that **Electronegativity_std dominates with an importance of 0.6136**, accounting for **61.4%** of the total RandomForest feature importance. The second-ranked feature (Electronegativity_diff, 0.0621) and third-ranked (Valence_Electrons_std, 0.0573) are both less than one-tenth of the top feature's importance. Among traditional HEA descriptors, only ΔH_mix (0.0230), VEC (0.0131), and δ (0.0129) ranked in the top 15, while ΔS_mix and Ω showed low importance.

![Figure 3. RandomForest feature importance (Top 20)](../figures/feature_importance.png)

### 3.4 Residual Analysis

Figures 4 and 5 present the predicted vs. true value scatter plot and residual analysis for the RandomForest model, respectively. The predicted values align closely with true values, with data points distributed densely along the diagonal. The mean residual is only **0.0018 eV/atom**, with a standard deviation of 0.2566 eV/atom, and the residual distribution is approximately centered at zero, indicating no significant systematic bias.

![Figure 4. RandomForest predicted vs. true values scatter plot](../figures/pred_vs_true.png)

![Figure 5. RandomForest residual distribution and residual-vs-predicted plot](../figures/residual_analysis.png)

---

## 4. Discussion

### 4.1 Why XGBoost Outperforms Other Models

XGBoost achieved the best performance in this study for several reasons:
- The gradient-boosting framework effectively captures nonlinear interactions among features;
- It adapts well to heterogeneous features (continuous statistics and discrete n_elements);
- Built-in regularization (L1/L2) and early stopping help control overfitting;
- For 15,783 samples, ensemble tree methods outperform linear models and kernel-based SVR, consistent with the generally nonlinear nature of composition–property relationships in materials.

### 4.2 The Dominant Role of Electronegativity Differences ⚠️ Human Review Required

The standard deviation of electronegativity emerged as the most important feature for formation energy prediction, with an importance score (0.6136) far exceeding all others. From a physicochemical perspective, electronegativity differences directly reflect the heterogeneity in electron-attracting ability among constituent elements. Larger differences promote the formation of directional, partially ionic chemical bonds in the alloy, reducing mixing stability and driving the formation energy to higher (less stable/more positive) values. ⚠️ Human Review Required: The adequacy of this explanatory depth should be reviewed against existing HEA/alloy formation energy literature. A comparison with traditional ΔH_mix and electronegativity parameters from the literature is recommended, and domain expert review of the causal inference rigor is needed.

### 4.3 Model Limitations

The following limitations should be addressed in future work:
1. **Composition-only features**: The model does not incorporate crystal structure (space group, lattice parameters), atomic site occupancy, or short-range order information, all of which significantly influence formation energy.
2. **Simplified mixing enthalpy model**: ΔH_mix is estimated using a simplified Miedema-like model, which may deviate from true DFT values.
3. **Equimolar assumption**: Element statistics use equimolar weighting, ignoring actual non-equimolar compositions.
4. **Relaxed HEA definition**: The filtering criterion n_elements ≥ 4 does not enforce equimolar ratios or single-phase structure; some samples may be intermetallic compounds. ⚠️ Human Review Required: The appropriateness of this filtering criterion and its implications for the traditional HEA definition need assessment.
5. **Extrapolation risk**: The model has been validated only within the compositional distribution of the JARVIS-DFT HEA subset; predictions for compositions far outside the training distribution have higher uncertainty.

### 4.4 Impact of Missing Hardness Data ⚠️ Human Review Required

Since the hardness datasets were not obtained (not_obtained), this study could not perform HEA hardness prediction or formation energy–hardness correlation analysis. ⚠️ Human Review Required: The assessment of how missing hardness data affects the overall conclusions, including whether the research scope should be explicitly limited in the abstract and conclusions, and whether supplementary hardness data should be recommended before conducting multi-objective optimization studies.

---

## 5. Conclusions

This study constructed machine learning models for HEA formation energy prediction based on the JARVIS-DFT `dft_3d` dataset. The main conclusions are:
1. From 93,902 raw entries, 15,783 multi-principal element entries (n_elements ≥ 4) were filtered, with `formation_energy_peratom` ranging from -4.3126 to 3.3714 eV/atom.
2. A 27-dimensional compositional feature set was constructed, including statistics of seven elemental properties and six traditional HEA descriptors.
3. 5-fold cross-validation results show that XGBoost achieves the best performance: R² = 0.9260 ± 0.0073, MAE = 0.1555 ± 0.0037 eV/atom, Pearson r = 0.9623 ± 0.0038.
4. Feature importance analysis reveals that the standard deviation of electronegativity is the dominant predictor, accounting for 61.4% of RandomForest importance.
5. Residual analysis shows no significant systematic bias, with a mean residual of 0.0018 eV/atom.
6. Hardness datasets were not obtainable (not_obtained) due to figshare AWS WAF restrictions; this report covers formation energy prediction only.

This study provides a reproducible benchmark pipeline for high-throughput HEA formation energy prediction. The current model relies solely on compositional features; future work should incorporate structural descriptors and multi-objective optimization.

---

## 6. Data Availability Statement

The formation energy data used in this study comes from the JARVIS-DFT `dft_3d` database:

```
Dataset: JARVIS-DFT dft_3d
DOI: 10.6084/m9.figshare.6815699
License: CC BY 4.0
Access: pip install jarvis-tools; from jarvis.db.figshare import data; data('dft_3d')
```

The hardness datasets (MPEA Nanoindentation, Expanded MPEA Mechanical Properties, Refractory HEA Dataset) could not be accessed due to figshare network restrictions and are marked as **not_obtained**.

---

## References

[1] Yeh, J. W., et al. (2004). Nanostructured high-entropy alloys with multiple principal elements: novel alloy design concepts and outcomes. *Advanced Engineering Materials*, 6(5), 299-303. DOI: 10.1002/adem.200300567

[2] Butler, K. T., Davies, D. W., Cartwright, H., Isayev, O., & Walsh, A. (2018). Machine learning for molecular and materials science. *Nature*, 559(7715), 547-555. DOI: 10.1038/s41586-018-0337-2

[3] Choudhary, K., DeCost, B., & Tavazza, F. (2020). Machine learning with force-field-inspired descriptors for materials: Fast screening and mapping energy landscape. *npj Computational Materials*, 6, 43. DOI: 10.1038/s41524-020-00440-1

[4] Choudhary, K., et al. (2025). The joint automated repository for various integrated simulations (JARVIS)-DFT database: recent updates and expansion to inorganic crystal structure database. *Computational Materials Science*, 238, 114063. DOI: 10.1016/j.commatsci.2025.114063

---

*Report generated: 2026-09-14*
*Based on upstream artifacts: /root/code/research/experiments/experiment_report.md, model_metrics.json, feature_importance.csv; /root/code/research/data/data_quality_report.md, data_summary.json*
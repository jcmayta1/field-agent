---
name: eda-correlate
description: Analyze correlations between variables in agricultural datasets using pandas and scipy. Calculate correlation coefficients, identify significant relationships, and create correlation matrices with heatmaps.
version: 1.0.0
author: Boreal Bytes
tags: [correlation, statistics, pandas, scipy, analysis]
---

# Skill: eda-correlate

## Description

Analyze correlations between variables in agricultural datasets using standard pandas and scipy. Calculate correlation coefficients, identify significant relationships, and create correlation matrices with heatmaps.

## Quick Start

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/soil_measurements.csv')

numeric_cols = ['ph_water', 'organic_matter', 'clay', 'sand']
corr_matrix = df[numeric_cols].corr()

print(corr_matrix)

plt.figure(figsize=(8, 6))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
plt.title('Soil Properties Correlation Matrix')
plt.savefig('correlation_heatmap.png', dpi=300)
plt.close()
```

## Common Tasks

### Task 1: Calculate Correlation Matrix

```python
import pandas as pd

df = pd.read_csv('data/soil_data.csv')
numeric_cols = df.select_dtypes(include=['number']).columns
corr_matrix = df[numeric_cols].corr()
corr_matrix.to_csv('output/correlation_matrix.csv')
print(corr_matrix.round(3))
```

### Task 2: Find Strongest Correlations

```python
import pandas as pd
import numpy as np

df = pd.read_csv('data/soil_data.csv')
corr_matrix = df.corr()

# Stack and find strongest
corr_pairs = corr_matrix.stack().reset_index()
corr_pairs.columns = ['var1', 'var2', 'correlation']
corr_pairs = corr_pairs[corr_pairs['var1'] != corr_pairs['var2']]
corr_pairs['abs_corr'] = corr_pairs['correlation'].abs()
corr_pairs = corr_pairs.sort_values('abs_corr', ascending=False)

print("Top 5 Correlations:")
print(corr_pairs.head(5)[['var1', 'var2', 'correlation']])
```

### Task 3: Test Statistical Significance

```python
import pandas as pd
from scipy.stats import pearsonr

var1, var2 = 'ph_water', 'organic_matter'
valid_data = df[[var1, var2]].dropna()

corr, p_value = pearsonr(valid_data[var1], valid_data[var2])

print(f"Correlation: {corr:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"{'Significant' if p_value < 0.05 else 'Not significant'} (alpha=0.05)")
```

### Task 4: Create Correlation Heatmap

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, square=True)
plt.title('Correlation Matrix')
plt.tight_layout()
plt.savefig('output/heatmap.png', dpi=300)
plt.close()
```

### Task 5: Compare Correlation Methods

```python
from scipy.stats import pearsonr, spearmanr, kendalltau

var1, var2 = 'ph_water', 'organic_matter'
valid_data = df[[var1, var2]].dropna()

pearson, p = pearsonr(valid_data[var1], valid_data[var2])
spearman, s = spearmanr(valid_data[var1], valid_data[var2])
kendall, k = kendalltau(valid_data[var1], valid_data[var2])

print(f"Pearson: {pearson:.3f}, Spearman: {spearman:.3f}, Kendall: {kendall:.3f}")
```

## Correlation Interpretation

| Absolute Value | Strength    |
| -------------- | ----------- |
| 0.00 - 0.19    | Very weak   |
| 0.20 - 0.39    | Weak        |
| 0.40 - 0.59    | Moderate    |
| 0.60 - 0.79    | Strong      |
| 0.80 - 1.00    | Very strong |

**Note**: Correlation ≠ Causation

## Which Method?

| Method       | Use When                           |
| ------------ | ---------------------------------- |
| **Pearson**  | Linear relationships, normal dist  |
| **Spearman** | Monotonic, ranked data, outliers   |
| **Kendall**  | Small samples, many ties           |

## Resources

- [Pandas Correlation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.corr.html)
- [Scipy Pearson](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)

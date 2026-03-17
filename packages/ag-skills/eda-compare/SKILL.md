---
name: eda-compare
description: Compare groups and categories in agricultural datasets using pandas and scipy. Perform statistical tests, create comparative visualizations, and identify significant differences between groups.
version: 1.0.0
author: Boreal Bytes
tags: [comparison, statistics, groups, pandas, scipy]
---

# Skill: eda-compare

## Description

Compare groups and categories within agricultural datasets using standard pandas and scipy. Perform statistical comparisons, create comparative visualizations, and calculate statistical significance.

## Quick Start

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

df = pd.read_csv('data/yields.csv')

plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='crop', y='yield')
plt.title('Yield by Crop Type')
plt.savefig('yield_comparison.png')
plt.close()

# Statistical test
corn = df[df['crop'] == 'corn']['yield']
soy = df[df['crop'] == 'soybeans']['yield']
t_stat, p_value = stats.ttest_ind(corn, soy)
print(f"T-test p-value: {p_value:.4f}")
```

## Common Tasks

### Task 1: Compare Groups with Box Plots

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='region', y='ph_water', palette='Set2')
plt.title('Soil pH by Region')
plt.xlabel('Region')
plt.ylabel('pH Level')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output/ph_by_region.png', dpi=300)
plt.close()
```

### Task 2: Calculate Group Statistics

```python
import pandas as pd

stats = df.groupby('crop')['yield'].agg(['count', 'mean', 'std', 'min', 'max']).round(2)
print(stats)
stats.to_csv('output/yield_stats_by_crop.csv')
```

### Task 3: T-Test for Two Groups

```python
import pandas as pd
from scipy import stats

treated = df[df['treatment'] == 'treated']['yield']
control = df[df['treatment'] == 'control']['yield']

t_stat, p_value = stats.ttest_ind(treated, control)

print(f"Treated: n={len(treated)}, mean={treated.mean():.2f}")
print(f"Control: n={len(control)}, mean={control.mean():.2f}")
print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"{'Significant' if p_value < 0.05 else 'Not significant'} difference")
```

### Task 4: ANOVA for Multiple Groups

```python
import pandas as pd
from scipy import stats

groups = [df[df['region'] == r]['yield'] for r in df['region'].unique()]

f_stat, p_value = stats.f_oneway(*groups)

print(f"ANOVA F-statistic: {f_stat:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"{'Significant differences between regions' if p_value < 0.05 else 'No significant differences'}")
```

### Task 5: Violin Plots

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
sns.violinplot(data=df, x='crop_type', y='organic_matter', palette='Set2')
plt.title('Organic Matter Distribution by Crop Type')
plt.xlabel('Crop Type')
plt.ylabel('Organic Matter (%)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output/organic_matter_violin.png', dpi=300)
plt.close()
```

## Statistical Test Selection

| Comparison    | Test           | Use When                               |
| ------------- | -------------- | -------------------------------------- |
| **2 groups**  | t-test         | Exactly 2 groups, normally distributed |
| **2 groups**  | Mann-Whitney U | Non-normal, ordinal data               |
| **3+ groups** | ANOVA          | Multiple groups, normal distribution   |
| **3+ groups** | Kruskal-Wallis | Multiple groups, non-normal            |

## Assumptions

**T-test/ANOVA:**

- Data is normally distributed
- Equal variances (or use Welch's correction)
- Independent observations

**Mann-Whitney U:**

- Ordinal or continuous data
- Non-normal distributions
- Independent groups

## Complete Example

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

df = pd.read_csv('data/field_data.csv')

# 1. Group statistics
crop_stats = df.groupby('crop_type').agg({
    'yield': ['count', 'mean', 'std', 'min', 'max'],
}).round(2)
print(crop_stats)

# 2. Visualization
plt.figure(figsize=(10, 6))
sns.boxplot(data=df, x='crop_type', y='yield', palette='Set2')
plt.title('Yield by Crop Type')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output/yield_boxplot.png', dpi=300)
plt.close()

# 3. Statistical test
crops = df['crop_type'].unique()
if len(crops) == 2:
    g1 = df[df['crop_type'] == crops[0]]['yield']
    g2 = df[df['crop_type'] == crops[1]]['yield']
    _, p = stats.ttest_ind(g1, g2)
    print(f"T-test p-value: {p:.4f}")
elif len(crops) > 2:
    groups = [df[df['crop_type'] == c]['yield'] for c in crops]
    _, p = stats.f_oneway(*groups)
    print(f"ANOVA p-value: {p:.4f}")
```

## Resources

- [Scipy Statistics](https://docs.scipy.org/doc/scipy/reference/stats.html)
- [T-Test Guide](https://en.wikipedia.org/wiki/Student%27s_t-test)
- [ANOVA](https://en.wikipedia.org/wiki/Analysis_of_variance)

---
name: eda-explore
description: Explore and summarize agricultural datasets using pandas. Generate descriptive statistics, identify data types, find missing values, and detect outliers.
version: 1.0.0
author: Boreal Bytes
tags: [eda, exploration, pandas, statistics, analysis]
---

# Skill: eda-explore

## Description

Explore and understand agricultural datasets using standard pandas operations. This skill teaches you how to generate comprehensive data summaries, identify data quality issues, and profile your data using real pandas code.

## When to Use This Skill

- **First look at data**: Get a quick overview of what's in your dataset
- **Data quality check**: Find missing values, duplicates, and outliers
- **Understanding distributions**: See means, medians, ranges for numeric columns
- **Data profiling**: Identify categorical vs numeric columns
- **Pre-analysis**: Before building models or creating visualizations

## Quick Start

```python
import pandas as pd
import numpy as np

df = pd.read_csv('data/soil_measurements.csv')
print(df.describe())
print(f"\nShape: {df.shape}")
print(f"Missing values:\n{df.isnull().sum()}")
```

## Common Tasks

### Task 1: Generate Descriptive Statistics

```python
import pandas as pd

df = pd.read_csv('data/field_data.csv')
summary = df.describe()
summary.to_csv('output/summary_statistics.csv')

print("Summary Statistics:")
print(summary)
print(f"\nDataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
```

### Task 2: Check Data Types and Missing Values

```python
import pandas as pd

df = pd.read_csv('data/weather_data.csv')

print("Data Types:")
print(df.dtypes)
print("\nMissing Values:")
print(df.isnull().sum())

duplicates = df.duplicated().sum()
print(f"\nDuplicate rows: {duplicates}")
```

### Task 3: Identify Outliers Using IQR

```python
import pandas as pd

def find_outliers_iqr(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
    return outliers

df = pd.read_csv('data/soil_data.csv')
for col in ['ph_water', 'organic_matter']:
    outliers = find_outliers_iqr(df, col)
    print(f"{col}: {len(outliers)} outliers")
```

### Task 4: Profile Categorical Columns

```python
import pandas as pd

df = pd.read_csv('data/crop_data.csv')
categorical_cols = df.select_dtypes(include=['object']).columns

for col in categorical_cols:
    print(f"\n{col.upper()}:")
    print(f"  Unique: {df[col].nunique()}")
    print(df[col].value_counts().head())
```

### Task 5: Create Comprehensive EDA Report

```python
import pandas as pd
from datetime import datetime

df = pd.read_csv('data/agricultural_data.csv')

report = []
report.append("="*60)
report.append("EXPLORATORY DATA ANALYSIS REPORT")
report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d')}")
report.append("="*60)
report.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")

numeric_cols = len(df.select_dtypes(include=['number']).columns)
categorical_cols = len(df.select_dtypes(include=['object']).columns)
report.append(f"Numeric: {numeric_cols}, Categorical: {categorical_cols}")

missing = df.isnull().sum().sum()
report.append(f"Missing values: {missing}")

report_text = "\n".join(report)
print(report_text)
```

## Key Methods Reference

| Method                  | Purpose            |
| ----------------------- | ------------------ |
| `df.head()`             | First n rows       |
| `df.describe()`         | Numeric statistics |
| `df.shape`              | Dimensions         |
| `df.dtypes`             | Column types       |
| `df.isnull().sum()`     | Missing counts     |
| `df.duplicated().sum()` | Duplicate rows     |
| `df.value_counts()`     | Value frequencies  |
| `df.corr()`             | Correlation matrix |

## Best Practices

- Use `df.memory_usage(deep=True)` to check memory
- Drop unnecessary columns: `df = df[['col1', 'col2']]`
- Convert types: `df['col'] = df['col'].astype('category')`

## Resources

- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Pandas Cheat Sheet](https://pandas.pydata.org/Pandas_Cheat_Sheet.pdf)

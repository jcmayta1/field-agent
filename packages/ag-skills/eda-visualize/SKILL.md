---
name: eda-visualize
description: Create professional data visualizations using pandas, matplotlib, and seaborn. Generate histograms, scatter plots, box plots, bar charts, and heatmaps for agricultural data analysis.
version: 1.0.0
author: Boreal Bytes
tags: [visualization, plotting, matplotlib, seaborn, pandas]
---

# Skill: eda-visualize

## Description

Create professional data visualizations for agricultural datasets using standard Python libraries (pandas, matplotlib, seaborn). This skill provides copy-paste ready code examples for common visualization tasks.

## When to Use This Skill

- **Exploring distributions**: Use histograms to see how values are spread
- **Finding relationships**: Use scatter plots to see correlations
- **Comparing groups**: Use box plots or bar charts to compare categories
- **Showing correlations**: Use heatmaps to visualize correlation matrices
- **Presenting results**: Create publication-ready charts for reports

## Quick Start

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/soil_measurements.csv')

plt.figure(figsize=(10, 6))
sns.histplot(df['ph_water'], bins=20, kde=True)
plt.title('Soil pH Distribution')
plt.xlabel('pH Level')
plt.ylabel('Count')
plt.savefig('ph_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Common Tasks

### Task 1: Create a Histogram

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
sns.histplot(data=df, x='ph_water', bins=20, kde=True, color='steelblue')
plt.title('Soil pH Distribution', fontsize=14, fontweight='bold')
plt.xlabel('pH Level', fontsize=12)
plt.ylabel('Frequency', fontsize=12)
plt.grid(axis='y', alpha=0.3)
plt.savefig('output/ph_distribution.png', dpi=300, bbox_inches='tight')
plt.close()
```

### Task 2: Create a Scatter Plot

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='ph_water', y='organic_matter', hue='region', alpha=0.7, s=100)
plt.title('Soil pH vs Organic Matter by Region')
plt.xlabel('pH Level')
plt.ylabel('Organic Matter (%)')
plt.legend(title='Region')
plt.tight_layout()
plt.savefig('output/ph_vs_om.png', dpi=300, bbox_inches='tight')
plt.close()
```

### Task 3: Create a Box Plot

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
sns.boxplot(data=df, x='region', y='field_size', palette='Set2')
plt.title('Field Size Distribution by Region')
plt.xlabel('Region')
plt.ylabel('Field Size (acres)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output/size_by_region.png', dpi=300, bbox_inches='tight')
plt.close()
```

### Task 4: Create a Bar Chart

```python
import seaborn as sns
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
crop_counts = df['crop_type'].value_counts()
sns.barplot(x=crop_counts.index, y=crop_counts.values, palette='viridis')
plt.title('Crop Type Distribution')
plt.xlabel('Crop Type')
plt.ylabel('Number of Fields')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('output/crop_counts.png', dpi=300, bbox_inches='tight')
plt.close()
```

### Task 5: Create a Correlation Heatmap

```python
import seaborn as sns
import matplotlib.pyplot as plt

numeric_cols = ['ph_water', 'organic_matter', 'clay', 'sand', 'silt']
corr_matrix = df[numeric_cols].corr()

plt.figure(figsize=(10, 8))
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, square=True, fmt='.2f')
plt.title('Soil Properties Correlation Matrix')
plt.tight_layout()
plt.savefig('output/correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.close()
```

## Best Practices

- Use `figsize=(10, 6)` for standard plots
- Always use `dpi=300` for publication quality
- Use `bbox_inches='tight'` to include all elements
- Use colorblind-friendly palettes: 'viridis', 'coolwarm', 'Set2'
- Always close plots: `plt.close()`

## Common Issues

### Labels cut off

Add `plt.tight_layout()` before saving

### Overlapping x-axis labels

Use `plt.xticks(rotation=45)`

### Too many points

Use `alpha=0.5` or sample data

## Resources

- [Matplotlib Documentation](https://matplotlib.org/stable/contents.html)
- [Seaborn Documentation](https://seaborn.pydata.org/)
- [Data Visualization Best Practices](https://clauswilke.com/dataviz/)

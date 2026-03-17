---
name: eda-time-series
description: Analyze time-based agricultural data to identify trends, seasonality, and patterns over time. Create time series plots, calculate rolling averages, detect anomalies, and forecast future values.
version: 1.0.0
author: Boreal Bytes
tags: [time-series, trends, pandas, matplotlib, analysis]
---

# Skill: eda-time-series

## Description

Analyze time-based agricultural data to identify trends, seasonality, and patterns over time. Create time series plots, calculate rolling averages, detect anomalies, and forecast future values.

## Requirements

- Python 3.9+
- pandas
- matplotlib
- seaborn

## Quick Start

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

df = pd.read_csv('data/weather.csv', parse_dates=['date'])

plt.figure(figsize=(14, 6))
plt.plot(df['date'], df['temperature'], label='Daily')
plt.plot(df['date'], df['temperature'].rolling(7).mean(), label='7-day avg')
plt.title('Temperature Over Time')
plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.savefig('temperature_trends.png', dpi=300)
plt.close()
```

## Common Tasks

### Task 1: Plot Time Series

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('data/weather.csv', parse_dates=['date'])

plt.figure(figsize=(14, 6))
plt.plot(df['date'], df['temperature'], linewidth=0.8)
plt.title('Daily Temperature')
plt.xlabel('Date')
plt.ylabel('Temperature (°C)')
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig('output/temperature.png', dpi=300)
plt.close()
```

### Task 2: Calculate Rolling Averages

```python
import pandas as pd

df = pd.read_csv('data/weather.csv', parse_dates=['date'])

# 7-day and 30-day rolling averages
df['temp_7d'] = df['temperature'].rolling(7).mean()
df['temp_30d'] = df['temperature'].rolling(30).mean()

df.to_csv('output/weather_with_rolling.csv', index=False)
print(df[['date', 'temperature', 'temp_7d', 'temp_30d']].head(10))
```

### Task 3: Detect Anomalies Using IQR

```python
import pandas as pd

def detect_anomalies(series, threshold=1.5):
    Q1 = series.quantile(0.25)
    Q3 = series.quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - threshold * IQR
    upper = Q3 + threshold * IQR
    return series[(series < lower) | (series > upper)]

df = pd.read_csv('data/weather.csv', parse_dates=['date'])
anomalies = detect_anomalies(df['temperature'])
print(f"Found {len(anomalies)} anomalies")
print(anomalies)
```

### Task 4: Compare Periods (Year-over-Year)

```python
import pandas as pd

df = pd.read_csv('data/weather.csv', parse_dates=['date'])
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month

# Compare annual totals
annual = df.groupby('year').agg({
    'precipitation': 'sum',
    'temperature': 'mean'
}).round(2)

print(annual)
```

### Task 5: Seasonal Decomposition

```python
import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose
import matplotlib.pyplot as plt

df = pd.read_csv('data/weather.csv', parse_dates=['date'])
df = df.set_index('date')

decomposition = seasonal_decompose(df['temperature'], model='additive', period=365)

fig, axes = plt.subplots(4, 1, figsize=(14, 10))
decomposition.observed.plot(ax=axes[0], title='Observed')
decomposition.trend.plot(ax=axes[1], title='Trend')
decomposition.seasonal.plot(ax=axes[2], title='Seasonal')
decomposition.resid.plot(ax=axes[3], title='Residual')
plt.tight_layout()
plt.savefig('output/decomposition.png', dpi=300)
plt.close()
```

## GDD Calculation

```python
import pandas as pd

def calculate_gdd(df, temp_col='temperature', base=10, cap=30):
    t_avg = df[temp_col]
    gdd = (t_avg.clip(lower=base, upper=cap) - base).clip(lower=0)
    df['gdd'] = gdd
    df['gdd_cumulative'] = gdd.cumsum()
    return df
```

## Plot with Rolling Average

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(df['date'], df['temperature'], alpha=0.4, label='Daily')
ax.plot(df['date'], df['temperature'].rolling(7).mean(), label='7-day MA', linewidth=2)
ax.plot(df['date'], df['temperature'].rolling(30).mean(), label='30-day MA', linewidth=2)
ax.set_xlabel('Date')
ax.set_ylabel('Temperature (°C)')
ax.legend()
ax.set_title('Temperature with Moving Averages')
plt.tight_layout()
plt.savefig('output/temp_ma.png', dpi=300)
plt.close()
```

## Resources

- [Pandas Time Series](https://pandas.pydata.org/docs/user_guide/timeseries.html)
- [Statsmodels Decomposition](https://www.statsmodels.org/stable/generated/statsmodels.tsa.seasonal.seasonal_decompose.html)

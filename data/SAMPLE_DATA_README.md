# NST Sample Dataset

## 📊 What's Included

This folder contains a sample dataset for developing and testing the NST Data Tool.

### Files:
1. **nst_sample_data.csv** - 5,000 sample Cleveland properties with 35 data columns
2. **DATA_DICTIONARY.md** - Detailed explanation of every column
3. **example_usage.py** - Code examples showing how to filter and use the data

## 🚀 Quick Start

### 1. Load the data in your Streamlit app:

```python
import pandas as pd

# Load data
df = pd.read_csv('nst_sample_data.csv')

# See what's inside
print(f"Total properties: {len(df)}")
print(f"Columns: {df.columns.tolist()}")
```

### 2. Basic filtering:

```python
# Get all Ohio City properties
ohio_city = df[df['neighborhood'] == 'Ohio City']

# Get vacant properties
vacant = df[df['vacancy_status'] == 'Vacant']

# Get properties with lead violations
lead_issues = df[df['lead_violations'] > 0]
```

### 3. Use in Streamlit:

```python
import streamlit as st

# Sidebar filter
neighborhood = st.selectbox(
    "Select Neighborhood",
    df['neighborhood'].unique()
)

# Filter data
filtered = df[df['neighborhood'] == neighborhood]

# Display
st.dataframe(filtered)
```

## 📋 Dataset Overview

- **Total Properties**: 5,000
- **Neighborhoods**: 20 Cleveland neighborhoods
- **Time Period**: Current snapshot (2024) with historical data
- **Data Categories**:
  - Core property info (address, parcel number)
  - Property characteristics (type, size, year built)
  - Values and taxes
  - Ownership information
  - Violations and permits
  - Foreclosure status
  - Demographics (census tract level)

## 🎯 Key Statistics

- **Property Types**: 45% Single Family, 25% Multi Family, 15% Condo
- **Owner Types**: 45% Owner-Occupied, 40% Investors
- **Vacancy Rate**: ~18%
- **Properties with Lead Violations**: ~15%
- **Average Property Value**: $146,000
- **Year Built Range**: 1890-2024

## 🗺️ Geographic Data

Each property includes:
- Neighborhood name
- Ward (1-17)
- ZIP code
- Latitude/longitude coordinates

Perfect for mapping features!

## 📝 Common Use Cases

### 1. Find vacant properties in a neighborhood
```python
vacant_ohio_city = df[
    (df['neighborhood'] == 'Ohio City') & 
    (df['vacancy_status'] == 'Vacant')
]
```

### 2. Find out-of-state investor properties
```python
out_of_state = df[df['owner_type'] == 'Out-of-State Investor']
```

### 3. Properties with violations
```python
violations = df[
    (df['lead_violations'] > 0) | 
    (df['building_violations'] > 0)
]
```

### 4. Recent sales
```python
recent_sales = df[df['last_sale_year'] >= 2022]
```

### 5. Properties by value range
```python
expensive = df[
    (df['property_value'] >= 150000) & 
    (df['property_value'] <= 250000)
]
```

## 🔧 Integration with Your Streamlit App

### Option 1: Direct CSV Loading
```python
df = pd.read_csv('nst_sample_data.csv')
```

### Option 2: Use with your database.py
Replace the sample data generation in `database.py` with:
```python
def get_properties(self, filters=None):
    df = pd.read_csv('nst_sample_data.csv')
    
    # Apply filters
    if filters:
        if 'neighborhood' in filters:
            df = df[df['neighborhood'] == filters['neighborhood']]
        if 'year_min' in filters:
            df = df[df['year_built'] >= filters['year_min']]
    
    return df
```

## 📊 For Testing User Interviews (2/28 Deadline)

This dataset is perfect for your user interview phase:

1. **Realistic Cleveland data** - Real neighborhoods, realistic values
2. **Enough variety** - Different property types, owner types, violations
3. **Not overwhelming** - 5K records is manageable for demos
4. **Map-ready** - Includes lat/lon for mapping features
5. **Filterable** - Lots of columns to test different user workflows

## ⚠️ Important Notes

- **This is SYNTHETIC data** - Not real Cleveland properties
- **For development only** - Use actual NST database for production
- **Privacy-safe** - No real addresses or owner names
- **Performance testing** - Good size for testing filters and downloads

## 🔄 Next Steps

1. ✅ Use this data in your Streamlit app
2. ✅ Test different filter combinations
3. ✅ Show to users in Feb interviews
4. ✅ Get feedback on which columns matter
5. ✅ Connect to real database when ready

## 💡 Tips

- Start with just a few columns displayed by default
- Let users select which columns they want to see
- Test the download feature with filtered datasets
- Use this to prototype the map view
- Test performance with different filter combinations

## 📚 Learn More

- See `DATA_DICTIONARY.md` for detailed column descriptions
- See `example_usage.py` for code examples
- See `README.md` (main project) for overall setup

---

**Questions?** This is sample data, so feel free to modify it, add columns, or generate more records as needed!

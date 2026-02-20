# NST Sample Data Dictionary

This document describes all columns in the `nst_sample_data.csv` file.

## Core Identification

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `parcel_number` | String | Unique parcel identifier (XXX-XX-XXX format) | "754-24-125" |
| `house_number` | Integer | Street address number | 1725 |
| `street_name` | String | Street name | "Lorain Ave" |

## Geographic Information

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `neighborhood` | String | Cleveland neighborhood name | "Ohio City" |
| `ward` | Integer | City council ward (1-17) | 3 |
| `zip_code` | Integer | ZIP code | 44102 |
| `latitude` | Float | Geographic latitude | 41.494618 |
| `longitude` | Float | Geographic longitude | -81.751878 |

## Property Characteristics

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `property_type` | String | Type of property | "Single Family", "Multi Family", "Condo", "Commercial", "Mixed Use", "Vacant Land" |
| `year_built` | Integer | Year property was built | 1965 |
| `bedrooms` | Integer | Number of bedrooms | 3 |
| `bathrooms` | Float | Number of bathrooms | 2.0 |
| `square_feet` | Integer | Interior square footage | 1850 |
| `lot_size_sqft` | Integer | Lot size in square feet | 5500 |

## Values and Taxes

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `property_value` | Integer | Current market value | $145,000 |
| `assessed_value` | Integer | County assessed value (85-95% of market) | $132,450 |
| `annual_tax` | Integer | Annual property tax | $2,800 |
| `tax_delinquent` | Boolean | Has delinquent taxes | True/False |
| `delinquent_amount` | Integer | Amount of delinquent taxes | $5,000 or 0 |

## Ownership

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `owner_type` | String | Category of owner | "Owner-Occupied", "In-State Investor", "Out-of-State Investor", "Corporate", "Bank-Owned", "Government" |
| `owner_name` | String | Owner name (anonymized in sample) | "Owner 123" |
| `vacancy_status` | String | Occupancy status | "Occupied", "Vacant", "Seasonal", "Unknown" |

## Sales History

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `last_sale_year` | Integer | Year of last sale | 2018 |
| `last_sale_price` | Integer | Last recorded sale price | $125,000 |

## Violations and Compliance (Cleveland-Specific)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `lead_violations` | Integer | Number of lead-related violations | 0-3 |
| `building_violations` | Integer | Number of building code violations | 0-5 |
| `code_violations` | Integer | Number of general code violations | 0-4 |
| `lead_safe_certified` | Boolean | Has lead-safe certification | True/False |

## Permits and Inspections

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `permits_issued` | Integer | Building permits issued (last 5 years) | 0-5 |
| `last_inspection_year` | Integer or None | Most recent inspection year | 2023 or None |
| `property_condition` | String | Assessed condition | "Excellent", "Good", "Fair", "Poor", "Unknown" |

## Foreclosure

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `foreclosure_status` | String | Current foreclosure status | "None", "Pre-Foreclosure", "Foreclosure", "Bank-Owned" |

## Neighborhood Context (Census Tract Level)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `median_income_tract` | Integer | Median household income in census tract | $45,000 |
| `poverty_rate_tract` | Float | Poverty rate in census tract (%) | 22.5 |
| `school_rating` | Integer | School district rating (1-10) | 7 |

---

## Data Statistics

**Total Records**: 5,000 properties  
**Time Period**: 2024 snapshot with historical data back to 2000  
**Geographic Coverage**: 20 Cleveland neighborhoods

### Distributions

**Property Types**:
- Single Family: 45%
- Multi Family: 25%
- Condo: 15%
- Commercial: 8%
- Mixed Use: 5%
- Vacant Land: 2%

**Owner Types**:
- Owner-Occupied: 45%
- In-State Investor: 25%
- Out-of-State Investor: 15%
- Corporate: 8%
- Bank-Owned: 5%
- Government: 2%

**Vacancy Rate**: ~18%  
**Properties with Lead Violations**: ~15%  
**Tax Delinquent**: ~12%

---

## Notes

- This is **synthetic/sample data** for development and testing purposes
- All addresses, owner names, and specific values are randomly generated
- Distributions are based on rough approximations of Cleveland housing data
- Geographic coordinates are randomized within Cleveland boundaries
- Use this data for UI/UX development and user testing
- Replace with actual NST database queries for production

---

## Common Queries Examples

### Filter vacant properties in Ohio City
```python
df[(df['neighborhood'] == 'Ohio City') & (df['vacancy_status'] == 'Vacant')]
```

### Find properties with lead violations
```python
df[df['lead_violations'] > 0]
```

### Properties by out-of-state investors
```python
df[df['owner_type'] == 'Out-of-State Investor']
```

### Recent sales (last 2 years)
```python
df[df['last_sale_year'] >= 2022]
```

### Properties in foreclosure
```python
df[df['foreclosure_status'] != 'None']
```

### High-value properties (>$200k)
```python
df[df['property_value'] > 200000]
```

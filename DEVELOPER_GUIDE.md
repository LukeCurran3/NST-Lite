# NST 2.0 Developer Guide

A quick-reference guide for understanding and modifying the NST Streamlit app.

---

## Project Structure

```
NST UI/
├── streamlitapp.py          ← Entire app (single file, ~1820 lines)
├── assets/
│   ├── logo.jpg             ← Browser tab icon
│   ├── upperleft logo.jpg   ← Navbar logo
│   └── cleveland backdrop.jpg ← Home page hero image
├── data/
│   ├── nst_sample_data.csv  ← 5,000 synthetic properties, 35 columns
│   ├── sampledatadictionary.md ← Column definitions
│   └── SAMPLE_DATA_README.md
└── DEVELOPER_GUIDE.md       ← This file
```

---

## How the App is Organized

The app is one file split into clear sections. Here's the map:

| Lines (approx.) | Section | What it does |
|---|---|---|
| 1–23 | Module docstring | High-level overview, routing table, color scheme |
| 25–34 | Imports | All Python imports |
| 36–61 | Setup | Load images, configure page, read URL params |
| 63–421 | Global CSS | All shared styles (navbar, hero, cards, buttons) |
| 424–485 | Navbar HTML | Navigation bar rendered on every page |
| 488–493 | Routing comment | Instructions for adding new pages |
| 496–948 | **Datasets page** | `?page=datasets` — search, filter, results, export |
| 951–1413 | **Map Explorer** | `?page=maps` — map overview + neighborhood profiles |
| 1416–1701 | **Property Search** | `?page=property-search` — single property lookup |
| 1705–1819 | **Home page** | Default landing — hero, info cards, partners, footer |

---

## Page Routing

There is **no multi-page setup**. Routing is done with URL query parameters:

```python
query_params = st.query_params
current_page = query_params.get("page", "home")

if current_page == "datasets":
    # datasets page code
elif current_page == "maps":
    # maps page code
elif current_page == "property-search":
    # property search code
else:
    # home page (default)
```

### How to add a new page

1. Add an `elif current_page == "your-page":` block before the `else:` (home page)
2. Add a link in the navbar HTML (look for the `<div class="navbar-links">` section)
3. Use `?page=your-page` as the URL

---

## Navigation Patterns

There are **two ways** to navigate between pages. Use the right one:

### From HTML (links, buttons)
```html
<a href="?page=maps&hood=Tremont" target="_self">View Tremont</a>
```
**`target="_self"` is required.** Streamlit runs in an iframe — without it, links open a new tab instead of navigating.

### From Python (dropdowns, click handlers)
```python
st.query_params["page"] = "maps"
st.rerun()
```
Use this when responding to Streamlit widget interactions (selectbox, button, map click, etc.).

---

## Data Loading

All pages load data from CSV using cached functions:

```python
@st.cache_data
def load_data():
    return pd.read_csv("data/nst_sample_data.csv")
```

`@st.cache_data` means the CSV is read once and reused across reruns. If you swap in a database, replace the body of these functions — the caching decorator still works.

Each page has its **own** `load_data()` function (they're defined inside the page's `if` block so they don't conflict).

---

## Styling

All CSS lives in one big `st.markdown("""<style>...</style>""")` block near the top (lines 63–421). Key classes:

| CSS Class | Used for |
|---|---|
| `.navbar`, `.navbar-container` | Top navigation bar |
| `.navbar-links` | Nav link row |
| `.dropdown-*` | Dropdown menus in navbar |
| `.hero-section` | Home page hero banner |
| `.data-card` | Stat cards (Map Explorer profiles) |
| `.partner-card` | Partner logos on home page |
| `.stExpander` (Streamlit built-in) | Export Options styling override |

### Color scheme
- **Navy:** `#003071` (primary — headers, buttons, accents)
- **Gold:** `#FFD700` (highlights, hover states)
- **Light gray:** `#f8f9fc` (page backgrounds)
- **Font:** Inter (loaded from Google Fonts)

### CSS gotcha
The navbar uses **negative margins** (`margin-left: -100px`, etc.) to break out of Streamlit's default container padding. This is intentional — don't remove it.

---

## Map Explorer: Two States

The Map Explorer page (`?page=maps`) has two states controlled by whether `hood` is in the URL:

### State 1 — Map Overview (`?page=maps`)
- Left sidebar: dropdown + clickable neighborhood list
- Right side: Folium map with colored circles for each neighborhood
- **Click detection:** `st_folium` returns `last_object_clicked_tooltip`, which contains the neighborhood name. Code checks if it's a valid name, then navigates via `st.query_params`.

### State 2 — Neighborhood Profile (`?page=maps&hood=Tremont`)
- Stat cards (total properties, avg value, vacancy rate, etc.)
- Three tabs: Overview (charts), Data (table), Download (CSV/GeoJSON/Shapefile)
- "Back to Map" link at the top

---

## Search (How It Works)

Both the Datasets page and Property Search page let users search by address. The search combines `house_number` and `street_name` into one field:

```python
full_address = df["house_number"].astype(str) + " " + df["street_name"].fillna("")
mask = full_address.str.contains(query, case=False, na=False)
```

This way searching "1725 Pearl Rd" matches a row where `house_number=1725` and `street_name=Pearl Rd`.

---

## Export / Download

The Datasets page and Map Explorer profiles both offer data export:

- **CSV:** `df.to_csv()` → `st.download_button()`
- **GeoJSON:** Manually built from `latitude`/`longitude` columns (no geopandas needed)
- **Shapefile:** Uses `geopandas` + `zipfile` to create a `.zip` with `.shp/.shx/.dbf/.prj` files. Wrapped in `try/except` — if geopandas isn't installed, shows a warning instead of crashing.

---

## Common Tasks

### Change the data source
Replace the CSV read inside `load_data()` with your database query. Keep the `@st.cache_data` decorator. Make sure the returned DataFrame has the same column names (or update references).

### Add a stat card to a neighborhood profile
Find the stat cards section in the Map Explorer (look for `st.markdown('<div class="data-card">`). Copy one card block and change the metric/value.

### Change the navbar links
Search for `navbar-links` in the HTML. Each link is an `<a>` tag. Remember `target="_self"`.

### Add a new export format
Find the Download tab in the relevant page (look for `with tab3:` or `with download_tab:`). Add a new `st.download_button()`.

---

## Dependencies

```
streamlit
streamlit-folium
folium
pandas
Pillow
geopandas (optional — only needed for shapefile export)
```

Run with: `streamlit run streamlitapp.py`

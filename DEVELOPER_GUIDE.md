# NST 2.0 Developer Guide

Quick reference for understanding and modifying the NST Streamlit app.

---

## Project Structure

```
NST UI/
├── streamlitapp.py              Entry point. Auth, styles, navbar, routing.
├── config.py                    Constants: colors, column groups, presets, regex.
├── auth.py                      Password gate.
├── navbar.py                    Top navbar HTML and asset loading.
├── styles.py                    All CSS. One injector per page.
│
├── loaders/                     Cached data loaders (@st.cache_data).
│   ├── __init__.py              Re-exports every public loader.
│   ├── core.py                  load_data, load_neighborhoods, load_map_agg, load_neighborhood_data.
│   ├── property_search.py       ps_search + per-parcel history pulls.
│   ├── distressed_rentals.py    load_distressed_rentals (big multi-CTE SQL).
│   └── oos_owners.py            load_oos_data.
│
├── utils/                       Shared helpers used across pages.
│   ├── formatting.py            fmt_money, fmt_text, fmt_year, fmt_int, flag_yn, flag_yn_colored.
│   ├── html.py                  cell, grid, section (small HTML builders).
│   └── parcel.py                normalize_parcel, strip_suffix, STREET_SUFFIXES.
│
├── nst_pages/                   One file per page. Each exports render().
│   ├── home.py                  Hero banner, data cards, partner logos.
│   ├── maps.py                  County-wide neighborhood choropleth + sidebar list.
│   ├── neighborhood.py          Neighborhood profile page.
│   ├── property_search.py       Lookup by address / parcel / owner. Five detail tabs.
│   ├── methodology.py           Documentation tabs.
│   ├── projects.py              Popular projects hub.
│   ├── contact.py               Contact cards.
│   ├── oos_owners.py            Out-of-state owner finder.
│   ├── distressed_rentals.py    Distressed rentals browser.
│   │
│   └── datasets/                Datasets page as a package.
│       ├── __init__.py          Re-exports render.
│       ├── page.py              Orchestrator. Wires filters, tabs, export together.
│       ├── presets.py           6 preset toggle buttons.
│       ├── filters.py           All filter widgets + the filter-application if-chain.
│       ├── summary.py           Active-filter summary line + 4 KPI stat boxes.
│       ├── tab_table.py         Table view + column customizer.
│       ├── tab_map.py           Folium choropleth / marker cluster.
│       ├── tab_charts.py        Plotly bar charts.
│       ├── tab_summary.py       Summary tab.
│       └── export.py            CSV / GeoJSON / Shapefile download buttons.
│
├── scripts/
│   ├── nst_sync.py              Nightly SAS to Parquet pipeline.
│   ├── nst_sync.bat             Windows Task Scheduler entry point.
│   └── explore_sas.py           Dev utility: inspect SAS schemas.
│
├── assets/                      Logos, hero image, partner SVGs, favicon.
├── data/                        Parquet files + shapefiles (not committed).
├── requirements.txt
└── DEVELOPER_GUIDE.md           This file.
```

---

## How Routing Works

There is no multi-page setup. All routing is done with the `?page=` URL query parameter.
`streamlitapp.py` reads it and calls the matching `render()` function:

```python
if current_page == "datasets":
    datasets.render()
elif current_page == "maps":
    maps.render()
...
else:
    home.render(ASSETS)
```

Two ways to navigate:

- From HTML links: `<a href="?auth=1&page=maps" target="_self">`. The `target="_self"` is required.
- From Python handlers: `st.query_params["page"] = "maps"; st.rerun()`.

---

## Common Tasks

### Add a new page

1. Create `nst_pages/your_page.py` with a `render()` function.
2. Import it in `streamlitapp.py` and add one `elif current_page == "your-page":` branch.
3. Add a link in `navbar.py` under the appropriate dropdown.

### Add or change CSS

All CSS lives in `styles.py`. Each page has its own injector (`styles.inject_X()`) called at the
top of its `render()`. If you need a new shared style, add it to `_global_css()`. For a page-specific
style, extend that page's injector function. Colors come from `config.COLOR_NAVY`, `COLOR_GOLD`,
`COLOR_LIGHT_GRAY`; use f-string interpolation inside the CSS to reference them.

Never write a raw `st.markdown("<style>...</style>")` inside a page. Put it in `styles.py`.

### Add a shared utility

Formatting of values: `utils/formatting.py`.
HTML snippet builders: `utils/html.py`.
Parcel ID or street name helpers: `utils/parcel.py`.
If a helper doesn't fit any of those, add a new file under `utils/` with a clear name.

### Add or change a data loader

Shared county-wide loaders go in `loaders/core.py`. Page-specific loaders go in their matching
file (e.g. `loaders/property_search.py`). After adding a new function, re-export it from
`loaders/__init__.py` so pages can still do `from loaders import your_new_loader`.

Every loader must use `@st.cache_data`.

### Modify filters on the Datasets page

Filter widgets and the filter-application logic both live in `nst_pages/datasets/filters.py`.
Each filter has three parts:
1. Widget drawn inside `_render_advanced` or `render_filters`.
2. State key written into the `state` dict.
3. Branch inside `apply_filters` that narrows the DataFrame.

Keep all three in sync when adding a new filter.

### Modify a tab on the Datasets page

Each tab is its own file: `tab_table.py`, `tab_map.py`, `tab_charts.py`, `tab_summary.py`.
They all take the already-filtered DataFrame and render.

### Change the data source

Replace the DuckDB query inside the relevant loader in `loaders/`. Keep the `@st.cache_data`
decorator and the return DataFrame schema the same.

---

## Styling

Theme tokens in `config.py`:
- `COLOR_NAVY` (`#003071`) is the primary brand color.
- `COLOR_GOLD` (`#FFD700`) is the accent / hover color.
- `COLOR_LIGHT_GRAY` (`#f8f9fc`) is the pale background used by stat boxes.
- Font: Inter, loaded from Google Fonts in `styles._global_css`.

Tab styling (`.stTabs`) is set globally so every tab bar on every page is full-width with
equal column widths. If you want a page-specific tab style, override inside that page's injector.

The navbar uses negative margins (`margin-left: -100px` etc.) to break out of Streamlit's
default padding. Don't remove them.

---

## Password Gate

`auth.check_password()` is called once at the top of `streamlitapp.py`. It returns True if
the URL contains `?auth=1` or if the session has already authenticated. The site password
lives in `config.SITE_PASSWORD`. Every internal link uses `?auth=1&page=...` so navigation
doesn't re-prompt.

---

## Deployment

The app runs on the internal Windows server `msassneocandod1`, served via IIS reverse
proxy on port 80 to Streamlit on 8501. NSSM manages it as the `NST-Streamlit` service.

To push an update:

```bash
cd C:\nst\app
git pull
C:\nst\nssm.exe restart NST-Streamlit
```

The nightly SAS to Parquet sync runs at 3 AM via Windows Task Scheduler and lives in
`scripts/nst_sync.py`.

---

## Running Locally

```bash
venv\Scripts\streamlit.exe run streamlitapp.py
```

The venv must be used (system Python lacks duckdb). Data files must be present under
`data/parquets917/` for the app to load.

---

## Dependencies

See `requirements.txt`. Core: `streamlit`, `duckdb`, `pandas`, `geopandas`, `folium`,
`streamlit-folium`, `plotly`, `Pillow`.

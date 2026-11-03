# NST UI — Claude Context

## Project
NST (Neighborhood Strategy Technology) — a Streamlit web app for Cleveland/Cuyahoga County housing data. Built by Luke Curran at CWRU Center on Poverty and Community Development. Live at http://msassneocandod1 (internal CWRU network).

## Stack
- **Frontend**: Streamlit (Python), Folium/Leaflet.js for maps, Plotly for charts
- **Data**: DuckDB querying 4 Parquet files (nst.parquet ~40MB, tax_bill.parquet ~26MB, sales.parquet ~110MB, parcel_history.parquet ~74MB)
- **Server**: msassneocandod1 (Windows Server), app at C:\nst\app\, data at C:\nst\data\
- **Auth**: Password gate (`poverty2026center`), served via IIS reverse proxy on port 80 → Streamlit on 8501
- **Service**: NSSM Windows service (NST-Streamlit), nightly sync via Task Scheduler at 3AM
- **Repo**: https://github.com/LukeCurran3/NST2.0.git

## File Structure
- `streamlitapp.py` — entry point, auth, navbar, routing by `?page=` param
- `config.py` — constants: SITE_PASSWORD, PARQUET_DIR, COL_GROUPS, PRESET_COLUMNS, distressed rentals config
- `loaders.py` — all @st.cache_data functions (load_data, ps_search, load_distressed_rentals, etc.)
- `nst_pages/` — one file per page (datasets, maps, property_search, neighborhood, distressed_rentals, methodology, home, projects, contact, oos_owners)
- `scripts/nst_sync.py` — nightly SAS→Parquet sync (reads from Z:\, writes to C:\nst\data\)
- `assets/` — images, shapefiles

## Data Sources
- nst.parquet from `acrosssource.sas7bdat` (Z: drive = \\msasspovertyp1\epilots\data\)
- tax_bill.parquet from `tt_bill_sep2026.sas7bdat`
- sales.parquet from `msales.sas7bdat`
- parcel_history.parquet from `property.sas7bdat`
- Join keys: nst.PARCEL = sales.PROPERTY_NUMBER = parcel_history.parcel = tax_bill.PROPERTY_NUMBER

## Key Conventions
- No em dashes (—) anywhere in UI text — use periods or colons
- No inline code/technical jargon in user-facing text (no `field_name`, no SQL snippets)
- No emojis unless explicitly requested
- Font: Inter (Google Fonts), loaded globally in streamlitapp.py CSS
- Colors: Navy #003071, Gold #FFD700, Green #1e8449 (WCAG AA), Red #c0392b
- All maps use Folium + streamlit-folium (OpenStreetMap tiles, no API key)
- No AI-style comments in code — comments should be minimal and concise

## Pages
- **Home** — hero banner, data cards, partner logos
- **Datasets** — filter/browse 177k Cleveland parcels; preset buttons (Vacant, Violations, Tax Delinquent, OOS Owners, Foreclosure, Failed Lead Certification); Table/Map/Charts/Summary tabs; CSV/Excel export
- **Maps** — county-wide choropleth by neighborhood; click → Neighborhood Profile
- **Property Search** — search by address/parcel/owner; 5 tabs: Overview, Values & History, Violations & Lead, Evictions, Location; joins all 4 parquets
- **Neighborhood Profile** — stats, charts, parcel download for a specific neighborhood
- **Distressed Rentals** — Austin Cummings' R methodology: rental universe, 5 distress indicators, owner classification, portfolio clustering with shared-mailing-address detection
- **Methodology** — 3 tabs: Overview, Variables Reference, Distressed Rentals Methodology (plain English, no code)
- **Popular Projects** — links to Distressed Rentals and Out-of-State Owner Finder
- **Out-of-State Owners** — guided tool for finding out-of-state landlords

## Distressed Rentals Methodology
Based on Austin Cummings' R code. Five stages:
1. Filter to current parcels (NNN-NN-NNN format, parcel_status = CURRENT)
2. Rental universe: exclude non-residential/vacant land/homestead; include apartments, registered rentals, LLCs, multi-family
3. Five distress indicators: tax delinquent ≥$500, violation 2021-2026, complaint 2021-2026, grade declined TCI2015→WRLC2023, any evictions 2021-2025
4. Owner classification: Non-Profit/Gov → Corporate → Trust → Joint → Individual (regex on PRIMARY_OWNER_NAME)
5. Portfolio clustering: group by tax mailing address (from tax_bill.parquet), detect multi-LLC same-address patterns; mail drops filtered when name_ratio > 0.5 AND size ≥ 10

## Known Issues / Pending
- `red25` (2.5% owner-occupant reduction) not in nst.parquet yet — homestead flag used as proxy
- CIA complaint source deprecated — mayor complaints field currently empty
- Date windows hardcoded to 2021-01-01 → 2026-07-31
- nst_sync.py column lists verified against actual SAS schemas on server (Oct 2026)
- Pandas4Warning on select_dtypes(include='object') — cosmetic, no impact
- Preset filter button text size: CSS targeting `.preset-section button [data-testid="stMarkdownContainer"] p` — may need DevTools verification if still not rendering larger

## Server Deployment Notes
- Python: embeddable 3.11.9 at C:\Python311\ (no installer, uses directory junction)
- Junction: `mklink /J C:\nst\app\data\parquets917 C:\nst\data`
- IIS site "NST" on port 80 with ARR reverse proxy → localhost:8501
- WebSockets work via `--browser.serverAddress msassneocandod1 --browser.serverPort 80` args in NSSM
- Update deploy: `cd C:\nst\app && git pull && C:\nst\nssm.exe restart NST-Streamlit`
- Group Policy blocks .exe installers and winget on this server

## Recent Changes (Oct 2026)
- Multi-select preset filter buttons (session_state set)
- Removed redundant checkboxes (vacant/violations/tax/foreclosure) — use preset buttons instead
- Year built: null < 1800, slider defaults to 1950→present
- Street suffix stripping in search (both Datasets and Property Search)
- Accessibility: green #27ae60 → #1e8449 (passes WCAG AA)
- Hero button hover fix: added !important to hover color
- Methodology page: plain English, removed Derived Fields and Limitations tabs
- Distressed Rentals page: IIS + WebSocket fix, NA grade_declined bug fixed
- Bar charts on Datasets page converted to Plotly with fixedrange=True (no scroll zoom)
- Tab logo changed to assets/logo.png

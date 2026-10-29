"""Methodology page: documents data sources, derived fields, and limitations."""

import pandas as pd
import streamlit as st


def render():
    st.markdown(
        '<div style="font-size:0.95rem;color:#666;margin-bottom:1.5rem;">'
        '<a href="?auth=1&page=home" target="_self" style="color:#003071;text-decoration:none;">Home</a>'
        ' &nbsp;/&nbsp; Our Work &nbsp;/&nbsp; <strong>Methodology</strong></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div style="font-size:2.5rem;font-weight:700;color:#003071;margin-bottom:0.3rem;">Data Methodology</div>', unsafe_allow_html=True)
    st.markdown(
        '<div style="font-size:1.1rem;color:#666;margin-bottom:1.5rem;max-width:900px;">'
        'Every variable in NST comes from a specific source, and every derived field is computed via explicit logic. '
        'This page documents the pipeline from raw county records to the tables you see in the app: '
        'so you can judge what any value does and does not mean.'
        '</div>',
        unsafe_allow_html=True,
    )

    _m_tab_overview, _m_tab_vars, _m_tab_derived, _m_tab_dr, _m_tab_limits = st.tabs([
        "Overview", "Variables Reference", "Derived Fields",
        "Distressed Rentals Methodology", "Limitations & Caveats",
    ])

    with _m_tab_overview:
        st.markdown("""
### Primary Data Sources

- **Cuyahoga County Fiscal Office / Auditor**: parcel identification, ownership, appraised values, tax balances, assessment, foreclosure case data
- **City of Cleveland Division of Building & Housing**: code violations, complaints, lead safe certifications, rental registration
- **Cleveland Municipal Housing Court**: eviction case filings
- **Cuyahoga County Court of Common Pleas**: foreclosure case filings
- **CMHA / HUD**: Section 8 and HUD subsidy flags
- **USPS vacancy survey**: one input to the vacancy composite flag
- **Western Reserve Land Conservancy (WRLC)**: 2023 property condition survey
- **Thriving Communities Institute (TCI)**: 2015 property condition survey
- **City of Cleveland Land Bank / CCLRC**: land bank disposition records

### Geographic Scope

The dataset covers **all of Cuyahoga County** (~604k parcels). Some fields: violations, rental registration, lead safe certification, permits, evictions: are populated only for parcels within **City of Cleveland** limits. Fields marked "CLE Only" in the Datasets page column selector reflect this.

### Update Cadence

Source systems are refreshed by the county on various schedules (daily to monthly depending on the field), and NST is re-synced nightly. Some fields: like court case updates and violation notices: can lag the real-world event by days to weeks.
""")

    with _m_tab_vars:
        st.caption("Every variable in the NST dataset, grouped by category. Click any section to expand.")

        _var_groups = [
            ("Core Identity & Address", [
                ("PARCEL", "Cuyahoga County Fiscal Office", "The county's unique parcel ID in NNN-NN-NNN format. Primary join key."),
                ("PPN", "Cuyahoga County Fiscal Office", "Permanent Parcel Number: alternate ID without hyphens. Join key for tax_bill when PROPERTY_NUMBER is empty."),
                ("number, street", "Fiscal Office / LBRS", "Address components. Combined into `address` when `address` is empty or zero-prefixed."),
                ("address", "Fiscal Office / LBRS", "Primary site address. Cleaned by removing leading `0 ` placeholders (the county uses `0` as a 'no house number' marker)."),
                ("parcel_status", "Fiscal Office", "`current` means the parcel appears in the latest county geospatial file; `probably expired` means it has likely been consolidated or split."),
            ]),
            ("Geography", [
                ("NEIGHBOR10", "City of Cleveland Planning", "One of Cleveland's 36 statistical planning areas. Blank for parcels outside Cleveland city limits."),
                ("ward2025", "Cleveland City Council", "Cleveland council ward based on 2025 redistricting. Blank outside Cleveland."),
                ("zip", "Fiscal Office", "5-digit ZIP code for the parcel."),
                ("cuyregion", "County planning", "Cuyahoga County planning region (east side / west side / inner-ring / outer-ring)."),
                ("tract", "US Census", "Census tract GEOID at the parcel location."),
                ("cia14_name", "Cleveland Impact Area", "CIA (Community Impact Area) designation."),
                ("LATITUDE, LONGITUDE", "LBRS geocoding", "Parcel centroid coordinates in WGS84."),
            ]),
            ("Ownership", [
                ("PRIMARY_OWNER_NAME", "Fiscal Office: latest grantee", "Current owner as of the latest real estate transfer. For LLCs this is the registered entity name."),
                ("MAIL_STATE", "Fiscal Office tax mailing address", "State the tax bill is mailed to. Used to flag out-of-state investor-owned properties."),
            ]),
            ("Property Characteristics", [
                ("pclass", "Fiscal Office", "Internal administrative property class code (e.g. RESIDENTIAL, COMMERCIAL)."),
                ("luc", "City of Cleveland", "Land use code: numeric classification of use type."),
                ("CLASSIFICATION_DESCR", "Fiscal Office", "Full text classification (e.g. SINGLE FAMILY DWELLING). Mapped to friendlier labels in the Datasets table: see Derived Fields tab."),
                ("yrbuilt", "Fiscal Office", "Year the primary structure was built."),
                ("condition", "Fiscal Office appraiser", "Grade from a 6-year rotating physical inspection: EX/VG/G/AVG/F/PR/VP/US/SV. Expanded to full words in the Datasets table."),
                ("style", "Fiscal Office", "Architectural style code (RAN=ranch, COL=colonial, etc.)."),
                ("rextwall", "Fiscal Office", "Exterior wall material code."),
                ("numstory, basesqft, bedrooms, baths, units, totbldgs, propsize, zone_desc", "Fiscal Office", "Physical characteristics from the county appraisal record."),
            ]),
            ("Values & Taxes", [
                ("TAX_MARKET_TOTAL / LAND / IMPROVEMENT", "Fiscal Office mass appraisal", "County's estimated market value, split into land vs building. Updated every 3 years in the triennial reappraisal."),
                ("currentvalue2023, proposedvalue2024", "Fiscal Office", "Specific year assessment values."),
                ("NET_TAX_DELQ_DUE", "Cuyahoga County Treasurer", "Certified delinquent tax balance. Does not include late (non-certified) taxes."),
                ("HOMESTEAD_FLAG", "Fiscal Office", "Receives the Homestead Act tax reduction (65+ or disabled owner-occupant). Strong signal of owner-occupancy."),
                ("PAYMENT_PLAN_FLAG", "Treasurer", "On a tax payment plan."),
                ("taxabate", "Fiscal Office", "Tax abatement status (new construction, substantial rehab)."),
                ("CERT_PEND_FLAG / CERT_SOLD_FLAG", "Treasurer", "Tax certificate (lien) status. SOLD = lien has been transferred to a third party."),
                ("BOR_STATUS", "Board of Revision", "Status of any Board of Revision assessment appeal."),
                ("assessment", "Treasurer", "Taxable value used to compute the tax bill (Ohio: 35% of market value for residential)."),
            ]),
            ("Foreclosure & Forfeiture", [
                ("FORECLOSURE_FLAG", "Court of Common Pleas", "An active foreclosure case exists on this parcel."),
                ("lstatus, caseno, cdesig", "Court of Common Pleas", "Foreclosure case status, number, and type designation."),
                ("fo_deed_count", "Fiscal Office", "Number of recorded foreclosure deeds against this parcel."),
            ]),
            ("Vacancy & Condemnation", [
                ("combovac", "USPS + city vacancy list + water shutoff", "Composite vacancy flag: any of the three sources flagging triggers it. Indicates vacant **structure** (building exists but is unoccupied)."),
                ("vl", "City of Cleveland", "Vacant lot flag: the parcel has no structure at all."),
                ("lbvl", "City Land Bank", "Land bank vacant lot."),
                ("unoccupied", "USPS / city", "Alternative unoccupied flag."),
                ("active_condemn", "City Building & Housing", "An active condemnation order exists."),
            ]),
            ("Land Bank", [
                ("city_lb_flag", "City of Cleveland Land Bank", "In the City of Cleveland Land Bank inventory."),
                ("cclrc", "Cuyahoga County Land Reutilization Corporation", "In the county land bank inventory."),
                ("disp_status, demo_status, rehab_status", "Land Bank", "Disposition pipeline status (available / under contract / sold / scheduled for demo / rehab in progress)."),
            ]),
            ("Lead Safe Certification", [
                ("lsc_stat", "City Building & Housing", "Lead Safe Certification status: PASS / FAIL / PENDING / EXEMPT / REVOKED. Required for pre-1978 Cleveland rentals."),
                ("lsc_issue_dt", "City Building & Housing", "Date of latest LSC action."),
                ("lead_rollout", "City Building & Housing", "Rollout phase code: the city phased in LSC requirements by area."),
                ("compliance_acc, compliance_acc_dt", "City Building & Housing", "Compliance accepted status and date."),
            ]),
            ("Violations", [
                ("violation", "City Building & Housing", "Any housing code violation on record (flag)."),
                ("violation_vin, violation_file_date, violation_task_status, violation_vtype", "City Building & Housing", "Violation number, filing date, workflow status, and type."),
            ]),
            ("Complaints", [
                ("anycomplaint", "City Building & Housing", "Flag indicating any complaint from any of the six sources below."),
                ("cdc_comp / council_comp / mayor_comp / mac_comp / public_comp / other_comp", "City Building & Housing", "Flag per complaint source: Community Development Corporation, City Council, Mayor's office, Mobile Area Communications, Public (resident-filed), Other."),
                ("*_comp_file_date", "City Building & Housing", "The filing date for each complaint source. Used to compute recency windows."),
            ]),
            ("Rental Registration (Cleveland only)", [
                ("rentalreg", "City Building & Housing", "Rental registration on file."),
                ("RR_File_Date", "City Building & Housing", "Date registration was filed."),
                ("RR_units", "City Building & Housing", "Number of rental units at the parcel."),
                ("RR_status", "City Building & Housing", "Status: ACTIVE / ABOUT TO EXPIRE / REGISTRATION RENEWED / EXPIRED / PENDING / CLOSED / NO RENEWAL."),
                ("RR_owner, RR_owner_add, RR_owner_state", "City Building & Housing", "Registered rental owner contact information."),
            ]),
            ("Housing Programs", [
                ("sect8", "CMHA", "Receiving Section 8 / Housing Choice Voucher subsidy via the local housing authority."),
                ("sect8_cnty", "County HA", "Section 8 via county-level program."),
                ("hud", "HUD", "HUD-subsidized or HUD-owned."),
            ]),
            ("Code Enforcement (COD)", [
                ("cod_condemed_status", "City Building & Housing", "Current condemnation status from the Code Enforcement Online Database."),
                ("cod_current_violations", "City Building & Housing", "Current open violations count."),
                ("cod_current_bh_lead_violations", "City Building & Housing", "Current open Building & Housing lead violations (flag)."),
            ]),
            ("Permits (Cleveland only)", [
                ("last_permit_per_id, last_permit_category, last_permit_file_date", "City Building & Housing", "Most recent building permit: ID, category (electrical, plumbing, structural, etc.), and file date."),
            ]),
            ("Evictions (Cleveland Municipal Housing Court)", [
                ("evict_case_number, evict_case_status, evict_disp_status, evict_yr", "Housing Court", "Current/most recent eviction case details."),
                ("cases_filed_2016 ... cases_filed_2025", "Housing Court", "Number of eviction cases filed in each year, aggregated by address."),
            ]),
            ("Sales & Historical Values", [
                ("date, lsaleamt", "Fiscal Office transfer file", "Most recent sale date and amount shown on the main parcel record."),
                ("Full sales history", "Fiscal Office transfer file", "Every recorded sale for the parcel: year, amount, buyer (grantee), seller (grantor), deed type, whether it was a valid arms-length sale, and transfer type. Powers the sales history table on Property Search."),
                ("Year-by-year value history", "Fiscal Office annual snapshots", "Annual snapshots of market value (total / land / building), condition grade, owner, owner-occupancy status, and tax reduction flags. Powers the value and condition timeline charts on Property Search."),
                ("Annual tax bills", "Treasurer", "Yearly tax bill records including assessed values, total owed / paid / balance, homestead and foreclosure flags, payment plan and tax certificate status, and the current tax mailing address."),
            ]),
            ("Property Condition Surveys", [
                ("wrlc23_category", "WRLC 2023 survey", "Occupied Structure / Vacant Structure / Vacant Lot / With Adjacent / Parking Lot / Park / Other."),
                ("wrlc23_results", "WRLC 2023 survey", "Overall exterior condition grade A/B/C/D/F from WRLC volunteer walking survey (2022-2023)."),
                ("wrlc23_property_use, wrlc23_roof, wrlc23_siding, wrlc23_windows, wrlc23_porch, wrlc23_peeling_paint, wrlc23_garage, wrlc23_dumping", "WRLC 2023 survey", "Component-level survey grades."),
                ("tci2015_survey_grade, tci2015_survey_date", "TCI 2015-2017 survey", "Overall exterior grade A/B/C/D/F from Thriving Communities Institute survey (Cleveland properties, 2015-2017)."),
            ]),
        ]

        for group_name, variables in _var_groups:
            with st.expander(group_name, expanded=False):
                rows = pd.DataFrame(variables, columns=["Variable", "Source", "Definition"])
                st.dataframe(rows, use_container_width=True, hide_index=True)

    with _m_tab_derived:
        st.caption(
            "Fields the app computes on top of the raw county data. "
            "Each row here documents what the inference is, how it is computed, and why it is reasonable."
        )

        _derived = [
            ("`is_cleveland` boolean",
             "True when `ward2025` is populated (non-empty).",
             "Cleveland ward IDs are only assigned to parcels inside city limits. Any parcel with a non-blank ward is, by definition, in Cleveland. A handful of edge-case parcels (newly annexed or county islands) can be misclassified."),
            ("`CLASSIFICATION_DESCR` mapped labels",
             "Raw county codes like `SINGLE FAMILY DWELLING` are mapped to friendlier labels like `Single-Family Home` in the Datasets table.",
             "The county labels are consistent but all-caps and formal. The mapping is applied only for display; the raw values are retained behind the scenes for pattern-matching in the Distressed Rentals rental-detection logic."),
            ("Condition code expansion",
             "`EX → Excellent, VG → Very Good, G → Good, AVG → Average, F → Fair, PR → Poor, VP → Very Poor, US → Unsound`. `SV` (Salvage) is left as-is as a known gap.",
             "The county appraiser assigns these codes during physical inspection. We expand only for display: comparisons and ranks in the Distressed Rentals methodology use ordinal rankings (A=4, B=3, ...)."),
            ("Vacant composite (Map View color-coding)",
             "A parcel is colored as 'Vacant' on the Datasets Map View when `combovac = 1` **OR** `CLASSIFICATION_DESCR` starts with `Vacant Land`.",
             "The raw `combovac` flag covers only vacant **structures** (unoccupied buildings). Reclassified-to-vacant-land parcels have no structure and so `combovac = 0`, but they are vacant in every colloquial sense. The composite matches the WRLC / Thriving Communities Institute convention: 'vacant property' = either vacant structure OR vacant lot."),
            ("Date conversion",
             "Sale dates in the source data are stored as a number (days counted from a reference date) rather than a readable date. These are converted into standard YYYY-MM-DD format for display and sorting.",
             "Without this step, users would see values like `22344.0` instead of `2021-03-15`."),
            ("Address reconstruction",
             "When the primary address field is empty or starts with `0`, the app rebuilds the address from the separate house number and street name fields, and strips any leading `0` placeholder.",
             "The county records `0 MAIN ST` for parcels where no house number is on file. We treat that as missing and reconstruct a usable address when possible."),
            ("Blank value normalization",
             "The source data sometimes stores the literal word `NONE` in a text field to mean 'no value', rather than leaving the field truly empty. We convert these to real blanks.",
             "Without this step, a tenant looking for a landlord's name might see `NONE` and not realize it just means the field is empty."),
        ]

        for name, logic, why in _derived:
            with st.expander(name, expanded=False):
                st.markdown(f"**Computed as:** {logic}")
                st.markdown(f"**Why this is a reasonable inference:** {why}")

    with _m_tab_dr:
        st.markdown(
            "The Distressed Rentals page flags rental properties that show signs of extractive ownership: landlords who neglect upkeep, let violations pile up, and extract rent without reinvesting. "
            "The process has five stages: filter to current parcels, identify which parcels are rentals, compute five distress indicators per property, classify owners by type, and group parcels that share a tax mailing address to detect portfolios hidden across multiple LLCs."
        )

        st.markdown("### Stage 1: Base Filtering")
        st.markdown(
            "- Parcel ID must match `NNN-NN-NNN` format (filters out malformed records).\n"
            "- `parcel_status` must be `CURRENT` (filters out expired/consolidated parcels)."
        )

        st.markdown("### Stage 2: Rental Universe (`rent_flag`)")
        st.markdown(
            "Each parcel is assigned one of four values. We retain only parcels with `rent_flag IN (1, 2)` as the rental universe. "
            "**Order matters**: the first matching rule wins:"
        )
        rent_rules = pd.DataFrame([
            ("99: Not applicable", "`pclass` is AGRICULTURAL / PUBLIC UTILITIES / INDUSTRIAL / LAND BANK / MISSING / COMMON AREA / COMMUNITY SHOPPING CENTER / DAY CARE CENTERS"),
            ("2: Possibly a rental", "SFH or Condo owned by an LLC"),
            ("0: Not a rental (owner-occupied)", "SFH or Condo with `HOMESTEAD_FLAG = 1`"),
            ("2: Possibly a rental", "Two-Family or Three-Family Dwelling (multi-family housing is almost always rental)"),
            ("99: Not applicable", "No building AND zero building value (vacant land)"),
            ("2: Possibly a rental", "SFH or Condo with no homestead flag (likely rented out)"),
            ("1: Confirmed rental", "`RR_status` is ACTIVE / ABOUT TO EXPIRE / REGISTRATION RENEWED"),
            ("1: Confirmed rental", "`CLASSIFICATION_DESCR` contains `APARTMENT`"),
            ("99: Default", "Catch-all for anything else"),
        ], columns=["rent_flag → Meaning", "Rule"])
        st.dataframe(rent_rules, use_container_width=True, hide_index=True)

        st.markdown("### Stage 3: Five Distress Indicators")
        st.markdown(
            "Each is a 0 / 1 flag. The sum (0-5) is the `distress_score`. "
            "The 5-year window is **2021-01-01 to 2026-07-31**: recent enough to reflect current ownership behavior, long enough to capture persistent patterns."
        )
        distress = pd.DataFrame([
            ("1. Tax Delinquency", "`NET_TAX_DELQ_DUE ≥ 500`", "A $500 floor filters out trivial amounts that are often data lag / rounding."),
            ("2. Violation in last 5 years", "`violation_file_date` falls within the 5-year window", "Captures active patterns of neglect; older unresolved violations are already reflected elsewhere."),
            ("3. Complaint in last 5 years", "Any of CDC / Council / Mayor / MAC / Public / Other complaint date falls within the window", "Any-source signal because complaint origin varies by neighborhood."),
            ("4. Grade declined 2015 → 2023", "`wrlc23_results` grade < `tci2015_survey_grade` on the A=4 ... F=0 scale (NULL if either is missing)", "Direct evidence of exterior deterioration across the two most recent walking surveys."),
            ("5. Any evictions 2021-2025", "`cases_filed_2021 + ... + cases_filed_2025 > 0`", "Even one eviction is a meaningful signal; the exact count is also shown as a column."),
        ], columns=["Indicator", "Logic", "Rationale"])
        st.dataframe(distress, use_container_width=True, hide_index=True)

        st.markdown("### Stage 4: Owner Classification")
        st.markdown(
            "Each owner is classified into one `owner_type` by matching `PRIMARY_OWNER_NAME` against ordered regex patterns. "
            "**Non-Profit/Government is checked first** so a `LAND BANK LLC` is not mis-classified as a corporate entity."
        )
        owner_rules = pd.DataFrame([
            ("Non-Profit / Government", "`CITY OF`, `COUNTY OF`, `TOWNSHIP`, `DEPARTMENT`, `AUTHORITY`, `COMMISSION`, `CHURCH`, `CMHA`, `LAND BANK`, `UNIVERSITY`, `HOSPITAL`, and ~20 more"),
            ("Corporate Entity", "`LLC`, `INC`, `CORP`, `HOLDINGS`, `PROPERTIES`, `REALTY`, `INVESTMENTS`, `MANAGEMENT`, `CAPITAL`, `FUND`, and ~20 more"),
            ("Trust", "`TRUST`, `TRUSTEE`, `REVOCABLE`, `IRREVOCABLE`, `LIVING TRUST`, `FAMILY TRUST`"),
            ("Joint Ownership", "` & `, ` AND `, `JT`, `JOINT`, `JTWROS`, `JT TEN`"),
            ("Individual", "Two uppercase words (e.g. `SMITH, JOHN`)"),
            ("Unknown / Missing", "Catch-all for empty names or no pattern match"),
        ], columns=["Owner Type", "Regex pattern matches"])
        st.dataframe(owner_rules, use_container_width=True, hide_index=True)

        st.markdown("### Stage 5: Portfolio Clustering")
        st.markdown(
            "Groups parcels by their tax mailing address to detect landlords who split a single portfolio across multiple LLCs that all mail to one location."
        )
        st.markdown(
            "1. Take the most recent tax billing record for each parcel.\n"
            "2. Standardize the mailing address (uppercase, remove punctuation, normalize spacing) and append the 5-digit ZIP so near-duplicates collapse into one key.\n"
            "3. Group every parcel in the county by that cleaned address.\n"
            "4. For each address, compute: total parcels at that address, number of distinct owner names, the most common name, and the full list of entity names.\n"
            "5. Attach those portfolio stats back to each rental so you can see 'this parcel belongs to a 47-parcel portfolio with 12 different LLC names'."
        )

        st.markdown("### Mail-Drop Detection")
        st.markdown(
            "An address is classified as a **likely mail drop** when `unique_entity_count / true_portfolio_size > 0.5` AND `true_portfolio_size ≥ 10`. "
            "In plain English: if more than half of the parcels at a shared mailing address have distinct owner names and there are at least 10 of them, "
            "it is almost certainly a commercial mail-forwarding service (not one landlord using shell entities)."
        )
        st.markdown(
            "- Hidden by default in the UI (toggle to show).\n"
            "- Keeps the Top Portfolios section focused on real landlords.\n"
            "- Does not touch the per-parcel distress score."
        )

    with _m_tab_limits:
        st.caption("Known data gaps, assumptions that may not hold, and improvements planned or in progress.")

        _limits = [
            ("One complaint source currently missing",
             "The Distressed Rentals complaint flag looks at six complaint sources (CDC, City Council, Mayor's office, MAC, Public, Other). An earlier CIA complaint source was deprecated by the city and the Mayor's office source has not yet begun populating.",
             "Complaint flag coverage is slightly undercounted today. Will self-correct as the Mayor's office source comes online."),
            ("2.5% owner-occupant tax reduction approximated by Homestead flag",
             "The rental-detection logic uses the Homestead Exemption as the signal of owner-occupancy. A secondary signal (the Ohio 2.5% owner-occupant tax reduction) exists in the historical data but is not yet included in the main dataset.",
             "Owner-occupied properties that qualify for the 2.5% reduction but not the Homestead Exemption may be misclassified as possibly rental. The fix is a planned addition to the nightly data export."),
            ("Grade decline requires both surveys to cover the parcel",
             "The 'grade declined 2015 → 2023' indicator can only fire when BOTH `tci2015_survey_grade` AND `wrlc23_results` have A-F values for the parcel. Properties surveyed in only one year are NULL (not counted as declined, but also not counted as stable).",
             "Coverage gap: about 30-40% of parcels lack one or both surveys. For those, this indicator is silent."),
            ("Date windows are fixed",
             "The violation and complaint recency checks use the fixed window 2021-01-01 to 2026-07-31. The window does not automatically slide forward as time passes.",
             "Properties with violations in late 2026 and beyond will not count toward the distress score until the window is updated."),
            ("Zillow / third-party inconsistencies",
             "Property Type sometimes shows `Vacant Land` for a parcel that external sites (Zillow, Redfin) still show as a 5-bedroom house. This usually reflects a recent demolition or county reclassification that external aggregators have not caught yet.",
             "The county classification is authoritative for NST. External sites may lag by months."),
            ("`combovac` only flags vacant structures, not vacant lots",
             "The raw combovac field is sourced from USPS, city vacancy lists, and water shutoffs: all of which assume a building exists. Vacant lots never trigger it.",
             "The Datasets Map View color-coding uses a composite that includes vacant land classification; the raw combovac is kept as-is in filters so researchers can isolate structural vacancy specifically."),
            ("Mail-drop detection is a heuristic",
             "The `unique_entity_count / true_portfolio_size > 0.5 AND size ≥ 10` rule catches commercial mail services but may misflag genuine multi-family-office arrangements with many partners.",
             "The toggle to re-include mail drops is available in the Portfolio Filters."),
            ("Portfolio size counts all parcels at an address, not just rentals",
             "A government land bank at 601 Lakeside with 13,000+ parcels will show a very high `true_portfolio_size` even though most parcels are vacant lots, not rentals. The 'Rentals in Filter' column shows the subset relevant to the current view.",
             "Filter by Owner Type = 'Non-Profit/Government' = No to exclude. Future improvement: a 'rentals-only portfolio size' alongside the total."),
            ("Owner classification is name-regex based",
             "If an individual's name happens to contain a corporate keyword (e.g. `MARY HOLDINGS` as a surname) it will mis-classify as corporate. The inverse (an LLC that doesn't contain any corporate keyword) is also possible but rare.",
             "Spot-check expected categories periodically. Could be improved by cross-referencing with the Ohio Secretary of State business registry."),
            ("`parcel_status` field assumed CURRENT",
             "We filter out parcels where `parcel_status` is anything other than CURRENT. If the field is NULL we keep the parcel; this is almost always correct for recent exports but could mask some stale records.",
             "A fully-expired parcel with a NULL status would slip through. Unlikely but possible."),
        ]

        for title, what, impact in _limits:
            with st.expander(title, expanded=False):
                st.markdown(f"**What's going on:** {what}")
                st.markdown(f"**Impact / mitigation:** {impact}")

    st.markdown("---")
    st.caption(
        "Methodology maintained by the CWRU Center on Poverty and Community Development. "
        "Please report inaccuracies or add context via the Contact page."
    )

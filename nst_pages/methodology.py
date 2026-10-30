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

    _m_tab_overview, _m_tab_vars, _m_tab_dr = st.tabs([
        "Overview", "Variables Reference", "Distressed Rentals Methodology",
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
                ("CLASSIFICATION_DESCR", "Fiscal Office", "Full text classification (e.g. SINGLE FAMILY DWELLING). Mapped to friendlier labels in the Datasets table."),
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

    with _m_tab_dr:
        st.markdown(
            "The Distressed Rentals page flags rental properties that show signs of extractive ownership: landlords who neglect upkeep, let violations pile up, and extract rent without reinvesting. "
            "The process has five stages: filter to current parcels, identify which parcels are rentals, compute five distress indicators per property, classify owners by type, and group parcels that share a tax mailing address to detect portfolios hidden across multiple LLCs."
        )

        st.markdown("### Stage 1: Active Parcels Only")
        st.markdown(
            "The analysis starts by restricting to parcels that are currently active in the county's records. "
            "Expired, split, or consolidated parcels are excluded."
        )

        st.markdown("### Stage 2: Identifying the Rental Universe")
        st.markdown(
            "Each property is evaluated to determine whether it is likely a rental. "
            "Non-residential properties (industrial, agricultural, vacant land, common areas) are excluded. "
            "Properties with an active homestead exemption are treated as owner-occupied. "
            "Multi-family buildings, apartments, LLCs, and properties with active rental registrations are included as confirmed or probable rentals."
        )
        rent_rules = pd.DataFrame([
            ("Excluded", "Non-residential property types (industrial, agricultural, vacant land, common areas)"),
            ("Excluded", "Single-family or condo with a homestead exemption (owner-occupied)"),
            ("Probable rental", "Single-family or condo owned by a corporate entity (LLC, Inc, etc.)"),
            ("Probable rental", "Two-family or three-family dwelling"),
            ("Probable rental", "Single-family or condo with no homestead exemption"),
            ("Confirmed rental", "Property with an active City of Cleveland rental registration"),
            ("Confirmed rental", "Apartment building"),
        ], columns=["Classification", "Criteria"])
        st.dataframe(rent_rules, use_container_width=True, hide_index=True)

        st.markdown("### Stage 3: Five Distress Indicators")
        st.markdown(
            "Each property is scored on five indicators of neglect or disinvestment. "
            "The total score (0 to 5) reflects how many signs of distress a property shows. "
            "All recency-based indicators use a five-year window to capture current ownership behavior."
        )
        distress = pd.DataFrame([
            ("Tax Delinquency", "The property owes more than $500 in overdue property taxes.", "A meaningful threshold that filters out minor billing lag."),
            ("Code Violation", "A housing code violation was filed against this property in the last five years.", "Captures active patterns of neglect."),
            ("Complaint Filed", "A complaint was filed by a resident, council member, CDC, or other source in the last five years.", "Complaint origin varies by neighborhood; any source counts."),
            ("Condition Declined", "The property's exterior condition grade worsened between the 2015 and 2023 surveys.", "Direct evidence of physical deterioration over time."),
            ("Eviction Filed", "At least one eviction case was filed at this address between 2021 and 2025.", "Even a single eviction is a meaningful signal of housing instability."),
        ], columns=["Indicator", "What it means", "Why it matters"])
        st.dataframe(distress, use_container_width=True, hide_index=True)

        st.markdown("### Stage 4: Owner Classification")
        st.markdown(
            "Each property's owner name is classified into one of six categories based on how it is registered. "
            "Government and nonprofit entities are identified first to avoid misclassifying a city-affiliated LLC as a private investor."
        )
        owner_rules = pd.DataFrame([
            ("Non-Profit / Government", "City agencies, county offices, churches, universities, hospitals, CMHA, land banks, and similar public or charitable entities."),
            ("Corporate Entity", "LLCs, corporations, holding companies, property management firms, investment funds, and similar for-profit entities."),
            ("Trust", "Living trusts, family trusts, revocable or irrevocable trusts."),
            ("Joint Ownership", "Properties jointly held by two or more individuals (indicated by 'and', '&', or joint tenancy designations)."),
            ("Individual", "A single person identified by name."),
            ("Unknown / Missing", "Owner name is blank or does not match any of the above."),
        ], columns=["Owner Type", "Description"])
        st.dataframe(owner_rules, use_container_width=True, hide_index=True)

        st.markdown("### Stage 5: Portfolio Detection")
        st.markdown(
            "Some landlords obscure the true size of their portfolio by registering properties under multiple LLC names. "
            "To detect this, all properties in the county are grouped by their tax mailing address. "
            "If several differently-named entities all receive mail at the same location, they are likely controlled by the same person or organization. "
            "Each rental is then tagged with the total number of properties and entity names associated with that mailing address, "
            "so a user can see that a property belongs to a landlord who effectively controls dozens of parcels under different names."
        )

        st.markdown("### Filtering Out Mail Drops")
        st.markdown(
            "Some mailing addresses are commercial mail services used by hundreds of unrelated owners. "
            "These are automatically filtered out by default, since they do not indicate a single controlling landlord. "
            "A toggle in the Portfolio Filters section lets users include them if needed."
        )

    st.markdown("---")
    st.caption(
        "Methodology maintained by the CWRU Center on Poverty and Community Development. "
        "Please report inaccuracies or add context via the Contact page."
    )

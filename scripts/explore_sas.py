import pyreadstat

P = "P:/epilots/data/"

files = [
    "acrosssource.sas7bdat",
    "tt_bill_sep2026.sas7bdat",
    "msales.sas7bdat",
    "property.sas7bdat",
    "parcel_to_geo_lookup_w_latlon.sas7bdat",
]

for f in files:
    try:
        _, meta = pyreadstat.read_sas7bdat(
            P + f,
            metadataonly=True
        )
        print(f"\n{f}")
        print(f"  rows:    {meta.number_rows:,}")
        print(f"  columns: {meta.number_columns}")
        print(f"  cols:    {meta.column_names[:10]}...")
    except Exception as e:
        print(f"\n{f}  ERROR: {e}")

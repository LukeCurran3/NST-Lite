"""Export expander. CSV, GeoJSON, and Shapefile download buttons."""

import io
import json
import zipfile

import pandas as pd
import streamlit as st


def render(filtered_df, display_columns):
    with st.expander("Export Options"):
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            export_format = st.radio(
                "Format",
                ["CSV (Excel-friendly)", "GeoJSON (mapping)", "Shapefile (GIS software)"],
                key="export_fmt",
            )
        with ex_col2:
            export_columns_opt = st.radio(
                "Columns",
                ["Selected columns only", "All available columns"],
                key="export_cols",
            )

        total = len(filtered_df)
        all_columns = filtered_df.columns.tolist()
        export_df = filtered_df if export_columns_opt == "All available columns" else filtered_df[display_columns]

        if total == 0:
            st.warning("No data to export. Adjust your filters first.")
        elif export_format == "CSV (Excel-friendly)":
            _csv_download(export_df, total)
        elif export_format == "GeoJSON (mapping)":
            _geojson_download(filtered_df, display_columns, all_columns, export_columns_opt)
        else:
            _shapefile_download(filtered_df, display_columns, all_columns, export_columns_opt)


def _csv_download(export_df, total):
    csv_data = export_df.to_csv(index=False)
    st.download_button(
        label=f"Download {total:,} results as CSV",
        data=csv_data,
        file_name="nst_export.csv",
        mime="text/csv",
    )


def _geojson_download(filtered_df, display_columns, all_columns, export_columns_opt):
    features = []
    for _, row in filtered_df.iterrows():
        lat = row.get("LATITUDE")
        lon = row.get("LONGITUDE")
        if pd.notna(lat) and pd.notna(lon):
            cols_to_use = display_columns if export_columns_opt == "Selected columns only" else all_columns
            props = {c: (row[c].item() if hasattr(row[c], "item") else row[c])
                     for c in cols_to_use if c not in ("LATITUDE", "LONGITUDE")}
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "properties": props,
            })
    geojson = json.dumps({"type": "FeatureCollection", "features": features})
    st.download_button(
        label=f"Download {len(features):,} features as GeoJSON",
        data=geojson,
        file_name="nst_export.geojson",
        mime="application/geo+json",
    )


def _shapefile_download(filtered_df, display_columns, all_columns, export_columns_opt):
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        import tempfile, os
        import glob as glob_mod

        geo_rows = filtered_df.dropna(subset=["LATITUDE", "LONGITUDE"])
        geometry = [Point(lon, lat) for lat, lon in zip(geo_rows["LONGITUDE"], geo_rows["LATITUDE"])]
        cols_to_use = [
            c for c in (display_columns if export_columns_opt == "Selected columns only" else all_columns)
            if c not in ("LATITUDE", "LONGITUDE")
        ]
        gdf = gpd.GeoDataFrame(geo_rows[cols_to_use].reset_index(drop=True), geometry=geometry, crs="EPSG:4326")
        with tempfile.TemporaryDirectory() as tmpdir:
            shp_path = os.path.join(tmpdir, "nst_export.shp")
            gdf.to_file(shp_path, driver="ESRI Shapefile")
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for f_path in glob_mod.glob(os.path.join(tmpdir, "nst_export.*")):
                    zf.write(f_path, os.path.basename(f_path))
            buf.seek(0)
        st.download_button(
            label=f"Download {len(geo_rows):,} features as Shapefile (.zip)",
            data=buf.getvalue(),
            file_name="nst_export_shp.zip",
            mime="application/zip",
        )
    except ImportError:
        st.warning("Shapefile export requires `geopandas` and `shapely`.")
        st.code("pip install geopandas shapely", language="bash")

import uuid

import geopandas as gpd
import pandas as pd


def gdf_index_based_change_detection(new_gdf: gpd.GeoDataFrame, old_gdf: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    """
    Determine added, deleted, and modified records by comparing two GeoDataFrames.
    `new_gdf` and `old_gdf` are assumed to be snapshots of the same data at different points in time.
    It is the responsibility of the caller to ensure there is a shared index on input GDFs that is valid for making record comparisons,
    and that the temporal ordering of arguments passed as `new_gdf` and `old_gdf` is correct.
    """
    deleted_gdf = old_gdf.loc[~old_gdf.index.isin(new_gdf.index)]
    added_gdf = new_gdf.loc[~new_gdf.index.isin(old_gdf.index)]

    new_retained_gdf = new_gdf.loc[new_gdf.index.isin(old_gdf.index)]
    old_retained_gdf = old_gdf.loc[old_gdf.index.isin(new_gdf.index)]

    comparison_result = (new_retained_gdf == old_retained_gdf) | (
        new_retained_gdf.isna() & old_retained_gdf.isna()
    )
    modified_mask = ~comparison_result.all(axis=1)
    modified_gdf = new_retained_gdf.loc[modified_mask]

    return {"added": added_gdf, "deleted": deleted_gdf, "modified": modified_gdf}

def gdf_no_index_change_detection(new_gdf: gpd.GeoDataFrame, old_gdf: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    """
    Determine unique new records and unique old records by comparing two GeoDataFrames.
    Intended use case is when there is not a shared index on input GDFs that is valid for making record comparisons.
    `new_gdf` and `old_gdf` are assumed to be snapshots of the same data at different points in time.
    It is the responsibility of the caller to ensure that the temporal ordering of arguments passed as `new_gdf` and `old_gdf` is correct.
    """
    try:
        hash_column = uuid.uuid4().hex
        new_gdf[hash_column] = pd.util.hash_pandas_object(new_gdf, index=False)
        old_gdf[hash_column] = pd.util.hash_pandas_object(old_gdf, index=False)

        new_hash_set = set(new_gdf[hash_column])
        old_hash_set = set(old_gdf[hash_column])

        unique_new_mask = ~new_gdf[hash_column].isin(old_hash_set)
        unique_old_mask = ~old_gdf[hash_column].isin(new_hash_set)

        unique_new_gdf = new_gdf.loc[unique_new_mask]
        unique_old_gdf = old_gdf.loc[unique_old_mask]
    finally:
        for gdf in (new_gdf, old_gdf):
            gdf.drop(columns=hash_column, errors="ignore")

    return {"unique_new": unique_new_gdf, "unique_old": unique_old_gdf}

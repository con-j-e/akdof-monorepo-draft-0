from typing import Iterable

import geopandas as gpd
import pandas as pd
import shapely as shp

from akdof_shared.gis.coords_conversion import dd_to_ddm_lat, dd_to_ddm_lng

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def create_lifemed_base_gdf(
    lifemed_base_df: pd.DataFrame, 
    lifemed_aircraft_locations: dict[str, Iterable[str]], 
    target_epsg: int
) -> gpd.GeoDataFrame:
    """
    Create GeoDataFrame of LifeMed base locations with aircraft availability indicators.
    
    Parameters
    ----------
    lifemed_base_df : pd.DataFrame
        Base location data with coordinate columns (arp_longitude_dd, arp_latitude_dd).
    lifemed_aircraft_locations : dict[str, Iterable[str]]
        Aircraft types mapped to their base location IDs.
    target_epsg : int
        Target EPSG code for output coordinate system.
        
    Returns
    -------
    gpd.GeoDataFrame
        Base locations with geometry and aircraft availability columns.
    """
    lifemed_base_gdf = gpd.GeoDataFrame(
        data=lifemed_base_df,
        geometry=gpd.points_from_xy(lifemed_base_df["arp_longitude_dd"], lifemed_base_df["arp_latitude_dd"]),
        crs="EPSG:4326"
    )
    lifemed_base_gdf = lifemed_base_gdf.to_crs(epsg=target_epsg)

    lifemed_base_gdf["latitude_ddm"] = lifemed_base_gdf["arp_latitude_dd"].apply(dd_to_ddm_lat)
    lifemed_base_gdf["longitude_ddm"] = lifemed_base_gdf["arp_longitude_dd"].apply(dd_to_ddm_lng)

    columns_to_keep = ["loc_id", "name", "latitude_ddm", "longitude_ddm"]
    for aircraft, loc_ids in lifemed_aircraft_locations.items():
        lifemed_base_gdf[aircraft] = lifemed_base_gdf["loc_id"].apply(lambda loc: "{available}" if loc in loc_ids else "{}")
        columns_to_keep.append(aircraft)

    columns_to_keep.append("geometry")
    lifemed_base_gdf = lifemed_base_gdf[columns_to_keep]

    return lifemed_base_gdf


def get_lifemed_base_coords(lifemed_base_df: pd.DataFrame) -> dict[str, shp.Point]:
    """Extract base coordinates as Point geometries keyed by location ID."""
    lifemed_base_coords = dict()
    for row in lifemed_base_df.itertuples(index=False):
        lifemed_base_coords[row.loc_id] = shp.Point(row.arp_longitude_dd, row.arp_latitude_dd)
    return lifemed_base_coords
import geopandas as gpd
import pandas as pd
from pathlib import Path
import pyproj
import shapely as shp
import numpy as np
from typing import Iterable, Type

from akwf_utils.logging_utils import FileLoggingManager as LogManager
from akwf_gis.gis_utils import dd_to_ddm_lng, dd_to_ddm_lat

from config.py.process_config import PROJ_DIR
from core.faa_data_translators import DataFrameTranslator
from core.aircraft_fleet import AircraftFleet

logger = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log")

def create_runways_gdf(
    faa_data: dict[str, pd.DataFrame],
    lifemed_base_coords: dict[str, shp.Point],
    faa_data_translators: Iterable[Type[DataFrameTranslator]],
    aircraft_fleet: AircraftFleet,
    target_epsg: int
) -> pd.DataFrame:

    airports_df = faa_data["Airports"].reset_index(drop=True)
    runways_df = faa_data["Runways"].reset_index(drop=True)
    schedules_df = faa_data["Airport Schedules"].reset_index(drop=True)

    runways_df = pd.merge(
        left=runways_df,
        right=airports_df,
        how="inner",
        on="site_id",
        suffixes=(None, "_airport"),
        validate="many_to_one"
    )

    runway_counts = runways_df["loc_id"].value_counts()
    runways_df["loc_id_runway_count"] = runways_df["loc_id"].map(runway_counts)

    schedule_map = schedules_df.groupby("loc_id")["schedule"].apply(list)
    runways_df["schedules"] = runways_df["loc_id"].map(schedule_map)
    runways_df["schedules"] = runways_df["schedules"].apply(lambda x: x if isinstance(x, list) else [])

    runways_df[["length", "width"]] = runways_df[["length", "width"]].astype("Int32")

    runways_df["latitude_ddm"] = runways_df["arp_latitude_dd"].apply(dd_to_ddm_lat)
    runways_df["longitude_ddm"] = runways_df["arp_longitude_dd"].apply(dd_to_ddm_lng)

    for translator in faa_data_translators:
        runways_df[translator.target_column] = runways_df[translator.source_column].apply(translator.translate)

    runways_df = _calc_lifemed_base_geodesic_miles(runways_df, lifemed_base_coords)

    for aircraft in aircraft_fleet._hangar:
        runways_df[aircraft.alias] = runways_df.apply(aircraft.flight_time_estimate, axis=1)

    runways_gdf = gpd.GeoDataFrame(
        data=runways_df,
        geometry=gpd.points_from_xy(runways_df["arp_longitude_dd"], runways_df["arp_latitude_dd"]),
        crs="EPSG:4326"
    )
    runways_gdf = runways_gdf.to_crs(epsg=target_epsg)

    return runways_gdf

def _calc_lifemed_base_geodesic_miles(runways_df: pd.DataFrame, lifemed_base_coords: dict[str, shp.Point]) -> pd.DataFrame:

    geod = pyproj.Geod(ellps="WGS84")
    lngs, lats = runways_df["arp_longitude_dd"].values, runways_df["arp_latitude_dd"].values

    for loc_id, base_coords in lifemed_base_coords.items():
        base_lng, base_lat = base_coords.x, base_coords.y
        _, _, geod_dist = geod.inv(
            lngs,
            lats,
            np.full_like(lngs, base_lng),
            np.full_like(lats, base_lat)
        )
        runways_df[f"miles_{loc_id}"] = geod_dist / 1609.34

    return runways_df
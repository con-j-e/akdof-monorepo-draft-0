import geopandas as gpd
from pathlib import Path
from collections import defaultdict

from akwf_utils.logging_utils import FileLoggingManager as LogManager

from config.py.process_config import PROJ_DIR

from core.aircraft_fleet import Bell_407_Heli

logger = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log")

def create_heli_range_gdf(
    lifemed_base_gdf: gpd.GeoDataFrame,
    bell_407_heli: Bell_407_Heli,
    processing_epsg: int,
    target_epsg: int
) -> gpd.GeoDataFrame:

    heli_base_gdf = lifemed_base_gdf[
        lifemed_base_gdf["loc_id"].isin(bell_407_heli.base_locations)
    ]
    heli_base_gdf = heli_base_gdf.to_crs(epsg=processing_epsg)

    gdf_dict = defaultdict(list)

    for row in heli_base_gdf.itertuples(index=False):

        for i in range(1, 7):
            gdf_dict["departure_loc_id"].append(row.loc_id)
            gdf_dict["departure_name"].append(row.name)
            gdf_dict["departure_airport"].append(f"{row.name} ({row.loc_id})")
            #gdf_dict["aircraft"].append(bell_407_heli.alias.replace("_"," "))
            gdf_dict["aircraft"].append("Bell 407 GXP Helicopter") # explicitly assigning string value to match existing schema in target service

            minutes = i * 10
            gdf_dict["flight_minutes"].append(minutes)
            gdf_dict["flight_minutes_range"].append(f"{minutes - 10} - {minutes} minutes")

            buf_miles = (minutes / 60) * bell_407_heli.speed_mph
            buf_meters = buf_miles * 1609.34

            if i == 1:
                buffer = row.geometry.buffer(buf_meters)
                clip_buffer = buffer
            else:
                buffer = row.geometry.buffer(buf_meters).symmetric_difference(clip_buffer)
                clip_buffer = row.geometry.buffer(buf_meters)

            gdf_dict["geometry"].append(buffer)

        gdf_dict["departure_loc_id"].append(row.loc_id)
        gdf_dict["departure_name"].append(row.name)
        gdf_dict["departure_airport"].append(f"{row.name} ({row.loc_id})")
        #gdf_dict["aircraft"].append(bell_407_heli.alias.replace("_"," "))
        gdf_dict["aircraft"].append("Bell 407 GXP Helicopter") # explicitly assigning string value to match existing schema in target service

        remaining_miles = bell_407_heli.range_miles - buf_miles
        remaining_minutes = (remaining_miles / bell_407_heli.speed_mph) * 60
        remaining_meters = remaining_miles * 1609.34

        gdf_dict["flight_minutes"].append(60 + remaining_minutes)
        gdf_dict["flight_minutes_range"].append(f"60 - {int(60 + remaining_minutes)} minutes")

        buffer = row.geometry.buffer(buf_meters + remaining_meters).symmetric_difference(clip_buffer)
        gdf_dict["geometry"].append(buffer)

    heli_range_gdf = gpd.GeoDataFrame(
        data=gdf_dict,
        geometry="geometry",
        crs=heli_base_gdf.crs
    )
    heli_range_gdf = heli_range_gdf.to_crs(epsg=target_epsg)

    return heli_range_gdf

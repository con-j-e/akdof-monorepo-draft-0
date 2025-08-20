import geopandas as gpd
from pathlib import Path
from typing import Iterable
import shapely as shp

from akwf_utils.logging_utils import FileLoggingManager as LogManager

from config.py.process_config import PROJ_DIR

logger = LogManager.get_file_logger(name=__name__, log_file=PROJ_DIR / "logs" / f"{Path(__file__).stem}.log")

def create_flight_lines_gdf(lifemed_aircraft_locations: dict[str, Iterable[str]], runways_gdf: gpd.GeoDataFrame, lifemed_base_gdf: gpd.GeoDataFrame, target_epsg: int) -> gpd.GeoDataFrame:

    flight_lines_rows = list()
    for aircraft_alias in lifemed_aircraft_locations.keys():
        rows = _process_runways_and_bases(runways_gdf, lifemed_base_gdf, aircraft_alias)
        flight_lines_rows.append(rows)
    flight_lines_rows = [row for sublist in flight_lines_rows for row in sublist]

    flight_lines_gdf = gpd.GeoDataFrame(data=flight_lines_rows, geometry="geometry", crs=f"EPSG:{target_epsg}")
    flight_lines_gdf = flight_lines_gdf.drop_duplicates()
    flight_lines_gdf = flight_lines_gdf[flight_lines_gdf["aircraft_base_id"] != flight_lines_gdf["landing_airport_id"]]

    return flight_lines_gdf

def _process_runways_and_bases(runways_gdf: gpd.GeoDataFrame, lifemed_base_gdf: gpd.GeoDataFrame, aircraft_alias: str) -> gpd.GeoDataFrame:

    runways = runways_gdf[runways_gdf[aircraft_alias] != "{}"]
    bases = lifemed_base_gdf[lifemed_base_gdf[aircraft_alias] == "{available}"]

    rows = list()
    for row_a in runways.itertuples(index=False):
        flight_time_estimates = getattr(row_a, aircraft_alias)

        for row_b in bases.itertuples(index=False):
            if row_b.loc_id not in flight_time_estimates:
                continue
            
            flight_miles = getattr(row_a, f"miles_{row_b.loc_id}")
            line = shp.geometry.LineString([row_a.geometry, row_b.geometry])
            rows.append({
                "aircraft_base_id": row_b.loc_id,
                "aircraft_base_name": row_b.name,
                "landing_airport_id": row_a.loc_id,
                "landing_airport_name": row_a.name,
                "extraction_airport": f"{row_a.name} ({row_a.loc_id})",
                "miles": round(flight_miles, 2),
                "aircraft": _rename_aircraft(aircraft_alias),
                "estimated_flight_minutes": flight_time_estimates[row_b.loc_id],
                "learjet_45": "{available}" if aircraft_alias == "learjet_45" else "{}",
                "learjet_31_35": "{available}" if aircraft_alias == "learjet_31_and_35" else "{}",
                "beechcraft_king_air_200": "{available}" if aircraft_alias == "beechcraft_king_air_200" else "{}",
                "cessna_208_grand_caravan": "{available}" if aircraft_alias == "cessna_208_grand_caravan" else "{}",
                "bell_407_gxp_helicopter": "{available}" if aircraft_alias == "bell_407_gxp_helicopter" else "{}",
                "geometry": line
            })

    return rows

def _rename_aircraft(aircraft_alias: str) -> str:
    """Renaming implemented to achieve exact match with arbitrary string values used in target schema"""
    mapping = {
        "learjet_45": "Learjet 45",
        "learjet_31_and_35": "Learjet 31 / 35",
        "beechcraft_king_air_200": "King Air 200",
        "cessna_208_grand_caravan": "Cessna 208",
        "bell_407_gxp_helicopter": "Bell 407 Heli",
    }
    return mapping[aircraft_alias]
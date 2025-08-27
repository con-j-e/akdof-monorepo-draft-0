import asyncio
import json
import sys

from akdof_shared.protocol.file_logging_manager import ExitStatus
from akdof_shared.protocol.main_exit_manager import MainExitManager, EarlyExitSignal

from config.process_config import PROJ_DIR, TARGET_EPSG, PROCESSING_EPSG
from core.faa_data_manager import FAADataConfig, FaaDataManager
from config.logging_config import FLM
from config.secrets_config import GMAIL_SENDER, SOA_ARCGIS_AUTH
from core.aircraft_fleet import AircraftFleet
from core.medevac_aircraft_base import get_lifemed_base_coords, create_lifemed_base_gdf
from core.ak_runways import create_runways_gdf
from core.medevac_flight_paths import create_flight_lines_gdf
from core.heli_medevac_timezones import create_heli_range_gdf
from core.faa_data_translators import FAA_DATA_TRANSLATORS
from core.update_target_layers import update_target_layers

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

def main() -> ExitStatus:
    with MainExitManager(
        project_directory=PROJ_DIR,
        file_logging_manager=FLM,
        main_logger=_LOGGER,
        gmail_sender=GMAIL_SENDER
    ) as exit_manager:
        
        faa_data_manager = FaaDataManager(
            proj_dir=PROJ_DIR,
            faa_data_config=FAADataConfig.load(PROJ_DIR / "config" / "faa_data_config.json")
        )

        faa_data_manager.refresh_data()
        if not faa_data_manager.fresh_data and not faa_data_manager.deleted_data:
            _LOGGER.info("No updated FAA data to process, exiting...")
            raise EarlyExitSignal
        
        complete_airports_df = faa_data_manager.complete_data["Airports"]
        lifemed_base_df = complete_airports_df[complete_airports_df["loc_id"].isin(AircraftFleet.get_lifemed_base_loc_ids())]

        lifemed_base_coords = get_lifemed_base_coords(lifemed_base_df)
        runways_gdf = create_runways_gdf(
            faa_data=faa_data_manager.complete_data,
            lifemed_base_coords=lifemed_base_coords,
            faa_data_translators=FAA_DATA_TRANSLATORS,
            aircraft_fleet=AircraftFleet,
            target_epsg=TARGET_EPSG
        )
        
        lifemed_aircraft_locations = AircraftFleet.get_lifemed_aircraft_locations()
        lifemed_base_gdf = create_lifemed_base_gdf(lifemed_base_df=lifemed_base_df, lifemed_aircraft_locations=lifemed_aircraft_locations, target_epsg=TARGET_EPSG)
        flight_lines_gdf = create_flight_lines_gdf(lifemed_aircraft_locations=lifemed_aircraft_locations, runways_gdf=runways_gdf, lifemed_base_gdf=lifemed_base_gdf, target_epsg=TARGET_EPSG)
        heli_range_gdf = create_heli_range_gdf(lifemed_base_gdf=lifemed_base_gdf, bell_407_heli=AircraftFleet.select["bell_407_gxp_helicopter"], processing_epsg=PROCESSING_EPSG, target_epsg=TARGET_EPSG)

        # ArcGIS Online Arcade expressions expect these fields to hold json formatted strings.
        # GeoDataFrame column values do not get converted by `create_runways_gdf()` because
        # data contained in dictionaries needs to be accessed by `create_flight_lines_gdf()`.
        aircraft_flight_time_cols = ["learjet_45", "learjet_31_and_35", "beechcraft_king_air_200", "cessna_208_grand_caravan", "bell_407_gxp_helicopter"]
        runways_gdf[aircraft_flight_time_cols] = runways_gdf[aircraft_flight_time_cols].map(json.dumps)

        soa_token = SOA_ARCGIS_AUTH.checkout_token(minutes_needed=10)
        status = asyncio.run(update_target_layers(
            features_to_update={
                "ak_runways": runways_gdf,
                "heli_medevac_timezones": heli_range_gdf,
                "medevac_aircraft_base": lifemed_base_gdf,
                "medevac_flight_paths": flight_lines_gdf
            },
            token=soa_token
        ))
        if status["success"] is True:
            faa_data_manager.update_cache()

    return exit_manager.exit_status or ExitStatus.CRITICAL

if __name__ == "__main__":
    sys.exit(main())
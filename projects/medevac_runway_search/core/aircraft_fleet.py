from abc import ABC, abstractmethod
from typing import Iterable, Type
import re

import pandas as pd

class FixedWingAircraft(ABC):
    alias: str
    base_locations: Iterable[str]
    range_miles: int
    speed_mph: float
    taxi_minutes: int

    @classmethod
    def flight_time_estimate(cls, row: pd.Series) -> dict[str, int]:
        base_distances_miles = {loc_id: row[f"miles_{loc_id}"] for loc_id in cls.base_locations}
        return cls._assess_runway_viability(base_distances_miles, row["surface"], row["length"])
    
    @classmethod
    @abstractmethod
    def _assess_runway_viability(cls, base_distances_miles: dict[str, float], surface: str, length: float) -> dict[str, int]:
        raise NotImplementedError("Subclasses are required to implement an _assess_runway_viability method.")

class Learjet_45(FixedWingAircraft):
    alias: str = "learjet_45"
    base_locations: Iterable[str] = ("ANC", "FAI")
    range_miles: int = 2300
    speed_mph: float = 506.3
    taxi_minutes: int = 15

    @classmethod
    def _assess_runway_viability(cls, base_distances_miles: dict[str, float], surface: str, length: float) -> dict[str, int]:
        flight_minutes = dict()
        if surface in ("Asphalt", "Concrete") and length >= 5000:
            for loc_id, distance_miles in base_distances_miles.items():
                if distance_miles <= cls.range_miles:
                    flight_minutes[loc_id] = int((distance_miles / cls.speed_mph) * 60) + cls.taxi_minutes
        return flight_minutes
    
class Learjet_31_35(FixedWingAircraft):
    alias: str = "learjet_31_and_35"
    base_locations: Iterable[str] = ("ANC", "FAI")
    range_miles: int = 2000
    speed_mph: float = 506.3
    taxi_minutes: int = 15

    @classmethod
    def _assess_runway_viability(cls, base_distances_miles: dict[str, float], surface: str, length: float) -> dict[str, int]:
        flight_minutes = dict()
        if surface in ("Asphalt", "Concrete") and length >= 4000:
            for loc_id, distance_miles in base_distances_miles.items():
                if distance_miles <= cls.range_miles:
                    flight_minutes[loc_id] = int((distance_miles / cls.speed_mph) * 60) + cls.taxi_minutes
        return flight_minutes
    
class Beechcraft_200(FixedWingAircraft):
    alias: str = "beechcraft_king_air_200"
    base_locations: Iterable[str] = ("ADQ", "ANC", "DUT", "FAI")
    range_miles: int = 1400
    speed_mph: float = 299.2
    taxi_minutes: int = 15

    @classmethod
    def _assess_runway_viability(cls, base_distances_miles: dict[str, float], surface: str, length: float) -> dict[str, int]:
        flight_minutes = dict()
        if (surface in ("Asphalt", "Concrete") and length >= 2500) or (surface == "Gravel" and length >= 3000):
            for loc_id, distance_miles in base_distances_miles.items():
                if distance_miles <= cls.range_miles:
                    flight_minutes[loc_id] = int((distance_miles / cls.speed_mph) * 60) + cls.taxi_minutes
        return flight_minutes
    
class Cessna_208(FixedWingAircraft):
    alias: str = "cessna_208_grand_caravan"
    base_locations: Iterable[str] = ("BET",)
    range_miles: int = 862
    speed_mph: float = 161.1
    taxi_minutes: int = 10

    @classmethod
    def _assess_runway_viability(cls, base_distances_miles: dict[str, float], surface: str, length: float) -> dict[str, int]:
        flight_minutes = dict()
        if surface != "Water" and length >= 1800:
            for loc_id, distance_miles in base_distances_miles.items():
                if distance_miles <= cls.range_miles:
                    flight_minutes[loc_id] = int((distance_miles / cls.speed_mph) * 60) + cls.taxi_minutes
        return flight_minutes
    
class Bell_407_Heli:
    alias: str = "bell_407_gxp_helicopter"
    base_locations: Iterable[str] = ("4AK6", "SD1")
    range_miles: int = 150
    speed_mph: float = 138.1

    @classmethod
    def flight_time_estimate(cls, row: pd.Series) -> dict[str, int]:
        base_distances_miles = {loc_id: row[f"miles_{loc_id}"] for loc_id in cls.base_locations}
        return cls._assess_helipad_viability(base_distances_miles, row["surface"], row["runway_id"])

    @classmethod
    def _assess_helipad_viability(cls, base_distances_miles: dict[str, float], surface: str, runway_id: str) -> dict[str, int]:
        flight_minutes = dict()
        heli_pad_pattern = r"^H\d{1,2}$"
        if re.fullmatch(heli_pad_pattern, runway_id) and surface != "Water":
            for loc_id, distance_miles in base_distances_miles.items():
                if distance_miles <= cls.range_miles:
                    flight_minutes[loc_id] = int((distance_miles / cls.speed_mph) * 60)
        return flight_minutes

class AircraftFleet:
    _hangar: Iterable[Type[FixedWingAircraft] | Bell_407_Heli] = (
        Learjet_31_35,
        Learjet_45,
        Beechcraft_200,
        Cessna_208,
        Bell_407_Heli
    )
    select: dict[str, Type[FixedWingAircraft] | Bell_407_Heli] = {
        aircraft.alias: aircraft for aircraft in _hangar
    }

    @classmethod
    def get_lifemed_base_loc_ids(cls) -> set[str]:
        lifemed_base_loc_ids = set()
        for aircraft in cls._hangar:
            lifemed_base_loc_ids.update(aircraft.base_locations)
        return lifemed_base_loc_ids
    
    @classmethod
    def get_lifemed_aircraft_locations(cls) -> dict[str, Iterable[str]]:
        lifemed_aircraft_locations = dict()
        for aircraft in cls._hangar:
            lifemed_aircraft_locations[aircraft.alias] = aircraft.base_locations
        return lifemed_aircraft_locations
from abc import ABC, abstractmethod
from typing import Hashable, Any, Iterable, Type

class DataFrameTranslator(ABC):
    target_column: str
    source_column: str
    mapping: dict[Hashable, Any]

    @classmethod
    @abstractmethod
    def translate(cls, value: Any) -> Any: ...

class TranslateSurface(DataFrameTranslator):
    target_column = "surface"
    source_column = "surface_type_condition"
    mapping = {
        "CONC": "Concrete",
        "ASPH": "Asphalt",
        "SNOW": "Snow",
        "ICE": "Ice",
        "MATS": "Landing Mats",
        "TREATED": "Treated",
        "TRTD": "Treated",
        "GRAVEL": "Gravel",
        "GRVL": "Gravel",
        "TURF": "Turf",
        "DIRT": "Dirt",
        "WATER": "Water",
        "WOOD": "Wood",
        "GRASS": "Grass",
        "DECK": "Deck",
        "ROOF": "Roof-top",
    }
    @classmethod
    def translate(cls, value):
        for prefix, label in cls.mapping.items():
            if value.startswith(prefix):
                return label
        return value
    
class TranslateCondition(DataFrameTranslator):
    target_column = "condition"
    source_column = "surface_type_condition"
    mapping = {
        "-E": "Excellent",
        "-G": "Good",
        "-F": "Fair",
        "-P": "Poor",
        "-L": "Failed"
    }
    @classmethod
    def translate(cls, value):
        for suffix, label in cls.mapping.items():
            if value.endswith(suffix):
                return label
        return "UNKNOWN"
    
class TranslateOwnership(DataFrameTranslator):
    target_column = "ownership"
    source_column = "ownership"
    mapping = {
        "CG": "Coast Guard",
        "MA": "Air Force",
        "MN": "Navy",
        "MR": "Army",
        "PR": "Private",
        "PU": "Public",
    }
    @classmethod
    def translate(cls, value):
        return cls.mapping.get(value, value)
    
class TranslateUse(DataFrameTranslator):
    target_column = "use_" # underscore is to match a typo that exists in the schema of the target service
    source_column = "use"
    mapping = {
        "PU": "Public",
        "PR": "Private",
    }
    @classmethod
    def translate(cls, value):
        return cls.mapping.get(value, value)

class TranslateLightIntensity(DataFrameTranslator):
    target_column = "edge_light_intensity"
    source_column = "edge_light_intensity"
    mapping = {
        "HIGH": "High",
        "MED": "Medium",
        "LOW": "Low",
        "NSTD": "Non-standard lights",
        "PERI": "Perimeter lights",
    }
    @classmethod
    def translate(cls, value):
        return cls.mapping.get(value, value)
    
FAA_DATA_TRANSLATORS: Iterable[Type[DataFrameTranslator]] = (
    TranslateSurface,
    TranslateCondition,
    TranslateOwnership,
    TranslateUse,
    TranslateLightIntensity,
)
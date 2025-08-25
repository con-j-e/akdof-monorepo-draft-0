import requests

from akwf_gis.json_io import arcgis_json_to_gdf, gdf_to_arcgis_json

def test_arcgis_json_io(services: dict[str,str]) -> None:
    for alias, url in services.items():
        resp = requests.get(f"{url}/query?", params={"f":"json","where":"1=1","outfields":"*"}, timeout=60)
        resp.raise_for_status()
        feats_0 = resp.json()
        gdf = arcgis_json_to_gdf(feats_0)
        feats_1 = gdf_to_arcgis_json(gdf)
        assert feats_0["features"] == feats_1["features"], f"{alias} features have been altered by conversion logic"
        print(f"{alias} ({len(feats_1["features"])} features) underwent succesful round-trip conversion!")

if __name__ == "__main__":

    services: dict[str, str] = {
        "AK_Runways": "https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/AK_Runways/FeatureServer/0",
        "medevac_aircraft_base": "https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Medevac_Aircraft_Base/FeatureServer/0",
        "Medevac_Flight_Paths": "https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Medevac_Flight_Paths/FeatureServer/0",
        "Heli_Medevac_Timezones": "https://services1.arcgis.com/7HDiw78fcUiM2BWn/arcgis/rest/services/Heli_Medevac_Timezones/FeatureServer/0"
    }

    test_arcgis_json_io(services)

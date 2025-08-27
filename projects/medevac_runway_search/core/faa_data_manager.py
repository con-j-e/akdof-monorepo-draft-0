from dataclasses import dataclass
import json
from pathlib import Path

import pandas as pd

from config.logging_config import FLM

_LOGGER = FLM.get_file_logger(logger_name=__name__, file_name=__file__)

@dataclass
class SheetConfig:
    """
    Configuration for accessing data from a single sheet in the ADIP Published 5010.

    Attributes
    ----------
    state_column : str
        Name of the column containing state identifiers for filtering.
    index : list[str]
        Column names to use as the DataFrame index for the processed data.
    columns_to_keep : list[str]
        List of column names to retain from the original sheet data.
    cached_csv : str
        Relative path to the cached CSV file for this sheet's data.
    """
    state_column: str
    index: list[str]
    columns_to_keep: list[str]
    cached_csv: str

@dataclass
class FAADataConfig:
    """
    Configuration for accessing all data sheets in the ADIP Published 5010.

    Attributes
    ----------
    url : str
        URL to the FAA Excel file containing all airport data sheets.
    state_of_interest : str
        State code used to filter data (e.g., "AK" for Alaska).
    sheets : dict[str, SheetConfig]
        Mapping of sheet names to their individual configurations.
    """
    url: str
    state_of_interest: str
    sheets: dict[str, SheetConfig]

    @classmethod
    def load(cls, json_path: Path):
        """Load the `FAADataConfig` from a locally saved JSON file."""
        with open(json_path) as f:
            data = json.load(f)
        return cls._from_dict(data)
    
    @classmethod
    def _from_dict(cls, data: dict):
        """Create the `FAADataConfig` from a Python dictionary."""
        sheets = {
            name: SheetConfig(**sheet_data) 
            for name, sheet_data in data["sheets"].items()
        }
        return cls(
            url=data["url"],
            state_of_interest=data["state_of_interest"],
            sheets=sheets
        )
    
class FaaDataManager():
    """
    Manages data retrieval, new data identification, and data caching for the ADIP Published 5010 online excel workbook.

    Attributes
    ----------
    proj_dir : Path
        Base directory path for the project, used to resolve relative cache file paths.
    faa_data_config : FAADataConfig
        Configuration object specifying data source URL, target state, and sheet processing rules.
    fresh_data : dict[str, pd.DataFrame]
        Mapping of sheet names to DataFrames containing records that are new or updated since last cache.
    complete_data : dict[str, pd.DataFrame]
        Mapping of sheet names to DataFrames containing all current records from the FAA data source.
    deleted_data : dict[str, pd.DataFrame]
        Mapping of sheet names to DataFrames containing records present in cache but missing from current data.
    """
    def __init__(self, proj_dir: Path, faa_data_config: FAADataConfig):
        self.proj_dir = proj_dir
        self.faa_data_config = faa_data_config

        self.fresh_data = dict()
        self.complete_data = dict()
        self.deleted_data = dict()

    def refresh_data(self):
        """Loads all current FAA data specified by `self.faa_data_config`. Saves fresh data, complete data, and deleted data to instance attributes."""

        for sheet_name, sheet_config in self.faa_data_config.sheets.items():

            # load current data and filter/format to create complete dataframe specified by `faa_data_config`
            complete_df = pd.read_excel(io=self.faa_data_config.url, sheet_name=sheet_name)
            complete_df = complete_df[complete_df[sheet_config.state_column] == self.faa_data_config.state_of_interest]
            complete_df = complete_df[sheet_config.columns_to_keep]
            complete_df = complete_df.rename(columns={c: c.replace(" ", "_").lower() for c in complete_df.columns})
            complete_df = complete_df.set_index(sheet_config.index, drop=False, verify_integrity=True)
            self.complete_data[sheet_name] = complete_df

            self._assert_interchangeable_loc_id_site_id()

            # load cached data
            with open(self.proj_dir / sheet_config.cached_csv, "r") as file:
                cache_df = pd.read_csv(file)
            cache_df = cache_df.set_index(sheet_config.index, drop=False, verify_integrity=True)

            # check for cached records with indices not represented in the current complete dataframe
            deleted_df = cache_df.loc[~cache_df.index.isin(complete_df.index)]
            if len(deleted_df) > 0:
                self.deleted_data[sheet_name] = deleted_df
                _LOGGER.info(f"The '{sheet_name}' FAA data sheet has {len(deleted_df)} deleted records")

            # remove any cached record with an index not represented in the current complete dataframe
            retained_df = cache_df.loc[cache_df.index.isin(complete_df.index)]

            # identify fresh data (i.e. records in the current complete dataframe that are not in the cache dataframe)
            combined_df = pd.concat((complete_df, retained_df))
            fresh_df = combined_df.drop_duplicates(keep=False)
            if len(fresh_df) > 0:
                self.fresh_data[sheet_name] = fresh_df
                _LOGGER.info(f"The '{sheet_name}' FAA data sheet has {len(fresh_df)} updated records")

        self._get_related_records()

    def update_cache(self):
        """Overwrite cached CSV files with the current complete data retrieved by `self.refresh_data()`."""
        for sheet_name, sheet_config in self.faa_data_config.sheets.items():
            complete_df = self.complete_data[sheet_name]
            with open(self.proj_dir / sheet_config.cached_csv, "w", newline="") as file:
                complete_df.to_csv(file, index=False)
    
    def _get_related_records(self):
        """Ensure fresh dataframes contain all current complete records for any Site Id represented in the fresh data that was identified by `self.refresh_data()`."""

        fresh_site_ids = set()
        for fresh_df in self.fresh_data.values():
            site_id_vals = fresh_df["site_id"].to_list()
            fresh_site_ids.update(site_id_vals)

        if fresh_site_ids:
            for sheet_name, complete_df in self.complete_data.items():
                complete_df = complete_df[complete_df["site_id"].isin(fresh_site_ids)]
                fresh_df = self.fresh_data.get(sheet_name, pd.DataFrame())
                combined_df = pd.concat((complete_df, fresh_df))
                fresh_df = combined_df.drop_duplicates(keep="first")
                self.fresh_data[sheet_name] = fresh_df


    def _assert_interchangeable_loc_id_site_id(self):
        """
        The original code supporting the web services this project now updates made the implicit assumption that `Loc Id` is interchangeable with `Site Id` for unique record identification in the FAA data schema.
        This method asserts that this assumption still holds true upon every update cycle.
        If this assertion fails, the way in which `Loc Id` is used in the service update logic and user facing applications deserves reconsideration.
        """

        for sheet_name, df in self.complete_data.items():

            df = df.reset_index(drop=True)

            col1_to_col2_mapping = df.groupby("site_id")["loc_id"].nunique()
            assert (col1_to_col2_mapping == 1).all(), f"{sheet_name}: site_id values map inconsistently to loc_id values"
            
            col2_to_col1_mapping = df.groupby("loc_id")["site_id"].nunique()
            assert (col2_to_col1_mapping == 1).all(), f"{sheet_name}: loc_id values map inconsistently to site_id values"
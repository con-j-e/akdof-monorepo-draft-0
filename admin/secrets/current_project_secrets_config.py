"""
Static configuration documenting what information is currently in the cryptfile.
For developer reference, or in case the cryptfile needs to be rebuilt from the ground up.
"""

from akdof_shared.security.cryptfile_keyring_manager import ProjectSecret

CURRENT_PROJECT_SECRETS = (
    ProjectSecret(
        service_name="https://soa-dnr.maps.arcgis.com/",
        username="for_admin",
    ),
    ProjectSecret(
        service_name="https://nifc.maps.arcgis.com/",
        username="AK_State_Authoritative_nifc",
    ),
    ProjectSecret(
        service_name="ftp.wildfire.gov",
        username="cedick",
    ),
    ProjectSecret(
        service_name="gmail",
        username="akdofscripts@gmail.com",
    ),
    ProjectSecret(
        service_name="send_gmail",
        username="ak_parcels",
    ),
    ProjectSecret(
        service_name="send_gmail",
        username="regional_kmz_for_ftp",
    )
)
"""All project secrets that have been added to the cryptfile as of September 2025"""
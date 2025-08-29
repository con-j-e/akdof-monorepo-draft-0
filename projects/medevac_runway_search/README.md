↩️ [Back to repository overview](../../README.md)

↩️ [Back to projects](../README.md)

# About

This project updates a suite of ArcGIS Online hosted feature layers that drive core functionality of the [Alaska Medevac Runway Search](https://soa-dnr.maps.arcgis.com/home/item.html?id=442f4e69f4f248a88d09e9100b400975) web application. Updates are triggered by relevant changes in the [ADIP Published 5010](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fadip.faa.gov%2FpublishedAirports%2Fall-airport-data.xlsx&wdOrigin=BROWSELINK).

Data used to assess runway viability and estimate aircraft cruise times is gathered from the following sources:

- [Airport Data and Information Program Published 5010](https://view.officeapps.live.com/op/view.aspx?src=https%3A%2F%2Fadip.faa.gov%2FpublishedAirports%2Fall-airport-data.xlsx&wdOrigin=BROWSELINK)  
- [LifeMed Alaska’s public website](https://lifemedalaska.com/)  

Additionally, email correspondence with representatives from LifeMed Alaska, Aero Air, Air Methods, and Fly Grant during July and August of 2024 helped to guide how data gets processed in the production of this application.

---
# Requirements

## Software
* Miniconda
## Permissions
* Credentials for updating ArcGIS Online hosted feature layers that are owned by the [Alaska Department of Natural Resources](https://soa-dnr.maps.arcgis.com/home/index.html)
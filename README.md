## About
This is a shared repository for code produced by Alaska Division of Forestry and Fire Protection staff. A [monorepo](https://en.wikipedia.org/wiki/Monorepo) architecture was chosen with the following benefits in mind:
1. Ease of code reuse across different projects.
2. Implementation of standardized protocols for logging, event notification, secret management, reproducable environments, and more.
3. Establishment of consistent project organization to help facilitate long term maintainability.

## Repository Structure
```
akdof-monorepo/
	admin/
		certs/
		env/
		exit_log/
		secrets/
		tasks/
	library/
		akdof_shared/
	projects/
		...
```

## Documentation
- [**REQUIREMENTS**](requirements.md)
- [admin](admin/README.md)
- [admin/certs](admin/certs/README.md)
- [library](library/README.md)
- [projects](projects/README.md)
- [projects/ak_parcels](projects/ak_parcels/README.md) 
- [projects/medevac_runway_search](projects/medevac_runway_search/README.md)
- [projects/regional_kmz_for_ftp](projects/regional_kmz_for_ftp/README.md)
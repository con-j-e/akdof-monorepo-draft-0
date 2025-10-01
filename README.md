# ⚠️ Notice
This entire repository is being used as a drafting workspace. A new repository will be started when initial drafting stages are complete.

# About
This is a shared repository for projects that are developed by the Alaska Division of Forestry and Fire Protection GIS Unit. A [monorepo](https://en.wikipedia.org/wiki/Monorepo) was chosen with the following benefits in mind:
1. Ease of code reuse across different projects.
2. Standardized protocols for logging, event notification, secret management, reproducible environments, and more.
3. Consistent project organization to help facilitate long term maintainability.

# Repository Structure
```
akdof-monorepo/
├── admin/
│   ├── certs/
│   ├── exit_log/
│   ├── scripts/
│   ├── secrets/
│   └── tasks/
├── library/
│   └── ...
└── projects/
    └── ...
```

# Documentation
Our documentation maps onto the overall repository structure, with forward-links and back-links connecting related markdown files. It should be noted that documentation is primarily written for internal use and not necessarily with the interests of a broader audience in mind.

- [**REQUIREMENTS**](REQUIREMENTS.md)
- [admin](admin/README.md)
- [admin / certs](admin/certs/README.md)
- [admin / exit_log](admin/exit_log/README.md)
- [admin / scripts](admin/scripts/README.md)
- [admin / secrets](admin/secrets/README.md)
- [admin / tasks](admin/tasks/README.md)
- [library](library/README.md)
- [projects](projects/README.md)
- [projects / ak_parcels](projects/ak_parcels/README.md) 
- [projects / medevac_runway_search](projects/medevac_runway_search/README.md)
- [projects / regional_kmz_for_ftp](projects/regional_kmz_for_ftp/README.md)

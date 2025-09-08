↩️ [Back to repository overview](../README.md)

# About
Library subdirectories are [local packages](https://pip.pypa.io/en/stable/topics/local-project-installs) containing Python code that is implemented by multiple projects. Note that `env/setup.ps1` scripts in this repository will install local packages in [editable mode](https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs).

To begin with, all shared Python code has been organized into subpackages in a single package called [`akdof_shared`](akdof_shared). This is a conscious trade-off favoring simplified environment setup and package management over rigorous dependency isolation. If the scale and complexity of projects increases, or dependency conflicts are encountered, separation into multiple distinct packages may be warranted. 

A [src-layout](https://setuptools.pypa.io/en/latest/userguide/package_discovery.html#src-layout) is preferred for any local packages added to the library:
```
library/
└── {package_name}/
    ├── src/
    │   └── {package_name}/
    │       ├── __init__.py
    │       ├── module.py
    │       ├── sub_package_1/
    │       │   ├── __init__.py
    │       │   └── module.py
    │       └── sub_package_2/
    │           ├── __init__.py
    │           └── module.py
    ├── tests/
    └── pyproject.toml
```

"""Dynamic cross-category demand propagation.

Public API re-exported from the package submodules:

- ``state``: analytical state construction (``exposure_index``,
  ``inventory_transition``, ``bin_inventory``).
- ``synthetic_panel``: synthetic household-week panel generator
  (``generate_synthetic_panel``).
"""

from importlib.metadata import PackageNotFoundError, version

from . import state as _state_api
from . import synthetic_panel as _synthetic_panel_api
from .state import *  # noqa: F401,F403
from .synthetic_panel import *  # noqa: F401,F403

__all__ = list(_state_api.__all__) + list(_synthetic_panel_api.__all__)

# Package version from installed metadata (set by `pip install -e .`).
# Falls back to "0.0.0" when the package is imported without being installed.
try:
    __version__ = version("demand_propagation")
except PackageNotFoundError:
    __version__ = "0.0.0"

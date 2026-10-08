"""
Environment check: import every library this repository uses.

Overview:
- Purpose: Fail fast with a clear message if the environment is not set up
  (see the Installation steps in README.md) before any other test runs.
- Used by: `pytest` (run from the repository root; see README).
"""


def test_import_libraries() -> None:
    """Third-party libraries and the project package should all import."""
    import numpy  # noqa: F401
    import pandas  # noqa: F401

    import demand_propagation  # noqa: F401
    import demand_propagation.state  # noqa: F401
    import demand_propagation.synthetic_panel  # noqa: F401

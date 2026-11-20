"""Environment check: every library the package uses imports."""


def test_import_libraries() -> None:
    """numpy, pandas, scipy, and every dscdemand module import."""
    import numpy  # noqa: F401
    import pandas  # noqa: F401
    import scipy  # noqa: F401

    import dscdemand  # noqa: F401
    import dscdemand.bellman  # noqa: F401
    import dscdemand.counterfactual  # noqa: F401
    import dscdemand.data  # noqa: F401
    import dscdemand.em  # noqa: F401
    import dscdemand.likelihood  # noqa: F401
    import dscdemand.models  # noqa: F401
    import dscdemand.states  # noqa: F401

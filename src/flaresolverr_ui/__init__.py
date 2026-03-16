"""
FlareSolverr UI – simple web UI to check status and test URL solving.
Run from project root: python -m src.flaresolverr_ui
"""
from .app import create_app

__all__ = ["create_app"]

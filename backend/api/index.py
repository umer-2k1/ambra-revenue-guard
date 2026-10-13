"""Vercel Python entry point.

Vercel's Python runtime serves the ASGI ``app`` found here. It simply puts the
backend directory on the path and re-exports the FastAPI application, so the
exact same app runs locally and on Vercel.

(On Vercel, set the project's **Root Directory = backend**, so this file is at
``api/index.py`` relative to the project root.)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app  # noqa: E402

__all__ = ["app"]

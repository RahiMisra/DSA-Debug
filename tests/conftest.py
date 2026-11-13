"""Pytest configuration and shared fixtures."""

import tkinter as tk
import pytest


@pytest.fixture(scope="session")
def session_tk_root():
    """Provide a session-scoped withdrawn Tk root for headless UI tests."""
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass

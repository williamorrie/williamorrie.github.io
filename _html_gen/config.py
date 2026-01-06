#!/usr/bin/env python3
"""
Shared configuration settings for HTML generation.
"""

from pathlib import Path

script_dir = Path(__file__).resolve().parent
app_data_dir = script_dir.parent / "data"
hid_data_dir = script_dir.parent / "_data"
"""Approved report branding, embedded so saved HTML works offline."""
from base64 import b64encode
from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def report_logo_uri() -> str:
    image = files('aegislog').joinpath('assets/aegislog-logo.png').read_bytes()
    return 'data:image/png;base64,' + b64encode(image).decode('ascii')

"""Implementation of the JsonPatch specification for Pydantic.
"""
from .models import JsonPatch, JsonPatchElement
from .patcher import apply_patch

__version__ = "0.1.0"

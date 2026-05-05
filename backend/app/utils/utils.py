"""Utility functions."""

from typing import Any, Dict
import json


def dict_to_json_safe(d: Dict[str, Any]) -> str:
    """Convert dict to JSON string, handling non-serializable objects."""
    return json.dumps(d, default=str)


def json_to_dict(s: str) -> Dict[str, Any]:
    """Convert JSON string to dict."""
    try:
        return json.loads(s)
    except:
        return {}

"""Validation helpers for generation inputs and Godot-facing object names."""

from __future__ import annotations

import re
from typing import Iterable

from .constants import OBJECT_PREFIXES, VALID_DETAIL_LEVELS, VALID_FACTIONS, VALID_HULL_PROFILES, VALID_ROLES, VALID_SHIP_TYPES

_GODOT_SAFE_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


class ValidationError(ValueError):
    """Raised when ship generation input is not compatible with the pipeline."""


def validate_role(role: str) -> str:
    if role not in VALID_ROLES:
        raise ValidationError(f"Unsupported ship role: {role!r}")
    return role


def validate_faction(faction: str) -> str:
    if faction not in VALID_FACTIONS:
        raise ValidationError(f"Unsupported faction: {faction!r}")
    return faction


def validate_ship_type(ship_type: str) -> str:
    if ship_type not in VALID_SHIP_TYPES:
        raise ValidationError(f"Unsupported ship type: {ship_type!r}")
    return ship_type


def validate_hull_profile(hull_profile: str) -> str:
    if hull_profile not in VALID_HULL_PROFILES:
        raise ValidationError(f"Unsupported hull profile: {hull_profile!r}")
    return hull_profile


def validate_detail_level(detail_level: str) -> str:
    if detail_level not in VALID_DETAIL_LEVELS:
        raise ValidationError(f"Unsupported detail level: {detail_level!r}")
    return detail_level


def validate_seed(seed: int) -> int:
    if not isinstance(seed, int):
        raise ValidationError("Seed must be an integer.")
    if seed < 0:
        raise ValidationError("Seed must be zero or greater.")
    return seed


def validate_asset_id(asset_id: str) -> str:
    if not asset_id:
        raise ValidationError("Asset ID cannot be empty.")
    if not _GODOT_SAFE_NAME.match(asset_id):
        raise ValidationError(f"Asset ID is not Godot-friendly: {asset_id!r}")
    return asset_id


def validate_object_name(name: str) -> str:
    if not name:
        raise ValidationError("Generated object name cannot be empty.")
    if not _GODOT_SAFE_NAME.match(name):
        raise ValidationError(f"Object name is not Godot-friendly: {name!r}")
    if not name.startswith(OBJECT_PREFIXES):
        raise ValidationError(f"Object name has no supported prefix: {name!r}")
    return name


def validate_object_names(names: Iterable[str]) -> None:
    for name in names:
        validate_object_name(name)

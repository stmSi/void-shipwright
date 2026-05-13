"""Validation helpers for generation inputs and Godot-facing object names."""

from __future__ import annotations

import re
from typing import Iterable

from .constants import (
    OBJECT_PREFIXES,
    VALID_DETAIL_LEVELS,
    VALID_FACTIONS,
    VALID_HULL_PROFILES,
    VALID_MATERIAL_STYLES,
    VALID_ROLES,
    VALID_SHIP_TYPES,
    VALID_TEXTURE_WORKFLOWS,
)
from .design_language import VALID_DESIGN_LANGUAGES, VALID_SILHOUETTE_BIASES, VALID_VISUAL_QUALITIES
from .material_library import VALID_MATERIAL_COMPLEXITIES, VALID_TEXTURE_QUALITIES
from .modular import VALID_SHIP_FRAMES

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


def validate_ship_frame(ship_frame: str) -> str:
    if ship_frame != "auto" and ship_frame not in VALID_SHIP_FRAMES:
        raise ValidationError(f"Unsupported ship frame: {ship_frame!r}")
    return ship_frame


def validate_hardpoint_preset(hardpoint_preset: str) -> str:
    if hardpoint_preset not in {"frame_default", "minimal", "combat", "industrial"}:
        raise ValidationError(f"Unsupported hardpoint preset: {hardpoint_preset!r}")
    return hardpoint_preset


def validate_component_slot_preset(component_slot_preset: str) -> str:
    if component_slot_preset not in {"frame_default", "minimal", "expanded"}:
        raise ValidationError(f"Unsupported component slot preset: {component_slot_preset!r}")
    return component_slot_preset


def validate_hull_profile(hull_profile: str) -> str:
    if hull_profile not in VALID_HULL_PROFILES:
        raise ValidationError(f"Unsupported hull profile: {hull_profile!r}")
    return hull_profile


def validate_detail_level(detail_level: str) -> str:
    if detail_level not in VALID_DETAIL_LEVELS:
        raise ValidationError(f"Unsupported detail level: {detail_level!r}")
    return detail_level


def validate_visual_quality(visual_quality: str) -> str:
    if visual_quality not in VALID_VISUAL_QUALITIES:
        raise ValidationError(f"Unsupported visual quality: {visual_quality!r}")
    return visual_quality


def validate_design_language(design_language: str) -> str:
    if design_language not in VALID_DESIGN_LANGUAGES:
        raise ValidationError(f"Unsupported design language: {design_language!r}")
    return design_language


def validate_silhouette_bias(silhouette_bias: str) -> str:
    if silhouette_bias not in VALID_SILHOUETTE_BIASES:
        raise ValidationError(f"Unsupported silhouette bias: {silhouette_bias!r}")
    return silhouette_bias


def validate_material_style(material_style: str) -> str:
    if material_style not in VALID_MATERIAL_STYLES:
        raise ValidationError(f"Unsupported material style: {material_style!r}")
    return material_style


def validate_texture_workflow(texture_workflow: str) -> str:
    if texture_workflow not in VALID_TEXTURE_WORKFLOWS:
        raise ValidationError(f"Unsupported texture workflow: {texture_workflow!r}")
    return texture_workflow


def validate_texture_resolution(texture_resolution: int) -> int:
    if not isinstance(texture_resolution, int):
        raise ValidationError("Texture resolution must be an integer.")
    if texture_resolution < 64 or texture_resolution > 2048:
        raise ValidationError("Texture resolution must be between 64 and 2048.")
    return texture_resolution


def validate_texture_quality(texture_quality: str) -> str:
    if texture_quality not in VALID_TEXTURE_QUALITIES:
        raise ValidationError(f"Unsupported texture quality: {texture_quality!r}")
    return texture_quality


def validate_material_complexity(material_complexity: str) -> str:
    if material_complexity not in VALID_MATERIAL_COMPLEXITIES:
        raise ValidationError(f"Unsupported material complexity: {material_complexity!r}")
    return material_complexity


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

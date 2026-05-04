"""Metadata extraction and JSON serialization for generated ships."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .constants import (
    ADDON_NAME,
    REQUIRED_COLLISION_PROXIES,
    REQUIRED_DAMAGE_MARKERS,
    REQUIRED_SOCKETS,
    SCHEMA_VERSION,
)
from .validation import validate_asset_id, validate_faction, validate_object_names, validate_role, validate_seed


def _round_float(value: float) -> float:
    return round(float(value), 4)


def _vector3(values: Iterable[float]) -> list[float]:
    return [_round_float(value) for value in values]


def _raw_vector3(values: Any) -> list[float] | None:
    if values is None:
        return None

    try:
        vector = list(values)
    except TypeError:
        return None

    if len(vector) < 3:
        return None

    try:
        return [float(vector[0]), float(vector[1]), float(vector[2])]
    except (TypeError, ValueError):
        return None


def _object_box_size(obj: Any) -> list[float]:
    scale = _raw_vector3(getattr(obj, "scale", None)) or [1.0, 1.0, 1.0]
    bounds = getattr(obj, "bound_box", None)
    if bounds is not None:
        try:
            corners = [tuple(corner) for corner in bounds]
        except TypeError:
            corners = []

        if corners:
            local_size = [
                max(corner[index] for corner in corners) - min(corner[index] for corner in corners)
                for index in range(3)
            ]
            size = [local_size[index] * abs(scale[index]) for index in range(3)]
            if any(value > 0.0001 for value in size):
                return _vector3(size)

    dimensions = _raw_vector3(getattr(obj, "dimensions", None))
    if dimensions is not None and any(abs(value) > 0.0001 for value in dimensions):
        return _vector3(abs(value) for value in dimensions)

    return _vector3(abs(value) * 2.0 for value in scale)


def _socket_type(name: str) -> str:
    if name.startswith("SOCKET_Weapon_"):
        return "weapon"
    if name.startswith("SOCKET_Missile_"):
        return "missile"
    if name.startswith("SOCKET_Engine_"):
        return "engine"
    if name.startswith("SOCKET_Camera_"):
        return "camera"
    if name.startswith("SOCKET_Target_"):
        return "target"
    if name.startswith("SOCKET_Loot_"):
        return "loot"
    if name.startswith("SOCKET_Boarding_"):
        return "boarding"
    return "generic"


def _object_transform_entry(obj: Any) -> dict[str, Any]:
    rotation = getattr(obj, "rotation_euler", (0.0, 0.0, 0.0))
    scale = getattr(obj, "scale", (1.0, 1.0, 1.0))
    return {
        "name": obj.name,
        "position": _vector3(obj.location),
        "rotation_euler": _vector3(rotation),
        "scale": _vector3(scale),
    }


def collect_scene_objects(objects: Iterable[Any]) -> dict[str, list[dict[str, Any]]]:
    """Collect Godot-facing objects into schema sections.

    The function accepts Blender objects but intentionally uses duck typing so
    it can be unit-tested outside Blender.
    """

    sorted_objects = sorted(objects, key=lambda item: item.name)
    validate_object_names(obj.name for obj in sorted_objects)

    sockets: list[dict[str, Any]] = []
    collisions: list[dict[str, Any]] = []
    damage: list[dict[str, Any]] = []
    vfx: list[dict[str, Any]] = []
    cameras: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    meshes: list[dict[str, Any]] = []

    for obj in sorted_objects:
        entry = _object_transform_entry(obj)
        if obj.name.startswith("SOCKET_"):
            entry["socket_type"] = _socket_type(obj.name)
            sockets.append(entry)
        elif obj.name.startswith("COLLISION_"):
            entry["shape"] = "box"
            entry["size"] = _object_box_size(obj)
            entry["disabled_by_default"] = False
            collisions.append(entry)
        elif obj.name.startswith("DAMAGE_"):
            entry["zone"] = obj.name.removeprefix("DAMAGE_")
            damage.append(entry)
        elif obj.name.startswith("VFX_"):
            entry["vfx_type"] = obj.name.removeprefix("VFX_").lower()
            vfx.append(entry)
        elif obj.name.startswith("CAMERA_"):
            entry["camera_type"] = obj.name.removeprefix("CAMERA_").lower()
            cameras.append(entry)
        elif obj.name.startswith("TARGET_"):
            entry["target_type"] = obj.name.removeprefix("TARGET_").lower()
            targets.append(entry)
        elif obj.name.startswith("MESH_"):
            entry["mesh_role"] = obj.name.removeprefix("MESH_").lower()
            meshes.append(entry)

    return {
        "meshes": meshes,
        "sockets": sockets,
        "collision_proxies": collisions,
        "damage_zones": damage,
        "vfx_markers": vfx,
        "camera_markers": cameras,
        "target_markers": targets,
    }


def build_metadata(
    *,
    ship_id: str,
    role: str,
    faction: str,
    seed: int,
    variant: str,
    objects: Iterable[Any],
) -> dict[str, Any]:
    validate_role(role)
    validate_faction(faction)
    validate_seed(seed)
    validate_asset_id(ship_id)
    validate_asset_id(variant)

    sections = collect_scene_objects(objects)
    metadata = {
        "schema_version": SCHEMA_VERSION,
        "generator": ADDON_NAME,
        "ship_id": ship_id,
        "role": role,
        "faction": faction,
        "seed": seed,
        "variant": variant,
        "units": "meters",
        "source_axis": {"forward": "-Y", "up": "Z", "right": "X"},
        "godot_axis": {"forward": "-Z", "up": "Y", "right": "X"},
        "required_contract": {
            "sockets": list(REQUIRED_SOCKETS),
            "damage_zones": list(REQUIRED_DAMAGE_MARKERS),
            "collision_proxies": list(REQUIRED_COLLISION_PROXIES),
        },
        **sections,
    }
    validate_metadata_contract(metadata)
    return metadata


def validate_metadata_contract(metadata: dict[str, Any]) -> None:
    socket_names = {item["name"] for item in metadata.get("sockets", [])}
    damage_names = {item["name"] for item in metadata.get("damage_zones", [])}
    collision_names = {item["name"] for item in metadata.get("collision_proxies", [])}

    missing_sockets = sorted(set(REQUIRED_SOCKETS) - socket_names)
    missing_damage = sorted(set(REQUIRED_DAMAGE_MARKERS) - damage_names)
    missing_collisions = sorted(set(REQUIRED_COLLISION_PROXIES) - collision_names)

    failures = []
    if missing_sockets:
        failures.append(f"missing sockets: {', '.join(missing_sockets)}")
    if missing_damage:
        failures.append(f"missing damage markers: {', '.join(missing_damage)}")
    if missing_collisions:
        failures.append(f"missing collision proxies: {', '.join(missing_collisions)}")
    if failures:
        raise ValueError("Generated metadata violates Godot contract: " + "; ".join(failures))


def write_metadata(path: str | Path, metadata: dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")

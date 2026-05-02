"""Procedural Blender geometry generation for Void Shipwright."""

from __future__ import annotations

import random
from math import cos, pi, sin
from dataclasses import dataclass
from typing import Any

import bpy
from mathutils import Vector

from .constants import (
    FACTION_PROFILES,
    REQUIRED_CAMERA_MARKERS,
    REQUIRED_COLLISION_PROXIES,
    REQUIRED_DAMAGE_MARKERS,
    REQUIRED_SOCKETS,
    REQUIRED_VFX_MARKERS,
    ROLE_PROFILES,
)
from .metadata import build_metadata
from .validation import validate_detail_level, validate_faction, validate_hull_profile, validate_role, validate_seed, validate_ship_type


@dataclass(frozen=True)
class ShipGenerationConfig:
    role: str
    faction: str
    seed: int
    ship_type: str = "light_raider"
    ship_id: str = "void_ship"
    variant: str = "default"
    collection_name: str = "Void Shipwright Generated"
    clear_existing: bool = True
    detail_level: str = "hero"
    hull_profile: str = "raider"
    wing_span: float = 1.0
    engine_scale: float = 1.0
    hull_length: float = 1.0
    hull_width: float = 1.0
    hull_height: float = 1.0
    armor_density: float = 1.0
    greeble_density: float = 0.85
    decal_density: float = 1.0
    wear_amount: float = 0.65
    glow_strength: float = 1.2
    weapon_density: float = 0.75
    missile_density: float = 0.65
    cargo_density: float = 0.2
    asymmetry: float = 0.15
    use_custom_colors: bool = False
    primary_hue: tuple[float, float, float] | None = None
    accent_hue: tuple[float, float, float] | None = None
    emissive_hue: tuple[float, float, float] | None = None
    show_helpers: bool = False
    presentation_scene: bool = True


def generate_ship(config: ShipGenerationConfig) -> dict[str, Any]:
    validate_role(config.role)
    validate_faction(config.faction)
    validate_ship_type(config.ship_type)
    validate_hull_profile(config.hull_profile)
    validate_detail_level(config.detail_level)
    validate_seed(config.seed)

    rng = random.Random(config.seed)
    collection = _prepare_collection(config.collection_name, clear_existing=config.clear_existing)
    materials = _create_materials(config.faction, glow_strength=config.glow_strength, config=config)
    dimensions = _dimensions_for(
        config.role,
        rng,
        ship_type=config.ship_type,
        hull_profile=config.hull_profile,
        hull_length=config.hull_length,
        hull_width=config.hull_width,
        hull_height=config.hull_height,
        wing_span=config.wing_span,
        engine_scale=config.engine_scale,
    )

    generated_objects: list[Any] = []
    generated_objects.extend(_create_meshes(collection, materials, dimensions, rng, config))
    generated_objects.extend(_create_collision_proxies(collection, dimensions))
    generated_objects.extend(_create_damage_markers(collection, dimensions))
    generated_objects.extend(_create_sockets(collection, dimensions))
    generated_objects.extend(_create_vfx_markers(collection, dimensions))
    generated_objects.extend(_create_camera_markers(collection, dimensions))
    generated_objects.extend(_create_target_markers(collection, dimensions))
    if config.show_helpers:
        _show_technical_helpers(generated_objects)
    else:
        _hide_technical_helpers(generated_objects)

    root = _create_empty(collection, f"TARGET_{_safe_id(config.ship_id)}_Root", (0.0, 0.0, 0.0))
    root.empty_display_size = 0.05
    generated_objects.append(root)
    for obj in generated_objects:
        if obj is not root:
            obj.parent = root

    metadata = build_metadata(
        ship_id=config.ship_id,
        role=config.role,
        faction=config.faction,
        seed=config.seed,
        variant=config.variant,
        objects=generated_objects,
    )
    root["void_shipwright_metadata"] = metadata
    root["void_shipwright_role"] = config.role
    root["void_shipwright_faction"] = config.faction
    root["void_shipwright_seed"] = config.seed
    if config.presentation_scene:
        _setup_presentation_scene(collection, dimensions)
    return metadata


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in value)


def _prepare_collection(name: str, *, clear_existing: bool) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    if clear_existing:
        for obj in list(collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
    return collection


def _mix_color(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    amount: float,
) -> tuple[float, float, float, float]:
    return (
        a[0] * (1.0 - amount) + b[0] * amount,
        a[1] * (1.0 - amount) + b[1] * amount,
        a[2] * (1.0 - amount) + b[2] * amount,
        a[3] * (1.0 - amount) + b[3] * amount,
    )


def _scale_color(color: tuple[float, float, float, float], amount: float) -> tuple[float, float, float, float]:
    return (
        min(max(color[0] * amount, 0.0), 1.0),
        min(max(color[1] * amount, 0.0), 1.0),
        min(max(color[2] * amount, 0.0), 1.0),
        color[3],
    )


def _rgba_from_rgb(value: tuple[float, float, float] | None, fallback: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    if value is None:
        return fallback
    return (value[0], value[1], value[2], 1.0)


def _create_materials(
    faction: str,
    *,
    glow_strength: float = 1.0,
    config: ShipGenerationConfig | None = None,
) -> dict[str, bpy.types.Material]:
    profile = FACTION_PROFILES[faction]
    use_custom_colors = bool(config and config.use_custom_colors)
    faction_hull = _rgba_from_rgb(config.primary_hue if use_custom_colors and config else None, profile["color"])
    accent_color = _rgba_from_rgb(config.accent_hue if use_custom_colors and config else None, profile["accent"])
    graphite = (0.028, 0.031, 0.033, 1.0)
    armor = _mix_color((0.045, 0.047, 0.047, 1.0), faction_hull, 0.18)
    worn_edge = _mix_color((0.38, 0.37, 0.34, 1.0), faction_hull, 0.12)
    trim_color = (0.008, 0.01, 0.012, 1.0)
    raider_red = (0.72, 0.055, 0.035, 1.0)
    glow_color = _rgba_from_rgb(
        config.emissive_hue if use_custom_colors and config else None,
        (
            min(accent_color[0] * 0.24 + 0.02, 1.0),
            min(accent_color[1] * 0.45 + 0.72, 1.0),
            min(accent_color[2] * 0.55 + 0.86, 1.0),
            1.0,
        ),
    )
    window_color = (
        min(glow_color[0] * 0.65 + 0.2, 1.0),
        min(glow_color[1] * 0.7 + 0.25, 1.0),
        min(glow_color[2] + 0.15, 1.0),
        1.0,
    )
    return {
        "hull": _material("VS_Textured_Graphite_Hull", graphite, metallic=0.32, roughness=0.58, noise_scale=72.0, noise_strength=0.34, bump_strength=0.07),
        "armor": _material("VS_Textured_Armor_Plates", armor, metallic=0.42, roughness=0.52, noise_scale=44.0, noise_strength=0.28, bump_strength=0.05),
        "accent": _material("VS_Faction_Accent", accent_color, metallic=0.35, roughness=0.4, noise_scale=38.0, noise_strength=0.12, bump_strength=0.02),
        "trim": _material("VS_Black_Ceramic_Trim", trim_color, metallic=0.42, roughness=0.34, noise_scale=92.0, noise_strength=0.2, bump_strength=0.04),
        "panel": _material("VS_Deep_Panel_Seams", (0.002, 0.003, 0.004, 1.0), metallic=0.25, roughness=0.62),
        "wear": _material("VS_Chipped_Edge_Wear", worn_edge, metallic=0.15, roughness=0.72, noise_scale=115.0, noise_strength=0.22),
        "red_decal": _material("VS_Raider_Red_Livery", raider_red, metallic=0.08, roughness=0.38, noise_scale=80.0, noise_strength=0.18),
        "ordnance": _material("VS_Ordnance_Amber", (0.9, 0.48, 0.10, 1.0), metallic=0.18, roughness=0.44, emission_color=(0.9, 0.28, 0.04, 1.0), emission_strength=0.22 * glow_strength, noise_scale=58.0, noise_strength=0.08),
        "glass": _material("VS_CanopyGlass", (0.08, 0.32, 0.46, 0.72), alpha=0.72, metallic=0.0, roughness=0.12),
        "glow": _material("VS_EngineGlow", glow_color, emission_color=glow_color, emission_strength=3.5 * glow_strength),
        "window": _material("VS_WindowLights", window_color, emission_color=window_color, emission_strength=2.2 * glow_strength),
        "decal": _material("VS_DesignerDecals", accent_color, emission_color=accent_color, emission_strength=0.35, metallic=0.05, roughness=0.28),
        "collision": _material("VS_CollisionProxy", (0.15, 0.85, 0.45, 0.25), alpha=0.25),
        "marker": _material("VS_Marker", (0.1, 0.55, 1.0, 1.0)),
    }


def _material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    alpha: float = 1.0,
    metallic: float = 0.0,
    roughness: float = 0.5,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    noise_scale: float = 0.0,
    noise_strength: float = 0.0,
    bump_strength: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf is not None:
        for node in list(nodes):
            if node.name not in {"Principled BSDF", "Material Output"}:
                nodes.remove(node)
        _set_input(bsdf, "Base Color", color)
        _set_input(bsdf, "Alpha", alpha)
        _set_input(bsdf, "Metallic", metallic)
        _set_input(bsdf, "Roughness", roughness)
        if emission_color is not None:
            _set_input(bsdf, "Emission Color", emission_color)
            _set_input(bsdf, "Emission Strength", emission_strength)
        if noise_scale > 0.0 and noise_strength > 0.0:
            noise = nodes.new("ShaderNodeTexNoise")
            noise.inputs["Scale"].default_value = noise_scale
            noise.inputs["Detail"].default_value = 13.0
            noise.inputs["Roughness"].default_value = 0.62
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].position = 0.18
            ramp.color_ramp.elements[0].color = _scale_color(color, max(0.08, 1.0 - noise_strength))
            ramp.color_ramp.elements[1].position = 1.0
            ramp.color_ramp.elements[1].color = _mix_color(color, (0.9, 0.88, 0.78, color[3]), noise_strength * 0.18)
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            if bump_strength > 0.0 and "Normal" in bsdf.inputs:
                bump = nodes.new("ShaderNodeBump")
                bump.inputs["Strength"].default_value = bump_strength
                bump.inputs["Distance"].default_value = 0.08
                links.new(noise.outputs["Fac"], bump.inputs["Height"])
                links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
    return material


def _set_input(node: bpy.types.Node, name: str, value: Any) -> None:
    if name in node.inputs:
        node.inputs[name].default_value = value


def _dimensions_for(
    role: str,
    rng: random.Random,
    *,
    ship_type: str,
    hull_profile: str,
    hull_length: float,
    hull_width: float,
    hull_height: float,
    wing_span: float,
    engine_scale: float,
) -> dict[str, float]:
    profile = ROLE_PROFILES[role]
    jitter = 1.0 + rng.uniform(-0.06, 0.06)
    if role == "boss":
        length_scale = 1.08
        width_scale = 0.86
        height_scale = 0.82
    elif role in {"civilian", "background_traffic"}:
        length_scale = 1.16
        width_scale = 0.74
        height_scale = 0.82
    elif role == "drone":
        length_scale = 1.05
        width_scale = 0.78
        height_scale = 0.76
    else:
        length_scale = 1.24
        width_scale = 0.68
        height_scale = 0.78
    if hull_profile == "needle":
        length_scale *= 1.18
        width_scale *= 0.72
        height_scale *= 0.88
    elif hull_profile == "heavy":
        length_scale *= 0.95
        width_scale *= 1.18
        height_scale *= 1.08
    elif hull_profile == "cargo":
        length_scale *= 1.1
        width_scale *= 0.9
        height_scale *= 1.0
    if ship_type == "missile_corvette":
        length_scale *= 0.98
        width_scale *= 1.48
        height_scale *= 1.18
        wing_span *= 0.58
        engine_scale *= 1.28
    elif ship_type == "interceptor":
        length_scale *= 1.16
        width_scale *= 0.76
        height_scale *= 0.82
        wing_span *= 0.85
        engine_scale *= 1.45
    elif ship_type == "gunship":
        length_scale *= 0.92
        width_scale *= 1.22
        height_scale *= 1.08
        wing_span *= 0.72
        engine_scale *= 1.1
    elif ship_type == "freighter":
        length_scale *= 1.12
        width_scale *= 1.05
        height_scale *= 1.15
        wing_span *= 0.45
        engine_scale *= 0.9
    return {
        "length": profile["length"] * jitter * length_scale * hull_length,
        "width": profile["width"] * (1.0 + rng.uniform(-0.04, 0.04)) * width_scale * hull_width,
        "height": profile["height"] * (1.0 + rng.uniform(-0.05, 0.05)) * height_scale * hull_height,
        "wing": profile["wing"] * wing_span,
        "engine": profile["engine"] * engine_scale,
    }


def _detail_multiplier(level: str) -> float:
    return {
        "low": 0.45,
        "medium": 0.72,
        "high": 1.0,
        "hero": 1.35,
    }.get(level, 1.0)


def _lerp(a: float, b: float, amount: float) -> float:
    return a * (1.0 - amount) + b * amount


def _raider_profile_rings(length: float, width: float, height: float) -> list[tuple[float, float, float, float]]:
    return [
        (-length * 0.66, width * 0.018, height * 0.035, -height * 0.02),
        (-length * 0.56, width * 0.06, height * 0.10, -height * 0.015),
        (-length * 0.42, width * 0.16, height * 0.22, 0.0),
        (-length * 0.22, width * 0.28, height * 0.34, height * 0.02),
        (length * 0.02, width * 0.36, height * 0.38, height * 0.01),
        (length * 0.25, width * 0.30, height * 0.31, -height * 0.02),
        (length * 0.47, width * 0.18, height * 0.20, -height * 0.035),
        (length * 0.60, width * 0.08, height * 0.10, -height * 0.03),
    ]


def _raider_profile_at_y(length: float, width: float, height: float, y: float) -> tuple[float, float, float]:
    rings = _raider_profile_rings(length, width, height)
    if y <= rings[0][0]:
        _, half_width, half_height, offset_z = rings[0]
        return half_width, half_height, offset_z
    if y >= rings[-1][0]:
        _, half_width, half_height, offset_z = rings[-1]
        return half_width, half_height, offset_z

    for start, end in zip(rings, rings[1:]):
        y0, width0, height0, z0 = start
        y1, width1, height1, z1 = end
        if y0 <= y <= y1:
            amount = (y - y0) / (y1 - y0)
            return _lerp(width0, width1, amount), _lerp(height0, height1, amount), _lerp(z0, z1, amount)
    _, half_width, half_height, offset_z = rings[-1]
    return half_width, half_height, offset_z


def _hull_top_z(length: float, width: float, height: float, x: float, y: float, *, clearance: float = 0.0) -> float:
    half_width, half_height, offset_z = _raider_profile_at_y(length, width, height, y)
    width_ratio = min(abs(x) / max(half_width, 0.001), 1.0)
    crown = offset_z + half_height
    shoulder = offset_z + half_height * 0.38
    return _lerp(crown, shoulder, width_ratio**1.35) + clearance


def _hull_side_z(length: float, width: float, height: float, x: float, y: float, *, clearance: float = 0.0) -> float:
    _, half_height, offset_z = _raider_profile_at_y(length, width, height, y)
    return offset_z + half_height * 0.06 + clearance


def _create_meshes(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    engine = dimensions["engine"]

    objects = [
        _raider_hull(collection, "MESH_Hull_Core", length, width, height, materials["hull"], rng),
        _raider_upper_armor(collection, "MESH_Dorsal_Armor_Shell", length, width, height, materials["armor"]),
        _raider_keel(collection, "MESH_Ventral_Keel", length, width, height, materials["trim"]),
        _raider_cockpit(collection, "MESH_Canopy_Glass", length, width, height, materials["glass"]),
        _raider_wing(collection, "MESH_Wing_Left", -1, length, width, height, wing, materials["hull"]),
        _raider_wing(collection, "MESH_Wing_Right", 1, length, width, height, wing, materials["hull"]),
        _raider_wing_armor(collection, "MESH_Wing_Armor_Left", -1, length, width, height, wing, materials["armor"]),
        _raider_wing_armor(collection, "MESH_Wing_Armor_Right", 1, length, width, height, wing, materials["armor"]),
        _raider_winglet(collection, "MESH_Winglet_Left", -1, length, width, height, wing, materials["armor"]),
        _raider_winglet(collection, "MESH_Winglet_Right", 1, length, width, height, wing, materials["armor"]),
        _smooth_engine_pod(
            collection,
            "MESH_Engine_Main_Pod",
            (0.0, length * 0.42, 0.0),
            length * 0.28,
            width * 0.18,
            height * 0.26 * engine,
            materials["armor"],
        ),
        _engine_glow(
            collection,
            "MESH_Engine_Main_Glow",
            (0.0, length * 0.58, 0.0),
            width * 0.13,
            length * 0.025,
            materials["glow"],
        ),
        _smooth_engine_pod(
            collection,
            "MESH_Engine_Left_Pod",
            (-width * 0.27, length * 0.39, -height * 0.05),
            length * 0.24,
            width * 0.095 * engine,
            height * 0.18 * engine,
            materials["armor"],
        ),
        _engine_glow(
            collection,
            "MESH_Engine_Left_Glow",
            (-width * 0.27, length * 0.535, -height * 0.05),
            width * 0.065 * engine,
            length * 0.022,
            materials["glow"],
        ),
        _smooth_engine_pod(
            collection,
            "MESH_Engine_Right_Pod",
            (width * 0.27, length * 0.39, -height * 0.05),
            length * 0.24,
            width * 0.095 * engine,
            height * 0.18 * engine,
            materials["armor"],
        ),
        _engine_glow(
            collection,
            "MESH_Engine_Right_Glow",
            (width * 0.27, length * 0.535, -height * 0.05),
            width * 0.065 * engine,
            length * 0.022,
            materials["glow"],
        ),
        _raider_tail_fin(collection, "MESH_Dorsal_Fin", length, width, height, 1, materials["armor"]),
        _raider_tail_fin(collection, "MESH_Ventral_Fin", length, width, height, -1, materials["trim"]),
        _weapon_barrel(collection, "MESH_Weapon_Front_01", (-width * 0.08, -length * 0.60, -height * 0.04), width * 0.018, length * 0.26, materials["trim"]),
        _weapon_barrel(collection, "MESH_Weapon_Front_02", (width * 0.08, -length * 0.60, -height * 0.04), width * 0.018, length * 0.26, materials["trim"]),
        _weapon_barrel(collection, "MESH_Nose_Needle_Left", (-width * 0.18, -length * 0.56, -height * 0.02), width * 0.012, length * 0.34, materials["trim"]),
        _weapon_barrel(collection, "MESH_Nose_Needle_Right", (width * 0.18, -length * 0.56, -height * 0.02), width * 0.012, length * 0.34, materials["trim"]),
    ]

    objects.extend(_create_panel_details(collection, materials, dimensions, rng, config))
    objects.extend(_create_greebles(collection, materials, dimensions, rng, config))
    objects.extend(_create_role_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_faction_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_archetype_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_designer_detail_layer(collection, materials, dimensions, rng, config))

    if config.role == "boss" or config.faction in {"sector_navy", "corporate_security"}:
        objects.append(
            _rounded_pod(
                collection,
                "MESH_Dorsal_Command_Ridge",
                (0.0, length * 0.06, height * 0.62),
                length * 0.24,
                width * 0.11,
                height * 0.14,
                materials["accent"],
            )
        )

    if config.role in {"civilian", "background_traffic"}:
        objects.extend(
            [
                _rounded_pod(
                    collection,
                    "MESH_Cargo_Pod_Left",
                    (-width * 0.21, length * 0.2, -height * 0.36),
                    length * 0.28,
                    width * 0.08,
                    height * 0.13,
                    materials["accent"],
                ),
                _rounded_pod(
                    collection,
                    "MESH_Cargo_Pod_Right",
                    (width * 0.21, length * 0.2, -height * 0.36),
                    length * 0.28,
                    width * 0.08,
                    height * 0.13,
                    materials["accent"],
                ),
            ]
        )

    for obj in objects:
        obj["void_shipwright_kind"] = "visual_mesh"
        obj["void_shipwright_seed_offset"] = rng.randint(1, 999999)
    return objects


def _raider_hull(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
    rng: random.Random,
) -> bpy.types.Object:
    offset = rng.uniform(-width * 0.015, width * 0.015)
    rings = [
        (-length * 0.66, width * 0.018, height * 0.035, -height * 0.02, 0.0),
        (-length * 0.56, width * 0.06, height * 0.10, -height * 0.015, 0.0),
        (-length * 0.42, width * 0.16, height * 0.22, 0.0, -offset),
        (-length * 0.22, width * 0.28, height * 0.34, height * 0.02, offset),
        (length * 0.02, width * 0.36, height * 0.38, height * 0.01, 0.0),
        (length * 0.25, width * 0.30, height * 0.31, -height * 0.02, -offset),
        (length * 0.47, width * 0.18, height * 0.20, -height * 0.035, 0.0),
        (length * 0.60, width * 0.08, height * 0.10, -height * 0.03, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.018)


def _raider_upper_armor(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    outline = [
        (-width * 0.045, -length * 0.50),
        (width * 0.11, -length * 0.34),
        (width * 0.18, -length * 0.06),
        (width * 0.15, length * 0.30),
        (width * 0.055, length * 0.50),
        (-width * 0.055, length * 0.50),
        (-width * 0.15, length * 0.30),
        (-width * 0.18, -length * 0.06),
        (-width * 0.11, -length * 0.34),
    ]
    return _plate_prism(collection, name, outline, height * 0.39, height * 0.025, material, bevel=0.012)


def _raider_keel(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    outline = [
        (-width * 0.055, -length * 0.36),
        (width * 0.055, -length * 0.36),
        (width * 0.10, length * 0.36),
        (0.0, length * 0.56),
        (-width * 0.10, length * 0.36),
    ]
    return _plate_prism(collection, name, outline, -height * 0.31, height * 0.03, material, bevel=0.01)


def _raider_cockpit(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.43, width * 0.020, height * 0.018, height * 0.32, 0.0),
        (-length * 0.34, width * 0.055, height * 0.050, height * 0.43, 0.0),
        (-length * 0.22, width * 0.080, height * 0.070, height * 0.48, 0.0),
        (-length * 0.10, width * 0.050, height * 0.046, height * 0.43, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.006, top_bias=1.2, bottom_bias=0.18)


def _raider_wing(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    outline = [
        (side * width * 0.13, -length * 0.28),
        (side * width * 0.35, -length * 0.23),
        (side * width * (0.84 + wing * 0.09), -length * 0.09),
        (side * width * (0.98 + wing * 0.10), length * 0.04),
        (side * width * 0.62, length * 0.20),
        (side * width * 0.20, length * 0.34),
    ]
    return _hard_airfoil_plate(collection, name, outline, -height * 0.08, height * 0.045, material)


def _raider_wing_armor(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    outline = [
        (side * width * 0.28, -length * 0.18),
        (side * width * 0.48, -length * 0.13),
        (side * width * (0.72 + wing * 0.05), -length * 0.04),
        (side * width * 0.50, length * 0.10),
        (side * width * 0.28, length * 0.15),
    ]
    return _hard_airfoil_plate(collection, name, outline, height * 0.01, height * 0.025, material)


def _raider_winglet(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    root_x = side * width * (0.68 + wing * 0.08)
    tip_x = side * width * (1.05 + wing * 0.10)
    vertices = [
        (root_x, -length * 0.08, -height * 0.04),
        (root_x, length * 0.14, -height * 0.02),
        (tip_x, length * 0.04, height * 0.08),
        (root_x, -length * 0.08, height * 0.06),
        (root_x, length * 0.14, height * 0.10),
        (tip_x, length * 0.04, height * 0.18),
    ]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.008)


def _raider_tail_fin(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    direction: int,
    material: bpy.types.Material,
) -> bpy.types.Object:
    z_root = direction * height * 0.28
    z_tip = direction * height * 0.88
    half_width = width * 0.025
    vertices = [
        (-half_width, length * 0.18, z_root),
        (half_width, length * 0.18, z_root),
        (-half_width, length * 0.52, z_root * 0.75),
        (half_width, length * 0.52, z_root * 0.75),
        (0.0, length * 0.47, z_tip),
    ]
    faces = [(0, 2, 4), (1, 4, 3), (0, 1, 3, 2), (0, 4, 1), (2, 3, 4)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.008)


def _faceted_loft_y(
    collection: bpy.types.Collection,
    name: str,
    rings: list[tuple[float, float, float, float, float]],
    material: bpy.types.Material,
    *,
    bevel: float = 0.0,
    top_bias: float = 1.0,
    bottom_bias: float = 0.62,
) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    for y, half_width, half_height, offset_z, offset_x in rings:
        vertices.extend(
            [
                (offset_x, y, offset_z + half_height * top_bias),
                (offset_x + half_width * 0.62, y, offset_z + half_height * 0.42),
                (offset_x + half_width, y, offset_z),
                (offset_x + half_width * 0.50, y, offset_z - half_height * bottom_bias),
                (offset_x, y, offset_z - half_height * (bottom_bias + 0.18)),
                (offset_x - half_width * 0.50, y, offset_z - half_height * bottom_bias),
                (offset_x - half_width, y, offset_z),
                (offset_x - half_width * 0.62, y, offset_z + half_height * 0.42),
            ]
        )

    segments = 8
    faces: list[tuple[int, ...]] = []
    for ring in range(len(rings) - 1):
        base = ring * segments
        next_base = (ring + 1) * segments
        for index in range(segments):
            faces.append((base + index, base + (index + 1) % segments, next_base + (index + 1) % segments, next_base + index))
    faces.append(tuple(reversed(range(segments))))
    last_base = (len(rings) - 1) * segments
    faces.append(tuple(last_base + index for index in range(segments)))
    return _mesh_object(collection, name, vertices, faces, material, bevel=bevel)


def _hard_airfoil_plate(
    collection: bpy.types.Collection,
    name: str,
    outline: list[tuple[float, float]],
    z_center: float,
    half_thickness: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    count = len(outline)
    vertices: list[tuple[float, float, float]] = []
    for index, (x, y) in enumerate(outline):
        crown = 0.45 + 0.35 * sin(pi * index / max(count - 1, 1))
        vertices.append((x, y, z_center - half_thickness * 0.42))
        vertices.append((x, y, z_center + half_thickness * crown))
    faces: list[tuple[int, ...]] = [tuple(index * 2 for index in range(count)), tuple(index * 2 + 1 for index in reversed(range(count)))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index * 2, next_index * 2, next_index * 2 + 1, index * 2 + 1))
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.012)


def _smooth_hull(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
    rng: random.Random,
) -> bpy.types.Object:
    shoulder = rng.uniform(-0.02, 0.02)
    rings = [
        (-length * 0.57, width * 0.018, height * 0.035, -height * 0.01, 0.0),
        (-length * 0.49, width * 0.10, height * 0.15, -height * 0.005, 0.0),
        (-length * 0.36, width * 0.23, height * 0.29, height * 0.01, shoulder * width),
        (-length * 0.16, width * 0.35, height * 0.40, height * 0.035, 0.0),
        (length * 0.08, width * 0.39, height * 0.43, height * 0.02, 0.0),
        (length * 0.31, width * 0.31, height * 0.36, 0.0, -shoulder * width),
        (length * 0.48, width * 0.20, height * 0.25, -height * 0.015, 0.0),
        (length * 0.58, width * 0.08, height * 0.12, -height * 0.02, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=28, top_scale=1.1, bottom_scale=0.78)


def _smooth_spine(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.34, width * 0.035, height * 0.035, height * 0.38, 0.0),
        (-length * 0.18, width * 0.085, height * 0.08, height * 0.48, 0.0),
        (length * 0.12, width * 0.12, height * 0.11, height * 0.48, 0.0),
        (length * 0.38, width * 0.07, height * 0.07, height * 0.40, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=18, top_scale=0.85, bottom_scale=0.45)


def _smooth_canopy(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.34, width * 0.025, height * 0.025, height * 0.52, 0.0),
        (-length * 0.27, width * 0.075, height * 0.055, height * 0.61, 0.0),
        (-length * 0.17, width * 0.105, height * 0.075, height * 0.63, 0.0),
        (-length * 0.07, width * 0.07, height * 0.055, height * 0.57, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=20, top_scale=1.0, bottom_scale=0.28)


def _smooth_engine_pod(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.48, radius_x * 0.45, radius_z * 0.52, 0.0, 0.0),
        (-length * 0.20, radius_x * 0.95, radius_z * 0.88, 0.0, 0.0),
        (length * 0.22, radius_x, radius_z, 0.0, 0.0),
        (length * 0.50, radius_x * 0.74, radius_z * 0.78, 0.0, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=24, location=location)


def _smooth_wing(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    inner_front = side * width * 0.16
    inner_back = side * width * 0.22
    outer = side * width * (0.62 + wing * 0.08)
    mid_outer = side * width * (0.72 + wing * 0.1)
    outline = [
        (inner_front, -length * 0.31),
        (side * width * 0.34, -length * 0.25),
        (outer, -length * 0.12),
        (mid_outer, length * 0.06),
        (side * width * 0.55, length * 0.23),
        (inner_back, length * 0.32),
    ]
    return _airfoil_plate(collection, name, outline, -height * 0.08, height * 0.075, material)


def _smooth_winglet(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    root_x = side * width * (0.54 + wing * 0.08)
    tip_x = side * width * (0.73 + wing * 0.08)
    vertices = [
        (root_x, -length * 0.14, -height * 0.03),
        (root_x, length * 0.14, height * 0.02),
        (tip_x, length * 0.08, height * 0.13),
        (tip_x, -length * 0.08, height * 0.08),
        (root_x, -length * 0.14, height * 0.08),
        (root_x, length * 0.14, height * 0.12),
    ]
    faces = [(0, 1, 2, 3), (0, 4, 5, 1), (4, 3, 2, 5), (0, 3, 4), (1, 5, 2)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.018, smooth=True, subdivision=1)


def _smooth_fin(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    direction: int,
    material: bpy.types.Material,
) -> bpy.types.Object:
    half_width = width * 0.018
    y_front = length * 0.10
    y_back = length * 0.42
    z_root = height * 0.42
    z_tip = height * (0.95 if direction > 0 else -0.72)
    vertices = [
        (-half_width, y_front, z_root),
        (half_width, y_front, z_root),
        (-half_width, y_back, z_root),
        (half_width, y_back, z_root),
        (-half_width * 0.4, y_back * 0.9, z_tip),
        (half_width * 0.4, y_back * 0.9, z_tip),
    ]
    faces = [(0, 2, 4), (1, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 1, 0)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.014, smooth=True, subdivision=1)


def _lofted_ellipse_y(
    collection: bpy.types.Collection,
    name: str,
    rings: list[tuple[float, float, float, float, float]],
    material: bpy.types.Material,
    *,
    radial_segments: int = 24,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    top_scale: float = 1.0,
    bottom_scale: float = 1.0,
) -> bpy.types.Object:
    vertices: list[tuple[float, float, float]] = []
    for y, radius_x, radius_z, offset_z, offset_x in rings:
        for index in range(radial_segments):
            angle = 2.0 * pi * index / radial_segments
            z_scale = top_scale if sin(angle) >= 0.0 else bottom_scale
            vertices.append(
                (
                    offset_x + cos(angle) * radius_x,
                    y,
                    offset_z + sin(angle) * radius_z * z_scale,
                )
            )

    faces: list[tuple[int, ...]] = []
    ring_count = len(rings)
    for ring in range(ring_count - 1):
        base = ring * radial_segments
        next_base = (ring + 1) * radial_segments
        for index in range(radial_segments):
            faces.append(
                (
                    base + index,
                    base + (index + 1) % radial_segments,
                    next_base + (index + 1) % radial_segments,
                    next_base + index,
                )
            )
    faces.append(tuple(reversed(range(radial_segments))))
    last_base = (ring_count - 1) * radial_segments
    faces.append(tuple(last_base + index for index in range(radial_segments)))
    return _mesh_object(collection, name, vertices, faces, material, location=location, smooth=True, subdivision=1)


def _airfoil_plate(
    collection: bpy.types.Collection,
    name: str,
    outline: list[tuple[float, float]],
    z_center: float,
    half_thickness: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    count = len(outline)
    vertices: list[tuple[float, float, float]] = []
    for x, y in outline:
        crown = 0.45 + 0.55 * (1.0 - abs(y) / max(abs(point[1]) for point in outline))
        vertices.append((x, y, z_center - half_thickness * 0.55))
        vertices.append((x, y, z_center + half_thickness * crown))

    faces: list[tuple[int, ...]] = []
    faces.append(tuple(index * 2 for index in range(count)))
    faces.append(tuple(index * 2 + 1 for index in reversed(range(count))))
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index * 2, next_index * 2, next_index * 2 + 1, index * 2 + 1))
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.02, smooth=True, subdivision=1)


def _box(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    scale: tuple[float, float, float],
    material: bpy.types.Material,
    *,
    bevel: float = 0.0,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=2.0, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.scale = scale
    obj.data.materials.append(material)
    _add_surface_modifiers(obj, bevel=bevel)
    _move_to_collection(obj, collection)
    return obj


def _tapered_prism(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    front_half_width: float,
    rear_half_width: float,
    front_half_height: float,
    rear_half_height: float,
    material: bpy.types.Material,
    *,
    bevel: float = 0.0,
) -> bpy.types.Object:
    vertices = [
        (-front_half_width, -half_length, -front_half_height),
        (front_half_width, -half_length, -front_half_height),
        (front_half_width, -half_length, front_half_height),
        (-front_half_width, -half_length, front_half_height),
        (-rear_half_width, half_length, -rear_half_height),
        (rear_half_width, half_length, -rear_half_height),
        (rear_half_width, half_length, rear_half_height),
        (-rear_half_width, half_length, rear_half_height),
    ]
    faces = [
        (0, 1, 2, 3),
        (4, 7, 6, 5),
        (0, 4, 5, 1),
        (1, 5, 6, 2),
        (2, 6, 7, 3),
        (3, 7, 4, 0),
    ]
    return _mesh_object(collection, name, vertices, faces, material, location=location, bevel=bevel)


def _wing_plate(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    inner_x = side * width * 0.15
    outer_front_x = side * width * (0.54 + 0.08 * wing)
    outer_rear_x = side * width * (0.46 + 0.08 * wing)
    points = [
        (inner_x, -length * 0.27),
        (side * width * 0.2, length * 0.26),
        (outer_rear_x, length * 0.16),
        (outer_front_x, -length * 0.18),
    ]
    return _plate_prism(collection, name, points, -height * 0.1, height * 0.06, material, bevel=0.02)


def _winglet(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    wing: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    x = side * width * (0.48 + 0.08 * wing)
    points = [
        (x, -length * 0.18),
        (x, length * 0.1),
        (x + side * width * 0.12, length * 0.02),
        (x + side * width * 0.12, -length * 0.1),
    ]
    return _plate_prism(collection, name, points, height * 0.03, height * 0.09, material, bevel=0.012)


def _plate_prism(
    collection: bpy.types.Collection,
    name: str,
    points_xy: list[tuple[float, float]],
    z_center: float,
    half_thickness: float,
    material: bpy.types.Material,
    *,
    bevel: float = 0.0,
) -> bpy.types.Object:
    bottom = [(x, y, z_center - half_thickness) for x, y in points_xy]
    top = [(x, y, z_center + half_thickness) for x, y in points_xy]
    count = len(points_xy)
    vertices = bottom + top
    faces = [tuple(range(count)), tuple(range(count, count * 2))]
    for index in range(count):
        faces.append((index, (index + 1) % count, ((index + 1) % count) + count, index + count))
    return _mesh_object(collection, name, vertices, faces, material, bevel=bevel)


def _vertical_fin(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    direction: int,
    material: bpy.types.Material,
) -> bpy.types.Object:
    half_width = width * 0.025
    y_front = length * 0.13
    y_back = length * 0.38
    z_root = height * 0.45
    z_tip = height * (0.85 if direction > 0 else -0.7)
    vertices = [
        (-half_width, y_front, z_root),
        (half_width, y_front, z_root),
        (-half_width, y_back, z_root),
        (half_width, y_back, z_root),
        (-half_width, y_back * 0.92, z_tip),
        (half_width, y_back * 0.92, z_tip),
    ]
    faces = [(0, 2, 4), (1, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 1, 0)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.012)


def _engine_nozzle(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _cylinder_y(collection, name, location, radius, depth, material, vertices=32, bevel=0.012)


def _engine_glow(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _cylinder_y(collection, name, location, radius, depth, material, vertices=32, bevel=0.0)


def _weapon_barrel(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _cylinder_y(collection, name, location, radius, depth, material, vertices=16, bevel=0.004)


def _cylinder_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
    *,
    vertices: int,
    bevel: float,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=(pi / 2.0, 0.0, 0.0))
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    _add_surface_modifiers(obj, bevel=bevel, weighted_normals=True)
    _move_to_collection(obj, collection)
    return obj


def _create_panel_details(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects = []

    detail = _detail_multiplier(config.detail_level)
    panel_rows = max(1, min(6, round(4 * detail)))
    y_factors = [(-0.29 + index * (0.58 / max(panel_rows - 1, 1))) for index in range(panel_rows)]
    for index, y_factor in enumerate(y_factors, start=1):
        panel_width = width * rng.uniform(0.035, 0.055)
        panel_length = length * rng.uniform(0.045, 0.075)
        x = width * rng.uniform(0.08, 0.17)
        y = length * y_factor
        left_z = _hull_top_z(length, width, height, -x, y, clearance=height * 0.018)
        right_z = _hull_top_z(length, width, height, x, y, clearance=height * 0.018)
        objects.append(_raised_strip_y(collection, f"MESH_Panel_Top_Left_{index:02d}", (-x, y, left_z), panel_length, panel_width, height * 0.012, materials["panel"]))
        objects.append(_raised_strip_y(collection, f"MESH_Panel_Top_Right_{index:02d}", (x, y, right_z), panel_length, panel_width, height * 0.012, materials["panel"]))

    spine_xs = (-width * 0.2, 0.0, width * 0.2) if detail > 0.7 else (0.0,)
    for index, x in enumerate(spine_xs, start=1):
        y = length * rng.uniform(-0.18, 0.22)
        objects.append(
            _raised_strip_y(
                collection,
                f"MESH_Accent_Spine_{index:02d}",
                (x, y, _hull_top_z(length, width, height, x, y, clearance=height * 0.025)),
                length * 0.13,
                width * 0.025,
                height * 0.014,
                materials["accent"],
            )
        )
    return objects


def _create_greebles(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    detail = _detail_multiplier(config.detail_level)
    count = round((4 if length < 8.0 else 6) * detail * config.greeble_density)
    objects = []
    for index in range(1, count + 1):
        y = rng.uniform(-length * 0.1, length * 0.32)
        sx = rng.uniform(width * 0.025, width * 0.045)
        sy = rng.uniform(length * 0.035, length * 0.075)
        sz = rng.uniform(height * 0.025, height * 0.055)
        x = width * rng.uniform(0.26, 0.34)
        left_z = _hull_side_z(length, width, height, -x, y, clearance=height * rng.uniform(0.02, 0.06))
        right_z = _hull_side_z(length, width, height, x, y, clearance=height * rng.uniform(0.02, 0.06))
        objects.append(_angular_surface_greeble(collection, f"MESH_Greeble_Left_{index:02d}", -x, y, left_z, sx, sy, sz, -1, materials["trim"]))
        objects.append(_angular_surface_greeble(collection, f"MESH_Greeble_Right_{index:02d}", x, y, right_z, sx, sy, sz, 1, materials["trim"]))
    return objects


def _angular_surface_greeble(
    collection: bpy.types.Collection,
    name: str,
    x: float,
    y: float,
    z: float,
    half_width: float,
    half_length: float,
    half_height: float,
    side: int,
    material: bpy.types.Material,
) -> bpy.types.Object:
    skew = side * half_width * 0.55
    outline = [
        (x - side * half_width + skew, y - half_length),
        (x + side * half_width * 0.8 + skew, y - half_length * 0.55),
        (x + side * half_width, y + half_length),
        (x - side * half_width * 0.65, y + half_length * 0.55),
    ]
    return _plate_prism(collection, name, outline, z, max(half_height * 0.35, 0.006), material, bevel=0.004)


def _raised_strip_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-half_length, radius_x * 0.12, radius_z * 0.3, 0.0, 0.0),
        (-half_length * 0.72, radius_x, radius_z, 0.0, 0.0),
        (half_length * 0.72, radius_x, radius_z, 0.0, 0.0),
        (half_length, radius_x * 0.12, radius_z * 0.3, 0.0, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=12, location=location, top_scale=0.8, bottom_scale=0.18)


def _rounded_pod(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-half_length, radius_x * 0.1, radius_z * 0.1, 0.0, 0.0),
        (-half_length * 0.55, radius_x, radius_z, 0.0, 0.0),
        (half_length * 0.55, radius_x, radius_z, 0.0, 0.0),
        (half_length, radius_x * 0.1, radius_z * 0.1, 0.0, 0.0),
    ]
    return _lofted_ellipse_y(collection, name, rings, material, radial_segments=14, location=location)


def _create_role_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    role = config.role
    objects: list[bpy.types.Object] = []

    if role in {"enemy", "player", "ally"} and config.weapon_density > 0.05:
        objects.extend(
            [
                _weapon_barrel(
                    collection,
                    "MESH_Weapon_Left_Pod",
                    (-width * 0.48, -length * 0.08, -height * 0.02),
                    width * 0.03,
                    length * (0.12 + 0.10 * config.weapon_density),
                    materials["trim"],
                ),
                _weapon_barrel(
                    collection,
                    "MESH_Weapon_Right_Pod",
                    (width * 0.48, -length * 0.08, -height * 0.02),
                    width * 0.03,
                    length * (0.12 + 0.10 * config.weapon_density),
                    materials["trim"],
                ),
            ]
        )

    if role == "boss":
        for index, x_factor in enumerate((-0.34, -0.18, 0.18, 0.34), start=1):
            objects.append(
                _engine_nozzle(
                    collection,
                    f"MESH_Boss_Engine_Nozzle_{index:02d}",
                    (width * x_factor, length * 0.48, -height * 0.04),
                    width * 0.075,
                    length * 0.18,
                    materials["trim"],
                )
            )
            objects.append(
                _engine_glow(
                    collection,
                    f"MESH_Boss_Engine_Glow_{index:02d}",
                    (width * x_factor, length * 0.59, -height * 0.04),
                    width * 0.055,
                    length * 0.025,
                    materials["glow"],
                )
            )
        objects.append(
            _rounded_pod(
                collection,
                "MESH_Boss_Armor_Belt",
                (0.0, length * 0.06, height * 0.02),
                length * 0.22,
                width * 0.42,
                height * 0.08,
                materials["trim"],
            )
        )

    if role == "drone":
        objects.append(
            _torus_y(
                collection,
                "MESH_Drone_Core_Ring",
                (0.0, -length * 0.02, 0.0),
                width * 0.23,
                width * 0.018,
                materials["accent"],
            )
        )
        objects.append(
            _engine_glow(
                collection,
                "MESH_Drone_Core_Glow",
                (0.0, -length * 0.02, 0.0),
                width * 0.08,
                length * 0.02,
                materials["glow"],
            )
        )

    if role in {"civilian", "background_traffic"} or config.cargo_density > 0.45:
        tank_count = max(0, min(4, round(2 + config.cargo_density * 2)))
        x_factors = [-0.34, 0.34, -0.22, 0.22][:tank_count]
        for index, x_factor in enumerate(x_factors, start=1):
            objects.append(
                _cylinder_y(
                    collection,
                    f"MESH_Civilian_Tank_{index:02d}",
                    (width * x_factor, length * 0.17, -height * 0.32),
                    width * 0.06,
                    length * 0.45,
                    materials["accent"],
                    vertices=20,
                    bevel=0.006,
                )
            )

    if role == "background_traffic":
        objects.append(
            _rounded_pod(
                collection,
                "MESH_Traffic_Beacon",
                (0.0, -length * 0.34, height * 0.68),
                length * 0.025,
                width * 0.035,
                height * 0.035,
                materials["glow"],
            )
        )

    if role in {"neutral", "civilian"} and rng.random() < 0.65:
        objects.append(
            _antenna(
                collection,
                "MESH_Comms_Antenna",
                (width * 0.16, -length * 0.04, height * 0.68),
                width * 0.01,
                height * 0.42,
                materials["trim"],
            )
        )

    return objects


def _create_faction_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    faction = config.faction
    objects: list[bpy.types.Object] = []

    if faction in {"pirate_clan", "smuggler_network"} and config.asymmetry > 0.05:
        pod_count = max(1, min(3, round(1 + config.asymmetry * 2)))
        for index in range(1, pod_count + 1):
            side = -1 if rng.random() < 0.5 else 1
            y = length * rng.uniform(-0.02, 0.22)
            x = side * width * rng.uniform(0.37, 0.46)
            objects.append(
                _rounded_pod(
                    collection,
                    f"MESH_Asymmetry_Salvage_Pod_{index:02d}",
                    (x, y, _hull_side_z(length, width, height, x, y, clearance=-height * 0.16)),
                    length * rng.uniform(0.11, 0.18),
                    width * rng.uniform(0.045, 0.07),
                    height * rng.uniform(0.075, 0.12),
                    materials["trim"],
                )
            )
        for index, y_factor in enumerate((-0.2, -0.02, 0.16), start=1):
            objects.append(
                _spike(
                    collection,
                    f"MESH_Raider_Spike_Left_{index:02d}",
                    (-width * 0.38, length * y_factor, height * 0.04),
                    -1,
                    width * 0.16,
                    height * 0.05,
                    materials["trim"],
                )
            )
            objects.append(
                _spike(
                    collection,
                    f"MESH_Raider_Spike_Right_{index:02d}",
                    (width * 0.38, length * y_factor, height * 0.04),
                    1,
                    width * 0.16,
                    height * 0.05,
                    materials["trim"],
                )
            )

    if faction in {"sector_navy", "corporate_security"}:
        for index, x_factor in enumerate((-0.23, 0.23), start=1):
            x = width * x_factor
            y = length * 0.04
            objects.append(
                _raised_strip_y(
                    collection,
                    f"MESH_Regulation_Armor_Plate_{index:02d}",
                    (x, y, _hull_top_z(length, width, height, x, y, clearance=height * 0.035)),
                    length * 0.31,
                    width * 0.08,
                    height * 0.025,
                    materials["accent"],
                )
            )

    if faction == "ancient_relic":
        objects.append(
            _torus_y(
                collection,
                "MESH_Relic_Aft_Halo",
                (0.0, length * 0.35, 0.0),
                width * 0.34,
                width * 0.018,
                materials["glow"],
            )
        )
        for index, y_factor in enumerate((-0.22, -0.04, 0.14), start=1):
            y = length * y_factor
            objects.append(
                _raised_strip_y(
                    collection,
                    f"MESH_Relic_Glyph_{index:02d}",
                    (0.0, y, _hull_top_z(length, width, height, 0.0, y, clearance=height * 0.035)),
                    length * 0.035,
                    width * 0.035,
                    height * 0.012,
                    materials["glow"],
                )
            )

    if faction == "mining_guild":
        objects.extend(
            [
                _rounded_pod(
                    collection,
                    "MESH_Mining_Left_Clamp",
                    (-width * 0.44, -length * 0.32, -height * 0.05),
                    length * 0.11,
                    width * 0.045,
                    height * 0.04,
                    materials["trim"],
                ),
                _rounded_pod(
                    collection,
                    "MESH_Mining_Right_Clamp",
                    (width * 0.44, -length * 0.32, -height * 0.05),
                    length * 0.11,
                    width * 0.045,
                    height * 0.04,
                    materials["trim"],
                ),
            ]
        )

    if faction == "trade_consortium":
        objects.append(
            _rounded_pod(
                collection,
                "MESH_Trade_Cargo_Keel",
                (0.0, length * 0.22, -height * 0.45),
                length * 0.3,
                width * 0.18,
                height * 0.09,
                materials["accent"],
            )
        )

    return objects


def _create_archetype_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    if config.ship_type == "missile_corvette":
        return _create_missile_corvette_features(collection, materials, dimensions, rng, config)
    if config.ship_type == "interceptor":
        return _create_interceptor_features(collection, materials, dimensions, rng)
    if config.ship_type == "gunship":
        return _create_gunship_features(collection, materials, dimensions, rng)
    if config.ship_type == "freighter":
        return _create_freighter_features(collection, materials, dimensions, rng)
    return []


def _create_missile_corvette_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []

    objects.append(
        _box(
            collection,
            "MESH_Corvette_Command_Bridge",
            (0.0, -length * 0.08, _hull_top_z(length, width, height, 0.0, -length * 0.08, clearance=height * 0.09)),
            (width * 0.16, length * 0.08, height * 0.065),
            materials["armor"],
            bevel=0.012,
        )
    )
    objects.append(
        _box(
            collection,
            "MESH_Targeting_Suite_Block",
            (0.0, -length * 0.24, _hull_top_z(length, width, height, 0.0, -length * 0.24, clearance=height * 0.08)),
            (width * 0.09, length * 0.055, height * 0.05),
            materials["trim"],
            bevel=0.01,
        )
    )
    objects.append(
        _antenna(
            collection,
            "MESH_Targeting_Sensor_Mast",
            (0.0, -length * 0.27, _hull_top_z(length, width, height, 0.0, -length * 0.27, clearance=height * 0.22)),
            width * 0.008,
            height * 0.38,
            materials["trim"],
        )
    )

    bank_index = 1
    bank_count = max(0, min(4, round(config.missile_density * 4)))
    bank_slots = (-0.12, 0.06, 0.24, 0.40)
    for side in (-1, 1):
        for y_factor in bank_slots[:bank_count]:
            bank_x = side * width * rng.uniform(0.20, 0.31)
            bank_y = length * y_factor
            bank_z = _hull_top_z(length, width, height, bank_x, bank_y, clearance=height * 0.07)
            objects.extend(
                _missile_pod_bank(
                    collection,
                    f"MESH_Missile_Pod_Bank_{bank_index:02d}",
                    (bank_x, bank_y, bank_z),
                    side,
                    width,
                    length,
                    height,
                    materials,
                    missile_density=config.missile_density,
                )
            )
            bank_index += 1

    for side in (-1, 1):
        objects.append(
            _hard_airfoil_plate(
                collection,
                f"MESH_Corvette_Stabilizer_{'L' if side < 0 else 'R'}",
                [
                    (side * width * 0.25, length * 0.20),
                    (side * width * 0.54, length * 0.30),
                    (side * width * 0.68, length * 0.47),
                    (side * width * 0.30, length * 0.40),
                ],
                -height * 0.14,
                height * 0.035,
                materials["armor"],
            )
        )
        objects.append(
            _box(
                collection,
                f"MESH_Siege_Anchor_{'L' if side < 0 else 'R'}",
                (side * width * 0.50, length * 0.42, -height * 0.22),
                (width * 0.035, length * 0.11, height * 0.035),
                materials["trim"],
                bevel=0.006,
            )
        )

    if config.missile_density > 0.35 or config.cargo_density > 0.5:
        for side in (-1, 1):
            objects.append(
                _box(
                    collection,
                    f"MESH_Mine_Dispenser_{'L' if side < 0 else 'R'}",
                    (side * width * 0.34, length * 0.50, _hull_side_z(length, width, height, side * width * 0.34, length * 0.50, clearance=height * 0.02)),
                    (width * 0.075, length * 0.07, height * 0.055),
                    materials["armor"],
                    bevel=0.008,
                )
            )

    for index, x_factor in enumerate((-0.28, -0.12, 0.12, 0.28), start=1):
        objects.append(
            _smooth_engine_pod(
                collection,
                f"MESH_Corvette_Engine_Pod_{index:02d}",
                (width * x_factor, length * 0.55, -height * 0.02),
                length * 0.17,
                width * 0.075,
                height * 0.12,
                materials["armor"],
            )
        )
        objects.append(
            _engine_glow(
                collection,
                f"MESH_Corvette_Engine_Glow_{index:02d}",
                (width * x_factor, length * 0.66, -height * 0.02),
                width * 0.055,
                length * 0.020,
                materials["glow"],
            )
        )

    if config.weapon_density > 0.05:
        rail_count = max(1, min(3, round(1 + config.weapon_density * 2)))
        rail_slots = (-0.38, -0.30, -0.23)
        for side in (-1, 1):
            for index, y_factor in enumerate(rail_slots[:rail_count], start=1):
                objects.append(
                    _weapon_barrel(
                        collection,
                        f"MESH_Corvette_Prow_Rail_{'L' if side < 0 else 'R'}_{index:02d}",
                        (side * width * (0.08 + index * 0.05), length * y_factor, -height * 0.04),
                        width * 0.012,
                        length * (0.14 + 0.14 * config.weapon_density),
                        materials["trim"],
                    )
                )

    if config.asymmetry > 0.05:
        aux_count = max(1, min(4, round(1 + config.asymmetry * 3)))
        for index in range(1, aux_count + 1):
            side = -1 if rng.random() < 0.5 else 1
            y = length * rng.uniform(-0.04, 0.34)
            x = side * width * rng.uniform(0.32, 0.43)
            objects.append(
                _box(
                    collection,
                    f"MESH_Corvette_Aux_Module_{index:02d}",
                    (x, y, _hull_side_z(length, width, height, x, y, clearance=height * rng.uniform(0.02, 0.06))),
                    (width * rng.uniform(0.030, 0.055), length * rng.uniform(0.045, 0.085), height * rng.uniform(0.030, 0.055)),
                    materials["trim"],
                    bevel=0.006,
                )
            )

    return objects


def _missile_pod_bank(
    collection: bpy.types.Collection,
    base_name: str,
    location: tuple[float, float, float],
    side: int,
    width: float,
    length: float,
    height: float,
    materials: dict[str, bpy.types.Material],
    *,
    missile_density: float,
) -> list[bpy.types.Object]:
    x, y, z = location
    objects: list[bpy.types.Object] = []
    objects.append(
        _box(
            collection,
            base_name,
            (x, y, z),
            (width * 0.10, length * 0.085, height * 0.035),
            materials["armor"],
            bevel=0.007,
        )
    )
    row_count = max(1, min(4, round(1 + missile_density * 3)))
    column_count = 3 if missile_density > 0.82 else 2
    x_step = width * 0.044
    y_step = length * 0.030
    x_origin = -x_step * (column_count - 1) * 0.5
    y_origin = -y_step * (row_count - 1) * 0.5
    for row in range(row_count):
        for column in range(column_count):
            cell_x = x + side * (x_origin + column * x_step)
            cell_y = y + y_origin + row * y_step
            objects.append(
                _box(
                    collection,
                    f"{base_name}_Cell_{row + 1:02d}_{column + 1:02d}",
                    (cell_x, cell_y, z + height * 0.043),
                    (width * 0.017, length * 0.012, height * 0.010),
                    materials["ordnance"],
                    bevel=0.002,
                )
            )
    return objects


def _create_interceptor_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        objects.append(_weapon_barrel(collection, f"MESH_Interceptor_Lance_{'L' if side < 0 else 'R'}", (side * width * 0.26, -length * 0.58, -height * 0.02), width * 0.010, length * 0.38, materials["trim"]))
        objects.append(_raised_strip_y(collection, f"MESH_Interceptor_Engine_Slit_{'L' if side < 0 else 'R'}", (side * width * 0.31, length * 0.32, _hull_side_z(length, width, height, side * width * 0.31, length * 0.32, clearance=height * 0.05)), length * 0.13, width * 0.012, height * 0.010, materials["glow"]))
    return objects


def _create_gunship_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        for index, y_factor in enumerate((-0.18, 0.04, 0.25), start=1):
            objects.append(_weapon_barrel(collection, f"MESH_Gunship_Side_Cannon_{'L' if side < 0 else 'R'}_{index:02d}", (side * width * 0.46, length * y_factor, _hull_side_z(length, width, height, side * width * 0.46, length * y_factor, clearance=height * 0.02)), width * 0.018, length * 0.18, materials["trim"]))
    return objects


def _create_freighter_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        for index, y_factor in enumerate((-0.16, 0.10, 0.34), start=1):
            objects.append(_rounded_pod(collection, f"MESH_Freighter_Cargo_Pod_{'L' if side < 0 else 'R'}_{index:02d}", (side * width * 0.38, length * y_factor, -height * 0.28), length * 0.12, width * 0.065, height * 0.10, materials["armor"]))
    return objects


def _create_designer_detail_layer(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []

    objects.extend(_create_raider_armor_tiles(collection, materials, length, width, height, rng, config))
    objects.extend(_create_panel_seams(collection, materials, length, width, height))
    objects.extend(_create_light_slits(collection, materials, length, width, height, rng, config))
    objects.extend(_create_teal_light_strips(collection, materials, length, width, height))
    objects.extend(_create_engine_cable_runs(collection, materials, length, width, height))
    objects.extend(_create_nose_chevrons(collection, materials, length, width, height, config))
    objects.extend(_create_wing_decal_sets(collection, materials, length, width, height, rng, config))
    objects.extend(_create_micro_vents(collection, materials, length, width, height, rng, config))
    objects.extend(_create_paint_scuffs(collection, materials, length, width, height, rng, config))
    objects.extend(_create_faction_insignia(collection, materials, length, width, height, config.faction))
    return objects


def _create_raider_armor_tiles(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    detail = _detail_multiplier(config.detail_level)
    tile_count = max(0, min(10, round(7 * detail * config.armor_density)))
    y_factors = [(-0.39 + index * (0.79 / max(tile_count - 1, 1))) for index in range(tile_count)]
    for index, y_factor in enumerate(y_factors, start=1):
        half_w = width * rng.uniform(0.10, 0.19)
        half_l = length * rng.uniform(0.030, 0.052)
        skew = width * rng.uniform(-0.035, 0.035)
        y = length * y_factor
        outline = [
            (-half_w + skew, y - half_l),
            (half_w * 0.82 + skew, y - half_l * 0.76),
            (half_w - skew, y + half_l),
            (-half_w * 0.74 - skew, y + half_l * 0.82),
        ]
        tile_z = _hull_top_z(length, width, height, 0.0, y, clearance=height * 0.026 + rng.uniform(-height * 0.004, height * 0.006))
        objects.append(_plate_prism(collection, f"MESH_Armor_Top_Tile_{index:02d}", outline, tile_z, height * 0.010, materials["armor"], bevel=0.006))

    for side in (-1, 1):
        side_count = max(0, min(6, round(4 * detail * config.armor_density)))
        side_factors = [(-0.30 + index * (0.58 / max(side_count - 1, 1))) for index in range(side_count)]
        for index, y_factor in enumerate(side_factors, start=1):
            x = side * width * rng.uniform(0.28, 0.37)
            y = length * y_factor
            objects.append(
                _raised_strip_y(
                    collection,
                    f"MESH_Side_Armor_{'L' if side < 0 else 'R'}_{index:02d}",
                    (x, y, _hull_side_z(length, width, height, x, y, clearance=height * rng.uniform(0.035, 0.075))),
                    length * rng.uniform(0.035, 0.065),
                    width * rng.uniform(0.030, 0.045),
                    height * 0.018,
                    materials["armor"],
                )
            )
    return objects


def _create_panel_seams(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    objects.append(
        _curve_path(
            collection,
            "MESH_Seam_Centerline",
            [
                (0.0, -length * 0.47, _hull_top_z(length, width, height, 0.0, -length * 0.47, clearance=height * 0.014)),
                (0.0, -length * 0.22, _hull_top_z(length, width, height, 0.0, -length * 0.22, clearance=height * 0.014)),
                (0.0, length * 0.18, _hull_top_z(length, width, height, 0.0, length * 0.18, clearance=height * 0.014)),
                (0.0, length * 0.45, _hull_top_z(length, width, height, 0.0, length * 0.45, clearance=height * 0.014)),
            ],
            materials["panel"],
            bevel_depth=width * 0.0035,
        )
    )
    for index, side in enumerate((-1, 1), start=1):
        objects.append(
            _curve_path(
                collection,
                f"MESH_Seam_Shoulder_{index:02d}",
                [
                    (side * width * 0.08, -length * 0.43, _hull_top_z(length, width, height, side * width * 0.08, -length * 0.43, clearance=height * 0.012)),
                    (side * width * 0.25, -length * 0.2, _hull_top_z(length, width, height, side * width * 0.25, -length * 0.2, clearance=height * 0.012)),
                    (side * width * 0.32, length * 0.1, _hull_top_z(length, width, height, side * width * 0.32, length * 0.1, clearance=height * 0.012)),
                    (side * width * 0.19, length * 0.4, _hull_top_z(length, width, height, side * width * 0.19, length * 0.4, clearance=height * 0.012)),
                ],
                materials["panel"],
                bevel_depth=width * 0.003,
            )
        )
        objects.append(
            _curve_path(
                collection,
                f"MESH_Seam_Lower_Rail_{index:02d}",
                [
                    (side * width * 0.18, -length * 0.24, _hull_side_z(length, width, height, side * width * 0.18, -length * 0.24, clearance=-height * 0.11)),
                    (side * width * 0.35, length * 0.02, _hull_side_z(length, width, height, side * width * 0.35, length * 0.02, clearance=-height * 0.11)),
                    (side * width * 0.28, length * 0.35, _hull_side_z(length, width, height, side * width * 0.28, length * 0.35, clearance=-height * 0.08)),
                ],
                materials["panel"],
                bevel_depth=width * 0.0028,
            )
        )

    for index, y_factor in enumerate((-0.34, -0.18, 0.02, 0.22, 0.38), start=1):
        objects.append(
            _curve_path(
                collection,
                f"MESH_Seam_Cross_{index:02d}",
                [
                    (-width * 0.17, length * y_factor, _hull_top_z(length, width, height, -width * 0.17, length * y_factor, clearance=height * 0.012)),
                    (-width * 0.05, length * (y_factor + 0.018), _hull_top_z(length, width, height, -width * 0.05, length * (y_factor + 0.018), clearance=height * 0.012)),
                    (width * 0.05, length * (y_factor + 0.018), _hull_top_z(length, width, height, width * 0.05, length * (y_factor + 0.018), clearance=height * 0.012)),
                    (width * 0.17, length * y_factor, _hull_top_z(length, width, height, width * 0.17, length * y_factor, clearance=height * 0.012)),
                ],
                materials["panel"],
                bevel_depth=width * 0.0025,
            )
        )
    return objects


def _create_light_slits(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    detail = _detail_multiplier(config.detail_level)
    row_count = max(0, min(6, round((5 if config.role in {"boss", "civilian"} else 3) * detail * config.glow_strength)))
    for row in range(row_count):
        y = -length * 0.24 + row * length * 0.105
        for side in (-1, 1):
            if rng.random() < 0.18 and config.role not in {"civilian", "boss"}:
                continue
            x0 = side * width * rng.uniform(0.13, 0.22)
            x1 = side * width * rng.uniform(0.21, 0.31)
            y0 = y + rng.uniform(-length * 0.006, length * 0.006)
            y1 = y + length * rng.uniform(0.018, 0.032)
            objects.append(
                _curve_path(
                    collection,
                    f"MESH_Light_Slit_{'L' if side < 0 else 'R'}_{row + 1:02d}",
                    [
                        (x0, y0, _hull_top_z(length, width, height, x0, y0, clearance=height * 0.018)),
                        (x1, y1, _hull_top_z(length, width, height, x1, y1, clearance=height * 0.018)),
                    ],
                    materials["window"],
                    bevel_depth=width * 0.004,
                )
            )
    return objects


def _create_window_lights(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    role: str,
) -> list[bpy.types.Object]:
    return []


def _create_teal_light_strips(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        objects.append(
            _curve_path(
                collection,
                f"MESH_Teal_Side_Light_{'L' if side < 0 else 'R'}",
                [
                    (side * width * 0.32, -length * 0.18, _hull_side_z(length, width, height, side * width * 0.32, -length * 0.18, clearance=height * 0.015)),
                    (side * width * 0.39, length * 0.06, _hull_side_z(length, width, height, side * width * 0.39, length * 0.06, clearance=height * 0.015)),
                    (side * width * 0.31, length * 0.31, _hull_side_z(length, width, height, side * width * 0.31, length * 0.31, clearance=height * 0.015)),
                ],
                materials["glow"],
                bevel_depth=width * 0.006,
            )
        )
        objects.append(
            _raised_strip_y(
                collection,
                f"MESH_Teal_Wing_Light_{'L' if side < 0 else 'R'}",
                (side * width * 0.58, length * 0.04, height * 0.045),
                length * 0.07,
                width * 0.012,
                height * 0.012,
                materials["glow"],
            )
        )
    return objects


def _create_engine_cable_runs(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for index, side in enumerate((-1, 1), start=1):
        x = side * width * 0.28
        objects.append(
            _curve_path(
                collection,
                f"MESH_Engine_Cable_Upper_{index:02d}",
                [
                    (side * width * 0.18, length * 0.12, height * 0.25),
                    (x, length * 0.26, height * 0.18),
                    (x, length * 0.48, height * 0.05),
                ],
                materials["panel"],
                bevel_depth=width * 0.006,
            )
        )
        objects.append(
            _curve_path(
                collection,
                f"MESH_Engine_Cable_Lower_{index:02d}",
                [
                    (side * width * 0.13, length * 0.16, -height * 0.16),
                    (x, length * 0.31, -height * 0.13),
                    (x, length * 0.48, -height * 0.05),
                ],
                materials["trim"],
                bevel_depth=width * 0.0045,
            )
        )
    return objects


def _create_nose_chevrons(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    count = max(0, min(4, round(3 * _detail_multiplier(config.detail_level) * config.decal_density)))
    y_factors = [(-0.48 + index * (0.12 / max(count - 1, 1))) for index in range(count)]
    for index, y_factor in enumerate(y_factors, start=1):
        spread = width * (0.04 + index * 0.028)
        y = length * y_factor
        left_y = y + length * 0.028
        right_y = y + length * 0.028
        objects.append(
            _curve_path(
                collection,
                f"MESH_Nose_Chevron_{index:02d}",
                [
                    (-spread, left_y, _hull_top_z(length, width, height, -spread, left_y, clearance=height * 0.016)),
                    (0.0, y, _hull_top_z(length, width, height, 0.0, y, clearance=height * 0.016)),
                    (spread, right_y, _hull_top_z(length, width, height, spread, right_y, clearance=height * 0.016)),
                ],
                materials["red_decal"],
                bevel_depth=width * 0.006,
            )
        )
    return objects


def _create_wing_decal_sets(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        count = max(0, min(5, round(3 * _detail_multiplier(config.detail_level) * config.decal_density)))
        y_factors = [(-0.14 + index * (0.30 / max(count - 1, 1))) for index in range(count)]
        for index, y_factor in enumerate(y_factors, start=1):
            x0 = side * width * rng.uniform(0.32, 0.5)
            x1 = side * width * rng.uniform(0.48, 0.66)
            objects.append(
                _curve_path(
                    collection,
                    f"MESH_Wing_Decal_{'L' if side < 0 else 'R'}_{index:02d}",
                    [(x0, length * y_factor, height * 0.02), (x1, length * (y_factor + 0.035), height * 0.035)],
                    materials["red_decal"],
                    bevel_depth=width * 0.0045,
                )
            )
    return objects


def _create_micro_vents(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        bank_count = max(0, min(5, round(3 * _detail_multiplier(config.detail_level) * config.greeble_density)))
        blade_count = max(2, min(7, round(5 * _detail_multiplier(config.detail_level))))
        for bank in range(bank_count):
            base_y = length * (-0.06 + bank * 0.14)
            base_x = side * width * rng.uniform(0.26, 0.34)
            for blade in range(blade_count):
                y0 = base_y + blade * length * 0.012
                y1 = y0 + length * 0.008
                x1 = base_x + side * width * 0.06
                objects.append(
                    _curve_path(
                        collection,
                        f"MESH_Vent_{'L' if side < 0 else 'R'}_{bank + 1:02d}_{blade + 1:02d}",
                        [
                            (base_x, y0, _hull_top_z(length, width, height, base_x, y0, clearance=height * 0.012)),
                            (x1, y1, _hull_top_z(length, width, height, x1, y1, clearance=height * 0.012)),
                        ],
                        materials["panel"],
                        bevel_depth=width * 0.0035,
                    )
                )
    return objects


def _create_paint_scuffs(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    count = max(0, min(48, round(28 * _detail_multiplier(config.detail_level) * config.wear_amount)))
    for index in range(count):
        side = -1 if rng.random() < 0.5 else 1
        x = side * width * rng.uniform(0.04, 0.38)
        y = length * rng.uniform(-0.42, 0.46)
        dx = side * width * rng.uniform(0.015, 0.055)
        dy = length * rng.uniform(0.010, 0.035)
        z0 = _hull_top_z(length, width, height, x, y, clearance=height * 0.018)
        z1 = _hull_top_z(length, width, height, x + dx, y + dy, clearance=height * 0.018)
        objects.append(
            _curve_path(
                collection,
                f"MESH_Paint_Scuff_{index + 1:02d}",
                [(x, y, z0), (x + dx, y + dy, z1 + height * rng.uniform(-0.004, 0.004))],
                materials["wear"],
                bevel_depth=width * rng.uniform(0.0018, 0.0035),
            )
        )
    return objects


def _create_faction_insignia(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    length: float,
    width: float,
    height: float,
    faction: str,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    base_y = -length * 0.05
    z = _hull_top_z(length, width, height, 0.0, base_y, clearance=height * 0.024)
    scale = width * 0.055
    if faction == "ancient_relic":
        objects.append(_torus_y(collection, "MESH_Insignia_Relic_Ring", (0.0, base_y, z), scale, scale * 0.07, materials["glow"]))
        objects.append(_curve_path(collection, "MESH_Insignia_Relic_Line", [(0.0, base_y - scale, z), (0.0, base_y + scale, z)], materials["glow"], bevel_depth=width * 0.004))
    elif faction in {"pirate_clan", "smuggler_network"}:
        objects.append(_curve_path(collection, "MESH_Insignia_Raider_A", [(-scale, base_y + scale, z), (0.0, base_y - scale, z), (scale, base_y + scale, z)], materials["red_decal"], bevel_depth=width * 0.006))
        objects.append(_curve_path(collection, "MESH_Insignia_Raider_B", [(-scale * 0.55, base_y, z), (scale * 0.55, base_y, z)], materials["red_decal"], bevel_depth=width * 0.005))
    else:
        objects.append(_curve_path(collection, "MESH_Insignia_Primary_A", [(-scale, base_y, z), (0.0, base_y - scale * 0.9, z), (scale, base_y, z)], materials["decal"], bevel_depth=width * 0.005))
        objects.append(_curve_path(collection, "MESH_Insignia_Primary_B", [(-scale * 0.75, base_y + scale * 0.45, z), (scale * 0.75, base_y + scale * 0.45, z)], materials["decal"], bevel_depth=width * 0.005))
    return objects


def _torus_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(
        major_segments=48,
        minor_segments=8,
        location=location,
        major_radius=major_radius,
        minor_radius=minor_radius,
        rotation=(pi / 2.0, 0.0, 0.0),
    )
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.data.materials.append(material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    _add_surface_modifiers(obj, bevel=0.0, weighted_normals=True)
    _move_to_collection(obj, collection)
    return obj


def _antenna(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=radius, depth=height, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.rotation_euler[0] = pi * 0.08
    obj.data.materials.append(material)
    _add_surface_modifiers(obj, bevel=0.002)
    _move_to_collection(obj, collection)
    return obj


def _spike(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    side: int,
    length: float,
    half_width: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    vertices = [
        (0.0, -half_width, -half_width),
        (0.0, half_width, -half_width),
        (0.0, half_width, half_width),
        (0.0, -half_width, half_width),
        (side * length, 0.0, 0.0),
    ]
    faces = [(0, 1, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)]
    return _mesh_object(collection, name, vertices, faces, material, location=location, bevel=0.004)


def _mesh_object(
    collection: bpy.types.Collection,
    name: str,
    vertices: list[tuple[float, float, float]],
    faces: list[tuple[int, ...]],
    material: bpy.types.Material,
    *,
    location: tuple[float, float, float] = (0.0, 0.0, 0.0),
    bevel: float = 0.0,
    smooth: bool = False,
    subdivision: int = 0,
) -> bpy.types.Object:
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.data.materials.append(material)
    collection.objects.link(obj)
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    _add_surface_modifiers(obj, bevel=bevel, subdivision=subdivision)
    return obj


def _curve_path(
    collection: bpy.types.Collection,
    name: str,
    points: list[tuple[float, float, float]],
    material: bpy.types.Material,
    *,
    bevel_depth: float,
    resolution: int = 3,
) -> bpy.types.Object:
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = resolution
    curve.bevel_depth = bevel_depth
    curve.bevel_resolution = 2
    curve.materials.append(material)
    spline = curve.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for point, coordinates in zip(spline.points, points):
        point.co = (coordinates[0], coordinates[1], coordinates[2], 1.0)
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    return obj


def _add_surface_modifiers(
    obj: bpy.types.Object,
    *,
    bevel: float = 0.0,
    weighted_normals: bool = True,
    subdivision: int = 0,
) -> None:
    if subdivision > 0:
        modifier = obj.modifiers.new("VS_Subdivision", "SUBSURF")
        modifier.levels = subdivision
        modifier.render_levels = subdivision
    if bevel > 0.0:
        modifier = obj.modifiers.new("VS_Bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 1
        modifier.affect = "EDGES"
    if weighted_normals:
        obj.modifiers.new("VS_WeightedNormals", "WEIGHTED_NORMAL")


def _hide_technical_helpers(objects: list[Any]) -> None:
    for obj in objects:
        if not obj.name.startswith("MESH_"):
            obj.hide_viewport = True
            obj.hide_render = True


def _show_technical_helpers(objects: list[Any]) -> None:
    for obj in objects:
        if not obj.name.startswith("MESH_"):
            obj.hide_viewport = False
            obj.hide_render = obj.name.startswith("COLLISION_")


def _setup_presentation_scene(collection: bpy.types.Collection, dimensions: dict[str, float]) -> None:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]

    bpy.context.scene.world.color = (0.006, 0.008, 0.012)
    _presentation_light(collection, "VoidShipwright_Key_Light", "AREA", (width * 1.1, -length * 0.7, height * 4.2), 550.0, size=5.0)
    _presentation_light(collection, "VoidShipwright_Rim_Light", "AREA", (-width * 1.4, length * 0.8, height * 2.4), 180.0, size=4.0)
    _presentation_light(collection, "VoidShipwright_Engine_Kicker", "POINT", (0.0, length * 0.75, height * 0.6), 120.0, size=0.0)

    camera_data = bpy.data.cameras.new("VoidShipwright_Preview_Camera_Data")
    camera = bpy.data.objects.new("VoidShipwright_Preview_Camera", camera_data)
    camera.location = (width * 1.25, -length * 1.35, height * 1.25)
    direction = Vector((0.0, 0.0, height * 0.12)) - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 55
    camera_data.dof.use_dof = True
    camera_data.dof.focus_distance = direction.length
    camera_data.dof.aperture_fstop = 5.6
    collection.objects.link(camera)
    bpy.context.scene.camera = camera


def _presentation_light(
    collection: bpy.types.Collection,
    name: str,
    light_type: str,
    location: tuple[float, float, float],
    energy: float,
    *,
    size: float,
) -> bpy.types.Object:
    data = bpy.data.lights.new(name + "_Data", light_type)
    data.energy = energy
    if light_type == "AREA":
        data.size = size
    elif light_type == "POINT":
        data.shadow_soft_size = max(size, 2.0)
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    collection.objects.link(obj)
    return obj


def _move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for linked_collection in list(obj.users_collection):
        linked_collection.objects.unlink(obj)
    collection.objects.link(obj)


def _create_collision_proxies(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    proxy_specs = {
        "COLLISION_Hull-colonly": ((0.0, 0.0, 0.0), (width * 0.3, length * 0.48, height * 0.5)),
        "COLLISION_Engine-colonly": ((0.0, length * 0.41, 0.0), (width * 0.34, length * 0.12, height * 0.24)),
        "COLLISION_Cargo-colonly": ((0.0, length * 0.12, -height * 0.08), (width * 0.22, length * 0.32, height * 0.28)),
        "COLLISION_Bridge-colonly": ((0.0, -length * 0.15, height * 0.38), (width * 0.14, length * 0.12, height * 0.18)),
    }
    material = _material("VS_CollisionProxy", (0.15, 0.85, 0.45, 0.25), alpha=0.25)
    objects = []
    for name in REQUIRED_COLLISION_PROXIES:
        location, scale = proxy_specs[name]
        obj = _box(collection, name, location, scale, material)
        obj.display_type = "WIRE"
        obj.hide_viewport = True
        obj.hide_render = True
        obj["void_shipwright_kind"] = "collision_proxy"
        obj["godot_collision_shape"] = "BoxShape3D"
        objects.append(obj)
    return objects


def _create_damage_markers(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    height = dimensions["height"]
    locations = {
        "DAMAGE_Hull": (0.0, 0.0, 0.0),
        "DAMAGE_Engine": (0.0, length * 0.42, 0.0),
        "DAMAGE_Weapons": (0.0, -length * 0.36, 0.0),
        "DAMAGE_Cargo": (0.0, length * 0.14, -height * 0.12),
        "DAMAGE_Bridge": (0.0, -length * 0.15, height * 0.46),
        "DAMAGE_Shield_Generator": (0.0, 0.04 * length, height * 0.22),
    }
    objects = []
    for name in REQUIRED_DAMAGE_MARKERS:
        obj = _create_empty(collection, name, locations[name], display_type="SPHERE")
        obj["void_shipwright_kind"] = "damage_zone_marker"
        objects.append(obj)
    return objects


def _create_sockets(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    locations = {
        "SOCKET_Weapon_Front_01": (-width * 0.08, -length * 0.5, 0.0),
        "SOCKET_Weapon_Front_02": (width * 0.08, -length * 0.5, 0.0),
        "SOCKET_Weapon_Left_01": (-width * 0.48, -length * 0.05, 0.0),
        "SOCKET_Weapon_Right_01": (width * 0.48, -length * 0.05, 0.0),
        "SOCKET_Missile_Left_01": (-width * 0.34, -length * 0.24, -height * 0.08),
        "SOCKET_Missile_Right_01": (width * 0.34, -length * 0.24, -height * 0.08),
        "SOCKET_Engine_Main_01": (0.0, length * 0.54, 0.0),
        "SOCKET_Engine_Left_01": (-width * 0.24, length * 0.5, -height * 0.04),
        "SOCKET_Engine_Right_01": (width * 0.24, length * 0.5, -height * 0.04),
        "SOCKET_Camera_Follow": (0.0, length * 1.2, height * 0.72),
        "SOCKET_Camera_Look_At": (0.0, -length * 0.08, height * 0.18),
        "SOCKET_Target_Lock_Center": (0.0, -length * 0.06, 0.0),
        "SOCKET_Loot_Drop": (0.0, length * 0.18, -height * 0.62),
        "SOCKET_Boarding_Attach": (width * 0.4, length * 0.02, 0.0),
    }
    objects = []
    for name in REQUIRED_SOCKETS:
        obj = _create_empty(collection, name, locations[name], display_type="ARROWS")
        obj["void_shipwright_kind"] = "socket"
        objects.append(obj)
    return objects


def _create_vfx_markers(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    locations = {
        "VFX_Engine_Main": (0.0, length * 0.58, 0.0),
        "VFX_Engine_Left": (-width * 0.24, length * 0.55, -height * 0.04),
        "VFX_Engine_Right": (width * 0.24, length * 0.55, -height * 0.04),
        "VFX_Shield_Impact": (0.0, 0.0, height * 0.78),
        "VFX_Explosion_Core": (0.0, 0.0, 0.0),
    }
    objects = []
    for name in REQUIRED_VFX_MARKERS:
        obj = _create_empty(collection, name, locations[name], display_type="PLAIN_AXES")
        obj["void_shipwright_kind"] = "vfx_marker"
        objects.append(obj)
    return objects


def _create_camera_markers(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    height = dimensions["height"]
    locations = {
        "CAMERA_Follow": (0.0, length * 1.2, height * 0.72),
        "CAMERA_Look_At": (0.0, -length * 0.08, height * 0.18),
    }
    objects = []
    for name in REQUIRED_CAMERA_MARKERS:
        obj = _create_empty(collection, name, locations[name], display_type="SINGLE_ARROW")
        obj["void_shipwright_kind"] = "camera_marker"
        objects.append(obj)
    return objects


def _create_target_markers(collection: bpy.types.Collection, dimensions: dict[str, float]) -> list[bpy.types.Object]:
    length = dimensions["length"]
    height = dimensions["height"]
    obj = _create_empty(collection, "TARGET_Lock_Center", (0.0, -length * 0.06, height * 0.05), display_type="SPHERE")
    obj["void_shipwright_kind"] = "target_marker"
    return [obj]


def _create_empty(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    *,
    display_type: str = "PLAIN_AXES",
) -> bpy.types.Object:
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display_type
    obj.empty_display_size = max(0.2, Vector(location).length * 0.03)
    obj.location = location
    collection.objects.link(obj)
    return obj

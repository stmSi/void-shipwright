"""Procedural Blender geometry generation for Void Shipwright."""

from __future__ import annotations

import random
from math import cos, pi, sin
from dataclasses import dataclass
from typing import Any, Callable

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
from .textures import painted_metal_material
from .validation import validate_detail_level, validate_faction, validate_hull_profile, validate_material_style, validate_role, validate_seed, validate_ship_type, validate_texture_resolution, validate_texture_workflow


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
    structure_density: float = 0.85
    decal_density: float = 1.0
    wear_amount: float = 0.65
    glow_strength: float = 1.2
    texture_workflow: str = "painted"
    texture_resolution: int = 256
    material_style: str = "gunmetal"
    rust_amount: float = 0.08
    scratch_amount: float = 0.42
    texture_scale: float = 1.0
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


@dataclass(frozen=True)
class ShipVariation:
    key: str
    index: int


VARIATION_PRESETS = (
    "blade",
    "fork",
    "hammerhead",
    "outrigger",
    "twinboom",
    "keel",
    "broadwing",
    "carrier",
    "compact",
    "asymmetric",
)

SUPPRESSED_VISUAL_NAME_FRAGMENTS = (
    "Armor",
    "Armored",
    "Lance",
    "Light_Slit",
    "Needle",
    "Paint_Scuff",
    "Razor",
    "Spear",
    "Winglet",
    "Nose_Chevron",
    "Mining_Manipulator",
)


def generate_ship(config: ShipGenerationConfig) -> dict[str, Any]:
    validate_role(config.role)
    validate_faction(config.faction)
    validate_ship_type(config.ship_type)
    validate_hull_profile(config.hull_profile)
    validate_detail_level(config.detail_level)
    validate_material_style(config.material_style)
    validate_texture_workflow(config.texture_workflow)
    validate_texture_resolution(config.texture_resolution)
    validate_seed(config.seed)

    rng = random.Random(config.seed)
    collection = _prepare_collection(config.collection_name, clear_existing=config.clear_existing)
    materials = _create_materials(config.faction, glow_strength=config.glow_strength, config=config)
    variation = _ship_variation(config)
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
    dimensions = _apply_ship_variation_dimensions(dimensions, variation)

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
    root["void_shipwright_visual_variant"] = variation.key
    root["void_shipwright_structure_density"] = config.structure_density
    root["void_shipwright_texture_workflow"] = config.texture_workflow
    root["void_shipwright_texture_resolution"] = config.texture_resolution
    if config.presentation_scene:
        _setup_presentation_scene(collection, dimensions)
    return metadata


def _safe_id(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("_", "-") else "_" for char in value)


def _stable_int_seed(seed: int, *parts: str) -> int:
    value = seed & 0xFFFFFFFF
    for part in parts:
        for char in part:
            value = ((value ^ ord(char)) * 16777619) & 0xFFFFFFFF
        value = ((value ^ 0x9E3779B9) * 2246822519) & 0xFFFFFFFF
    return value


def _ship_variation(config: ShipGenerationConfig) -> ShipVariation:
    raw_variant = _safe_id((config.variant or "default").strip().lower()) or "default"
    if raw_variant in VARIATION_PRESETS:
        return ShipVariation(raw_variant, VARIATION_PRESETS.index(raw_variant))

    seed = _stable_int_seed(config.seed, config.ship_type, config.role, config.faction, raw_variant)
    index = seed % len(VARIATION_PRESETS)
    return ShipVariation(VARIATION_PRESETS[index], index)


def _apply_ship_variation_dimensions(dimensions: dict[str, float], variation: ShipVariation) -> dict[str, float]:
    length_scale, width_scale, height_scale, wing_scale, engine_scale = {
        "blade": (1.18, 0.88, 0.92, 0.95, 1.08),
        "fork": (1.08, 1.06, 0.94, 1.05, 1.00),
        "hammerhead": (0.96, 1.22, 1.04, 0.75, 1.08),
        "outrigger": (1.02, 1.18, 0.98, 1.22, 1.12),
        "twinboom": (1.04, 1.08, 0.96, 1.10, 1.22),
        "keel": (1.08, 0.96, 1.22, 0.70, 0.92),
        "broadwing": (0.98, 1.02, 0.90, 1.48, 1.00),
        "carrier": (1.14, 1.16, 1.16, 0.58, 0.92),
        "compact": (0.86, 1.06, 1.03, 0.88, 1.28),
        "asymmetric": (1.02, 1.12, 0.98, 1.05, 1.04),
    }[variation.key]
    return {
        **dimensions,
        "length": dimensions["length"] * length_scale,
        "width": dimensions["width"] * width_scale,
        "height": dimensions["height"] * height_scale,
        "wing": dimensions["wing"] * wing_scale,
        "engine": dimensions["engine"] * engine_scale,
    }


def _side_name(side: int) -> str:
    return "Left" if side < 0 else "Right"


def _is_suppressed_visual_object(name: str) -> bool:
    return name.startswith("MESH_") and any(fragment in name for fragment in SUPPRESSED_VISUAL_NAME_FRAGMENTS)


def _remove_suppressed_visual_objects(objects: list[bpy.types.Object]) -> list[bpy.types.Object]:
    kept: list[bpy.types.Object] = []
    for obj in objects:
        if _is_suppressed_visual_object(obj.name):
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            kept.append(obj)
    return kept


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


MATERIAL_STYLE_PROFILES = {
    "gunmetal": {
        "base": (0.035, 0.038, 0.040, 1.0),
        "armor": (0.070, 0.074, 0.075, 1.0),
        "trim": (0.010, 0.012, 0.014, 1.0),
        "edge": (0.58, 0.57, 0.53, 1.0),
        "rust": (0.56, 0.18, 0.055, 1.0),
        "oxide": (0.12, 0.10, 0.075, 1.0),
        "metallic": 0.78,
        "roughness": 0.48,
        "rust_affinity": 0.70,
    },
    "worn_steel": {
        "base": (0.36, 0.36, 0.34, 1.0),
        "armor": (0.48, 0.48, 0.45, 1.0),
        "trim": (0.18, 0.18, 0.17, 1.0),
        "edge": (0.90, 0.88, 0.78, 1.0),
        "rust": (0.70, 0.25, 0.075, 1.0),
        "oxide": (0.25, 0.22, 0.17, 1.0),
        "metallic": 0.88,
        "roughness": 0.38,
        "rust_affinity": 0.55,
    },
    "dark_titanium": {
        "base": (0.060, 0.066, 0.078, 1.0),
        "armor": (0.10, 0.108, 0.122, 1.0),
        "trim": (0.018, 0.020, 0.026, 1.0),
        "edge": (0.62, 0.66, 0.70, 1.0),
        "rust": (0.34, 0.14, 0.060, 1.0),
        "oxide": (0.075, 0.095, 0.115, 1.0),
        "metallic": 0.82,
        "roughness": 0.44,
        "rust_affinity": 0.25,
    },
    "rusted_iron": {
        "base": (0.105, 0.098, 0.090, 1.0),
        "armor": (0.18, 0.17, 0.155, 1.0),
        "trim": (0.050, 0.047, 0.043, 1.0),
        "edge": (0.68, 0.64, 0.56, 1.0),
        "rust": (0.86, 0.28, 0.060, 1.0),
        "oxide": (0.34, 0.12, 0.045, 1.0),
        "metallic": 0.58,
        "roughness": 0.78,
        "rust_affinity": 1.45,
    },
    "oxidized_copper": {
        "base": (0.38, 0.22, 0.105, 1.0),
        "armor": (0.54, 0.32, 0.15, 1.0),
        "trim": (0.12, 0.075, 0.045, 1.0),
        "edge": (0.92, 0.55, 0.24, 1.0),
        "rust": (0.11, 0.58, 0.50, 1.0),
        "oxide": (0.060, 0.34, 0.31, 1.0),
        "metallic": 0.72,
        "roughness": 0.56,
        "rust_affinity": 1.10,
    },
    "painted_composite": {
        "base": (0.045, 0.045, 0.042, 1.0),
        "armor": (0.085, 0.085, 0.080, 1.0),
        "trim": (0.012, 0.012, 0.012, 1.0),
        "edge": (0.72, 0.70, 0.62, 1.0),
        "rust": (0.62, 0.20, 0.070, 1.0),
        "oxide": (0.13, 0.12, 0.10, 1.0),
        "metallic": 0.46,
        "roughness": 0.62,
        "rust_affinity": 0.85,
    },
}


def _part_material_profiles(selected_style: str) -> dict[str, dict[str, Any]]:
    base = MATERIAL_STYLE_PROFILES[selected_style]
    gunmetal = MATERIAL_STYLE_PROFILES["gunmetal"]
    worn_steel = MATERIAL_STYLE_PROFILES["worn_steel"]
    dark_titanium = MATERIAL_STYLE_PROFILES["dark_titanium"]
    rusted_iron = MATERIAL_STYLE_PROFILES["rusted_iron"]
    painted_composite = MATERIAL_STYLE_PROFILES["painted_composite"]
    return {
        "body": base,
        "body_panel": base,
        "wing": dark_titanium if selected_style != "dark_titanium" else gunmetal,
        "wing_edge": painted_composite,
        "armor": worn_steel if selected_style != "worn_steel" else base,
        "armor_top": worn_steel if selected_style != "worn_steel" else base,
        "armor_dark": gunmetal if selected_style != "gunmetal" else dark_titanium,
        "underbody": gunmetal if selected_style != "gunmetal" else dark_titanium,
        "engine_shell": dark_titanium,
        "weapon": dark_titanium if selected_style != "dark_titanium" else worn_steel,
        "cargo": rusted_iron,
        "system_bay": painted_composite,
        "panel": gunmetal,
        "wear": worn_steel,
        "decal": painted_composite,
        "ordnance": worn_steel,
    }


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(max(value, minimum), maximum)


class _LazyMaterialLibrary(dict[str, bpy.types.Material]):
    def __init__(self, builders: dict[str, Callable[[], bpy.types.Material]]) -> None:
        super().__init__()
        self._builders = builders

    def __getitem__(self, key: str) -> bpy.types.Material:
        if key not in self:
            builder = self._builders.get(key)
            if builder is None:
                raise KeyError(key)
            self[key] = builder()
        return dict.__getitem__(self, key)


def _create_materials(
    faction: str,
    *,
    glow_strength: float = 1.0,
    config: ShipGenerationConfig | None = None,
) -> _LazyMaterialLibrary:
    profile = FACTION_PROFILES[faction]
    selected_material_style = config.material_style if config else "gunmetal"
    material_profile = MATERIAL_STYLE_PROFILES[selected_material_style]
    part_profiles = _part_material_profiles(selected_material_style)
    texture_scale = max(config.texture_scale if config else 1.0, 0.1)
    raw_rust_amount = _clamp(config.rust_amount if config else 0.22)
    scratch_amount = _clamp(config.scratch_amount if config else 0.55)
    use_custom_colors = bool(config and config.use_custom_colors)
    faction_hull = _rgba_from_rgb(config.primary_hue if use_custom_colors and config else None, profile["color"])
    accent_color = _rgba_from_rgb(config.accent_hue if use_custom_colors and config else None, profile["accent"])
    graphite = _mix_color(material_profile["base"], faction_hull, 0.08)
    armor = _mix_color(material_profile["armor"], faction_hull, 0.16)
    worn_edge = _mix_color(material_profile["edge"], faction_hull, 0.08)
    trim_color = _mix_color(material_profile["trim"], faction_hull, 0.04)
    body_skin = _mix_color(graphite, (0.018, 0.020, 0.022, 1.0), 0.28)
    wing_skin = _mix_color(graphite, (0.010, 0.012, 0.014, 1.0), 0.44)
    wing_edge = _mix_color(accent_color, (0.65, 0.045, 0.035, 1.0), 0.48)
    armor_top = _mix_color(armor, material_profile["edge"], 0.10)
    armor_dark = _mix_color(armor, trim_color, 0.50)
    underbody = _mix_color(trim_color, (0.0, 0.0, 0.0, 1.0), 0.42)
    engine_shell = _mix_color(trim_color, (0.050, 0.072, 0.080, 1.0), 0.34)
    weapon_metal = _mix_color(trim_color, material_profile["edge"], 0.16)
    cargo_metal = _mix_color(armor, (0.13, 0.135, 0.13, 1.0), 0.34)
    bay_metal = _mix_color(armor_dark, accent_color, 0.16)
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

    def rust_for(part_name: str, multiplier: float = 1.0) -> float:
        return _clamp(raw_rust_amount * part_profiles[part_name]["rust_affinity"] * multiplier)

    texture_workflow = config.texture_workflow if config else "painted"
    texture_resolution = validate_texture_resolution(config.texture_resolution if config else 64)
    paint_seed = _stable_int_seed(config.seed, config.ship_type, config.variant, config.faction) if config else 0
    wear_amount = _clamp(config.wear_amount if config else 0.65)
    decal_density = _clamp(config.decal_density if config else 1.0)

    def metal(
        part_name: str,
        name: str,
        material_color: tuple[float, float, float, float],
        part_profile: dict[str, Any],
        *,
        rust_amount: float,
        scratch_amount: float,
        texture_scale: float,
        role_scale: float,
        metallic: float | None = None,
        roughness: float | None = None,
        emission_color: tuple[float, float, float, float] | None = None,
        emission_strength: float = 0.0,
    ) -> bpy.types.Material:
        if texture_workflow == "painted":
            return painted_metal_material(
                name,
                material_color,
                part_profile,
                part_name=part_name,
                seed=paint_seed,
                resolution=texture_resolution,
                rust_amount=rust_amount,
                scratch_amount=scratch_amount,
                wear_amount=wear_amount,
                decal_density=decal_density,
                texture_scale=texture_scale,
                role_scale=role_scale,
                accent_color=accent_color,
                metallic=metallic,
                roughness=roughness,
                emission_color=emission_color,
                emission_strength=emission_strength,
            )
        return _metal_material(
            name,
            material_color,
            part_profile,
            rust_amount=rust_amount,
            scratch_amount=scratch_amount,
            texture_scale=texture_scale,
            role_scale=role_scale,
            metallic=metallic,
            roughness=roughness,
            emission_color=emission_color,
            emission_strength=emission_strength,
        )

    library = _LazyMaterialLibrary(
        {
            "hull": lambda: library["body"],
            "body": lambda: metal("body", "VS_Metal_Body_Primary", body_skin, part_profiles["body"], rust_amount=rust_for("body"), scratch_amount=scratch_amount, texture_scale=texture_scale, role_scale=1.0),
            "body_panel": lambda: metal("body_panel", "VS_Metal_Body_Panel_Variation", graphite, part_profiles["body_panel"], rust_amount=rust_for("body_panel", 0.85), scratch_amount=scratch_amount * 0.78, texture_scale=texture_scale * 1.18, role_scale=0.85),
            "wing": lambda: metal("wing", "VS_Metal_Wing_Skin", wing_skin, part_profiles["wing"], rust_amount=rust_for("wing", 1.10), scratch_amount=scratch_amount * 1.12, texture_scale=texture_scale * 1.34, role_scale=0.72, metallic=part_profiles["wing"]["metallic"], roughness=part_profiles["wing"]["roughness"] + 0.08),
            "wing_edge": lambda: metal("wing_edge", "VS_Metal_Wing_Edge_Livery", wing_edge, part_profiles["wing_edge"], rust_amount=rust_for("wing_edge", 0.62), scratch_amount=scratch_amount * 1.22, texture_scale=texture_scale * 1.5, role_scale=0.48, metallic=0.22, roughness=0.50),
            "armor": lambda: metal("armor", "VS_Metal_Armor_Plates", armor_top, part_profiles["armor"], rust_amount=rust_for("armor", 0.9), scratch_amount=scratch_amount, texture_scale=texture_scale * 0.82, role_scale=1.15),
            "armor_top": lambda: metal("armor_top", "VS_Metal_Armor_Top_Plates", armor_top, part_profiles["armor_top"], rust_amount=rust_for("armor_top", 0.82), scratch_amount=scratch_amount * 1.05, texture_scale=texture_scale * 0.78, role_scale=1.20),
            "armor_dark": lambda: metal("armor_dark", "VS_Metal_Dark_Armor_Inset", armor_dark, part_profiles["armor_dark"], rust_amount=rust_for("armor_dark", 1.05), scratch_amount=scratch_amount * 0.70, texture_scale=texture_scale * 1.05, role_scale=0.88),
            "accent": lambda: metal("accent", "VS_Metal_Faction_Accent", accent_color, part_profiles["decal"], rust_amount=rust_for("decal", 0.55), scratch_amount=scratch_amount * 0.72, texture_scale=texture_scale * 0.75, role_scale=0.75, metallic=max(part_profiles["decal"]["metallic"] - 0.18, 0.18), roughness=max(part_profiles["decal"]["roughness"] - 0.08, 0.18)),
            "trim": lambda: library["underbody"],
            "underbody": lambda: metal("underbody", "VS_Metal_Underbody_Black", underbody, part_profiles["underbody"], rust_amount=rust_for("underbody", 1.30), scratch_amount=scratch_amount * 0.62, texture_scale=texture_scale * 1.45, role_scale=0.65, metallic=part_profiles["underbody"]["metallic"], roughness=part_profiles["underbody"]["roughness"] + 0.10),
            "engine_shell": lambda: metal("engine_shell", "VS_Metal_Engine_Heat_Stained", engine_shell, part_profiles["engine_shell"], rust_amount=rust_for("engine_shell", 0.62), scratch_amount=scratch_amount * 0.80, texture_scale=texture_scale * 1.1, role_scale=0.75, metallic=0.86, roughness=0.38),
            "weapon": lambda: metal("weapon", "VS_Metal_Weapon_Blued_Steel", weapon_metal, part_profiles["weapon"], rust_amount=rust_for("weapon", 0.48), scratch_amount=scratch_amount * 1.30, texture_scale=texture_scale * 1.75, role_scale=0.45, metallic=0.90, roughness=0.34),
            "cargo": lambda: metal("cargo", "VS_Metal_Cargo_Industrial", cargo_metal, part_profiles["cargo"], rust_amount=rust_for("cargo", 1.35), scratch_amount=scratch_amount * 0.58, texture_scale=texture_scale * 0.92, role_scale=1.0, metallic=max(part_profiles["cargo"]["metallic"] - 0.12, 0.32), roughness=part_profiles["cargo"]["roughness"] + 0.14),
            "system_bay": lambda: metal("system_bay", "VS_Metal_System_Bay_Module", bay_metal, part_profiles["system_bay"], rust_amount=rust_for("system_bay", 0.95), scratch_amount=scratch_amount * 0.92, texture_scale=texture_scale * 1.16, role_scale=0.9, metallic=part_profiles["system_bay"]["metallic"], roughness=part_profiles["system_bay"]["roughness"] + 0.06),
            "panel": lambda: metal("panel", "VS_Metal_Deep_Panel_Seams", (0.002, 0.003, 0.004, 1.0), part_profiles["panel"], rust_amount=rust_for("panel", 1.25), scratch_amount=scratch_amount * 0.40, texture_scale=texture_scale * 1.55, role_scale=0.45, metallic=max(part_profiles["panel"]["metallic"] - 0.30, 0.12), roughness=0.78),
            "wear": lambda: metal("wear", "VS_Metal_Chipped_Edge_Wear", worn_edge, part_profiles["wear"], rust_amount=rust_for("wear", 0.30), scratch_amount=1.0, texture_scale=texture_scale * 1.8, role_scale=0.35, metallic=0.72, roughness=0.42),
            "red_decal": lambda: metal("red_decal", "VS_Painted_Raider_Livery", raider_red, part_profiles["decal"], rust_amount=rust_for("decal", 0.45), scratch_amount=scratch_amount * 0.65, texture_scale=texture_scale * 1.2, role_scale=0.55, metallic=0.12, roughness=0.50),
            "ordnance": lambda: metal("ordnance", "VS_Metal_Ordnance_Amber", (0.9, 0.48, 0.10, 1.0), part_profiles["ordnance"], rust_amount=rust_for("ordnance", 0.25), scratch_amount=scratch_amount * 0.45, texture_scale=texture_scale, role_scale=0.45, metallic=0.34, roughness=0.42, emission_color=(0.9, 0.28, 0.04, 1.0), emission_strength=0.22 * glow_strength),
            "glass": lambda: _material("VS_CanopyGlass", (0.08, 0.32, 0.46, 0.72), alpha=0.72, metallic=0.0, roughness=0.12),
            "glow": lambda: _material("VS_EngineGlow", glow_color, emission_color=glow_color, emission_strength=3.5 * glow_strength),
            "window": lambda: _material("VS_WindowLights", window_color, emission_color=window_color, emission_strength=2.2 * glow_strength),
            "decal": lambda: _material("VS_DesignerDecals", accent_color, emission_color=accent_color, emission_strength=0.35, metallic=0.05, roughness=0.28),
            "collision": lambda: _material("VS_CollisionProxy", (0.15, 0.85, 0.45, 0.25), alpha=0.25),
            "marker": lambda: _material("VS_Marker", (0.1, 0.55, 1.0, 1.0)),
        }
    )
    return library


def _metal_material(
    name: str,
    color: tuple[float, float, float, float],
    profile: dict[str, Any],
    *,
    rust_amount: float,
    scratch_amount: float,
    texture_scale: float,
    role_scale: float,
    metallic: float | None = None,
    roughness: float | None = None,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> bpy.types.Material:
    rust_amount = _clamp(rust_amount)
    scratch_amount = _clamp(scratch_amount)
    texture_scale = max(texture_scale, 0.1)
    metallic_value = _clamp(profile["metallic"] if metallic is None else metallic)
    roughness_value = _clamp(profile["roughness"] if roughness is None else roughness, 0.08, 0.95)

    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    material["void_shipwright_material"] = "procedural_layered_metal"
    material["void_shipwright_texture_workflow"] = "non_organic_object_space_pbr_metal"
    material["void_shipwright_rust_amount"] = round(rust_amount, 4)
    material["void_shipwright_scratch_amount"] = round(scratch_amount, 4)

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        return material

    for node in list(nodes):
        if node.name not in {"Principled BSDF", "Material Output"}:
            nodes.remove(node)

    _set_input(bsdf, "Metallic", metallic_value)
    _set_input(bsdf, "Roughness", roughness_value)
    _set_input(bsdf, "Base Color", color)
    if emission_color is not None:
        _set_input(bsdf, "Emission Color", emission_color)
        _set_input(bsdf, "Emission Strength", emission_strength)

    texture_coordinates = nodes.new("ShaderNodeTexCoord")
    texture_coordinates.name = "VS_Object_Texture_Coordinates"
    mapping = nodes.new("ShaderNodeMapping")
    mapping.name = "VS_Object_Metal_Mapping"
    if "Scale" in mapping.inputs:
        mapping.inputs["Scale"].default_value = (1.0, 1.08, 0.96)
    if "Object" in texture_coordinates.outputs and "Vector" in mapping.inputs:
        links.new(texture_coordinates.outputs["Object"], mapping.inputs["Vector"])

    def link_vector(texture_node: bpy.types.Node) -> None:
        if "Vector" in texture_node.inputs and "Vector" in mapping.outputs:
            links.new(mapping.outputs["Vector"], texture_node.inputs["Vector"])

    grain_noise = nodes.new("ShaderNodeTexNoise")
    grain_noise.name = "VS_Metal_Grain_Noise"
    grain_noise.inputs["Scale"].default_value = 96.0 * texture_scale * max(role_scale, 0.45)
    grain_noise.inputs["Detail"].default_value = 10.0
    grain_noise.inputs["Roughness"].default_value = 0.56
    if "Distortion" in grain_noise.inputs:
        grain_noise.inputs["Distortion"].default_value = 0.035
    link_vector(grain_noise)

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.name = "VS_Metal_Base_Grain_Ramp"
    oxide_tint = _mix_color(profile["rust"], profile["oxide"], 0.58 + rust_amount * 0.20)
    rust_color = _mix_color(_scale_color(color, 0.58), oxide_tint, _clamp(rust_amount * 0.46, 0.0, 0.42))
    bright_wear = _mix_color(color, profile["edge"], 0.08 + scratch_amount * 0.18)
    color_ramp.color_ramp.elements[0].position = 0.16
    color_ramp.color_ramp.elements[0].color = _mix_color(_scale_color(color, 0.74), profile["trim"], 0.14)
    color_ramp.color_ramp.elements[1].position = 1.0
    color_ramp.color_ramp.elements[1].color = bright_wear
    mid_grain = color_ramp.color_ramp.elements.new(0.64)
    mid_grain.color = _mix_color(color, profile["edge"], 0.035)
    links.new(grain_noise.outputs["Fac"], color_ramp.inputs["Fac"])

    rust_voronoi = nodes.new("ShaderNodeTexVoronoi")
    rust_voronoi.name = "VS_Sparse_Oxide_Pit_Voronoi"
    rust_voronoi.inputs["Scale"].default_value = 58.0 * texture_scale * max(role_scale, 0.42)
    if "Randomness" in rust_voronoi.inputs:
        rust_voronoi.inputs["Randomness"].default_value = 0.78
    if "Detail" in rust_voronoi.inputs:
        rust_voronoi.inputs["Detail"].default_value = 6.0
    if "Roughness" in rust_voronoi.inputs:
        rust_voronoi.inputs["Roughness"].default_value = 0.58
    link_vector(rust_voronoi)

    rust_mask = nodes.new("ShaderNodeValToRGB")
    rust_mask.name = "VS_Sparse_Oxide_Pit_Mask"
    rust_mask.color_ramp.elements[0].position = _clamp(0.78 - rust_amount * 0.06, 0.62, 0.86)
    rust_mask.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    rust_mask.color_ramp.elements[1].position = _clamp(0.975 - rust_amount * 0.08, 0.84, 0.99)
    oxide_factor = _clamp(rust_amount * 0.28, 0.0, 0.30)
    rust_mask.color_ramp.elements[1].color = (oxide_factor, oxide_factor, oxide_factor, 1.0)

    rust_patch_color = nodes.new("ShaderNodeValToRGB")
    rust_patch_color.name = "VS_Sparse_Oxide_Color_Ramp"
    rust_patch_color.color_ramp.elements[0].position = 0.32
    rust_patch_color.color_ramp.elements[0].color = _mix_color(_scale_color(color, 0.66), profile["oxide"], rust_amount * 0.20)
    rust_patch_color.color_ramp.elements[1].position = 1.0
    rust_patch_color.color_ramp.elements[1].color = _mix_color(color, rust_color, 0.62)
    links.new(rust_voronoi.outputs["Distance"], rust_mask.inputs["Fac"])
    links.new(rust_voronoi.outputs["Distance"], rust_patch_color.inputs["Fac"])

    rust_mix = nodes.new("ShaderNodeMixRGB")
    rust_mix.name = "VS_Base_With_Oxide_Patches"
    rust_mix.blend_type = "MIX"
    links.new(rust_mask.outputs["Color"], rust_mix.inputs["Fac"])
    links.new(color_ramp.outputs["Color"], rust_mix.inputs["Color1"])
    links.new(rust_patch_color.outputs["Color"], rust_mix.inputs["Color2"])
    links.new(rust_mix.outputs["Color"], bsdf.inputs["Base Color"])

    rough_noise = nodes.new("ShaderNodeTexNoise")
    rough_noise.name = "VS_Roughness_Pitting_Noise"
    rough_noise.inputs["Scale"].default_value = 16.0 * texture_scale * role_scale
    rough_noise.inputs["Detail"].default_value = 11.0
    rough_noise.inputs["Roughness"].default_value = 0.72
    if "Distortion" in rough_noise.inputs:
        rough_noise.inputs["Distortion"].default_value = 0.12 + rust_amount * 0.18
    link_vector(rough_noise)
    pitting_voronoi = nodes.new("ShaderNodeTexVoronoi")
    pitting_voronoi.name = "VS_Micro_Pitting_Voronoi"
    pitting_voronoi.inputs["Scale"].default_value = 42.0 * texture_scale * max(role_scale, 0.35)
    if "Randomness" in pitting_voronoi.inputs:
        pitting_voronoi.inputs["Randomness"].default_value = 0.92
    link_vector(pitting_voronoi)
    rough_combine = nodes.new("ShaderNodeMath")
    rough_combine.name = "VS_Roughness_Noise_Max"
    rough_combine.operation = "MAXIMUM"
    links.new(rough_noise.outputs["Fac"], rough_combine.inputs[0])
    links.new(pitting_voronoi.outputs["Distance"], rough_combine.inputs[1])
    rough_map = nodes.new("ShaderNodeMapRange")
    rough_map.name = "VS_Roughness_Map"
    _set_input(rough_map, "From Min", 0.0)
    _set_input(rough_map, "From Max", 1.0)
    _set_input(rough_map, "To Min", _clamp(roughness_value - 0.18 * scratch_amount, 0.05, 1.0))
    _set_input(rough_map, "To Max", _clamp(roughness_value + 0.24 + rust_amount * 0.18, 0.05, 1.0))
    if "Value" in rough_map.inputs and "Result" in rough_map.outputs:
        links.new(rough_combine.outputs["Value"], rough_map.inputs["Value"])
        links.new(rough_map.outputs["Result"], bsdf.inputs["Roughness"])

    scratch_noise = nodes.new("ShaderNodeTexNoise")
    scratch_noise.name = "VS_Scratches_Bump_Noise"
    scratch_noise.inputs["Scale"].default_value = 115.0 * texture_scale * max(role_scale, 0.35)
    scratch_noise.inputs["Detail"].default_value = 16.0
    scratch_noise.inputs["Roughness"].default_value = 0.61
    if "Distortion" in scratch_noise.inputs:
        scratch_noise.inputs["Distortion"].default_value = 0.08
    link_vector(scratch_noise)
    fine_scratch_noise = nodes.new("ShaderNodeTexNoise")
    fine_scratch_noise.name = "VS_Fine_Chipped_Micro_Scratches"
    fine_scratch_noise.inputs["Scale"].default_value = 285.0 * texture_scale * max(role_scale, 0.35)
    fine_scratch_noise.inputs["Detail"].default_value = 9.0
    fine_scratch_noise.inputs["Roughness"].default_value = 0.50
    if "Distortion" in fine_scratch_noise.inputs:
        fine_scratch_noise.inputs["Distortion"].default_value = 0.0
    link_vector(fine_scratch_noise)
    scratch_isolate = nodes.new("ShaderNodeValToRGB")
    scratch_isolate.name = "VS_Micro_Scratch_Isolation"
    scratch_isolate.color_ramp.elements[0].position = _clamp(0.74 - scratch_amount * 0.06, 0.62, 0.82)
    scratch_isolate.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    scratch_isolate.color_ramp.elements[1].position = _clamp(0.985 - scratch_amount * 0.045, 0.88, 0.995)
    scratch_factor = _clamp(scratch_amount * 0.46, 0.0, 0.48)
    scratch_isolate.color_ramp.elements[1].color = (scratch_factor, scratch_factor, scratch_factor, 1.0)
    links.new(fine_scratch_noise.outputs["Fac"], scratch_isolate.inputs["Fac"])
    bump_height = nodes.new("ShaderNodeMath")
    bump_height.name = "VS_Bump_Combined_Pits_And_Scratches"
    bump_height.operation = "ADD"
    links.new(scratch_noise.outputs["Fac"], bump_height.inputs[0])
    links.new(scratch_isolate.outputs["Color"], bump_height.inputs[1])
    bump = nodes.new("ShaderNodeBump")
    bump.name = "VS_Metal_Bump"
    bump.inputs["Strength"].default_value = 0.018 + scratch_amount * 0.035 + rust_amount * 0.018
    bump.inputs["Distance"].default_value = 0.010 + rust_amount * 0.030
    links.new(bump_height.outputs["Value"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    material.blend_method = "OPAQUE"
    return material


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
        width_scale *= 0.94
        height_scale *= 1.24
    if ship_type == "missile_corvette":
        length_scale *= 0.98
        width_scale *= 1.48
        height_scale *= 1.36
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
        height_scale *= 1.42
        wing_span *= 0.45
        engine_scale *= 0.9
    elif ship_type == "heavy_fighter":
        length_scale *= 0.98
        width_scale *= 1.12
        height_scale *= 0.98
        wing_span *= 0.96
        engine_scale *= 1.32
    elif ship_type == "bomber":
        length_scale *= 1.18
        width_scale *= 0.96
        height_scale *= 1.08
        wing_span *= 0.74
        engine_scale *= 1.05
    elif ship_type == "patrol_cutter":
        length_scale *= 1.10
        width_scale *= 1.08
        height_scale *= 1.18
        wing_span *= 0.56
        engine_scale *= 1.04
    elif ship_type == "explorer":
        length_scale *= 1.24
        width_scale *= 0.88
        height_scale *= 1.06
        wing_span *= 0.62
        engine_scale *= 0.95
    elif ship_type == "dropship":
        length_scale *= 1.02
        width_scale *= 1.24
        height_scale *= 1.32
        wing_span *= 0.58
        engine_scale *= 1.16
    elif ship_type == "mining_ship":
        length_scale *= 1.12
        width_scale *= 1.02
        height_scale *= 1.34
        wing_span *= 0.48
        engine_scale *= 0.86
    elif ship_type == "salvage_ship":
        length_scale *= 1.08
        width_scale *= 1.08
        height_scale *= 1.18
        wing_span *= 0.54
        engine_scale *= 0.92
    elif ship_type == "medical_ship":
        length_scale *= 1.08
        width_scale *= 0.92
        height_scale *= 1.12
        wing_span *= 0.72
        engine_scale *= 1.0
    elif ship_type == "racing_ship":
        length_scale *= 1.26
        width_scale *= 0.68
        height_scale *= 0.72
        wing_span *= 1.05
        engine_scale *= 1.58
    elif ship_type == "luxury_yacht":
        length_scale *= 1.18
        width_scale *= 0.94
        height_scale *= 1.10
        wing_span *= 0.82
        engine_scale *= 0.92
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
    objects = _create_archetype_base(collection, materials, dimensions, rng, config)

    objects.extend(_create_role_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_faction_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_archetype_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_variation_features(collection, materials, dimensions, rng, config))
    objects.extend(_create_structural_corner_layer(collection, materials, dimensions, rng, config))
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
                materials["armor_top"],
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
                    materials["cargo"],
                ),
                _rounded_pod(
                    collection,
                    "MESH_Cargo_Pod_Right",
                    (width * 0.21, length * 0.2, -height * 0.36),
                    length * 0.28,
                    width * 0.08,
                    height * 0.13,
                    materials["cargo"],
                ),
            ]
        )

    objects = _remove_suppressed_visual_objects(objects)
    for obj in objects:
        obj["void_shipwright_kind"] = "visual_mesh"
        obj["void_shipwright_seed_offset"] = rng.randint(1, 999999)
    return objects


def _create_archetype_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    if config.ship_type == "missile_corvette":
        return _create_missile_corvette_base(collection, materials, dimensions)
    if config.ship_type == "interceptor":
        return _create_interceptor_base(collection, materials, dimensions, rng)
    if config.ship_type == "gunship":
        return _create_gunship_base(collection, materials, dimensions)
    if config.ship_type == "freighter":
        return _create_freighter_base(collection, materials, dimensions, config)
    if config.ship_type == "heavy_fighter":
        return _create_heavy_fighter_base(collection, materials, dimensions, rng)
    if config.ship_type == "bomber":
        return _create_bomber_base(collection, materials, dimensions, config)
    if config.ship_type == "patrol_cutter":
        return _create_patrol_cutter_base(collection, materials, dimensions)
    if config.ship_type == "explorer":
        return _create_explorer_base(collection, materials, dimensions)
    if config.ship_type == "dropship":
        return _create_dropship_base(collection, materials, dimensions)
    if config.ship_type == "mining_ship":
        return _create_mining_ship_base(collection, materials, dimensions)
    if config.ship_type == "salvage_ship":
        return _create_salvage_ship_base(collection, materials, dimensions, config)
    if config.ship_type == "medical_ship":
        return _create_medical_ship_base(collection, materials, dimensions)
    if config.ship_type == "racing_ship":
        return _create_racing_ship_base(collection, materials, dimensions, rng)
    if config.ship_type == "luxury_yacht":
        return _create_luxury_yacht_base(collection, materials, dimensions)
    return _create_light_raider_base(collection, materials, dimensions, rng)


def _create_light_raider_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    engine = dimensions["engine"]
    return [
        _raider_hull(collection, "MESH_Hull_Core", length, width, height, materials["body"], rng),
        _raider_keel(collection, "MESH_Ventral_Keel", length, width, height, materials["underbody"]),
        _raider_cockpit(collection, "MESH_Canopy_Glass", length, width, height, materials["glass"]),
        _raider_wing(collection, "MESH_Wing_Left", -1, length, width, height, wing, materials["wing"]),
        _raider_wing(collection, "MESH_Wing_Right", 1, length, width, height, wing, materials["wing"]),
        _smooth_engine_pod(collection, "MESH_Engine_Main_Pod", (0.0, length * 0.42, 0.0), length * 0.28, width * 0.18, height * 0.26 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Engine_Main_Glow", (0.0, length * 0.58, 0.0), width * 0.13, length * 0.025, materials["glow"]),
        _smooth_engine_pod(collection, "MESH_Engine_Left_Pod", (-width * 0.27, length * 0.39, -height * 0.05), length * 0.24, width * 0.095 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Engine_Left_Glow", (-width * 0.27, length * 0.535, -height * 0.05), width * 0.065 * engine, length * 0.022, materials["glow"]),
        _smooth_engine_pod(collection, "MESH_Engine_Right_Pod", (width * 0.27, length * 0.39, -height * 0.05), length * 0.24, width * 0.095 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Engine_Right_Glow", (width * 0.27, length * 0.535, -height * 0.05), width * 0.065 * engine, length * 0.022, materials["glow"]),
        _raider_tail_fin(collection, "MESH_Dorsal_Fin", length, width, height, 1, materials["wing_edge"]),
        _raider_tail_fin(collection, "MESH_Ventral_Fin", length, width, height, -1, materials["underbody"]),
        _weapon_barrel(collection, "MESH_Weapon_Front_01", (-width * 0.08, -length * 0.60, -height * 0.04), width * 0.018, length * 0.26, materials["weapon"]),
        _weapon_barrel(collection, "MESH_Weapon_Front_02", (width * 0.08, -length * 0.60, -height * 0.04), width * 0.018, length * 0.26, materials["weapon"]),
        _weapon_barrel(collection, "MESH_Nose_Gun_Left", (-width * 0.18, -length * 0.52, -height * 0.02), width * 0.018, length * 0.18, materials["weapon"]),
        _weapon_barrel(collection, "MESH_Nose_Gun_Right", (width * 0.18, -length * 0.52, -height * 0.02), width * 0.018, length * 0.18, materials["weapon"]),
    ]


def _create_missile_corvette_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _corvette_hull(collection, "MESH_Hull_Core", length, width, height, materials["body"]),
        _plate_prism(
            collection,
            "MESH_Corvette_Dorsal_Ordnance_Deck",
            [(-width * 0.34, -length * 0.36), (width * 0.34, -length * 0.36), (width * 0.46, length * 0.34), (width * 0.22, length * 0.52), (-width * 0.22, length * 0.52), (-width * 0.46, length * 0.34)],
            height * 0.50,
            height * 0.065,
            materials["armor_top"],
            bevel=0.014,
        ),
        _box(collection, "MESH_Corvette_Raised_Command_Spine", (0.0, length * 0.08, height * 0.66), (width * 0.15, length * 0.30, height * 0.12), materials["system_bay"], bevel=0.010),
        _box(collection, "MESH_Corvette_Bridge_Glass", (0.0, -length * 0.22, height * 0.84), (width * 0.10, length * 0.060, height * 0.050), materials["glass"], bevel=0.008),
        _box(collection, "MESH_Corvette_Port_Ordnance_Bay", (-width * 0.45, length * 0.06, height * 0.07), (width * 0.12, length * 0.31, height * 0.20), materials["system_bay"], bevel=0.012),
        _box(collection, "MESH_Corvette_Starboard_Ordnance_Bay", (width * 0.45, length * 0.06, height * 0.07), (width * 0.12, length * 0.31, height * 0.20), materials["system_bay"], bevel=0.012),
        _box(collection, "MESH_Corvette_Rear_Reactor_Block", (0.0, length * 0.43, -height * 0.02), (width * 0.30, length * 0.12, height * 0.22 * engine), materials["engine_shell"], bevel=0.012),
        _raised_strip_y(collection, "MESH_Corvette_Keel_Radiator", (0.0, length * 0.12, -height * 0.56), length * 0.36, width * 0.09, height * 0.025, materials["engine_shell"]),
    ]
    for index, x_factor in enumerate((-0.26, 0.0, 0.26), start=1):
        objects.append(_engine_glow(collection, f"MESH_Corvette_Reactor_Glow_{index:02d}", (width * x_factor, length * 0.58, -height * 0.03), width * 0.055, length * 0.024, materials["glow"]))
    return objects


def _create_interceptor_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    engine = dimensions["engine"]
    objects = [
        _interceptor_hull(collection, "MESH_Hull_Core", length, width, height, materials["body"], rng),
        _smooth_canopy(collection, "MESH_Interceptor_Bubble_Canopy", length * 0.88, width * 0.72, height * 0.82, materials["glass"]),
        _raised_strip_y(collection, "MESH_Interceptor_Dorsal_Racing_Spine", (0.0, length * 0.02, height * 0.40), length * 0.42, width * 0.026, height * 0.020, materials["wing_edge"]),
        _smooth_engine_pod(collection, "MESH_Interceptor_Engine_Left", (-width * 0.18, length * 0.43, -height * 0.02), length * 0.34, width * 0.10 * engine, height * 0.20 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Interceptor_Glow_Left", (-width * 0.18, length * 0.62, -height * 0.02), width * 0.072 * engine, length * 0.024, materials["glow"]),
        _smooth_engine_pod(collection, "MESH_Interceptor_Engine_Right", (width * 0.18, length * 0.43, -height * 0.02), length * 0.34, width * 0.10 * engine, height * 0.20 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Interceptor_Glow_Right", (width * 0.18, length * 0.62, -height * 0.02), width * 0.072 * engine, length * 0.024, materials["glow"]),
        _smooth_fin(collection, "MESH_Interceptor_Dorsal_V_Fin", length, width * 0.55, height, 1, materials["wing_edge"]),
    ]
    objects.append(_weapon_barrel(collection, "MESH_Interceptor_Centerline_Cannon", (0.0, -length * 0.54, -height * 0.015), width * 0.018, length * 0.24, materials["weapon"]))
    for side in (-1, 1):
        objects.append(_interceptor_swept_wing(collection, f"MESH_Interceptor_Swept_Wing_{'Left' if side < 0 else 'Right'}", side, length, width, height, wing, materials["wing"]))
        objects.append(_hard_airfoil_plate(collection, f"MESH_Interceptor_Canard_{'Left' if side < 0 else 'Right'}", [(side * width * 0.08, -length * 0.42), (side * width * 0.22, -length * 0.39), (side * width * 0.34, -length * 0.30), (side * width * 0.12, -length * 0.31)], height * 0.02, height * 0.018, materials["wing_edge"]))
    return objects


def _create_gunship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _gunship_hull(collection, "MESH_Hull_Core", length, width, height, materials["body"]),
        _box(collection, "MESH_Gunship_Bridge_Glass", (0.0, -length * 0.24, height * 0.52), (width * 0.12, length * 0.060, height * 0.040), materials["glass"], bevel=0.008),
        _box(collection, "MESH_Gunship_Left_Weapon_Sponson", (-width * 0.44, -length * 0.02, -height * 0.02), (width * 0.10, length * 0.28, height * 0.13), materials["weapon"], bevel=0.010),
        _box(collection, "MESH_Gunship_Right_Weapon_Sponson", (width * 0.44, -length * 0.02, -height * 0.02), (width * 0.10, length * 0.28, height * 0.13), materials["weapon"], bevel=0.010),
        _smooth_engine_pod(collection, "MESH_Gunship_Engine_Left", (-width * 0.22, length * 0.46, -height * 0.05), length * 0.24, width * 0.10 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Gunship_Glow_Left", (-width * 0.22, length * 0.61, -height * 0.05), width * 0.070 * engine, length * 0.024, materials["glow"]),
        _smooth_engine_pod(collection, "MESH_Gunship_Engine_Right", (width * 0.22, length * 0.46, -height * 0.05), length * 0.24, width * 0.10 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Gunship_Glow_Right", (width * 0.22, length * 0.61, -height * 0.05), width * 0.070 * engine, length * 0.024, materials["glow"]),
    ]
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_Gunship_Stub_Wing_{'Left' if side < 0 else 'Right'}", [(side * width * 0.24, -length * 0.20), (side * width * 0.55, -length * 0.10), (side * width * 0.60, length * 0.16), (side * width * 0.24, length * 0.22)], -height * 0.09, height * 0.045, materials["wing"]))
        objects.append(_weapon_barrel(collection, f"MESH_Gunship_Heavy_Nose_Cannon_{'Left' if side < 0 else 'Right'}", (side * width * 0.11, -length * 0.54, -height * 0.08), width * 0.020, length * 0.24, materials["weapon"]))
    return objects


def _create_freighter_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    cargo_slots = max(2, min(4, round(2 + config.cargo_density * 2)))
    cargo_y_slots = (-0.26, -0.06, 0.16, 0.36)
    objects = [
        _tapered_prism(collection, "MESH_Hull_Core", (0.0, 0.0, -height * 0.03), length * 0.58, width * 0.14, width * 0.22, height * 0.24, height * 0.34, materials["body"], bevel=0.016),
        _box(collection, "MESH_Freighter_Central_Truss", (0.0, length * 0.05, -height * 0.20), (width * 0.09, length * 0.50, height * 0.075), materials["underbody"], bevel=0.006),
        _box(collection, "MESH_Freighter_Upper_Utility_Spine", (0.0, length * 0.04, height * 0.31), (width * 0.10, length * 0.42, height * 0.08), materials["armor_top"], bevel=0.008),
        _box(collection, "MESH_Freighter_Bridge_Cab_Glass", (-width * 0.10, -length * 0.39, height * 0.48), (width * 0.09, length * 0.070, height * 0.075), materials["glass"], bevel=0.008),
        _box(collection, "MESH_Freighter_Engine_Tug_Block", (0.0, length * 0.50, -height * 0.02), (width * 0.27, length * 0.13, height * 0.24 * engine), materials["engine_shell"], bevel=0.012),
        _engine_glow(collection, "MESH_Freighter_Main_Engine_Glow", (0.0, length * 0.65, -height * 0.02), width * 0.12 * engine, length * 0.026, materials["glow"]),
    ]
    for side in (-1, 1):
        objects.append(_raised_strip_y(collection, f"MESH_Freighter_Side_Rail_{'Left' if side < 0 else 'Right'}", (side * width * 0.25, length * 0.05, -height * 0.03), length * 0.50, width * 0.018, height * 0.020, materials["underbody"]))
        for index, y_factor in enumerate(cargo_y_slots[:cargo_slots], start=1):
            y = length * y_factor
            objects.append(_box(collection, f"MESH_Freighter_Cargo_Block_{'Left' if side < 0 else 'Right'}_{index:02d}", (side * width * 0.37, y, -height * 0.04), (width * 0.14, length * 0.080, height * 0.21), materials["cargo"], bevel=0.006))
            objects.append(_box(collection, f"MESH_Freighter_Cargo_Upper_Stack_{'Left' if side < 0 else 'Right'}_{index:02d}", (side * width * 0.37, y + length * 0.010, height * 0.24), (width * 0.115, length * 0.060, height * 0.075), materials["system_bay"], bevel=0.005))
            if index % 2 == 0:
                objects.append(_box(collection, f"MESH_Freighter_Underslung_Module_{'Left' if side < 0 else 'Right'}_{index:02d}", (side * width * 0.34, y - length * 0.018, -height * 0.35), (width * 0.095, length * 0.050, height * 0.070), materials["underbody"], bevel=0.005))
            objects.append(_box(collection, f"MESH_Freighter_Cargo_Stripe_{'Left' if side < 0 else 'Right'}_{index:02d}", (side * width * 0.37, y - length * 0.083, height * 0.17), (width * 0.12, length * 0.008, height * 0.012), materials["accent"], bevel=0.002))
    return objects


def _create_heavy_fighter_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    engine = dimensions["engine"]
    objects = [
        _gunship_hull(collection, "MESH_Hull_Core", length, width * 0.82, height * 0.88, materials["body"]),
        _box(collection, "MESH_HeavyFighter_Canopy_Glass", (0.0, -length * 0.30, height * 0.38), (width * 0.105, length * 0.065, height * 0.050), materials["glass"], bevel=0.007),
        _box(collection, "MESH_HeavyFighter_Shoulder_Block_Left", (-width * 0.24, -length * 0.02, height * 0.22), (width * 0.11, length * 0.22, height * 0.070), materials["body_panel"], bevel=0.010),
        _box(collection, "MESH_HeavyFighter_Shoulder_Block_Right", (width * 0.24, -length * 0.02, height * 0.22), (width * 0.11, length * 0.22, height * 0.070), materials["body_panel"], bevel=0.010),
    ]
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_HeavyFighter_Swept_Wing_{_side_name(side)}", [(side * width * 0.20, -length * 0.18), (side * width * (0.58 + wing * 0.045), -length * 0.07), (side * width * (0.66 + wing * 0.050), length * 0.18), (side * width * 0.30, length * 0.18)], -height * 0.07, height * 0.052, materials["wing"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_HeavyFighter_Primary_Engine_{_side_name(side)}", (side * width * 0.31, length * 0.44, -height * 0.04), length * 0.27, width * 0.105 * engine, height * 0.175 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_HeavyFighter_Primary_Glow_{_side_name(side)}", (side * width * 0.31, length * 0.61, -height * 0.04), width * 0.075 * engine, length * 0.022, materials["glow"]))
        objects.append(_weapon_barrel(collection, f"MESH_HeavyFighter_Nose_Cannon_{_side_name(side)}", (side * width * 0.12, -length * 0.58, -height * 0.05), width * 0.018, length * (0.24 + rng.random() * 0.04), materials["weapon"]))
    return objects


def _create_bomber_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    bay_count = max(2, min(5, round(2 + config.missile_density * 3)))
    objects = [
        _faceted_loft_y(collection, "MESH_Hull_Core", [(-length * 0.62, width * 0.035, height * 0.050, -height * 0.02, 0.0), (-length * 0.42, width * 0.17, height * 0.18, 0.0, 0.0), (-length * 0.08, width * 0.28, height * 0.32, height * 0.01, 0.0), (length * 0.32, width * 0.24, height * 0.30, -height * 0.02, 0.0), (length * 0.58, width * 0.12, height * 0.17, -height * 0.04, 0.0)], materials["body"], bevel=0.016, top_bias=0.95, bottom_bias=0.64),
        _tapered_prism(collection, "MESH_Bomber_Reinforced_Keel", (0.0, length * 0.08, -height * 0.42), length * 0.43, width * 0.070, width * 0.160, height * 0.080, height * 0.135, materials["underbody"], bevel=0.010),
        _box(collection, "MESH_Bomber_Cockpit_Glass", (0.0, -length * 0.35, height * 0.34), (width * 0.090, length * 0.060, height * 0.045), materials["glass"], bevel=0.007),
        _box(collection, "MESH_Bomber_Aft_Reactor_Block", (0.0, length * 0.45, -height * 0.02), (width * 0.28, length * 0.11, height * 0.19 * engine), materials["engine_shell"], bevel=0.010),
    ]
    for index, y_factor in enumerate((-0.26, -0.12, 0.02, 0.16, 0.30)[:bay_count], start=1):
        objects.append(_box(collection, f"MESH_Bomber_Ordnance_Door_{index:02d}", (0.0, length * y_factor, -height * 0.56), (width * 0.105, length * 0.035, height * 0.018), materials["ordnance"], bevel=0.004))
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_Bomber_Low_Stabilizer_{_side_name(side)}", [(side * width * 0.19, length * 0.08), (side * width * 0.55, length * 0.16), (side * width * 0.62, length * 0.38), (side * width * 0.24, length * 0.30)], -height * 0.16, height * 0.034, materials["wing"]))
        objects.append(_engine_glow(collection, f"MESH_Bomber_Engine_Glow_{_side_name(side)}", (side * width * 0.18, length * 0.60, -height * 0.04), width * 0.055 * engine, length * 0.020, materials["glow"]))
    return objects


def _create_patrol_cutter_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _corvette_hull(collection, "MESH_Hull_Core", length, width * 0.84, height * 0.92, materials["body"]),
        _tapered_prism(collection, "MESH_Cutter_Prow_Wedge", (0.0, -length * 0.48, height * 0.02), length * 0.12, width * 0.055, width * 0.24, height * 0.070, height * 0.150, materials["armor_dark"], bevel=0.009),
        _box(collection, "MESH_Cutter_Command_Deck", (0.0, -length * 0.06, height * 0.53), (width * 0.15, length * 0.13, height * 0.090), materials["system_bay"], bevel=0.010),
        _box(collection, "MESH_Cutter_Bridge_Glass", (0.0, -length * 0.19, height * 0.62), (width * 0.115, length * 0.040, height * 0.035), materials["glass"], bevel=0.006),
        _box(collection, "MESH_Cutter_Aft_Utility_Block", (0.0, length * 0.42, -height * 0.04), (width * 0.25, length * 0.13, height * 0.18 * engine), materials["engine_shell"], bevel=0.010),
    ]
    for side in (-1, 1):
        objects.append(_box(collection, f"MESH_Cutter_Side_Mission_Rack_{_side_name(side)}", (side * width * 0.41, length * 0.10, -height * 0.05), (width * 0.070, length * 0.24, height * 0.090), materials["system_bay"], bevel=0.008))
        objects.append(_weapon_barrel(collection, f"MESH_Cutter_Patrol_Gun_{_side_name(side)}", (side * width * 0.13, -length * 0.46, -height * 0.02), width * 0.013, length * 0.18, materials["weapon"]))
        objects.append(_engine_glow(collection, f"MESH_Cutter_Engine_Glow_{_side_name(side)}", (side * width * 0.18, length * 0.58, -height * 0.04), width * 0.052 * engine, length * 0.019, materials["glow"]))
    return objects


def _create_explorer_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _faceted_loft_y(collection, "MESH_Hull_Core", [(-length * 0.60, width * 0.030, height * 0.060, -height * 0.02, 0.0), (-length * 0.42, width * 0.12, height * 0.16, 0.0, 0.0), (-length * 0.08, width * 0.20, height * 0.28, height * 0.03, 0.0), (length * 0.28, width * 0.18, height * 0.24, 0.0, 0.0), (length * 0.58, width * 0.075, height * 0.13, -height * 0.02, 0.0)], materials["body"], bevel=0.014, top_bias=1.05, bottom_bias=0.48),
        _box(collection, "MESH_Explorer_Panoramic_Bridge", (0.0, -length * 0.32, height * 0.34), (width * 0.105, length * 0.080, height * 0.055), materials["glass"], bevel=0.008),
        _rounded_pod(collection, "MESH_Explorer_Dorsal_Survey_Module", (0.0, length * 0.06, height * 0.46), length * 0.18, width * 0.075, height * 0.080, materials["system_bay"]),
        _raised_strip_y(collection, "MESH_Explorer_Long_Range_Spine", (0.0, length * 0.14, height * 0.60), length * 0.32, width * 0.020, height * 0.016, materials["accent"]),
    ]
    for side in (-1, 1):
        objects.append(_rounded_pod(collection, f"MESH_Explorer_Fuel_Pod_{_side_name(side)}", (side * width * 0.34, length * 0.18, -height * 0.14), length * 0.27, width * 0.055, height * 0.095, materials["cargo"]))
        objects.append(_antenna(collection, f"MESH_Explorer_Sensor_Mast_{_side_name(side)}", (side * width * 0.22, -length * 0.20, height * 0.56), width * 0.007, height * 0.32, materials["weapon"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_Explorer_Endurance_Engine_{_side_name(side)}", (side * width * 0.22, length * 0.43, -height * 0.03), length * 0.22, width * 0.070 * engine, height * 0.115 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Explorer_Engine_Glow_{_side_name(side)}", (side * width * 0.22, length * 0.58, -height * 0.03), width * 0.050 * engine, length * 0.018, materials["glow"]))
    return objects


def _create_dropship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _tapered_prism(collection, "MESH_Hull_Core", (0.0, 0.0, -height * 0.04), length * 0.56, width * 0.22, width * 0.31, height * 0.27, height * 0.34, materials["body"], bevel=0.014),
        _box(collection, "MESH_Dropship_Forward_Cockpit_Glass", (0.0, -length * 0.42, height * 0.38), (width * 0.135, length * 0.060, height * 0.055), materials["glass"], bevel=0.007),
        _box(collection, "MESH_Dropship_Belly_Ramp", (0.0, -length * 0.30, -height * 0.46), (width * 0.19, length * 0.12, height * 0.030), materials["underbody"], bevel=0.006),
        _box(collection, "MESH_Dropship_Cargo_Cabin", (0.0, length * 0.06, height * 0.11), (width * 0.28, length * 0.32, height * 0.18), materials["body_panel"], bevel=0.010),
    ]
    for side in (-1, 1):
        objects.append(_box(collection, f"MESH_Dropship_Side_Door_{_side_name(side)}", (side * width * 0.34, -length * 0.04, -height * 0.03), (width * 0.030, length * 0.15, height * 0.13), materials["system_bay"], bevel=0.005))
        objects.append(_smooth_engine_pod(collection, f"MESH_Dropship_Lift_Engine_Front_{_side_name(side)}", (side * width * 0.45, -length * 0.20, -height * 0.08), length * 0.13, width * 0.065 * engine, height * 0.110 * engine, materials["engine_shell"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_Dropship_Lift_Engine_Rear_{_side_name(side)}", (side * width * 0.45, length * 0.28, -height * 0.08), length * 0.13, width * 0.065 * engine, height * 0.110 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Dropship_Main_Glow_{_side_name(side)}", (side * width * 0.24, length * 0.60, -height * 0.06), width * 0.060 * engine, length * 0.020, materials["glow"]))
    return objects


def _create_mining_ship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _tapered_prism(collection, "MESH_Hull_Core", (0.0, length * 0.04, -height * 0.02), length * 0.52, width * 0.15, width * 0.25, height * 0.23, height * 0.30, materials["body"], bevel=0.014),
        _box(collection, "MESH_Mining_Operator_Cab_Glass", (0.0, -length * 0.34, height * 0.37), (width * 0.100, length * 0.060, height * 0.050), materials["glass"], bevel=0.007),
        _tapered_prism(collection, "MESH_Mining_Cutter_Boom", (0.0, -length * 0.62, -height * 0.05), length * 0.24, width * 0.035, width * 0.095, height * 0.040, height * 0.090, materials["weapon"], bevel=0.006),
        _box(collection, "MESH_Mining_Processing_Bay", (0.0, length * 0.12, -height * 0.31), (width * 0.19, length * 0.22, height * 0.10), materials["system_bay"], bevel=0.009),
    ]
    for side in (-1, 1):
        objects.append(_rounded_pod(collection, f"MESH_Mining_Ore_Canister_{_side_name(side)}", (side * width * 0.35, length * 0.16, -height * 0.10), length * 0.24, width * 0.070, height * 0.110, materials["cargo"]))
        objects.append(_engine_glow(collection, f"MESH_Mining_Engine_Glow_{_side_name(side)}", (side * width * 0.20, length * 0.58, -height * 0.03), width * 0.050 * engine, length * 0.018, materials["glow"]))
    return objects


def _create_salvage_ship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    side = -1 if _stable_int_seed(config.seed, config.variant, "salvage_base") % 2 == 0 else 1
    objects = [
        _faceted_loft_y(collection, "MESH_Hull_Core", [(-length * 0.56, width * 0.060, height * 0.080, -height * 0.03, 0.0), (-length * 0.34, width * 0.18, height * 0.22, 0.0, 0.0), (length * 0.02, width * 0.28, height * 0.31, height * 0.01, side * width * 0.025), (length * 0.38, width * 0.22, height * 0.25, -height * 0.02, 0.0), (length * 0.56, width * 0.095, height * 0.14, -height * 0.03, 0.0)], materials["body"], bevel=0.016, top_bias=0.95, bottom_bias=0.58),
        _box(collection, "MESH_Salvage_Cab_Glass", (side * width * 0.10, -length * 0.32, height * 0.35), (width * 0.085, length * 0.055, height * 0.050), materials["glass"], bevel=0.007),
        _box(collection, "MESH_Salvage_Processing_Bay", (side * width * 0.28, length * 0.08, -height * 0.11), (width * 0.115, length * 0.28, height * 0.130), materials["system_bay"], bevel=0.009),
        _rounded_pod(collection, "MESH_Salvage_Scrap_Canister", (-side * width * 0.30, length * 0.20, -height * 0.14), length * 0.25, width * 0.070, height * 0.105, materials["cargo"]),
    ]
    for arm_index, arm_side in enumerate((side, -side), start=1):
        objects.append(_raised_strip_y(collection, f"MESH_Salvage_Grappler_Arm_{arm_index:02d}", (arm_side * width * 0.28, -length * 0.34, -height * 0.08), length * 0.16, width * 0.018, height * 0.014, materials["weapon"]))
        objects.append(_rounded_pod(collection, f"MESH_Salvage_Grappler_Claw_{arm_index:02d}", (arm_side * width * 0.42, -length * 0.48, -height * 0.08), length * 0.055, width * 0.036, height * 0.034, materials["weapon"]))
    for glow_side in (-1, 1):
        objects.append(_engine_glow(collection, f"MESH_Salvage_Engine_Glow_{_side_name(glow_side)}", (glow_side * width * 0.20, length * 0.58, -height * 0.03), width * 0.048, length * 0.018, materials["glow"]))
    return objects


def _create_medical_ship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _smooth_hull(collection, "MESH_Hull_Core", length, width * 0.68, height * 0.82, materials["body"], random.Random(17)),
        _box(collection, "MESH_Medical_Panoramic_Cockpit", (0.0, -length * 0.34, height * 0.37), (width * 0.105, length * 0.075, height * 0.052), materials["glass"], bevel=0.008),
        _rounded_pod(collection, "MESH_Medical_Triage_Module", (0.0, length * 0.06, -height * 0.08), length * 0.28, width * 0.145, height * 0.150, materials["system_bay"]),
        _raised_strip_y(collection, "MESH_Medical_Dorsal_Life_Support", (0.0, length * 0.14, height * 0.46), length * 0.22, width * 0.050, height * 0.030, materials["accent"]),
    ]
    for side in (-1, 1):
        objects.append(_rounded_pod(collection, f"MESH_Medical_LifeSupport_Pod_{_side_name(side)}", (side * width * 0.30, length * 0.14, -height * 0.08), length * 0.22, width * 0.060, height * 0.095, materials["cargo"]))
        objects.append(_raised_strip_y(collection, f"MESH_Medical_Rescue_Light_{_side_name(side)}", (side * width * 0.23, -length * 0.18, height * 0.45), length * 0.075, width * 0.010, height * 0.010, materials["glow"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_Medical_Quiet_Engine_{_side_name(side)}", (side * width * 0.21, length * 0.43, -height * 0.02), length * 0.20, width * 0.060 * engine, height * 0.100 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Medical_Engine_Glow_{_side_name(side)}", (side * width * 0.21, length * 0.57, -height * 0.02), width * 0.044 * engine, length * 0.017, materials["glow"]))
    return objects


def _create_racing_ship_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    engine = dimensions["engine"]
    objects = [
        _interceptor_hull(collection, "MESH_Hull_Core", length, width * 0.62, height * 0.74, materials["body"], rng),
        _smooth_canopy(collection, "MESH_Racer_Bubble_Canopy", length * 0.78, width * 0.48, height * 0.62, materials["glass"]),
        _tapered_prism(collection, "MESH_Racer_Nose_Fairing", (0.0, -length * 0.56, -height * 0.01), length * 0.10, width * 0.035, width * 0.060, height * 0.026, height * 0.052, materials["body_panel"], bevel=0.007),
        _raised_strip_y(collection, "MESH_Racer_Dorsal_Number_Panel", (0.0, length * 0.05, height * 0.28), length * 0.17, width * 0.026, height * 0.010, materials["accent"]),
    ]
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_Racer_Side_Wing_{_side_name(side)}", [(side * width * 0.12, -length * 0.17), (side * width * (0.48 + wing * 0.075), -length * 0.08), (side * width * (0.62 + wing * 0.080), length * 0.14), (side * width * 0.22, length * 0.12)], -height * 0.055, height * 0.040, materials["wing"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_Racer_Thrust_Pod_{_side_name(side)}", (side * width * 0.22, length * 0.43, -height * 0.02), length * 0.36, width * 0.080 * engine, height * 0.150 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Racer_Thrust_Glow_{_side_name(side)}", (side * width * 0.22, length * 0.66, -height * 0.02), width * 0.058 * engine, length * 0.024, materials["glow"]))
    return objects


def _create_luxury_yacht_base(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _smooth_hull(collection, "MESH_Hull_Core", length, width * 0.70, height * 0.86, materials["body"], random.Random(29)),
        _rounded_pod(collection, "MESH_Yacht_Panoramic_Observation_Lounge", (0.0, -length * 0.18, height * 0.44), length * 0.18, width * 0.120, height * 0.070, materials["glass"]),
        _raised_strip_y(collection, "MESH_Yacht_Dorsal_Trim_Spine", (0.0, length * 0.12, height * 0.52), length * 0.34, width * 0.018, height * 0.014, materials["accent"]),
        _tapered_prism(collection, "MESH_Yacht_Smooth_Aft_Tail", (0.0, length * 0.48, -height * 0.02), length * 0.13, width * 0.18, width * 0.10, height * 0.11, height * 0.070, materials["body_panel"], bevel=0.012),
    ]
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_Yacht_Elegant_Side_Fin_{_side_name(side)}", [(side * width * 0.16, length * 0.02), (side * width * 0.48, length * 0.12), (side * width * 0.54, length * 0.36), (side * width * 0.20, length * 0.28)], -height * 0.08, height * 0.026, materials["wing_edge"]))
        objects.append(_smooth_engine_pod(collection, f"MESH_Yacht_Integrated_Nacelle_{_side_name(side)}", (side * width * 0.24, length * 0.42, -height * 0.03), length * 0.22, width * 0.060 * engine, height * 0.100 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Yacht_Soft_Engine_Glow_{_side_name(side)}", (side * width * 0.24, length * 0.57, -height * 0.03), width * 0.044 * engine, length * 0.017, materials["glow"]))
    return objects


def _corvette_hull(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.60, width * 0.08, height * 0.08, -height * 0.03, 0.0),
        (-length * 0.48, width * 0.22, height * 0.18, 0.0, 0.0),
        (-length * 0.28, width * 0.42, height * 0.34, height * 0.02, 0.0),
        (length * 0.04, width * 0.50, height * 0.42, height * 0.02, 0.0),
        (length * 0.34, width * 0.45, height * 0.36, -height * 0.015, 0.0),
        (length * 0.58, width * 0.26, height * 0.22, -height * 0.035, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.018, top_bias=0.82, bottom_bias=0.48)


def _interceptor_hull(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
    rng: random.Random,
) -> bpy.types.Object:
    offset = rng.uniform(-width * 0.006, width * 0.006)
    rings = [
        (-length * 0.66, width * 0.040, height * 0.055, -height * 0.015, 0.0),
        (-length * 0.54, width * 0.065, height * 0.090, -height * 0.010, 0.0),
        (-length * 0.34, width * 0.110, height * 0.155, height * 0.005, offset),
        (-length * 0.05, width * 0.150, height * 0.220, height * 0.015, 0.0),
        (length * 0.28, width * 0.130, height * 0.200, 0.0, -offset),
        (length * 0.58, width * 0.070, height * 0.110, -height * 0.020, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.010, top_bias=1.15, bottom_bias=0.50)


def _interceptor_swept_wing(
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
        (side * width * 0.12, -length * 0.19),
        (side * width * (0.42 + wing * 0.050), -length * 0.08),
        (side * width * (0.66 + wing * 0.055), length * 0.12),
        (side * width * (0.58 + wing * 0.035), length * 0.24),
        (side * width * 0.24, length * 0.25),
    ]
    return _hard_airfoil_plate(collection, name, outline, -height * 0.065, height * 0.044, material)


def _gunship_hull(
    collection: bpy.types.Collection,
    name: str,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-length * 0.55, width * 0.12, height * 0.10, -height * 0.02, 0.0),
        (-length * 0.40, width * 0.30, height * 0.25, 0.0, 0.0),
        (-length * 0.14, width * 0.45, height * 0.38, height * 0.015, 0.0),
        (length * 0.18, width * 0.48, height * 0.42, height * 0.005, 0.0),
        (length * 0.44, width * 0.33, height * 0.31, -height * 0.02, 0.0),
        (length * 0.60, width * 0.18, height * 0.18, -height * 0.035, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.020, top_bias=0.95, bottom_bias=0.58)


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
        (-length * 0.61, width * 0.055, height * 0.070, -height * 0.02, 0.0),
        (-length * 0.52, width * 0.10, height * 0.13, -height * 0.015, 0.0),
        (-length * 0.42, width * 0.16, height * 0.22, 0.0, -offset),
        (-length * 0.22, width * 0.28, height * 0.34, height * 0.02, offset),
        (length * 0.02, width * 0.36, height * 0.38, height * 0.01, 0.0),
        (length * 0.25, width * 0.30, height * 0.31, -height * 0.02, -offset),
        (length * 0.47, width * 0.18, height * 0.20, -height * 0.035, 0.0),
        (length * 0.60, width * 0.08, height * 0.10, -height * 0.03, 0.0),
    ]
    return _faceted_loft_y(collection, name, rings, material, bevel=0.018)


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
        (side * width * (0.72 + wing * 0.055), -length * 0.10),
        (side * width * (0.80 + wing * 0.055), length * 0.04),
        (side * width * 0.58, length * 0.19),
        (side * width * 0.22, length * 0.32),
    ]
    return _hard_airfoil_plate(collection, name, outline, -height * 0.08, height * 0.060, material)


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
    z_tip = direction * height * 0.70
    half_width = width * 0.030
    vertices = [
        (-half_width, length * 0.18, z_root),
        (half_width, length * 0.18, z_root),
        (-half_width, length * 0.52, z_root * 0.75),
        (half_width, length * 0.52, z_root * 0.75),
        (-half_width * 0.48, length * 0.46, z_tip),
        (half_width * 0.48, length * 0.46, z_tip),
    ]
    faces = [(0, 2, 4), (1, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 1, 0)]
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
    outline = _blunted_airfoil_outline(outline)
    count = len(outline)
    airfoil_thickness = max(half_thickness * 1.65, half_thickness + 0.002)
    vertices: list[tuple[float, float, float]] = []
    for index, (x, y) in enumerate(outline):
        crown = 0.55 + 0.35 * sin(pi * index / max(count - 1, 1))
        vertices.append((x, y, z_center - airfoil_thickness * 0.55))
        vertices.append((x, y, z_center + airfoil_thickness * crown))
    faces: list[tuple[int, ...]] = [tuple(index * 2 for index in range(count)), tuple(index * 2 + 1 for index in reversed(range(count)))]
    for index in range(count):
        next_index = (index + 1) % count
        faces.append((index * 2, next_index * 2, next_index * 2 + 1, index * 2 + 1))
    return _mesh_object(collection, name, vertices, faces, material, bevel=max(0.014, airfoil_thickness * 0.15))


def _blunted_airfoil_outline(outline: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if len(outline) < 4:
        return outline

    blunted: list[tuple[float, float]] = []
    for index, current in enumerate(outline):
        previous = outline[index - 1]
        following = outline[(index + 1) % len(outline)]
        prev_vec = (previous[0] - current[0], previous[1] - current[1])
        next_vec = (following[0] - current[0], following[1] - current[1])
        prev_len = (prev_vec[0] * prev_vec[0] + prev_vec[1] * prev_vec[1]) ** 0.5
        next_len = (next_vec[0] * next_vec[0] + next_vec[1] * next_vec[1]) ** 0.5
        if prev_len <= 0.0001 or next_len <= 0.0001:
            blunted.append(current)
            continue

        dot = (prev_vec[0] * next_vec[0] + prev_vec[1] * next_vec[1]) / (prev_len * next_len)
        if dot > 0.42:
            cut = min(prev_len, next_len) * 0.18
            blunted.append((current[0] + prev_vec[0] / prev_len * cut, current[1] + prev_vec[1] / prev_len * cut))
            blunted.append((current[0] + next_vec[0] / next_len * cut, current[1] + next_vec[1] / next_len * cut))
        else:
            blunted.append(current)
    return blunted


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
    corner_x = 0.22
    corner_y = 0.18
    top_inset_x = 0.10
    top_inset_y = 0.07
    bottom = [
        (-1.0 + corner_x, -1.0, -1.0),
        (1.0 - corner_x, -1.0, -1.0),
        (1.0, -1.0 + corner_y, -1.0),
        (1.0, 1.0 - corner_y, -1.0),
        (1.0 - corner_x, 1.0, -1.0),
        (-1.0 + corner_x, 1.0, -1.0),
        (-1.0, 1.0 - corner_y, -1.0),
        (-1.0, -1.0 + corner_y, -1.0),
    ]
    top = [
        (x * (1.0 - top_inset_x), y * (1.0 - top_inset_y), 1.0)
        for x, y, _ in bottom
    ]
    vertices = bottom + top
    faces: list[tuple[int, ...]] = [tuple(reversed(range(8))), tuple(range(8, 16))]
    for index in range(8):
        faces.append((index, (index + 1) % 8, ((index + 1) % 8) + 8, index + 8))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.scale = scale
    obj.data.materials.append(material)
    collection.objects.link(obj)
    obj["void_shipwright_surface_style"] = "cut_corner_hard_box"
    _add_surface_modifiers(obj, bevel=max(bevel, 0.0025), weighted_normals=True)
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
    def ring(y: float, half_width: float, half_height: float) -> list[tuple[float, float, float]]:
        return [
            (-half_width * 0.62, y, -half_height),
            (half_width * 0.62, y, -half_height),
            (half_width, y, -half_height * 0.48),
            (half_width, y, half_height * 0.48),
            (half_width * 0.56, y, half_height),
            (-half_width * 0.56, y, half_height),
            (-half_width, y, half_height * 0.48),
            (-half_width, y, -half_height * 0.48),
        ]

    vertices = ring(-half_length, front_half_width, front_half_height) + ring(half_length, rear_half_width, rear_half_height)
    faces: list[tuple[int, ...]] = [tuple(reversed(range(8))), tuple(range(8, 16))]
    for index in range(8):
        faces.append((index, (index + 1) % 8, ((index + 1) % 8) + 8, index + 8))
    obj = _mesh_object(collection, name, vertices, faces, material, location=location, bevel=max(bevel, 0.0025))
    obj["void_shipwright_surface_style"] = "octagonal_tapered_prism"
    return obj


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
    return _faceted_barrel_y(collection, name, location, radius, depth, material)


def _engine_glow(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _faceted_barrel_y(collection, name, location, radius, depth, material)


def _weapon_barrel(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _faceted_barrel_y(collection, name, location, radius, depth, material)


def _faceted_barrel_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-depth * 0.50, radius * 0.72, radius * 0.66),
        (-depth * 0.38, radius * 1.08, radius * 0.88),
        (depth * 0.22, radius * 0.92, radius * 0.74),
        (depth * 0.46, radius * 1.22, radius * 0.96),
        (depth * 0.50, radius * 0.78, radius * 0.62),
    ]
    radial_segments = 12
    vertices: list[tuple[float, float, float]] = []
    for y, radius_x, radius_z in rings:
        for index in range(radial_segments):
            angle = pi * 0.125 + (2.0 * pi * index / radial_segments)
            vertices.append((cos(angle) * radius_x, y, sin(angle) * radius_z))

    faces: list[tuple[int, ...]] = []
    for ring in range(len(rings) - 1):
        base = ring * radial_segments
        next_base = (ring + 1) * radial_segments
        for index in range(radial_segments):
            faces.append((base + index, base + (index + 1) % radial_segments, next_base + (index + 1) % radial_segments, next_base + index))
    faces.append(tuple(reversed(range(radial_segments))))
    last_base = (len(rings) - 1) * radial_segments
    faces.append(tuple(last_base + index for index in range(radial_segments)))
    return _mesh_object(collection, name, vertices, faces, material, location=location, bevel=max(radius * 0.08, 0.0015))


def _lance_assembly(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    depth: float,
    material: bpy.types.Material,
) -> list[bpy.types.Object]:
    x, y, z = location
    rail_offset = radius * 2.1
    return [
        _faceted_barrel_y(collection, name, location, radius, depth, material),
        _tapered_prism(
            collection,
            f"{name}_Rear_Collar",
            (x, y + depth * 0.31, z),
            depth * 0.075,
            radius * 2.7,
            radius * 3.6,
            radius * 1.20,
            radius * 1.55,
            material,
            bevel=max(radius * 0.08, 0.0015),
        ),
        _tapered_prism(
            collection,
            f"{name}_Muzzle_Shroud",
            (x, y - depth * 0.42, z),
            depth * 0.055,
            radius * 1.7,
            radius * 2.5,
            radius * 0.86,
            radius * 1.18,
            material,
            bevel=max(radius * 0.06, 0.0012),
        ),
        _raised_strip_y(collection, f"{name}_Left_Guide_Rail", (x - rail_offset, y - depth * 0.04, z + radius * 0.75), depth * 0.31, radius * 0.45, radius * 0.18, material),
        _raised_strip_y(collection, f"{name}_Right_Guide_Rail", (x + rail_offset, y - depth * 0.04, z + radius * 0.75), depth * 0.31, radius * 0.45, radius * 0.18, material),
    ]


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
    obj = _faceted_barrel_y(collection, name, location, radius, depth, material)
    obj["void_shipwright_requested_sides"] = vertices
    return obj


def _raised_strip_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    x, y, z = location
    cap = min(half_length * 0.24, radius_x * 1.35)
    inset = radius_x * 0.42
    points = [
        (x - radius_x * 0.52, y - half_length),
        (x + radius_x * 0.52, y - half_length),
        (x + radius_x, y - half_length + cap),
        (x + radius_x * 0.84, y + half_length - cap * 0.65),
        (x + radius_x * 0.46, y + half_length),
        (x - radius_x * 0.46, y + half_length),
        (x - radius_x * 0.84, y + half_length - cap * 0.65),
        (x - radius_x, y - half_length + cap),
    ]
    obj = _plate_prism(collection, name, points, z, max(radius_z * 0.95, 0.0045), material, bevel=max(radius_z * 0.22, 0.0025))
    obj["void_shipwright_surface_style"] = "chamfered_plate"
    obj["void_shipwright_panel_inset"] = round(inset, 4)
    return obj


def _rounded_pod(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    return _hard_pod_y(collection, name, location, half_length, radius_x, radius_z, material)


def _hard_pod_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    half_length: float,
    radius_x: float,
    radius_z: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    rings = [
        (-half_length, radius_x * 0.38, radius_z * 0.42),
        (-half_length * 0.68, radius_x, radius_z * 0.92),
        (half_length * 0.48, radius_x * 0.96, radius_z),
        (half_length, radius_x * 0.54, radius_z * 0.58),
    ]
    segments = 8
    vertices: list[tuple[float, float, float]] = []
    for y, half_width, half_height in rings:
        vertices.extend(
            [
                (0.0, y, half_height),
                (half_width * 0.62, y, half_height * 0.42),
                (half_width, y, 0.0),
                (half_width * 0.48, y, -half_height * 0.70),
                (0.0, y, -half_height),
                (-half_width * 0.48, y, -half_height * 0.70),
                (-half_width, y, 0.0),
                (-half_width * 0.62, y, half_height * 0.42),
            ]
        )
    faces: list[tuple[int, ...]] = []
    for ring in range(len(rings) - 1):
        base = ring * segments
        next_base = (ring + 1) * segments
        for index in range(segments):
            faces.append((base + index, base + (index + 1) % segments, next_base + (index + 1) % segments, next_base + index))
    faces.append(tuple(reversed(range(segments))))
    last_base = (len(rings) - 1) * segments
    faces.append(tuple(last_base + index for index in range(segments)))
    obj = _mesh_object(collection, name, vertices, faces, material, location=location, bevel=max(min(radius_x, radius_z) * 0.08, 0.0025))
    obj["void_shipwright_surface_style"] = "faceted_hard_pod"
    return obj


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
                    materials["weapon"],
                ),
                _weapon_barrel(
                    collection,
                    "MESH_Weapon_Right_Pod",
                    (width * 0.48, -length * 0.08, -height * 0.02),
                    width * 0.03,
                    length * (0.12 + 0.10 * config.weapon_density),
                    materials["weapon"],
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
                    materials["engine_shell"],
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
                    materials["cargo"],
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
                materials["weapon"],
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
                    materials["cargo"],
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
                    materials["weapon"],
                ),
                _rounded_pod(
                    collection,
                    "MESH_Mining_Right_Clamp",
                    (width * 0.44, -length * 0.32, -height * 0.05),
                    length * 0.11,
                    width * 0.045,
                    height * 0.04,
                    materials["weapon"],
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
                materials["cargo"],
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
            materials["armor_top"],
            bevel=0.012,
        )
    )
    objects.append(
        _box(
            collection,
            "MESH_Targeting_Suite_Block",
            (0.0, -length * 0.24, _hull_top_z(length, width, height, 0.0, -length * 0.24, clearance=height * 0.08)),
            (width * 0.09, length * 0.055, height * 0.05),
            materials["weapon"],
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
            materials["weapon"],
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
                materials["wing"],
            )
        )
        objects.append(
            _box(
                collection,
                f"MESH_Siege_Anchor_{'L' if side < 0 else 'R'}",
                (side * width * 0.50, length * 0.42, -height * 0.22),
                (width * 0.035, length * 0.11, height * 0.035),
                materials["underbody"],
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
                    materials["system_bay"],
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
                materials["engine_shell"],
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
                        materials["weapon"],
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
                    materials["system_bay"],
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
            materials["system_bay"],
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
        objects.append(_weapon_barrel(collection, f"MESH_Interceptor_Side_Cannon_{_side_name(side)}", (side * width * 0.26, -length * 0.50, -height * 0.02), width * 0.016, length * 0.20, materials["weapon"]))
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
            objects.append(_weapon_barrel(collection, f"MESH_Gunship_Side_Cannon_{'L' if side < 0 else 'R'}_{index:02d}", (side * width * 0.46, length * y_factor, _hull_side_z(length, width, height, side * width * 0.46, length * y_factor, clearance=height * 0.02)), width * 0.018, length * 0.18, materials["weapon"]))
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
            objects.append(_rounded_pod(collection, f"MESH_Freighter_Cargo_Pod_{'L' if side < 0 else 'R'}_{index:02d}", (side * width * 0.38, length * y_factor, -height * 0.28), length * 0.12, width * 0.065, height * 0.10, materials["cargo"]))
    return objects


def _create_variation_features(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    variation = _ship_variation(config)
    objects: list[bpy.types.Object] = []
    if variation.key == "blade":
        objects.extend(_create_blade_variant(collection, materials, dimensions))
    elif variation.key == "fork":
        objects.extend(_create_fork_variant(collection, materials, dimensions))
    elif variation.key == "hammerhead":
        objects.extend(_create_hammerhead_variant(collection, materials, dimensions))
    elif variation.key == "outrigger":
        objects.extend(_create_outrigger_variant(collection, materials, dimensions))
    elif variation.key == "twinboom":
        objects.extend(_create_twinboom_variant(collection, materials, dimensions))
    elif variation.key == "keel":
        objects.extend(_create_keel_variant(collection, materials, dimensions))
    elif variation.key == "broadwing":
        objects.extend(_create_broadwing_variant(collection, materials, dimensions))
    elif variation.key == "carrier":
        objects.extend(_create_carrier_variant(collection, materials, dimensions))
    elif variation.key == "compact":
        objects.extend(_create_compact_variant(collection, materials, dimensions))
    elif variation.key == "asymmetric":
        objects.extend(_create_asymmetric_variant(collection, materials, dimensions, config))
    objects.extend(_create_type_signature_variation(collection, materials, dimensions, variation, rng, config))
    return objects


def _create_structural_corner_layer(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    density = max(0.0, min(1.0, config.structure_density))
    if density <= 0.01:
        return []

    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    detail = _detail_multiplier(config.detail_level)
    objects: list[bpy.types.Object] = []

    shoulder_slots = (-0.36, -0.18, 0.02, 0.22, 0.40)
    shoulder_count = max(1, min(len(shoulder_slots), round((2.0 + detail * 2.0) * density)))
    for side in (-1, 1):
        for index, y_factor in enumerate(shoulder_slots[:shoulder_count], start=1):
            y = length * y_factor
            x = side * width * (0.17 + 0.035 * ((index + (1 if config.ship_type in {"freighter", "missile_corvette", "dropship"} else 0)) % 2))
            z = _hull_top_z(length, width, height, x, y, clearance=height * (0.055 + 0.008 * (index % 2)))
            objects.append(
                _box(
                    collection,
                    f"MESH_Structural_Shoulder_{_side_name(side)}_{index:02d}",
                    (x, y, z),
                    (
                        width * (0.050 + 0.012 * (index % 2)),
                        length * (0.050 + 0.010 * ((index + 1) % 2)),
                        height * (0.034 + 0.006 * detail),
                    ),
                    materials["body_panel"] if index % 2 else materials["system_bay"],
                    bevel=0.010,
                )
            )

    chine_slots = (-0.24, 0.04, 0.30)
    chine_count = max(1, min(len(chine_slots), round((1.2 + detail * 1.4) * density)))
    side_x_factor = 0.34 if config.ship_type in {"freighter", "dropship", "mining_ship", "salvage_ship"} else 0.40
    for side in (-1, 1):
        for index, y_factor in enumerate(chine_slots[:chine_count], start=1):
            y = length * y_factor
            x = side * width * side_x_factor
            z = _hull_side_z(length, width, height, x, y, clearance=height * (0.012 + index * 0.006))
            objects.append(
                _tapered_prism(
                    collection,
                    f"MESH_Structural_Chine_{_side_name(side)}_{index:02d}",
                    (x, y, z),
                    length * (0.085 + 0.010 * index),
                    width * 0.022,
                    width * (0.034 + 0.005 * index),
                    height * 0.040,
                    height * (0.052 + 0.006 * index),
                    materials["underbody"] if index % 2 else materials["body_panel"],
                    bevel=0.009,
                )
            )

    if density >= 0.34:
        frame_y = length * (0.06 + rng.uniform(-0.035, 0.035))
        frame_half_length = length * (0.095 + 0.025 * density)
        frame_half_height = height * (0.064 + 0.024 * density)
        for side in (-1, 1):
            x = side * width * (0.44 if config.ship_type not in {"freighter", "dropship"} else 0.36)
            z = _hull_side_z(length, width, height, x, frame_y, clearance=height * 0.070)
            objects.extend(
                [
                    _box(
                        collection,
                        f"MESH_Structural_Recess_Frame_{_side_name(side)}_Top",
                        (x, frame_y, z + frame_half_height),
                        (width * 0.026, frame_half_length, height * 0.012),
                        materials["system_bay"],
                        bevel=0.004,
                    ),
                    _box(
                        collection,
                        f"MESH_Structural_Recess_Frame_{_side_name(side)}_Bottom",
                        (x, frame_y, z - frame_half_height),
                        (width * 0.022, frame_half_length * 0.92, height * 0.012),
                        materials["underbody"],
                        bevel=0.004,
                    ),
                    _box(
                        collection,
                        f"MESH_Structural_Recess_Frame_{_side_name(side)}_Fore",
                        (x, frame_y - frame_half_length, z),
                        (width * 0.024, length * 0.012, frame_half_height),
                        materials["body_panel"],
                        bevel=0.004,
                    ),
                    _box(
                        collection,
                        f"MESH_Structural_Recess_Frame_{_side_name(side)}_Aft",
                        (x, frame_y + frame_half_length, z),
                        (width * 0.024, length * 0.012, frame_half_height),
                        materials["body_panel"],
                        bevel=0.004,
                    ),
                ]
            )

    if density >= 0.55:
        for side in (-1, 1):
            y = length * 0.38
            x = side * width * (0.23 if config.ship_type not in {"missile_corvette", "gunship"} else 0.30)
            z = _hull_top_z(length, width, height, x, y, clearance=height * 0.055)
            objects.append(
                _tapered_prism(
                    collection,
                    f"MESH_Structural_Aft_Buttress_{_side_name(side)}",
                    (x, y, z),
                    length * 0.150,
                    width * 0.048,
                    width * 0.082,
                    height * 0.048,
                    height * 0.075,
                    materials["engine_shell"],
                    bevel=0.010,
                )
            )

    return objects


def _create_blade_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects = [
        _tapered_prism(collection, "MESH_Variant_Blade_Front_Fairing", (0.0, -length * 0.50, -height * 0.015), length * 0.14, width * 0.060, width * 0.120, height * 0.040, height * 0.075, materials["body_panel"], bevel=0.008),
        _tapered_prism(collection, "MESH_Variant_Blade_Ventral_Keel", (0.0, length * 0.04, -height * 0.50), length * 0.42, width * 0.030, width * 0.100, height * 0.045, height * 0.080, materials["underbody"], bevel=0.008),
        _side_tail_fin(collection, "MESH_Variant_Blade_Dorsal_Sail", 0, length, width, height, materials["wing_edge"], z_direction=1),
        _side_tail_fin(collection, "MESH_Variant_Blade_Ventral_Sail", 0, length, width, height, materials["underbody"], z_direction=-1),
    ]
    for side in (-1, 1):
        objects.append(
            _hard_airfoil_plate(
                collection,
                f"MESH_Variant_Blade_Forward_Fin_{_side_name(side)}",
                [
                    (side * width * 0.11, -length * 0.37),
                    (side * width * 0.36, -length * 0.31),
                    (side * width * 0.52, -length * 0.15),
                    (side * width * 0.22, -length * 0.16),
                ],
                -height * 0.055,
                height * 0.030,
                materials["wing_edge"],
            )
        )
    return objects


def _create_fork_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = [
        _box(collection, "MESH_Variant_Fork_Nose_Bridge", (0.0, -length * 0.42, height * 0.015), (width * 0.18, length * 0.060, height * 0.055), materials["system_bay"], bevel=0.008),
    ]
    for side in (-1, 1):
        x = side * width * 0.145
        objects.append(_tapered_prism(collection, f"MESH_Variant_Fork_Nose_Rail_{_side_name(side)}", (x, -length * 0.54, -height * 0.015), length * 0.15, width * 0.050, width * 0.090, height * 0.036, height * 0.065, materials["body_panel"], bevel=0.008))
        objects.append(_raised_strip_y(collection, f"MESH_Variant_Fork_Inner_Glow_{_side_name(side)}", (x - side * width * 0.052, -length * 0.56, height * 0.040), length * 0.13, width * 0.006, height * 0.006, materials["glow"]))
    return objects


def _create_hammerhead_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects = [
        _box(collection, "MESH_Variant_Hammerhead_Crosshead", (0.0, -length * 0.43, height * 0.020), (width * 0.42, length * 0.070, height * 0.090), materials["body_panel"], bevel=0.014),
        _box(collection, "MESH_Variant_Hammerhead_Command_Glass", (0.0, -length * 0.485, height * 0.105), (width * 0.105, length * 0.025, height * 0.026), materials["glass"], bevel=0.006),
    ]
    for side in (-1, 1):
        objects.append(_rounded_pod(collection, f"MESH_Variant_Hammerhead_Cheek_{_side_name(side)}", (side * width * 0.38, -length * 0.42, -height * 0.010), length * 0.070, width * 0.085, height * 0.080, materials["system_bay"]))
        objects.append(_weapon_barrel(collection, f"MESH_Variant_Hammerhead_Recessed_Gun_{_side_name(side)}", (side * width * 0.37, -length * 0.51, -height * 0.018), width * 0.014, length * 0.13, materials["weapon"]))
    return objects


def _create_outrigger_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        objects.append(
            _hard_airfoil_plate(
                collection,
                f"MESH_Variant_Outrigger_Strut_{_side_name(side)}",
                [
                    (side * width * 0.20, length * 0.06),
                    (side * width * 0.62, length * 0.12),
                    (side * width * 0.68, length * 0.38),
                    (side * width * 0.26, length * 0.30),
                ],
                -height * 0.045,
                height * 0.032,
                materials["wing"],
            )
        )
        objects.append(_smooth_engine_pod(collection, f"MESH_Variant_Outrigger_Engine_{_side_name(side)}", (side * width * 0.70, length * 0.36, -height * 0.06), length * 0.25, width * 0.075 * engine, height * 0.125 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Variant_Outrigger_Glow_{_side_name(side)}", (side * width * 0.70, length * 0.52, -height * 0.06), width * 0.052 * engine, length * 0.018, materials["glow"]))
    return objects


def _create_twinboom_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        objects.append(_rounded_pod(collection, f"MESH_Variant_Twinboom_Boom_{_side_name(side)}", (side * width * 0.30, length * 0.34, -height * 0.065), length * 0.24, width * 0.060, height * 0.105, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Variant_Twinboom_Glow_{_side_name(side)}", (side * width * 0.30, length * 0.59, -height * 0.065), width * 0.048 * engine, length * 0.017, materials["glow"]))
        objects.append(_side_tail_fin(collection, f"MESH_Variant_Twinboom_Fin_{_side_name(side)}", side, length, width, height, materials["wing_edge"], z_direction=1))
    return objects


def _create_keel_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects = [
        _tapered_prism(collection, "MESH_Variant_Deep_Keel_Body", (0.0, length * 0.08, -height * 0.58), length * 0.43, width * 0.070, width * 0.150, height * 0.100, height * 0.165, materials["underbody"], bevel=0.012),
        _raised_strip_y(collection, "MESH_Variant_Keel_Center_Glow", (0.0, length * 0.04, -height * 0.755), length * 0.32, width * 0.014, height * 0.010, materials["glow"]),
    ]
    for side in (-1, 1):
        objects.append(_raised_strip_y(collection, f"MESH_Variant_Keel_Radiator_{_side_name(side)}", (side * width * 0.105, length * 0.10, -height * 0.705), length * 0.28, width * 0.012, height * 0.008, materials["engine_shell"]))
    return objects


def _create_broadwing_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    wing = dimensions["wing"]
    objects: list[bpy.types.Object] = []
    for side in (-1, 1):
        objects.append(
            _hard_airfoil_plate(
                collection,
                f"MESH_Variant_Broadwing_Outer_Wing_{_side_name(side)}",
                [
                    (side * width * 0.30, -length * 0.12),
                    (side * width * (0.74 + wing * 0.060), -length * 0.04),
                    (side * width * (0.90 + wing * 0.070), length * 0.18),
                    (side * width * 0.46, length * 0.17),
                ],
                -height * 0.090,
                height * 0.052,
                materials["wing"],
            )
        )
        objects.append(_rounded_pod(collection, f"MESH_Variant_Broadwing_Tip_Pod_{_side_name(side)}", (side * width * (0.92 + wing * 0.08), length * 0.12, -height * 0.055), length * 0.090, width * 0.030, height * 0.055, materials["system_bay"]))
    return objects


def _create_carrier_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    for index, y_factor in enumerate((-0.20, 0.02, 0.24), start=1):
        bay_y = length * y_factor
        bay_z = _hull_top_z(length, width, height, 0.0, bay_y, clearance=height * 0.11)
        objects.append(_box(collection, f"MESH_Variant_Carrier_Dorsal_Bay_{index:02d}", (0.0, bay_y, bay_z), (width * 0.20, length * 0.065, height * 0.060), materials["system_bay"], bevel=0.008))
        for side in (-1, 1):
            objects.append(_box(collection, f"MESH_Variant_Carrier_Side_Bay_{_side_name(side)}_{index:02d}", (side * width * 0.40, bay_y, _hull_side_z(length, width, height, side * width * 0.40, bay_y, clearance=height * 0.035)), (width * 0.080, length * 0.060, height * 0.075), materials["cargo"], bevel=0.007))
    return objects


def _create_compact_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    engine = dimensions["engine"]
    objects = [
        _box(collection, "MESH_Variant_Compact_Shoulder_Block_Left", (-width * 0.26, length * 0.20, height * 0.065), (width * 0.085, length * 0.150, height * 0.070), materials["body_panel"], bevel=0.010),
        _box(collection, "MESH_Variant_Compact_Shoulder_Block_Right", (width * 0.26, length * 0.20, height * 0.065), (width * 0.085, length * 0.150, height * 0.070), materials["body_panel"], bevel=0.010),
    ]
    for index, x_factor in enumerate((-0.30, -0.15, 0.0, 0.15, 0.30), start=1):
        objects.append(_smooth_engine_pod(collection, f"MESH_Variant_Compact_Engine_{index:02d}", (width * x_factor, length * 0.47, -height * 0.020), length * 0.145, width * 0.046 * engine, height * 0.080 * engine, materials["engine_shell"]))
        objects.append(_engine_glow(collection, f"MESH_Variant_Compact_Glow_{index:02d}", (width * x_factor, length * 0.57, -height * 0.020), width * 0.033 * engine, length * 0.014, materials["glow"]))
    return objects


def _create_asymmetric_variant(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    side = -1 if _stable_int_seed(config.seed, config.variant, config.ship_type, "asymmetric_side") % 2 == 0 else 1
    opposite = -side
    mission_y = length * 0.18
    return [
        _hard_airfoil_plate(
            collection,
            f"MESH_Variant_Asymmetric_Load_Boom_{_side_name(side)}",
            [
                (side * width * 0.20, -length * 0.06),
                (side * width * 0.66, length * 0.02),
                (side * width * 0.70, length * 0.32),
                (side * width * 0.26, length * 0.27),
            ],
            -height * 0.040,
            height * 0.030,
            materials["wing"],
        ),
        _rounded_pod(collection, f"MESH_Variant_Asymmetric_Mission_Pod_{_side_name(side)}", (side * width * 0.62, mission_y, -height * 0.09), length * 0.16, width * 0.075, height * 0.105, materials["system_bay"]),
        _smooth_engine_pod(collection, f"MESH_Variant_Asymmetric_Counter_Thruster_{_side_name(opposite)}", (opposite * width * 0.38, length * 0.38, -height * 0.06), length * 0.16, width * 0.060, height * 0.090, materials["engine_shell"]),
        _engine_glow(collection, f"MESH_Variant_Asymmetric_Counter_Glow_{_side_name(opposite)}", (opposite * width * 0.38, length * 0.50, -height * 0.06), width * 0.042, length * 0.014, materials["glow"]),
    ]


def _create_type_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
    rng: random.Random,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    if config.ship_type == "missile_corvette":
        return _create_corvette_signature_variation(collection, materials, dimensions, variation, config)
    if config.ship_type == "freighter":
        return _create_freighter_signature_variation(collection, materials, dimensions, variation, config)
    if config.ship_type == "interceptor":
        return _create_interceptor_signature_variation(collection, materials, dimensions, variation)
    if config.ship_type == "gunship":
        return _create_gunship_signature_variation(collection, materials, dimensions, variation, config)
    return _create_raider_signature_variation(collection, materials, dimensions, variation, rng)


def _create_corvette_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    if variation.key in {"carrier", "hammerhead", "fork"} or config.missile_density > 0.70:
        for index, y_factor in enumerate((-0.24, -0.06, 0.12, 0.30), start=1):
            z = _hull_top_z(length, width, height, 0.0, length * y_factor, clearance=height * 0.16)
            objects.append(_box(collection, f"MESH_Corvette_Variant_VLS_Battery_{index:02d}", (0.0, length * y_factor, z), (width * 0.13, length * 0.046, height * 0.045), materials["ordnance"], bevel=0.006))
    if variation.key in {"outrigger", "twinboom", "broadwing"}:
        for side in (-1, 1):
            objects.append(_rounded_pod(collection, f"MESH_Corvette_Variant_External_Rack_{_side_name(side)}", (side * width * 0.58, length * 0.18, -height * 0.06), length * 0.21, width * 0.050, height * 0.090, materials["ordnance"]))
    return objects


def _create_freighter_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    stack_count = max(1, min(4, round(1 + config.cargo_density * 3)))
    if variation.key in {"carrier", "keel", "compact", "hammerhead"}:
        for index, y_factor in enumerate((-0.24, -0.02, 0.20, 0.40)[:stack_count], start=1):
            objects.append(_box(collection, f"MESH_Freighter_Variant_Raised_Cargo_{index:02d}", (0.0, length * y_factor, height * 0.50), (width * 0.18, length * 0.080, height * 0.095), materials["cargo"], bevel=0.008))
    if variation.key in {"outrigger", "twinboom", "asymmetric"}:
        for side in (-1, 1):
            objects.append(_smooth_engine_pod(collection, f"MESH_Freighter_Variant_Tug_Engine_{_side_name(side)}", (side * width * 0.54, length * 0.48, -height * 0.04), length * 0.20, width * 0.075, height * 0.125, materials["engine_shell"]))
            objects.append(_engine_glow(collection, f"MESH_Freighter_Variant_Tug_Glow_{_side_name(side)}", (side * width * 0.54, length * 0.61, -height * 0.04), width * 0.052, length * 0.018, materials["glow"]))
    return objects


def _create_interceptor_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    if variation.key in {"blade", "fork", "broadwing"}:
        for side in (-1, 1):
            objects.append(_hard_airfoil_plate(collection, f"MESH_Interceptor_Variant_Broad_Canard_{_side_name(side)}", [(side * width * 0.08, -length * 0.48), (side * width * 0.26, -length * 0.45), (side * width * 0.36, -length * 0.34), (side * width * 0.14, -length * 0.36)], height * 0.015, height * 0.028, materials["wing_edge"]))
    if variation.key in {"compact", "twinboom", "outrigger"}:
        for side in (-1, 1):
            objects.append(_smooth_engine_pod(collection, f"MESH_Interceptor_Variant_Wingtip_Booster_{_side_name(side)}", (side * width * 0.48, length * 0.34, -height * 0.075), length * 0.16, width * 0.040, height * 0.070, materials["engine_shell"]))
            objects.append(_engine_glow(collection, f"MESH_Interceptor_Variant_Wingtip_Glow_{_side_name(side)}", (side * width * 0.48, length * 0.45, -height * 0.075), width * 0.030, length * 0.012, materials["glow"]))
    return objects


def _create_gunship_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
    config: ShipGenerationConfig,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    if variation.key in {"hammerhead", "keel", "compact"} or config.weapon_density > 0.80:
        for side in (-1, 1):
            objects.append(_box(collection, f"MESH_Gunship_Variant_Casemate_{_side_name(side)}", (side * width * 0.34, -length * 0.18, _hull_side_z(length, width, height, side * width * 0.34, -length * 0.18, clearance=height * 0.055)), (width * 0.095, length * 0.090, height * 0.080), materials["weapon"], bevel=0.009))
            objects.append(_weapon_barrel(collection, f"MESH_Gunship_Variant_Casemate_Barrel_{_side_name(side)}", (side * width * 0.34, -length * 0.30, -height * 0.025), width * 0.016, length * 0.17, materials["weapon"]))
    if variation.key in {"broadwing", "outrigger"}:
        for side in (-1, 1):
            objects.append(_hard_airfoil_plate(collection, f"MESH_Gunship_Variant_Wide_Stabilizer_{_side_name(side)}", [(side * width * 0.30, length * 0.05), (side * width * 0.70, length * 0.12), (side * width * 0.74, length * 0.34), (side * width * 0.32, length * 0.28)], -height * 0.12, height * 0.038, materials["wing"]))
    return objects


def _create_raider_signature_variation(
    collection: bpy.types.Collection,
    materials: dict[str, bpy.types.Material],
    dimensions: dict[str, float],
    variation: ShipVariation,
    rng: random.Random,
) -> list[bpy.types.Object]:
    length = dimensions["length"]
    width = dimensions["width"]
    height = dimensions["height"]
    objects: list[bpy.types.Object] = []
    if variation.key in {"blade", "fork", "asymmetric"}:
        for side in (-1, 1):
            y = -length * (0.18 + rng.random() * 0.08)
            objects.append(_raised_strip_y(collection, f"MESH_Raider_Variant_Shoulder_Intake_{_side_name(side)}", (side * width * 0.24, y, _hull_top_z(length, width, height, side * width * 0.24, y, clearance=height * 0.030)), length * 0.070, width * 0.018, height * 0.010, materials["engine_shell"]))
    if variation.key in {"carrier", "compact", "hammerhead"}:
        objects.append(_rounded_pod(collection, "MESH_Raider_Variant_Dorsal_Mission_Pod", (0.0, length * 0.16, _hull_top_z(length, width, height, 0.0, length * 0.16, clearance=height * 0.10)), length * 0.15, width * 0.070, height * 0.065, materials["system_bay"]))
    return objects


def _side_tail_fin(
    collection: bpy.types.Collection,
    name: str,
    side: int,
    length: float,
    width: float,
    height: float,
    material: bpy.types.Material,
    *,
    z_direction: int,
) -> bpy.types.Object:
    center_x = side * width * 0.32
    half_width = width * (0.020 if side else 0.028)
    y_front = length * 0.22
    y_back = length * 0.52
    z_root = height * (0.18 if z_direction > 0 else -0.20)
    z_tip = height * (0.62 if z_direction > 0 else -0.60)
    vertices = [
        (center_x - half_width, y_front, z_root),
        (center_x + half_width, y_front, z_root),
        (center_x - half_width, y_back, z_root),
        (center_x + half_width, y_back, z_root),
        (center_x - half_width * 0.60, y_back * 0.90, z_tip),
        (center_x + half_width * 0.60, y_back * 0.90, z_tip),
    ]
    faces = [(0, 2, 4), (1, 5, 3), (0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 1, 0)]
    return _mesh_object(collection, name, vertices, faces, material, bevel=0.012)


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

    objects.extend(_create_teal_light_strips(collection, materials, length, width, height, config))
    objects.extend(_create_engine_cable_runs(collection, materials, length, width, height))
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
    config: ShipGenerationConfig,
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
        if config.ship_type in {"light_raider", "interceptor"}:
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
        else:
            for index, y_factor in enumerate((-0.10, 0.18), start=1):
                x = side * width * (0.30 if config.ship_type == "freighter" else 0.42)
                y = length * y_factor
                objects.append(
                    _raised_strip_y(
                        collection,
                        f"MESH_Teal_System_Light_{'L' if side < 0 else 'R'}_{index:02d}",
                        (x, y, _hull_side_z(length, width, height, x, y, clearance=height * 0.035)),
                        length * 0.055,
                        width * 0.010,
                        height * 0.010,
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
                materials["engine_shell"],
                bevel_depth=width * 0.0045,
            )
        )
    return objects


def _torus_y(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    major_radius: float,
    minor_radius: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    major_segments = 18
    minor_segments = 6
    vertices: list[tuple[float, float, float]] = []
    for major_index in range(major_segments):
        major_angle = 2.0 * pi * major_index / major_segments
        radial = Vector((cos(major_angle), 0.0, sin(major_angle)))
        center = radial * major_radius
        for minor_index in range(minor_segments):
            minor_angle = 2.0 * pi * minor_index / minor_segments
            point = center + radial * (cos(minor_angle) * minor_radius) + Vector((0.0, sin(minor_angle) * minor_radius, 0.0))
            vertices.append((point.x, point.y, point.z))

    faces: list[tuple[int, ...]] = []
    for major_index in range(major_segments):
        next_major = (major_index + 1) % major_segments
        for minor_index in range(minor_segments):
            next_minor = (minor_index + 1) % minor_segments
            faces.append(
                (
                    major_index * minor_segments + minor_index,
                    next_major * minor_segments + minor_index,
                    next_major * minor_segments + next_minor,
                    major_index * minor_segments + next_minor,
                )
            )
    obj = _mesh_object(collection, name, vertices, faces, material, location=location, bevel=max(minor_radius * 0.08, 0.0015))
    obj["void_shipwright_surface_style"] = "faceted_ring"
    return obj


def _antenna(
    collection: bpy.types.Collection,
    name: str,
    location: tuple[float, float, float],
    radius: float,
    height: float,
    material: bpy.types.Material,
) -> bpy.types.Object:
    segments = 6
    vertices: list[tuple[float, float, float]] = []
    for z, ring_radius in ((-height * 0.5, radius * 1.2), (height * 0.5, radius * 0.72)):
        for index in range(segments):
            angle = 2.0 * pi * index / segments
            vertices.append((cos(angle) * ring_radius, sin(angle) * ring_radius, z))
    faces: list[tuple[int, ...]] = [tuple(reversed(range(segments))), tuple(range(segments, segments * 2))]
    for index in range(segments):
        faces.append((index, (index + 1) % segments, ((index + 1) % segments) + segments, index + segments))
    obj = _mesh_object(collection, name, vertices, faces, material, location=location, bevel=max(radius * 0.10, 0.001))
    obj.rotation_euler[0] = pi * 0.08
    obj["void_shipwright_surface_style"] = "faceted_sensor_mast"
    return obj


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
    _assign_box_projected_uvs(mesh)
    obj = bpy.data.objects.new(name, mesh)
    obj.location = location
    obj.data.materials.append(material)
    collection.objects.link(obj)
    if smooth:
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    _add_surface_modifiers(obj, bevel=bevel, subdivision=subdivision)
    obj["void_shipwright_texture_uv"] = "VS_PaintedUV"
    return obj


def _assign_box_projected_uvs(mesh: bpy.types.Mesh) -> None:
    if not mesh.vertices or not mesh.polygons:
        return
    coordinates = [vertex.co.copy() for vertex in mesh.vertices]
    minimum = Vector((min(co.x for co in coordinates), min(co.y for co in coordinates), min(co.z for co in coordinates)))
    maximum = Vector((max(co.x for co in coordinates), max(co.y for co in coordinates), max(co.z for co in coordinates)))
    span = maximum - minimum
    span.x = max(span.x, 0.0001)
    span.y = max(span.y, 0.0001)
    span.z = max(span.z, 0.0001)
    uv_layer = mesh.uv_layers.get("VS_PaintedUV") or mesh.uv_layers.new(name="VS_PaintedUV")

    for polygon in mesh.polygons:
        normal = polygon.normal
        ax = abs(normal.x)
        ay = abs(normal.y)
        az = abs(normal.z)
        for loop_index in polygon.loop_indices:
            vertex = mesh.vertices[mesh.loops[loop_index].vertex_index].co
            if az >= ax and az >= ay:
                u = (vertex.x - minimum.x) / span.x
                v = (vertex.y - minimum.y) / span.y
            elif ax >= ay:
                u = (vertex.y - minimum.y) / span.y
                v = (vertex.z - minimum.z) / span.z
            else:
                u = (vertex.x - minimum.x) / span.x
                v = (vertex.z - minimum.z) / span.z
            uv_layer.data[loop_index].uv = (u, v)
    mesh.update()


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
        modifier.segments = 3 if bevel >= 0.01 else 2
        modifier.profile = 0.45
        modifier.affect = "EDGES"
        if hasattr(modifier, "harden_normals"):
            modifier.harden_normals = True
    if weighted_normals:
        modifier = obj.modifiers.new("VS_WeightedNormals", "WEIGHTED_NORMAL")
        if hasattr(modifier, "keep_sharp"):
            modifier.keep_sharp = True


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

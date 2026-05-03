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
from .validation import validate_detail_level, validate_faction, validate_hull_profile, validate_material_style, validate_role, validate_seed, validate_ship_type


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
    material_style: str = "gunmetal"
    rust_amount: float = 0.22
    scratch_amount: float = 0.55
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


def generate_ship(config: ShipGenerationConfig) -> dict[str, Any]:
    validate_role(config.role)
    validate_faction(config.faction)
    validate_ship_type(config.ship_type)
    validate_hull_profile(config.hull_profile)
    validate_detail_level(config.detail_level)
    validate_material_style(config.material_style)
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
        "base": (0.16, 0.13, 0.10, 1.0),
        "armor": (0.22, 0.18, 0.13, 1.0),
        "trim": (0.070, 0.055, 0.045, 1.0),
        "edge": (0.64, 0.55, 0.43, 1.0),
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


def _create_materials(
    faction: str,
    *,
    glow_strength: float = 1.0,
    config: ShipGenerationConfig | None = None,
) -> dict[str, bpy.types.Material]:
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
    cargo_metal = _mix_color(armor, (0.16, 0.13, 0.10, 1.0), 0.30)
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

    return {
        "hull": _metal_material("VS_Metal_Body_Primary", body_skin, part_profiles["body"], rust_amount=rust_for("body"), scratch_amount=scratch_amount, texture_scale=texture_scale, role_scale=1.0),
        "body": _metal_material("VS_Metal_Body_Primary", body_skin, part_profiles["body"], rust_amount=rust_for("body"), scratch_amount=scratch_amount, texture_scale=texture_scale, role_scale=1.0),
        "body_panel": _metal_material("VS_Metal_Body_Panel_Variation", graphite, part_profiles["body_panel"], rust_amount=rust_for("body_panel", 0.85), scratch_amount=scratch_amount * 0.78, texture_scale=texture_scale * 1.18, role_scale=0.85),
        "wing": _metal_material("VS_Metal_Wing_Skin", wing_skin, part_profiles["wing"], rust_amount=rust_for("wing", 1.10), scratch_amount=scratch_amount * 1.12, texture_scale=texture_scale * 1.34, role_scale=0.72, metallic=part_profiles["wing"]["metallic"], roughness=part_profiles["wing"]["roughness"] + 0.08),
        "wing_edge": _metal_material("VS_Metal_Wing_Edge_Livery", wing_edge, part_profiles["wing_edge"], rust_amount=rust_for("wing_edge", 0.62), scratch_amount=scratch_amount * 1.22, texture_scale=texture_scale * 1.5, role_scale=0.48, metallic=0.22, roughness=0.50),
        "armor": _metal_material("VS_Metal_Armor_Plates", armor_top, part_profiles["armor"], rust_amount=rust_for("armor", 0.9), scratch_amount=scratch_amount, texture_scale=texture_scale * 0.82, role_scale=1.15),
        "armor_top": _metal_material("VS_Metal_Armor_Top_Plates", armor_top, part_profiles["armor_top"], rust_amount=rust_for("armor_top", 0.82), scratch_amount=scratch_amount * 1.05, texture_scale=texture_scale * 0.78, role_scale=1.20),
        "armor_dark": _metal_material("VS_Metal_Dark_Armor_Inset", armor_dark, part_profiles["armor_dark"], rust_amount=rust_for("armor_dark", 1.05), scratch_amount=scratch_amount * 0.70, texture_scale=texture_scale * 1.05, role_scale=0.88),
        "accent": _metal_material("VS_Metal_Faction_Accent", accent_color, part_profiles["decal"], rust_amount=rust_for("decal", 0.55), scratch_amount=scratch_amount * 0.72, texture_scale=texture_scale * 0.75, role_scale=0.75, metallic=max(part_profiles["decal"]["metallic"] - 0.18, 0.18), roughness=max(part_profiles["decal"]["roughness"] - 0.08, 0.18)),
        "trim": _metal_material("VS_Metal_Black_Trim", underbody, part_profiles["underbody"], rust_amount=rust_for("underbody", 1.15), scratch_amount=scratch_amount * 0.85, texture_scale=texture_scale * 1.25, role_scale=0.9, metallic=part_profiles["underbody"]["metallic"], roughness=part_profiles["underbody"]["roughness"] + 0.04),
        "underbody": _metal_material("VS_Metal_Underbody_Black", underbody, part_profiles["underbody"], rust_amount=rust_for("underbody", 1.30), scratch_amount=scratch_amount * 0.62, texture_scale=texture_scale * 1.45, role_scale=0.65, metallic=part_profiles["underbody"]["metallic"], roughness=part_profiles["underbody"]["roughness"] + 0.10),
        "engine_shell": _metal_material("VS_Metal_Engine_Heat_Stained", engine_shell, part_profiles["engine_shell"], rust_amount=rust_for("engine_shell", 0.62), scratch_amount=scratch_amount * 0.80, texture_scale=texture_scale * 1.1, role_scale=0.75, metallic=0.86, roughness=0.38),
        "weapon": _metal_material("VS_Metal_Weapon_Blued_Steel", weapon_metal, part_profiles["weapon"], rust_amount=rust_for("weapon", 0.48), scratch_amount=scratch_amount * 1.30, texture_scale=texture_scale * 1.75, role_scale=0.45, metallic=0.90, roughness=0.34),
        "cargo": _metal_material("VS_Metal_Cargo_Industrial", cargo_metal, part_profiles["cargo"], rust_amount=rust_for("cargo", 1.35), scratch_amount=scratch_amount * 0.58, texture_scale=texture_scale * 0.92, role_scale=1.0, metallic=max(part_profiles["cargo"]["metallic"] - 0.12, 0.32), roughness=part_profiles["cargo"]["roughness"] + 0.14),
        "system_bay": _metal_material("VS_Metal_System_Bay_Module", bay_metal, part_profiles["system_bay"], rust_amount=rust_for("system_bay", 0.95), scratch_amount=scratch_amount * 0.92, texture_scale=texture_scale * 1.16, role_scale=0.9, metallic=part_profiles["system_bay"]["metallic"], roughness=part_profiles["system_bay"]["roughness"] + 0.06),
        "panel": _metal_material("VS_Metal_Deep_Panel_Seams", (0.002, 0.003, 0.004, 1.0), part_profiles["panel"], rust_amount=rust_for("panel", 1.25), scratch_amount=scratch_amount * 0.40, texture_scale=texture_scale * 1.55, role_scale=0.45, metallic=max(part_profiles["panel"]["metallic"] - 0.30, 0.12), roughness=0.78),
        "wear": _metal_material("VS_Metal_Chipped_Edge_Wear", worn_edge, part_profiles["wear"], rust_amount=rust_for("wear", 0.30), scratch_amount=1.0, texture_scale=texture_scale * 1.8, role_scale=0.35, metallic=0.72, roughness=0.42),
        "red_decal": _metal_material("VS_Painted_Raider_Livery", raider_red, part_profiles["decal"], rust_amount=rust_for("decal", 0.45), scratch_amount=scratch_amount * 0.65, texture_scale=texture_scale * 1.2, role_scale=0.55, metallic=0.12, roughness=0.50),
        "ordnance": _metal_material("VS_Metal_Ordnance_Amber", (0.9, 0.48, 0.10, 1.0), part_profiles["ordnance"], rust_amount=rust_for("ordnance", 0.25), scratch_amount=scratch_amount * 0.45, texture_scale=texture_scale, role_scale=0.45, metallic=0.34, roughness=0.42, emission_color=(0.9, 0.28, 0.04, 1.0), emission_strength=0.22 * glow_strength),
        "glass": _material("VS_CanopyGlass", (0.08, 0.32, 0.46, 0.72), alpha=0.72, metallic=0.0, roughness=0.12),
        "glow": _material("VS_EngineGlow", glow_color, emission_color=glow_color, emission_strength=3.5 * glow_strength),
        "window": _material("VS_WindowLights", window_color, emission_color=window_color, emission_strength=2.2 * glow_strength),
        "decal": _material("VS_DesignerDecals", accent_color, emission_color=accent_color, emission_strength=0.35, metallic=0.05, roughness=0.28),
        "collision": _material("VS_CollisionProxy", (0.15, 0.85, 0.45, 0.25), alpha=0.25),
        "marker": _material("VS_Marker", (0.1, 0.55, 1.0, 1.0)),
    }


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
    material["void_shipwright_texture_workflow"] = "object_space_pbr_trim_decal_layered"
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
    mapping.name = "VS_Anisotropic_Object_Mapping"
    if "Scale" in mapping.inputs:
        mapping.inputs["Scale"].default_value = (1.0, 1.62, 0.74)
    if "Object" in texture_coordinates.outputs and "Vector" in mapping.inputs:
        links.new(texture_coordinates.outputs["Object"], mapping.inputs["Vector"])

    def link_vector(texture_node: bpy.types.Node) -> None:
        if "Vector" in texture_node.inputs and "Vector" in mapping.outputs:
            links.new(mapping.outputs["Vector"], texture_node.inputs["Vector"])

    grain_noise = nodes.new("ShaderNodeTexNoise")
    grain_noise.name = "VS_Metal_Grain_Noise"
    grain_noise.inputs["Scale"].default_value = 38.0 * texture_scale * role_scale
    grain_noise.inputs["Detail"].default_value = 15.0
    grain_noise.inputs["Roughness"].default_value = 0.68
    if "Distortion" in grain_noise.inputs:
        grain_noise.inputs["Distortion"].default_value = 0.22 + rust_amount * 0.55
    link_vector(grain_noise)

    color_ramp = nodes.new("ShaderNodeValToRGB")
    color_ramp.name = "VS_Metal_Base_Grain_Ramp"
    rust_start = _clamp(0.92 - rust_amount * 0.46, 0.42, 0.95)
    rust_color = _mix_color(profile["rust"], profile["oxide"], 0.25 + rust_amount * 0.35)
    bright_wear = _mix_color(color, profile["edge"], 0.18 + scratch_amount * 0.30)
    color_ramp.color_ramp.elements[0].position = 0.10
    color_ramp.color_ramp.elements[0].color = _scale_color(color, 0.48 + rust_amount * 0.08)
    color_ramp.color_ramp.elements[1].position = rust_start
    color_ramp.color_ramp.elements[1].color = bright_wear
    rust_element = color_ramp.color_ramp.elements.new(1.0)
    rust_element.color = _mix_color(bright_wear, rust_color, rust_amount)
    links.new(grain_noise.outputs["Fac"], color_ramp.inputs["Fac"])

    rust_voronoi = nodes.new("ShaderNodeTexVoronoi")
    rust_voronoi.name = "VS_Rust_Oxide_Patch_Voronoi"
    rust_voronoi.inputs["Scale"].default_value = 8.0 * texture_scale * max(role_scale, 0.38)
    if "Randomness" in rust_voronoi.inputs:
        rust_voronoi.inputs["Randomness"].default_value = 0.78
    if "Detail" in rust_voronoi.inputs:
        rust_voronoi.inputs["Detail"].default_value = 6.0
    if "Roughness" in rust_voronoi.inputs:
        rust_voronoi.inputs["Roughness"].default_value = 0.58
    link_vector(rust_voronoi)

    rust_mask = nodes.new("ShaderNodeValToRGB")
    rust_mask.name = "VS_Rust_Patch_Mask"
    rust_mask.color_ramp.elements[0].position = _clamp(0.36 - rust_amount * 0.10, 0.12, 0.48)
    rust_mask.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    rust_mask.color_ramp.elements[1].position = _clamp(0.88 - rust_amount * 0.30, 0.52, 0.94)
    rust_mask.color_ramp.elements[1].color = (rust_amount, rust_amount, rust_amount, 1.0)

    rust_patch_color = nodes.new("ShaderNodeValToRGB")
    rust_patch_color.name = "VS_Rust_Oxide_Color_Ramp"
    rust_patch_color.color_ramp.elements[0].position = 0.18
    rust_patch_color.color_ramp.elements[0].color = _mix_color(_scale_color(color, 0.46), profile["oxide"], rust_amount * 0.72)
    rust_patch_color.color_ramp.elements[1].position = 1.0
    rust_patch_color.color_ramp.elements[1].color = rust_color
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
        rough_noise.inputs["Distortion"].default_value = 0.45 + rust_amount
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
    scratch_wave = nodes.new("ShaderNodeTexWave")
    scratch_wave.name = "VS_Directional_Hairline_Scratches"
    scratch_wave.inputs["Scale"].default_value = 52.0 * texture_scale * max(role_scale, 0.35)
    if "Distortion" in scratch_wave.inputs:
        scratch_wave.inputs["Distortion"].default_value = 7.0 * scratch_amount
    if hasattr(scratch_wave, "bands_direction"):
        scratch_wave.bands_direction = "Y"
    link_vector(scratch_wave)
    scratch_isolate = nodes.new("ShaderNodeValToRGB")
    scratch_isolate.name = "VS_Scratch_Line_Isolation"
    scratch_isolate.color_ramp.elements[0].position = 0.55
    scratch_isolate.color_ramp.elements[0].color = (0.0, 0.0, 0.0, 1.0)
    scratch_isolate.color_ramp.elements[1].position = _clamp(0.96 - scratch_amount * 0.10, 0.78, 0.98)
    scratch_isolate.color_ramp.elements[1].color = (scratch_amount, scratch_amount, scratch_amount, 1.0)
    links.new(scratch_wave.outputs["Color"], scratch_isolate.inputs["Fac"])
    bump_height = nodes.new("ShaderNodeMath")
    bump_height.name = "VS_Bump_Combined_Pits_And_Scratches"
    bump_height.operation = "ADD"
    links.new(scratch_noise.outputs["Fac"], bump_height.inputs[0])
    links.new(scratch_isolate.outputs["Color"], bump_height.inputs[1])
    bump = nodes.new("ShaderNodeBump")
    bump.name = "VS_Metal_Bump"
    bump.inputs["Strength"].default_value = 0.035 + scratch_amount * 0.075 + rust_amount * 0.045
    bump.inputs["Distance"].default_value = 0.030 + rust_amount * 0.080
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
        _raider_upper_armor(collection, "MESH_Dorsal_Armor_Shell", length, width, height, materials["armor_top"]),
        _raider_keel(collection, "MESH_Ventral_Keel", length, width, height, materials["underbody"]),
        _raider_cockpit(collection, "MESH_Canopy_Glass", length, width, height, materials["glass"]),
        _raider_wing(collection, "MESH_Wing_Left", -1, length, width, height, wing, materials["wing"]),
        _raider_wing(collection, "MESH_Wing_Right", 1, length, width, height, wing, materials["wing"]),
        _raider_wing_armor(collection, "MESH_Wing_Armor_Left", -1, length, width, height, wing, materials["armor_dark"]),
        _raider_wing_armor(collection, "MESH_Wing_Armor_Right", 1, length, width, height, wing, materials["armor_dark"]),
        _raider_winglet(collection, "MESH_Winglet_Left", -1, length, width, height, wing, materials["wing_edge"]),
        _raider_winglet(collection, "MESH_Winglet_Right", 1, length, width, height, wing, materials["wing_edge"]),
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
        _weapon_barrel(collection, "MESH_Nose_Needle_Left", (-width * 0.18, -length * 0.56, -height * 0.02), width * 0.012, length * 0.34, materials["weapon"]),
        _weapon_barrel(collection, "MESH_Nose_Needle_Right", (width * 0.18, -length * 0.56, -height * 0.02), width * 0.012, length * 0.34, materials["weapon"]),
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
        _tapered_prism(collection, "MESH_Corvette_Blunt_Prow_Armor", (0.0, -length * 0.47, height * 0.08), length * 0.11, width * 0.11, width * 0.30, height * 0.11, height * 0.22, materials["armor_dark"], bevel=0.012),
        _box(collection, "MESH_Corvette_Raised_Command_Spine", (0.0, length * 0.08, height * 0.66), (width * 0.15, length * 0.30, height * 0.12), materials["system_bay"], bevel=0.010),
        _box(collection, "MESH_Corvette_Bridge_Glass", (0.0, -length * 0.22, height * 0.84), (width * 0.10, length * 0.060, height * 0.050), materials["glass"], bevel=0.008),
        _box(collection, "MESH_Corvette_Port_Ordnance_Bay", (-width * 0.45, length * 0.06, height * 0.07), (width * 0.12, length * 0.31, height * 0.20), materials["system_bay"], bevel=0.012),
        _box(collection, "MESH_Corvette_Starboard_Ordnance_Bay", (width * 0.45, length * 0.06, height * 0.07), (width * 0.12, length * 0.31, height * 0.20), materials["system_bay"], bevel=0.012),
        _box(collection, "MESH_Corvette_Rear_Reactor_Block", (0.0, length * 0.43, -height * 0.02), (width * 0.30, length * 0.12, height * 0.22 * engine), materials["engine_shell"], bevel=0.012),
        _box(collection, "MESH_Corvette_Ventral_Belly_Armor", (0.0, length * 0.10, -height * 0.42), (width * 0.22, length * 0.36, height * 0.11), materials["underbody"], bevel=0.010),
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
    objects.extend(_lance_assembly(collection, "MESH_Interceptor_Centerline_Lance", (0.0, -length * 0.66, -height * 0.015), width * 0.010, length * 0.52, materials["weapon"]))
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
        _plate_prism(collection, "MESH_Gunship_Dorsal_Armor_Slab", [(-width * 0.26, -length * 0.36), (width * 0.26, -length * 0.36), (width * 0.34, length * 0.30), (width * 0.18, length * 0.50), (-width * 0.18, length * 0.50), (-width * 0.34, length * 0.30)], height * 0.44, height * 0.055, materials["armor_top"], bevel=0.014),
        _box(collection, "MESH_Gunship_Bridge_Armored_Glass", (0.0, -length * 0.24, height * 0.52), (width * 0.12, length * 0.060, height * 0.040), materials["glass"], bevel=0.008),
        _box(collection, "MESH_Gunship_Left_Weapon_Sponson", (-width * 0.44, -length * 0.02, -height * 0.02), (width * 0.10, length * 0.28, height * 0.13), materials["weapon"], bevel=0.010),
        _box(collection, "MESH_Gunship_Right_Weapon_Sponson", (width * 0.44, -length * 0.02, -height * 0.02), (width * 0.10, length * 0.28, height * 0.13), materials["weapon"], bevel=0.010),
        _smooth_engine_pod(collection, "MESH_Gunship_Engine_Left", (-width * 0.22, length * 0.46, -height * 0.05), length * 0.24, width * 0.10 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Gunship_Glow_Left", (-width * 0.22, length * 0.61, -height * 0.05), width * 0.070 * engine, length * 0.024, materials["glow"]),
        _smooth_engine_pod(collection, "MESH_Gunship_Engine_Right", (width * 0.22, length * 0.46, -height * 0.05), length * 0.24, width * 0.10 * engine, height * 0.18 * engine, materials["engine_shell"]),
        _engine_glow(collection, "MESH_Gunship_Glow_Right", (width * 0.22, length * 0.61, -height * 0.05), width * 0.070 * engine, length * 0.024, materials["glow"]),
    ]
    for side in (-1, 1):
        objects.append(_hard_airfoil_plate(collection, f"MESH_Gunship_Armored_Stub_Wing_{'Left' if side < 0 else 'Right'}", [(side * width * 0.24, -length * 0.20), (side * width * 0.55, -length * 0.10), (side * width * 0.60, length * 0.16), (side * width * 0.24, length * 0.22)], -height * 0.09, height * 0.045, materials["wing"]))
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
        (-length * 0.72, width * 0.010, height * 0.018, -height * 0.015, 0.0),
        (-length * 0.58, width * 0.035, height * 0.060, -height * 0.010, 0.0),
        (-length * 0.34, width * 0.095, height * 0.150, height * 0.005, offset),
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
        (side * width * 0.12, -length * 0.20),
        (side * width * (0.46 + wing * 0.08), -length * 0.07),
        (side * width * (0.86 + wing * 0.10), length * 0.22),
        (side * width * 0.36, length * 0.12),
        (side * width * 0.18, length * 0.35),
    ]
    return _hard_airfoil_plate(collection, name, outline, -height * 0.065, height * 0.026, material)


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
        objects.append(_angular_surface_greeble(collection, f"MESH_Greeble_Left_{index:02d}", -x, y, left_z, sx, sy, sz, -1, materials["system_bay"]))
        objects.append(_angular_surface_greeble(collection, f"MESH_Greeble_Right_{index:02d}", x, y, right_z, sx, sy, sz, 1, materials["system_bay"]))
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
        objects.append(
            _rounded_pod(
                collection,
                "MESH_Boss_Armor_Belt",
                (0.0, length * 0.06, height * 0.02),
                length * 0.22,
                width * 0.42,
                height * 0.08,
                materials["armor_dark"],
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
        for index, y_factor in enumerate((-0.2, -0.02, 0.16), start=1):
            objects.append(
                _spike(
                    collection,
                    f"MESH_Raider_Spike_Left_{index:02d}",
                    (-width * 0.38, length * y_factor, height * 0.04),
                    -1,
                    width * 0.16,
                    height * 0.05,
                    materials["weapon"],
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
                    materials["weapon"],
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
                    materials["armor_top"],
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
        objects.extend(_lance_assembly(collection, f"MESH_Interceptor_Lance_{'L' if side < 0 else 'R'}", (side * width * 0.26, -length * 0.58, -height * 0.02), width * 0.010, length * 0.38, materials["weapon"]))
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
    objects.extend(_create_teal_light_strips(collection, materials, length, width, height, config))
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
        objects.append(_plate_prism(collection, f"MESH_Armor_Top_Tile_{index:02d}", outline, tile_z, height * 0.010, materials["armor_top"], bevel=0.006))

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
                    materials["armor_dark"],
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
    if config.ship_type not in {"light_raider", "interceptor"}:
        count = max(0, min(6, round(4 * _detail_multiplier(config.detail_level) * config.decal_density)))
        for index in range(count):
            side = -1 if index % 2 == 0 else 1
            x0 = side * width * (0.18 + 0.04 * (index % 3))
            y0 = length * (-0.30 + index * 0.11)
            x1 = side * width * (0.32 + 0.05 * (index % 2))
            y1 = y0 + length * 0.045
            objects.append(
                _curve_path(
                    collection,
                    f"MESH_Hull_Livery_Stripe_{index + 1:02d}",
                    [
                        (x0, y0, _hull_top_z(length, width, height, x0, y0, clearance=height * 0.018)),
                        (x1, y1, _hull_top_z(length, width, height, x1, y1, clearance=height * 0.018)),
                    ],
                    materials["red_decal"],
                    bevel_depth=width * 0.0045,
                )
            )
        return objects

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

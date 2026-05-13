"""Scene properties used by the Void Shipwright panel and operators."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty, StringProperty

from .constants import VALID_FACTIONS, VALID_HULL_PROFILES, VALID_MATERIAL_STYLES, VALID_ROLES, VALID_SHIP_TYPES, VALID_TEXTURE_WORKFLOWS


def _enum_items(values: tuple[str, ...]) -> list[tuple[str, str, str]]:
    return [(value, value.replace("_", " ").title(), value) for value in values]


DETAIL_LEVELS = (
    ("low", "Low", "Sparse surface detail"),
    ("medium", "Medium", "Balanced surface detail"),
    ("high", "High", "Dense professional hard-surface detail"),
    ("hero", "Hero", "Maximum texture, wear, and micro detail"),
)

HULL_PROFILE_LABELS = {
    "raider": ("Raider", "Long aggressive ambusher proportions with blunted hard-surface wings"),
    "needle": ("Slim", "Extra long and narrow silhouette with reduced pointiness"),
    "heavy": ("Heavy", "Broader reinforced silhouette"),
    "cargo": ("Cargo", "Longer utility silhouette with more mass"),
}

SHIP_TYPE_LABELS = {
    "light_raider": ("Light Raider", "Fast hit-and-run raider with clipped hard-surface wings and compact guns"),
    "missile_corvette": ("Missile Corvette", "Heavy area-denial corvette with missile banks and stabilizers"),
    "interceptor": ("Interceptor", "Lean pursuit ship with oversized engines"),
    "gunship": ("Gunship", "Broad weapons platform with heavy mounts"),
    "freighter": ("Freighter", "Utility hull with cargo pods and civilian massing"),
    "heavy_fighter": ("Heavy Fighter", "Twin-engine combat craft with broad shoulders and heavy weapon mounts"),
    "bomber": ("Bomber", "Long strike craft with internal ordnance bay and reinforced keel"),
    "patrol_cutter": ("Patrol Cutter", "Small naval/security ship with command deck, cutter prow, and utility racks"),
    "explorer": ("Explorer", "Survey ship with long-range sensor booms and extended fuel modules"),
    "dropship": ("Dropship", "Reinforced troop transport with side doors, belly ramp, and lift engines"),
    "mining_ship": ("Mining Ship", "Industrial extractor with forward cutter boom and ore containers"),
    "salvage_ship": ("Salvage Ship", "Recovery craft with asymmetrical processing bay and grappler arms"),
    "medical_ship": ("Medical Ship", "Rescue support craft with triage bay, life-support pods, and clean panels"),
    "racing_ship": ("Racing Ship", "Slim racing hull with oversized thrust pods and clipped wings"),
    "luxury_yacht": ("Luxury Yacht", "Sleek touring ship with panoramic glass and smooth nacelles"),
}

MATERIAL_STYLE_LABELS = {
    "gunmetal": ("Gunmetal", "Dark blued metal with oily wear and sharp bright edges"),
    "worn_steel": ("Worn Steel", "Brighter bare steel with brushed grain and scratches"),
    "dark_titanium": ("Dark Titanium", "Low-reflectance military alloy with subtle blue-gray variation"),
    "rusted_iron": ("Rusted Iron", "Aged industrial iron with oxide patches and rough corrosion"),
    "oxidized_copper": ("Oxidized Copper", "Warm copper/bronze with green-blue oxidation in recesses"),
    "painted_composite": ("Painted Composite", "Painted composite over metal with exposed chipped edges"),
}

TEXTURE_WORKFLOW_LABELS = {
    "painted": ("Painted Textures", "Generate packed image texture maps with painted metal, panel lines, chips, rust, roughness, and normal detail"),
    "procedural_shader": ("Procedural Shader", "Use Blender shader nodes instead of generated image texture maps"),
}

HULL_PROFILES = tuple((value, *HULL_PROFILE_LABELS[value]) for value in VALID_HULL_PROFILES)
SHIP_TYPES = tuple((value, *SHIP_TYPE_LABELS[value]) for value in VALID_SHIP_TYPES)
MATERIAL_STYLES = tuple((value, *MATERIAL_STYLE_LABELS[value]) for value in VALID_MATERIAL_STYLES)
TEXTURE_WORKFLOWS = tuple((value, *TEXTURE_WORKFLOW_LABELS[value]) for value in VALID_TEXTURE_WORKFLOWS)


class VoidShipwrightSettings(bpy.types.PropertyGroup):
    ship_type: EnumProperty(
        name="Ship Type",
        description="High-level visual and equipment archetype",
        items=SHIP_TYPES,
        default="light_raider",
    )
    role: EnumProperty(
        name="Role",
        description="Gameplay role for metadata and sizing",
        items=_enum_items(VALID_ROLES),
        default="enemy",
    )
    faction: EnumProperty(
        name="Faction",
        description="Faction style profile",
        items=_enum_items(VALID_FACTIONS),
        default="pirate_clan",
    )
    seed: IntProperty(
        name="Seed",
        description="Deterministic generation seed",
        default=1,
        min=0,
    )
    ship_id: StringProperty(
        name="Ship ID",
        description="Stable ID written to generated metadata",
        default="light_raider",
    )
    variant: StringProperty(
        name="Variant",
        description="Visual variant preset or seed salt. Presets: blade, fork, hammerhead, outrigger, twinboom, keel, broadwing, carrier, compact, asymmetric",
        default="default",
    )
    metadata_path: StringProperty(
        name="Metadata Path",
        description="Path for generated ship metadata JSON",
        default="//generated_ship.metadata.json",
        subtype="FILE_PATH",
    )
    clear_existing: BoolProperty(
        name="Clear Existing",
        description="Clear the generated collection before creating a new ship",
        default=True,
    )
    detail_level: EnumProperty(
        name="Detail",
        description="Overall generated visual detail budget",
        items=DETAIL_LEVELS,
        default="hero",
    )
    hull_profile: EnumProperty(
        name="Hull Profile",
        description="Primary silhouette family",
        items=HULL_PROFILES,
        default="raider",
    )
    wing_span: FloatProperty(
        name="Wing Span",
        description="Scale wing reach without changing hull size",
        default=1.0,
        min=0.45,
        max=1.8,
    )
    engine_scale: FloatProperty(
        name="Engine Scale",
        description="Scale visible engine pods and exhaust glow",
        default=1.0,
        min=0.5,
        max=1.8,
    )
    hull_length: FloatProperty(
        name="Hull Length",
        description="Designer scale for front-to-back hull length",
        default=1.0,
        min=0.55,
        max=1.8,
    )
    hull_width: FloatProperty(
        name="Hull Width",
        description="Designer scale for side-to-side hull mass",
        default=1.0,
        min=0.55,
        max=1.8,
    )
    hull_height: FloatProperty(
        name="Hull Height",
        description="Designer scale for vertical hull mass",
        default=1.0,
        min=0.55,
        max=1.8,
    )
    structure_density: FloatProperty(
        name="Structure Density",
        description="Amount of attached beveled corner blocks, hull shoulders, side chines, and frame structures",
        default=0.85,
        min=0.0,
        max=1.0,
    )
    decal_density: FloatProperty(
        name="Decal Density",
        description="How much painted livery and striping is generated",
        default=1.0,
        min=0.0,
        max=1.0,
    )
    wear_amount: FloatProperty(
        name="Wear Amount",
        description="Amount of chipped paint and bright edge scuffs",
        default=0.65,
        min=0.0,
        max=1.0,
    )
    glow_strength: FloatProperty(
        name="Glow Strength",
        description="Intensity of teal engines, windows, and light strips",
        default=1.2,
        min=0.0,
        max=3.0,
    )
    material_style: EnumProperty(
        name="Material Style",
        description="Metal texture color/material family",
        items=MATERIAL_STYLES,
        default="gunmetal",
    )
    texture_workflow: EnumProperty(
        name="Texture Workflow",
        description="How visible ship surface textures are generated",
        items=TEXTURE_WORKFLOWS,
        default="painted",
    )
    texture_resolution: IntProperty(
        name="Texture Resolution",
        description="Size of each exported painted material map. 256 uses half-resolution CPU painting and upscales for faster generation",
        default=256,
        min=64,
        max=256,
        step=64,
    )
    rust_amount: FloatProperty(
        name="Rust",
        description="Amount of rust, oxidation, and brown/green corrosion in metal textures",
        default=0.08,
        min=0.0,
        max=1.0,
    )
    scratch_amount: FloatProperty(
        name="Scratches",
        description="Amount of bright scratched metal and high-frequency brushed wear",
        default=0.42,
        min=0.0,
        max=1.0,
    )
    texture_scale: FloatProperty(
        name="Texture Scale",
        description="Scale of metal grain, painted panel lines, rust patches, and scratch detail",
        default=1.0,
        min=0.25,
        max=3.0,
    )
    weapon_density: FloatProperty(
        name="Weapon Density",
        description="How many gun barrels and weapon details are generated",
        default=0.75,
        min=0.0,
        max=1.0,
    )
    missile_density: FloatProperty(
        name="Missile Density",
        description="How many missile pods and ordnance cells are generated",
        default=0.65,
        min=0.0,
        max=1.0,
    )
    cargo_density: FloatProperty(
        name="Cargo Density",
        description="How many cargo, tank, bay, and utility modules are generated",
        default=0.2,
        min=0.0,
        max=1.0,
    )
    asymmetry: FloatProperty(
        name="Asymmetry",
        description="Amount of one-sided salvage, pod, and detail variation",
        default=0.15,
        min=0.0,
        max=1.0,
    )
    use_custom_colors: BoolProperty(
        name="Custom Colors",
        description="Use the color pickers below instead of the faction palette",
        default=False,
    )
    primary_hue: FloatVectorProperty(
        name="Primary Color",
        description="Override hull tint",
        subtype="COLOR",
        size=3,
        default=(0.03, 0.035, 0.04),
        min=0.0,
        max=1.0,
    )
    accent_hue: FloatVectorProperty(
        name="Accent Color",
        description="Override paint/decal accent tint",
        subtype="COLOR",
        size=3,
        default=(0.72, 0.055, 0.035),
        min=0.0,
        max=1.0,
    )
    emissive_hue: FloatVectorProperty(
        name="Emissive Color",
        description="Override engine/window light color",
        subtype="COLOR",
        size=3,
        default=(0.0, 0.92, 1.0),
        min=0.0,
        max=1.0,
    )
    show_helpers: BoolProperty(
        name="Show Helpers",
        description="Show sockets, collision proxies, damage markers, and other technical helpers",
        default=False,
    )
    presentation_scene: BoolProperty(
        name="Presentation Scene",
        description="Create preview camera and lighting after generation",
        default=True,
    )


CLASSES = (VoidShipwrightSettings,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.void_shipwright_settings = PointerProperty(type=VoidShipwrightSettings)


def unregister() -> None:
    if hasattr(bpy.types.Scene, "void_shipwright_settings"):
        del bpy.types.Scene.void_shipwright_settings
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

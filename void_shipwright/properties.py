"""Scene properties used by the Void Shipwright panel and operators."""

from __future__ import annotations

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, PointerProperty, StringProperty

from .constants import VALID_FACTIONS, VALID_HULL_PROFILES, VALID_MATERIAL_STYLES, VALID_ROLES, VALID_SHIP_TYPES, VALID_TEXTURE_WORKFLOWS
from .design_language import VALID_DESIGN_LANGUAGES, VALID_SILHOUETTE_BIASES, VALID_VISUAL_QUALITIES
from .material_library import VALID_MATERIAL_COMPLEXITIES, VALID_TEXTURE_QUALITIES
from .modular import VALID_SHIP_FRAMES


def _enum_items(values: tuple[str, ...]) -> list[tuple[str, str, str]]:
    return [(value, value.replace("_", " ").title(), value) for value in values]


DETAIL_LEVELS = (
    ("low", "Low", "Sparse surface detail"),
    ("medium", "Medium", "Balanced surface detail"),
    ("high", "High", "Dense professional hard-surface detail"),
    ("hero", "Hero", "Maximum texture, wear, and micro detail"),
)

VISUAL_QUALITY_LABELS = {
    "draft": ("Draft", "Fast layout pass with strong silhouette and reduced tertiary geometry"),
    "standard": ("Standard", "Balanced silhouette, secondary forms, and export-safe details"),
    "hero": ("Hero", "Screenshot-grade hard-surface hierarchy with dense connected geometry"),
    "cinematic": ("Cinematic", "Maximum designed silhouette, engine, bridge, armor, panel, and scale-detail geometry"),
}

DESIGN_LANGUAGE_LABELS = {
    "auto": ("Auto", "Choose art direction from ship type and faction"),
    "military": ("Military", "Wedge forms, organized armor belts, turret decks, and command structures"),
    "pirate": ("Pirate", "Aggressive asymmetry, patched armor, exposed engines, and field repairs"),
    "industrial": ("Industrial", "Utility frames, radiator racks, ore/cargo structures, and service hardware"),
    "luxury": ("Luxury", "Clean elegant surfaces, panoramic glass, smooth nacelles, and premium trim"),
    "ancient": ("Ancient", "Unusual arched symmetry, relic rings, glowing seams, and alien-like structure"),
    "racing": ("Racing", "Needle fuselages, blade canards, and oversized speed-focused engines"),
    "cargo": ("Cargo", "Spine-and-module construction with containers, rails, and loading latches"),
}

SILHOUETTE_BIAS_LABELS = {
    "balanced": ("Balanced", "Use the selected ship type's natural proportions"),
    "sleek": ("Sleek", "Longer and narrower silhouette with cleaner secondary mass"),
    "broad": ("Broad", "Wider shoulder mass, side sponsons, and larger engine banks"),
    "tall": ("Tall", "Stronger command tower, dorsal structure, and ventral keel"),
    "asymmetric": ("Asymmetric", "Controlled one-sided modules and salvage/pirate variation"),
    "capital": ("Capital", "Larger multi-section massing with terraces, bays, and engine clusters"),
}

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
    "boarding_frigate": ("Boarding Frigate", "Reinforced boarding craft with grapples and docking sockets"),
    "freighter": ("Freighter", "Utility hull with cargo pods and civilian massing"),
    "heavy_cruiser": ("Heavy Cruiser", "Large multi-engine combat hull with turrets and heavy systems"),
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
    "boss_capital_ship": ("Boss Capital Ship", "Large multi-section boss hull with capital hardpoints"),
}

SHIP_FRAME_LABELS = {
    "light_raider": ("Light Raider", "Small fast combat frame"),
    "interceptor": ("Interceptor", "High-speed pursuit frame"),
    "gunship": ("Gunship", "Weapon-heavy escort frame"),
    "boarding_frigate": ("Boarding Frigate", "Boarding and docking assault frame"),
    "missile_corvette": ("Missile Corvette", "Ordnance-focused corvette frame"),
    "freighter": ("Freighter", "Cargo and logistics frame"),
    "heavy_cruiser": ("Heavy Cruiser", "Large turret and component-heavy combat frame"),
    "mining_ship": ("Mining Ship", "Industrial mining frame"),
    "salvage_ship": ("Salvage Ship", "Industrial recovery frame"),
    "medical_ship": ("Medical Ship", "Support and rescue frame"),
    "racing_ship": ("Racing Ship", "Competition speed frame"),
    "luxury_yacht": ("Luxury Yacht", "Civilian premium utility frame"),
    "boss_capital_ship": ("Boss Capital Ship", "Oversized boss encounter frame"),
}

HARDPOINT_PRESETS = (
    ("frame_default", "Frame Default", "Use the frame's full default hardpoint layout"),
    ("minimal", "Minimal", "Generate only required hardpoints"),
    ("combat", "Combat", "Prefer weapons, turrets, missiles, and countermeasures"),
    ("industrial", "Industrial", "Prefer utility, mining, salvage, tractor, scanner, and cargo hardpoints"),
)

COMPONENT_SLOT_PRESETS = (
    ("frame_default", "Frame Default", "Use the frame's default component slots"),
    ("minimal", "Minimal", "Generate only required component slots"),
    ("expanded", "Expanded", "Generate all component slots for the frame"),
)

MATERIAL_STYLE_LABELS = {
    "auto": ("Auto From Class/Faction", "Choose a premium material preset from ship class and faction"),
    "gunmetal": ("Gunmetal", "Dark blued metal with oily wear and sharp bright edges"),
    "worn_steel": ("Worn Steel", "Brighter bare steel with brushed grain and scratches"),
    "dark_titanium": ("Dark Titanium", "Low-reflectance military alloy with subtle blue-gray variation"),
    "rusted_iron": ("Rusted Iron", "Aged industrial iron with oxide patches and rough corrosion"),
    "oxidized_copper": ("Oxidized Copper", "Warm copper/bronze with green-blue oxidation in recesses"),
    "painted_composite": ("Painted Composite", "Painted composite over metal with exposed chipped edges"),
    "naval_ceramic_armor": ("Naval Ceramic Armor", "Satin ceramic armor over aerospace structure with clean military wear"),
    "corporate_white_composite": ("Corporate White Composite", "Clean white composite panels with precise tactical trim"),
    "dark_military_titanium": ("Dark Military Titanium", "Premium anodized titanium plating with cool roughness breakup"),
    "black_ops_stealth": ("Black Ops Stealth", "Matte absorber panels with low-visibility markings"),
    "luxury_pearl_alloy": ("Luxury Pearl Alloy", "Pearl composite over brushed metal trim and very clean wear"),
    "racing_carbon_composite": ("Racing Carbon Composite", "Glossy dark composite with sport livery and low grime"),
    "industrial_hazard_plating": ("Industrial Hazard Plating", "Industrial yellow plating with hazard markings and utility grime"),
    "pirate_salvaged_metal": ("Pirate Salvaged Metal", "Mixed salvaged plates, patched paint, exposed metal, and warm wear"),
    "ancient_iridescent_alloy": ("Ancient Iridescent Alloy", "Clean alien alloy with turquoise/gold highlights and glowing seams"),
    "mining_worn_industrial": ("Mining Worn Industrial", "Dusty worn industrial paint with ore grime and heat-scuffed hardware"),
    "medical_rescue_composite": ("Medical Rescue Composite", "Clean rescue white composite with emergency markings and strobes"),
    "trade_consortium_cargo_paint": ("Trade Consortium Cargo Paint", "Cargo paint, loading scuffs, warning stripes, and logistics labels"),
}

TEXTURE_QUALITY_LABELS = {
    "low": ("Low 256", "Generate 256px export maps with premium masks sampled cheaply"),
    "standard": ("Standard 512", "Generate 512px export maps for normal design iteration"),
    "hero": ("Hero 1024", "Generate 1024px export maps for screenshots and hero assets"),
    "cinematic": ("Cinematic 2048", "Generate 2048px export maps; expensive but useful for close screenshots"),
}

MATERIAL_COMPLEXITY_LABELS = {
    "low": ("Low", "Base PBR layers with reduced masks"),
    "medium": ("Medium", "Balanced paint, roughness, normal, and decal layering"),
    "high": ("High", "Dense layered aerospace material response"),
    "ultra": ("Ultra", "Maximum masks and map variation for cinematic closeups"),
}

TEXTURE_WORKFLOW_LABELS = {
    "painted": ("Painted Textures", "Generate packed image texture maps with painted metal, panel lines, chips, rust, roughness, and normal detail"),
    "procedural_shader": ("Procedural Shader", "Use Blender shader nodes instead of generated image texture maps"),
}

HULL_PROFILES = tuple((value, *HULL_PROFILE_LABELS[value]) for value in VALID_HULL_PROFILES)
SHIP_TYPES = tuple((value, *SHIP_TYPE_LABELS[value]) for value in VALID_SHIP_TYPES)
SHIP_FRAMES = (("auto", "Auto From Ship Type", "Use the selected ship type's default frame"),) + tuple((value, *SHIP_FRAME_LABELS[value]) for value in VALID_SHIP_FRAMES)
MATERIAL_STYLES = tuple((value, *MATERIAL_STYLE_LABELS[value]) for value in VALID_MATERIAL_STYLES)
TEXTURE_WORKFLOWS = tuple((value, *TEXTURE_WORKFLOW_LABELS[value]) for value in VALID_TEXTURE_WORKFLOWS)
TEXTURE_QUALITIES = tuple((value, *TEXTURE_QUALITY_LABELS[value]) for value in VALID_TEXTURE_QUALITIES)
MATERIAL_COMPLEXITIES = tuple((value, *MATERIAL_COMPLEXITY_LABELS[value]) for value in VALID_MATERIAL_COMPLEXITIES)
VISUAL_QUALITIES = tuple((value, *VISUAL_QUALITY_LABELS[value]) for value in VALID_VISUAL_QUALITIES)
DESIGN_LANGUAGES = tuple((value, *DESIGN_LANGUAGE_LABELS[value]) for value in VALID_DESIGN_LANGUAGES)
SILHOUETTE_BIASES = tuple((value, *SILHOUETTE_BIAS_LABELS[value]) for value in VALID_SILHOUETTE_BIASES)


class VoidShipwrightSettings(bpy.types.PropertyGroup):
    ship_type: EnumProperty(
        name="Ship Type",
        description="High-level visual and equipment archetype",
        items=SHIP_TYPES,
        default="light_raider",
    )
    ship_frame: EnumProperty(
        name="Ship Frame",
        description="Runtime frame used for stats, hardpoints, components, and default loadout metadata",
        items=SHIP_FRAMES,
        default="auto",
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
        description="Visual variant preset or seed salt. Supports classic and cinematic presets such as arrowhead, manta, cathedral_capital, ring_engine, and railgun_spine",
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
    visual_quality: EnumProperty(
        name="Visual Quality",
        description="Art-quality mode for silhouette hierarchy and connected hard-surface geometry",
        items=VISUAL_QUALITIES,
        default="hero",
    )
    design_language: EnumProperty(
        name="Design Language",
        description="Art-direction grammar used for ship proportions, secondary forms, and geometry detail",
        items=DESIGN_LANGUAGES,
        default="auto",
    )
    silhouette_bias: EnumProperty(
        name="Silhouette Bias",
        description="Designer override for primary massing and silhouette intent",
        items=SILHOUETTE_BIASES,
        default="balanced",
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
    surface_geometry_density: FloatProperty(
        name="Surface Geometry",
        description="Amount of connected tertiary mesh panels, vents, ribs, and service details",
        default=0.80,
        min=0.0,
        max=1.0,
    )
    armor_layer_density: FloatProperty(
        name="Armor Layers",
        description="Amount of layered armor terraces and overlapping shell geometry",
        default=0.70,
        min=0.0,
        max=1.0,
    )
    panel_geometry_density: FloatProperty(
        name="Panel Geometry",
        description="Amount of physical recessed panels, cutlines, latches, and hatch geometry",
        default=0.70,
        min=0.0,
        max=1.0,
    )
    engine_complexity: FloatProperty(
        name="Engine Complexity",
        description="Amount of nacelle fairings, heat rings, nozzle clusters, and radiator geometry",
        default=0.90,
        min=0.0,
        max=1.0,
    )
    cockpit_bridge_complexity: FloatProperty(
        name="Bridge Complexity",
        description="Amount of cockpit, bridge, citadel, window strip, and sensor geometry",
        default=0.80,
        min=0.0,
        max=1.0,
    )
    faction_geometry_influence: FloatProperty(
        name="Faction Geometry",
        description="How strongly faction art direction modifies ship geometry",
        default=0.80,
        min=0.0,
        max=1.0,
    )
    avoid_boxy_shapes: BoolProperty(
        name="Avoid Boxy Shapes",
        description="Bias generation toward tapered, beveled, layered silhouettes and validate against flat slabs",
        default=True,
    )
    hardpoint_preset: EnumProperty(
        name="Hardpoint Preset",
        description="Which hardpoint layout subset to export",
        items=HARDPOINT_PRESETS,
        default="frame_default",
    )
    component_slot_preset: EnumProperty(
        name="Component Preset",
        description="Which component slot layout subset to export",
        items=COMPONENT_SLOT_PRESETS,
        default="frame_default",
    )
    generate_loadout_metadata: BoolProperty(
        name="Loadout Metadata",
        description="Include default equipment and component recommendations in metadata",
        default=True,
    )
    show_hardpoint_helpers: BoolProperty(
        name="Show Hardpoints",
        description="Keep SOCKET_HP hardpoint helpers visible even when other helper markers are hidden",
        default=False,
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
        description="PBR material preset and faction/class surface language",
        items=MATERIAL_STYLES,
        default="auto",
    )
    texture_workflow: EnumProperty(
        name="Texture Workflow",
        description="How visible ship surface textures are generated",
        items=TEXTURE_WORKFLOWS,
        default="painted",
    )
    texture_quality: EnumProperty(
        name="Texture Quality",
        description="Generated PBR texture map size target",
        items=TEXTURE_QUALITIES,
        default="standard",
    )
    texture_resolution: IntProperty(
        name="Texture Resolution",
        description="Custom generated map size. Texture Quality sets the recommended target; raising this value can request larger maps for tests or screenshots",
        default=512,
        min=64,
        max=2048,
        step=64,
    )
    material_complexity: EnumProperty(
        name="Material Complexity",
        description="Layer count for paint, roughness, normal, decal, dirt, heat, and mask generation",
        items=MATERIAL_COMPLEXITIES,
        default="high",
    )
    paint_layer_strength: FloatProperty(
        name="Paint Layer",
        description="Strength of paint over metal/composite substrate",
        default=0.82,
        min=0.0,
        max=1.0,
    )
    roughness_variation: FloatProperty(
        name="Roughness Variation",
        description="Broad and micro roughness breakup across panels",
        default=0.65,
        min=0.0,
        max=1.0,
    )
    metallic_variation: FloatProperty(
        name="Metallic Variation",
        description="Panel-by-panel and exposed-edge metallic variation",
        default=0.45,
        min=0.0,
        max=1.0,
    )
    edge_wear_amount: FloatProperty(
        name="Edge Wear",
        description="Controlled exposed-metal wear on panel edges and corners",
        default=0.34,
        min=0.0,
        max=1.0,
    )
    cavity_dirt_amount: FloatProperty(
        name="Cavity Dirt",
        description="Dark dirt collected in recesses, panel seams, vents, and cavities",
        default=0.42,
        min=0.0,
        max=1.0,
    )
    heat_stain_amount: FloatProperty(
        name="Heat Stain",
        description="Blued/browned thermal discoloration on engine and weapon parts",
        default=0.62,
        min=0.0,
        max=1.0,
    )
    soot_amount: FloatProperty(
        name="Soot",
        description="Dark exhaust soot applied mainly to engine and ordnance interiors",
        default=0.28,
        min=0.0,
        max=1.0,
    )
    decal_amount: FloatProperty(
        name="Decals",
        description="Generated serial marks, maintenance blocks, warning labels, and abstract faction markings",
        default=0.45,
        min=0.0,
        max=1.0,
    )
    livery_amount: FloatProperty(
        name="Livery",
        description="Painted faction accent panels and stripe strength",
        default=0.50,
        min=0.0,
        max=1.0,
    )
    emissive_density: FloatProperty(
        name="Emissive Density",
        description="Density of small windows, bay guide lights, warning lights, and controlled glow strips",
        default=0.40,
        min=0.0,
        max=1.0,
    )
    glass_tint: FloatProperty(
        name="Glass Tint",
        description="Cockpit/canopy tint strength",
        default=0.62,
        min=0.0,
        max=1.0,
    )
    engine_heat_intensity: FloatProperty(
        name="Engine Heat",
        description="Strength of engine heat discoloration, nozzle soot, and engine-core emission",
        default=0.75,
        min=0.0,
        max=1.0,
    )
    faction_material_influence: FloatProperty(
        name="Faction Material",
        description="How strongly faction identity changes material wear, dirt, decals, glow, and palette",
        default=0.85,
        min=0.0,
        max=1.0,
    )
    generate_emissive_map: BoolProperty(
        name="Emissive Map",
        description="Generate export-friendly emissive texture maps for glowing parts and light strips",
        default=True,
    )
    generate_ao_map: BoolProperty(
        name="AO Map",
        description="Generate ambient-occlusion style cavity maps alongside PBR textures",
        default=True,
    )
    generate_decal_mask: BoolProperty(
        name="Decal Mask",
        description="Generate a separate decal/livery mask texture for inspection or export",
        default=False,
    )
    generate_material_id_mask: BoolProperty(
        name="Material ID Mask",
        description="Generate a material-zone ID mask for debugging paint, metal, dirt, heat, and emissive regions",
        default=False,
    )
    export_texture_maps: BoolProperty(
        name="Export Texture Maps",
        description="Pack generated image texture maps into the Blender file for export workflows",
        default=True,
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
    show_design_helpers: BoolProperty(
        name="Show Design Helpers",
        description="Keep optional design-analysis helpers visible when generated",
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

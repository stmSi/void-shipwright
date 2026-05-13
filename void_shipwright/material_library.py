"""Premium PBR material language for Void Shipwright."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


VALID_TEXTURE_QUALITIES = ("low", "standard", "hero", "cinematic")
TEXTURE_QUALITY_RESOLUTIONS = {
    "low": 256,
    "standard": 512,
    "hero": 1024,
    "cinematic": 2048,
}

VALID_MATERIAL_COMPLEXITIES = ("low", "medium", "high", "ultra")

PREMIUM_MATERIAL_STYLES = (
    "naval_ceramic_armor",
    "corporate_white_composite",
    "dark_military_titanium",
    "black_ops_stealth",
    "luxury_pearl_alloy",
    "racing_carbon_composite",
    "industrial_hazard_plating",
    "pirate_salvaged_metal",
    "ancient_iridescent_alloy",
    "mining_worn_industrial",
    "medical_rescue_composite",
    "trade_consortium_cargo_paint",
)


@dataclass(frozen=True)
class MaterialCategory:
    key: str
    base_color_range: tuple[tuple[float, float, float, float], tuple[float, float, float, float]]
    metallic_range: tuple[float, float]
    roughness_range: tuple[float, float]
    normal_strength: float
    edge_wear_behavior: str
    dirt_behavior: str
    decal_behavior: str
    emissive_behavior: str = "none"
    glass_transmission_behavior: str = "opaque"
    faction_compatibility: tuple[str, ...] = ()
    ship_class_compatibility: tuple[str, ...] = ()


MATERIAL_CATEGORIES: dict[str, MaterialCategory] = {
    "military_armor": MaterialCategory(
        "military_armor",
        ((0.20, 0.22, 0.24, 1.0), (0.55, 0.58, 0.62, 1.0)),
        (0.10, 0.45),
        (0.38, 0.68),
        0.62,
        "controlled bright ceramic edge polish",
        "low cavity dust, no broad rust",
        "organized unit blocks and maintenance labels",
        faction_compatibility=("sector_navy", "corporate_security"),
        ship_class_compatibility=("gunship", "heavy_cruiser", "boss_capital_ship"),
    ),
    "anodized_titanium": MaterialCategory(
        "anodized_titanium",
        ((0.05, 0.06, 0.08, 1.0), (0.20, 0.24, 0.30, 1.0)),
        (0.68, 0.92),
        (0.32, 0.58),
        0.58,
        "cool bright edge anisotropic-like scratches",
        "thin oil in seams only",
        "small tactical markings",
        faction_compatibility=("sector_navy", "corporate_security", "smuggler_network"),
        ship_class_compatibility=("interceptor", "racing_ship", "light_raider"),
    ),
    "ceramic_composite": MaterialCategory(
        "ceramic_composite",
        ((0.62, 0.66, 0.68, 1.0), (0.93, 0.95, 0.94, 1.0)),
        (0.02, 0.18),
        (0.44, 0.72),
        0.42,
        "subtle satin worn corners",
        "soft grey cavity dust",
        "clean printed livery and rescue markings",
        faction_compatibility=("corporate_security", "medical_ship", "sector_navy"),
        ship_class_compatibility=("medical_ship", "luxury_yacht", "heavy_cruiser"),
    ),
    "carbon_composite": MaterialCategory(
        "carbon_composite",
        ((0.015, 0.016, 0.018, 1.0), (0.12, 0.13, 0.15, 1.0)),
        (0.00, 0.16),
        (0.22, 0.48),
        0.50,
        "fine bright resin scuffs",
        "very low dirt",
        "sport livery and alignment marks",
        faction_compatibility=("independent", "corporate_security", "smuggler_network"),
        ship_class_compatibility=("racing_ship", "interceptor", "luxury_yacht"),
    ),
    "dark_inset_rubber": MaterialCategory(
        "dark_inset_rubber",
        ((0.002, 0.003, 0.004, 1.0), (0.04, 0.045, 0.05, 1.0)),
        (0.00, 0.04),
        (0.70, 0.92),
        0.34,
        "matte rubbed corners",
        "cavity grime and dust",
        "none",
    ),
    "dark_recessed_metal": MaterialCategory(
        "dark_recessed_metal",
        ((0.008, 0.010, 0.012, 1.0), (0.08, 0.09, 0.10, 1.0)),
        (0.50, 0.85),
        (0.55, 0.86),
        0.64,
        "bright exposed rim scratches",
        "heavy recess dirt",
        "small service stencil blocks",
    ),
    "brushed_aluminum": MaterialCategory(
        "brushed_aluminum",
        ((0.52, 0.54, 0.54, 1.0), (0.92, 0.91, 0.86, 1.0)),
        (0.82, 0.98),
        (0.24, 0.48),
        0.44,
        "thin linear polished scratches",
        "low dust",
        "subtle serial blocks",
        ship_class_compatibility=("luxury_yacht", "freighter"),
    ),
    "gunmetal_plating": MaterialCategory(
        "gunmetal_plating",
        ((0.025, 0.028, 0.032, 1.0), (0.16, 0.17, 0.18, 1.0)),
        (0.68, 0.92),
        (0.36, 0.62),
        0.66,
        "bright chipped metal on exposed edges",
        "moderate seam dirt",
        "tactical arrows and panel numbers",
    ),
    "heat_stained_engine_metal": MaterialCategory(
        "heat_stained_engine_metal",
        ((0.04, 0.045, 0.050, 1.0), (0.28, 0.22, 0.16, 1.0)),
        (0.78, 0.98),
        (0.28, 0.58),
        0.74,
        "burnished nozzle lips",
        "soot near exhaust only",
        "service heat bands",
        emissive_behavior="adjacent engine glow",
    ),
    "exhaust_ceramic": MaterialCategory(
        "exhaust_ceramic",
        ((0.06, 0.055, 0.050, 1.0), (0.30, 0.27, 0.22, 1.0)),
        (0.00, 0.18),
        (0.62, 0.88),
        0.46,
        "chalky hot rim wear",
        "dark soot in nozzle cavities",
        "none",
    ),
    "emissive_engine_core": MaterialCategory(
        "emissive_engine_core",
        ((0.10, 0.65, 1.00, 1.0), (0.85, 1.00, 1.00, 1.0)),
        (0.0, 0.0),
        (0.18, 0.34),
        0.0,
        "none",
        "none",
        "none",
        emissive_behavior="strong contained engine core",
    ),
    "emissive_light_strip": MaterialCategory(
        "emissive_light_strip",
        ((0.06, 0.55, 0.95, 1.0), (0.80, 1.00, 1.00, 1.0)),
        (0.0, 0.0),
        (0.26, 0.48),
        0.0,
        "none",
        "none",
        "thin navigation and bay strips",
        emissive_behavior="small controlled strips",
    ),
    "cockpit_glass": MaterialCategory(
        "cockpit_glass",
        ((0.03, 0.14, 0.20, 0.62), (0.32, 0.65, 0.78, 0.78)),
        (0.0, 0.02),
        (0.04, 0.18),
        0.12,
        "subtle rim highlight",
        "almost none",
        "fine canopy reinforcement lines",
        emissive_behavior="interior glow",
        glass_transmission_behavior="alpha blended low-roughness glass",
    ),
    "reinforced_canopy_glass": MaterialCategory(
        "reinforced_canopy_glass",
        ((0.02, 0.10, 0.15, 0.70), (0.20, 0.42, 0.56, 0.82)),
        (0.0, 0.04),
        (0.08, 0.22),
        0.18,
        "framed rim highlight",
        "very low",
        "reinforcement line normals",
        emissive_behavior="subtle cockpit glow",
        glass_transmission_behavior="tinted reinforced alpha glass",
    ),
    "missile_bay_interior": MaterialCategory(
        "missile_bay_interior",
        ((0.015, 0.016, 0.015, 1.0), (0.18, 0.16, 0.13, 1.0)),
        (0.36, 0.78),
        (0.62, 0.86),
        0.72,
        "worn loading rails",
        "ordnance soot and oil",
        "warning stripes and bay labels",
    ),
    "weapon_barrel_metal": MaterialCategory(
        "weapon_barrel_metal",
        ((0.035, 0.038, 0.04, 1.0), (0.34, 0.34, 0.32, 1.0)),
        (0.82, 0.98),
        (0.22, 0.48),
        0.68,
        "bright muzzle rim wear",
        "low soot near barrel ends",
        "small serial marks",
    ),
    "cargo_container_paint": MaterialCategory(
        "cargo_container_paint",
        ((0.20, 0.22, 0.20, 1.0), (0.86, 0.68, 0.24, 1.0)),
        (0.08, 0.34),
        (0.50, 0.82),
        0.60,
        "loading scuffs",
        "moderate dust",
        "loading labels and alignment stripes",
    ),
    "industrial_yellow_paint": MaterialCategory(
        "industrial_yellow_paint",
        ((0.62, 0.38, 0.08, 1.0), (0.98, 0.72, 0.16, 1.0)),
        (0.06, 0.26),
        (0.54, 0.86),
        0.66,
        "scraped exposed metal",
        "high industrial grime",
        "hazard stripes",
    ),
    "rescue_white_paint": MaterialCategory(
        "rescue_white_paint",
        ((0.70, 0.78, 0.82, 1.0), (0.98, 0.98, 0.94, 1.0)),
        (0.00, 0.16),
        (0.42, 0.68),
        0.38,
        "clean service scuffs",
        "low grey dust",
        "rescue blocks and sterile labels",
        faction_compatibility=("independent", "corporate_security"),
        ship_class_compatibility=("medical_ship",),
    ),
    "luxury_pearl_composite": MaterialCategory(
        "luxury_pearl_composite",
        ((0.75, 0.74, 0.68, 1.0), (0.98, 0.96, 0.88, 1.0)),
        (0.02, 0.22),
        (0.18, 0.42),
        0.26,
        "barely visible polished edges",
        "almost none",
        "fine luxury pinstripes",
        ship_class_compatibility=("luxury_yacht",),
    ),
    "ancient_iridescent_alloy": MaterialCategory(
        "ancient_iridescent_alloy",
        ((0.16, 0.48, 0.42, 1.0), (0.72, 0.92, 0.74, 1.0)),
        (0.40, 0.78),
        (0.24, 0.54),
        0.30,
        "smooth luminous seams instead of chipped rust",
        "minimal industrial dirt",
        "abstract generated glyph seams",
        emissive_behavior="glowing seams",
        faction_compatibility=("ancient_relic",),
    ),
    "pirate_salvaged_plate": MaterialCategory(
        "pirate_salvaged_plate",
        ((0.08, 0.07, 0.06, 1.0), (0.50, 0.32, 0.18, 1.0)),
        (0.36, 0.86),
        (0.48, 0.88),
        0.72,
        "uneven exposed metal and patched paint",
        "moderate dirt, controlled rust",
        "tally marks and repair labels",
        faction_compatibility=("pirate_clan",),
    ),
    "stealth_absorber_panel": MaterialCategory(
        "stealth_absorber_panel",
        ((0.005, 0.006, 0.008, 1.0), (0.055, 0.060, 0.070, 1.0)),
        (0.02, 0.20),
        (0.72, 0.94),
        0.36,
        "matte rubbed edges",
        "low dirt, high roughness",
        "low-visibility glyph blocks",
        faction_compatibility=("smuggler_network",),
        ship_class_compatibility=("interceptor", "light_raider"),
    ),
}


PREMIUM_STYLE_PROFILES: dict[str, dict[str, Any]] = {
    "naval_ceramic_armor": {
        "category": "military_armor",
        "base": (0.34, 0.37, 0.40, 1.0),
        "armor": (0.56, 0.59, 0.62, 1.0),
        "trim": (0.060, 0.070, 0.085, 1.0),
        "edge": (0.86, 0.89, 0.90, 1.0),
        "rust": (0.22, 0.13, 0.07, 1.0),
        "oxide": (0.10, 0.11, 0.12, 1.0),
        "metallic": 0.18,
        "roughness": 0.56,
        "rust_affinity": 0.12,
    },
    "corporate_white_composite": {
        "category": "ceramic_composite",
        "base": (0.78, 0.82, 0.84, 1.0),
        "armor": (0.90, 0.92, 0.91, 1.0),
        "trim": (0.045, 0.055, 0.070, 1.0),
        "edge": (0.95, 0.96, 0.92, 1.0),
        "rust": (0.22, 0.14, 0.08, 1.0),
        "oxide": (0.17, 0.18, 0.18, 1.0),
        "metallic": 0.10,
        "roughness": 0.48,
        "rust_affinity": 0.08,
    },
    "dark_military_titanium": {
        "category": "anodized_titanium",
        "base": (0.055, 0.065, 0.082, 1.0),
        "armor": (0.12, 0.135, 0.16, 1.0),
        "trim": (0.010, 0.012, 0.018, 1.0),
        "edge": (0.68, 0.73, 0.78, 1.0),
        "rust": (0.24, 0.11, 0.055, 1.0),
        "oxide": (0.075, 0.09, 0.12, 1.0),
        "metallic": 0.86,
        "roughness": 0.42,
        "rust_affinity": 0.16,
    },
    "black_ops_stealth": {
        "category": "stealth_absorber_panel",
        "base": (0.010, 0.012, 0.016, 1.0),
        "armor": (0.030, 0.034, 0.042, 1.0),
        "trim": (0.002, 0.003, 0.004, 1.0),
        "edge": (0.30, 0.33, 0.36, 1.0),
        "rust": (0.14, 0.08, 0.05, 1.0),
        "oxide": (0.035, 0.040, 0.048, 1.0),
        "metallic": 0.08,
        "roughness": 0.86,
        "rust_affinity": 0.06,
    },
    "luxury_pearl_alloy": {
        "category": "luxury_pearl_composite",
        "base": (0.78, 0.76, 0.69, 1.0),
        "armor": (0.94, 0.92, 0.84, 1.0),
        "trim": (0.72, 0.61, 0.36, 1.0),
        "edge": (1.00, 0.95, 0.78, 1.0),
        "rust": (0.16, 0.10, 0.055, 1.0),
        "oxide": (0.13, 0.12, 0.10, 1.0),
        "metallic": 0.20,
        "roughness": 0.30,
        "rust_affinity": 0.04,
    },
    "racing_carbon_composite": {
        "category": "carbon_composite",
        "base": (0.018, 0.020, 0.024, 1.0),
        "armor": (0.095, 0.102, 0.112, 1.0),
        "trim": (0.005, 0.006, 0.008, 1.0),
        "edge": (0.55, 0.58, 0.62, 1.0),
        "rust": (0.12, 0.07, 0.04, 1.0),
        "oxide": (0.030, 0.034, 0.040, 1.0),
        "metallic": 0.08,
        "roughness": 0.34,
        "rust_affinity": 0.03,
    },
    "industrial_hazard_plating": {
        "category": "industrial_yellow_paint",
        "base": (0.32, 0.25, 0.12, 1.0),
        "armor": (0.82, 0.52, 0.12, 1.0),
        "trim": (0.045, 0.040, 0.034, 1.0),
        "edge": (0.82, 0.74, 0.58, 1.0),
        "rust": (0.66, 0.24, 0.07, 1.0),
        "oxide": (0.22, 0.16, 0.09, 1.0),
        "metallic": 0.34,
        "roughness": 0.72,
        "rust_affinity": 0.58,
    },
    "pirate_salvaged_metal": {
        "category": "pirate_salvaged_plate",
        "base": (0.13, 0.105, 0.085, 1.0),
        "armor": (0.29, 0.22, 0.16, 1.0),
        "trim": (0.030, 0.025, 0.020, 1.0),
        "edge": (0.78, 0.68, 0.50, 1.0),
        "rust": (0.62, 0.20, 0.065, 1.0),
        "oxide": (0.18, 0.12, 0.07, 1.0),
        "metallic": 0.58,
        "roughness": 0.68,
        "rust_affinity": 0.78,
    },
    "ancient_iridescent_alloy": {
        "category": "ancient_iridescent_alloy",
        "base": (0.16, 0.40, 0.36, 1.0),
        "armor": (0.34, 0.64, 0.52, 1.0),
        "trim": (0.08, 0.18, 0.18, 1.0),
        "edge": (0.72, 0.98, 0.78, 1.0),
        "rust": (0.08, 0.34, 0.30, 1.0),
        "oxide": (0.06, 0.26, 0.24, 1.0),
        "metallic": 0.52,
        "roughness": 0.38,
        "rust_affinity": 0.02,
    },
    "mining_worn_industrial": {
        "category": "industrial_yellow_paint",
        "base": (0.25, 0.19, 0.10, 1.0),
        "armor": (0.66, 0.42, 0.12, 1.0),
        "trim": (0.035, 0.030, 0.026, 1.0),
        "edge": (0.76, 0.68, 0.50, 1.0),
        "rust": (0.58, 0.22, 0.075, 1.0),
        "oxide": (0.20, 0.16, 0.10, 1.0),
        "metallic": 0.40,
        "roughness": 0.78,
        "rust_affinity": 0.72,
    },
    "medical_rescue_composite": {
        "category": "rescue_white_paint",
        "base": (0.76, 0.82, 0.84, 1.0),
        "armor": (0.94, 0.96, 0.94, 1.0),
        "trim": (0.09, 0.14, 0.18, 1.0),
        "edge": (0.98, 0.98, 0.93, 1.0),
        "rust": (0.20, 0.11, 0.06, 1.0),
        "oxide": (0.16, 0.17, 0.17, 1.0),
        "metallic": 0.06,
        "roughness": 0.50,
        "rust_affinity": 0.05,
    },
    "trade_consortium_cargo_paint": {
        "category": "cargo_container_paint",
        "base": (0.34, 0.34, 0.30, 1.0),
        "armor": (0.74, 0.54, 0.18, 1.0),
        "trim": (0.055, 0.062, 0.066, 1.0),
        "edge": (0.88, 0.82, 0.64, 1.0),
        "rust": (0.50, 0.19, 0.065, 1.0),
        "oxide": (0.18, 0.16, 0.12, 1.0),
        "metallic": 0.22,
        "roughness": 0.64,
        "rust_affinity": 0.34,
    },
}


FACTION_MATERIAL_LANGUAGE: dict[str, dict[str, float | str]] = {
    "pirate_clan": {"wear": 1.20, "dirt": 1.10, "rust": 1.18, "emissive": 0.92, "recommended_style": "pirate_salvaged_metal"},
    "sector_navy": {"wear": 0.72, "dirt": 0.65, "rust": 0.26, "emissive": 1.00, "recommended_style": "naval_ceramic_armor"},
    "trade_consortium": {"wear": 0.88, "dirt": 0.82, "rust": 0.42, "emissive": 0.86, "recommended_style": "trade_consortium_cargo_paint"},
    "mining_guild": {"wear": 1.10, "dirt": 1.38, "rust": 0.76, "emissive": 0.82, "recommended_style": "mining_worn_industrial"},
    "smuggler_network": {"wear": 0.76, "dirt": 0.58, "rust": 0.16, "emissive": 0.66, "recommended_style": "black_ops_stealth"},
    "corporate_security": {"wear": 0.58, "dirt": 0.48, "rust": 0.10, "emissive": 1.05, "recommended_style": "corporate_white_composite"},
    "ancient_relic": {"wear": 0.25, "dirt": 0.18, "rust": 0.02, "emissive": 1.36, "recommended_style": "ancient_iridescent_alloy"},
    "independent": {"wear": 0.92, "dirt": 0.82, "rust": 0.36, "emissive": 0.92, "recommended_style": "painted_composite"},
}


SHIP_CLASS_MATERIAL_LANGUAGE: dict[str, dict[str, float | str]] = {
    "light_raider": {"wear": 1.04, "dirt": 0.86, "decal": 0.88, "emissive": 1.05, "style": "dark_military_titanium"},
    "interceptor": {"wear": 0.58, "dirt": 0.42, "decal": 0.72, "emissive": 1.24, "style": "dark_military_titanium"},
    "gunship": {"wear": 0.82, "dirt": 0.70, "decal": 0.82, "emissive": 0.92, "style": "naval_ceramic_armor"},
    "boarding_frigate": {"wear": 1.08, "dirt": 0.92, "decal": 0.78, "emissive": 0.86, "style": "dark_military_titanium"},
    "missile_corvette": {"wear": 0.74, "dirt": 0.64, "decal": 1.14, "emissive": 0.98, "style": "naval_ceramic_armor"},
    "freighter": {"wear": 1.04, "dirt": 1.06, "decal": 1.08, "emissive": 0.76, "style": "trade_consortium_cargo_paint"},
    "heavy_cruiser": {"wear": 0.70, "dirt": 0.62, "decal": 0.86, "emissive": 0.96, "style": "naval_ceramic_armor"},
    "mining_ship": {"wear": 1.12, "dirt": 1.34, "decal": 1.10, "emissive": 0.82, "style": "mining_worn_industrial"},
    "salvage_ship": {"wear": 1.28, "dirt": 1.28, "decal": 0.78, "emissive": 0.86, "style": "pirate_salvaged_metal"},
    "medical_ship": {"wear": 0.36, "dirt": 0.32, "decal": 1.20, "emissive": 1.22, "style": "medical_rescue_composite"},
    "racing_ship": {"wear": 0.22, "dirt": 0.18, "decal": 1.28, "emissive": 1.32, "style": "racing_carbon_composite"},
    "luxury_yacht": {"wear": 0.14, "dirt": 0.10, "decal": 0.54, "emissive": 0.96, "style": "luxury_pearl_alloy"},
    "boss_capital_ship": {"wear": 0.78, "dirt": 0.72, "decal": 0.92, "emissive": 1.10, "style": "dark_military_titanium"},
}


@dataclass(frozen=True)
class MaterialControlProfile:
    style: str
    texture_resolution: int
    material_complexity: str
    paint_layer_strength: float
    roughness_variation: float
    metallic_variation: float
    edge_wear_amount: float
    cavity_dirt_amount: float
    heat_stain_amount: float
    soot_amount: float
    decal_amount: float
    livery_amount: float
    emissive_density: float
    engine_heat_intensity: float
    faction_material_influence: float
    category_tags: tuple[str, ...] = field(default_factory=tuple)


def effective_texture_resolution(texture_quality: str, texture_resolution: int) -> int:
    quality_resolution = TEXTURE_QUALITY_RESOLUTIONS[texture_quality]
    return max(64, min(max(int(texture_resolution), quality_resolution), 2048))


def recommended_style_for(faction: str, ship_type: str, explicit_style: str) -> str:
    if explicit_style != "auto":
        return explicit_style
    class_style = SHIP_CLASS_MATERIAL_LANGUAGE.get(ship_type, {}).get("style")
    if isinstance(class_style, str):
        return class_style
    faction_style = FACTION_MATERIAL_LANGUAGE.get(faction, {}).get("recommended_style")
    return faction_style if isinstance(faction_style, str) else "painted_composite"


def material_language_multiplier(faction: str, ship_type: str, key: str, influence: float) -> float:
    influence = max(0.0, min(influence, 1.0))
    faction_value = FACTION_MATERIAL_LANGUAGE.get(faction, {}).get(key, 1.0)
    class_value = SHIP_CLASS_MATERIAL_LANGUAGE.get(ship_type, {}).get(key, 1.0)
    faction_multiplier = faction_value if isinstance(faction_value, float) else 1.0
    class_multiplier = class_value if isinstance(class_value, float) else 1.0
    target = faction_multiplier * class_multiplier
    return 1.0 + (target - 1.0) * influence


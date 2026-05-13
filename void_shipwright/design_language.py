"""Art-direction grammar for Void Shipwright visual generation."""

from __future__ import annotations

from dataclasses import dataclass


VALID_VISUAL_QUALITIES = ("draft", "standard", "hero", "cinematic")
VALID_DESIGN_LANGUAGES = ("auto", "military", "pirate", "industrial", "luxury", "ancient", "racing", "cargo")
VALID_SILHOUETTE_BIASES = ("balanced", "sleek", "broad", "tall", "asymmetric", "capital")


@dataclass(frozen=True)
class DesignLanguage:
    silhouette_style: str
    nose_style: str
    body_section_style: str
    wing_style: str
    engine_layout: str
    armor_layer_style: str
    panel_language: str
    faction_shape_language: str
    faction_surface_language: str
    hero_detail_level: float
    elegance_score: float
    aggression_score: float
    industrial_score: float
    luxury_score: float
    military_score: float
    pirate_score: float


QUALITY_MULTIPLIERS = {
    "draft": {
        "secondary": 0.52,
        "tertiary": 0.35,
        "bevel": 0.70,
        "engine": 0.55,
        "bridge": 0.55,
    },
    "standard": {
        "secondary": 0.82,
        "tertiary": 0.62,
        "bevel": 0.88,
        "engine": 0.78,
        "bridge": 0.78,
    },
    "hero": {
        "secondary": 1.0,
        "tertiary": 1.0,
        "bevel": 1.0,
        "engine": 1.0,
        "bridge": 1.0,
    },
    "cinematic": {
        "secondary": 1.24,
        "tertiary": 1.38,
        "bevel": 1.15,
        "engine": 1.30,
        "bridge": 1.24,
    },
}


SHIP_TYPE_LANGUAGE = {
    "light_raider": "pirate",
    "interceptor": "racing",
    "gunship": "military",
    "boarding_frigate": "military",
    "missile_corvette": "military",
    "freighter": "cargo",
    "heavy_cruiser": "military",
    "heavy_fighter": "military",
    "bomber": "military",
    "patrol_cutter": "military",
    "explorer": "luxury",
    "dropship": "military",
    "mining_ship": "industrial",
    "salvage_ship": "industrial",
    "medical_ship": "luxury",
    "racing_ship": "racing",
    "luxury_yacht": "luxury",
    "boss_capital_ship": "military",
}


FACTION_LANGUAGE = {
    "pirate_clan": "pirate",
    "sector_navy": "military",
    "trade_consortium": "cargo",
    "mining_guild": "industrial",
    "smuggler_network": "pirate",
    "corporate_security": "military",
    "ancient_relic": "ancient",
    "independent": "cargo",
}


LANGUAGE_PROFILES = {
    "military": DesignLanguage(
        silhouette_style="wedge_citadel",
        nose_style="armored_prow",
        body_section_style="terraced_belts",
        wing_style="stub_stabilizers",
        engine_layout="clustered_nozzles",
        armor_layer_style="organized_terraces",
        panel_language="orthogonal_service_bays",
        faction_shape_language="symmetrical_command",
        faction_surface_language="clean_tactical_trim",
        hero_detail_level=1.0,
        elegance_score=0.58,
        aggression_score=0.76,
        industrial_score=0.42,
        luxury_score=0.18,
        military_score=0.92,
        pirate_score=0.05,
    ),
    "pirate": DesignLanguage(
        silhouette_style="predatory_asymmetric",
        nose_style="hooked_blade",
        body_section_style="patched_compact",
        wing_style="clipped_fins",
        engine_layout="exposed_overdrive",
        armor_layer_style="offset_patchwork",
        panel_language="field_repairs",
        faction_shape_language="asymmetric_raider",
        faction_surface_language="scavenged_metal",
        hero_detail_level=0.92,
        elegance_score=0.36,
        aggression_score=0.92,
        industrial_score=0.50,
        luxury_score=0.04,
        military_score=0.32,
        pirate_score=1.0,
    ),
    "industrial": DesignLanguage(
        silhouette_style="utility_frame",
        nose_style="tool_boom",
        body_section_style="external_frame",
        wing_style="radiator_racks",
        engine_layout="tug_nacelles",
        armor_layer_style="service_panels",
        panel_language="maintenance_grid",
        faction_shape_language="exposed_mechanical",
        faction_surface_language="hazard_trim",
        hero_detail_level=0.86,
        elegance_score=0.24,
        aggression_score=0.30,
        industrial_score=1.0,
        luxury_score=0.02,
        military_score=0.24,
        pirate_score=0.20,
    ),
    "luxury": DesignLanguage(
        silhouette_style="smooth_swan",
        nose_style="swept_canopy",
        body_section_style="clean_spine",
        wing_style="integrated_fins",
        engine_layout="faired_nacelles",
        armor_layer_style="flush_plating",
        panel_language="minimal_premium",
        faction_shape_language="balanced_sleek",
        faction_surface_language="polished_trim",
        hero_detail_level=0.82,
        elegance_score=1.0,
        aggression_score=0.10,
        industrial_score=0.12,
        luxury_score=1.0,
        military_score=0.16,
        pirate_score=0.0,
    ),
    "ancient": DesignLanguage(
        silhouette_style="arched_relic",
        nose_style="split_arc",
        body_section_style="nested_symmetry",
        wing_style="crescent_arches",
        engine_layout="ring_core",
        armor_layer_style="curved_shells",
        panel_language="glowing_seams",
        faction_shape_language="alien_ordered",
        faction_surface_language="luminal_inlays",
        hero_detail_level=1.12,
        elegance_score=0.88,
        aggression_score=0.54,
        industrial_score=0.06,
        luxury_score=0.42,
        military_score=0.36,
        pirate_score=0.0,
    ),
    "racing": DesignLanguage(
        silhouette_style="needle_speedform",
        nose_style="long_dagger",
        body_section_style="compact_fuselage",
        wing_style="blade_canards",
        engine_layout="oversized_pods",
        armor_layer_style="lightweight_skin",
        panel_language="aero_cutlines",
        faction_shape_language="speed_focused",
        faction_surface_language="sport_livery",
        hero_detail_level=0.78,
        elegance_score=0.86,
        aggression_score=0.45,
        industrial_score=0.08,
        luxury_score=0.40,
        military_score=0.12,
        pirate_score=0.0,
    ),
    "cargo": DesignLanguage(
        silhouette_style="spine_and_modules",
        nose_style="cab_forward",
        body_section_style="container_frame",
        wing_style="utility_rails",
        engine_layout="rear_tug_bank",
        armor_layer_style="practical_panels",
        panel_language="loading_latches",
        faction_shape_language="modular_civilian",
        faction_surface_language="logistics_markings",
        hero_detail_level=0.80,
        elegance_score=0.34,
        aggression_score=0.12,
        industrial_score=0.70,
        luxury_score=0.18,
        military_score=0.14,
        pirate_score=0.05,
    ),
}


def resolve_design_language(ship_type: str, faction: str, requested: str) -> DesignLanguage:
    if requested != "auto":
        return LANGUAGE_PROFILES[requested]
    if faction == "ancient_relic":
        return LANGUAGE_PROFILES["ancient"]
    return LANGUAGE_PROFILES[SHIP_TYPE_LANGUAGE.get(ship_type, FACTION_LANGUAGE.get(faction, "cargo"))]


def quality_multiplier(visual_quality: str, key: str) -> float:
    return QUALITY_MULTIPLIERS.get(visual_quality, QUALITY_MULTIPLIERS["hero"]).get(key, 1.0)


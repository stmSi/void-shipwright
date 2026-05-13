"""Data-driven ship frames, hardpoints, slots, and default loadout metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


VALID_SHIP_FRAMES = (
    "light_raider",
    "interceptor",
    "gunship",
    "boarding_frigate",
    "missile_corvette",
    "freighter",
    "heavy_cruiser",
    "mining_ship",
    "salvage_ship",
    "medical_ship",
    "racing_ship",
    "luxury_yacht",
    "boss_capital_ship",
)

HARDPOINT_TYPES = (
    "weapon_fixed",
    "weapon_gimbal",
    "turret",
    "missile_rack",
    "torpedo_rack",
    "utility",
    "mining",
    "salvage",
    "tractor",
    "shield",
    "engine",
    "maneuver_thruster",
    "cargo",
    "boarding",
    "scanner",
    "countermeasure",
    "docking",
    "cosmetic",
)

COMPONENT_SLOT_TYPES = (
    "power_plant",
    "cooler",
    "shield_generator",
    "quantum_or_warp_drive",
    "radar",
    "scanner",
    "life_support",
    "avionics",
    "armor_plating",
    "cargo_module",
    "crew_module",
    "repair_module",
    "stealth_module",
)

COMPONENT_GRADES = (
    "civilian",
    "industrial",
    "military",
    "competition",
    "stealth",
    "pirate",
    "ancient",
)

EQUIPMENT_CATEGORIES = (
    "laser_cannon",
    "ballistic_cannon",
    "plasma_repeater",
    "railgun",
    "missile_launcher",
    "torpedo_launcher",
    "mine_layer",
    "emp_projector",
    "shield_disruptor",
    "tractor_beam",
    "mining_laser",
    "salvage_beam",
    "repair_drone_launcher",
    "countermeasure_launcher",
    "boarding_grapple",
    "cargo_pod",
    "scanner_array",
)

MOUNT_MODES = ("fixed", "gimbal", "turret", "rack", "internal", "external")

SHIP_TYPE_TO_FRAME = {
    "light_raider": "light_raider",
    "missile_corvette": "missile_corvette",
    "interceptor": "interceptor",
    "gunship": "gunship",
    "freighter": "freighter",
    "heavy_fighter": "gunship",
    "bomber": "missile_corvette",
    "patrol_cutter": "gunship",
    "explorer": "luxury_yacht",
    "dropship": "boarding_frigate",
    "mining_ship": "mining_ship",
    "salvage_ship": "salvage_ship",
    "medical_ship": "medical_ship",
    "racing_ship": "racing_ship",
    "luxury_yacht": "luxury_yacht",
    "boarding_frigate": "boarding_frigate",
    "heavy_cruiser": "heavy_cruiser",
    "boss_capital_ship": "boss_capital_ship",
}

COMBAT_GUNS = ("laser_cannon", "ballistic_cannon", "plasma_repeater", "railgun")
MISSILES = ("missile_launcher", "mine_layer")
TORPEDOES = ("torpedo_launcher",)
UTILITY_EQUIPMENT = ("emp_projector", "shield_disruptor", "tractor_beam", "repair_drone_launcher", "scanner_array")
INDUSTRIAL_EQUIPMENT = ("mining_laser", "salvage_beam", "tractor_beam")

FRAME_DEFINITIONS: dict[str, dict[str, Any]] = {
    "light_raider": {
        "display_name": "Light Raider",
        "base_hull_hp": 850,
        "base_shield_capacity": 420,
        "mass": 18.0,
        "cargo_capacity": 4,
        "crew_capacity": 1,
        "power_output": 135,
        "heat_capacity": 95,
        "cooling_capacity": 72,
        "maneuverability": 0.92,
        "max_speed": 270,
        "boost_strength": 1.28,
        "allowed_hardpoint_groups": ["weapon_fixed", "weapon_gimbal", "missile_rack", "utility", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "avionics", "stealth_module"],
        "role_tags": ["combat", "pirate", "raider"],
    },
    "interceptor": {
        "display_name": "Interceptor",
        "base_hull_hp": 720,
        "base_shield_capacity": 360,
        "mass": 14.0,
        "cargo_capacity": 1,
        "crew_capacity": 1,
        "power_output": 150,
        "heat_capacity": 82,
        "cooling_capacity": 86,
        "maneuverability": 1.18,
        "max_speed": 335,
        "boost_strength": 1.55,
        "allowed_hardpoint_groups": ["weapon_fixed", "weapon_gimbal", "maneuver_thruster", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "avionics"],
        "role_tags": ["combat", "pursuit"],
    },
    "gunship": {
        "display_name": "Gunship",
        "base_hull_hp": 1450,
        "base_shield_capacity": 720,
        "mass": 36.0,
        "cargo_capacity": 6,
        "crew_capacity": 3,
        "power_output": 230,
        "heat_capacity": 150,
        "cooling_capacity": 118,
        "maneuverability": 0.58,
        "max_speed": 190,
        "boost_strength": 0.92,
        "allowed_hardpoint_groups": ["weapon_fixed", "weapon_gimbal", "turret", "missile_rack", "utility", "shield", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "avionics", "armor_plating"],
        "role_tags": ["combat", "escort"],
    },
    "boarding_frigate": {
        "display_name": "Boarding Frigate",
        "base_hull_hp": 2350,
        "base_shield_capacity": 980,
        "mass": 68.0,
        "cargo_capacity": 14,
        "crew_capacity": 12,
        "power_output": 320,
        "heat_capacity": 210,
        "cooling_capacity": 170,
        "maneuverability": 0.42,
        "max_speed": 145,
        "boost_strength": 0.74,
        "allowed_hardpoint_groups": ["weapon_fixed", "turret", "tractor", "boarding", "docking", "utility", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "armor_plating", "crew_module"],
        "role_tags": ["combat", "boarding"],
    },
    "missile_corvette": {
        "display_name": "Missile Corvette",
        "base_hull_hp": 1900,
        "base_shield_capacity": 900,
        "mass": 54.0,
        "cargo_capacity": 8,
        "crew_capacity": 5,
        "power_output": 285,
        "heat_capacity": 195,
        "cooling_capacity": 145,
        "maneuverability": 0.50,
        "max_speed": 165,
        "boost_strength": 0.82,
        "allowed_hardpoint_groups": ["weapon_fixed", "turret", "missile_rack", "torpedo_rack", "utility", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "avionics", "armor_plating"],
        "role_tags": ["combat", "ordnance"],
    },
    "freighter": {
        "display_name": "Freighter",
        "base_hull_hp": 1700,
        "base_shield_capacity": 620,
        "mass": 86.0,
        "cargo_capacity": 120,
        "crew_capacity": 4,
        "power_output": 210,
        "heat_capacity": 175,
        "cooling_capacity": 122,
        "maneuverability": 0.34,
        "max_speed": 125,
        "boost_strength": 0.60,
        "allowed_hardpoint_groups": ["weapon_fixed", "utility", "tractor", "cargo", "engine", "countermeasure", "docking"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "life_support", "avionics", "cargo_module", "crew_module"],
        "role_tags": ["cargo", "civilian"],
    },
    "heavy_cruiser": {
        "display_name": "Heavy Cruiser",
        "base_hull_hp": 4200,
        "base_shield_capacity": 1850,
        "mass": 150.0,
        "cargo_capacity": 32,
        "crew_capacity": 28,
        "power_output": 620,
        "heat_capacity": 420,
        "cooling_capacity": 335,
        "maneuverability": 0.26,
        "max_speed": 118,
        "boost_strength": 0.52,
        "allowed_hardpoint_groups": ["weapon_fixed", "turret", "missile_rack", "torpedo_rack", "utility", "shield", "engine", "countermeasure", "docking"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "armor_plating", "crew_module", "repair_module"],
        "role_tags": ["combat", "capital"],
    },
    "mining_ship": {
        "display_name": "Mining Ship",
        "base_hull_hp": 1550,
        "base_shield_capacity": 520,
        "mass": 62.0,
        "cargo_capacity": 54,
        "crew_capacity": 3,
        "power_output": 260,
        "heat_capacity": 220,
        "cooling_capacity": 185,
        "maneuverability": 0.38,
        "max_speed": 132,
        "boost_strength": 0.68,
        "allowed_hardpoint_groups": ["mining", "tractor", "utility", "cargo", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "cargo_module"],
        "role_tags": ["industrial", "mining", "cargo"],
    },
    "salvage_ship": {
        "display_name": "Salvage Ship",
        "base_hull_hp": 1500,
        "base_shield_capacity": 500,
        "mass": 58.0,
        "cargo_capacity": 46,
        "crew_capacity": 4,
        "power_output": 245,
        "heat_capacity": 205,
        "cooling_capacity": 160,
        "maneuverability": 0.40,
        "max_speed": 138,
        "boost_strength": 0.66,
        "allowed_hardpoint_groups": ["salvage", "tractor", "utility", "cargo", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "cargo_module", "repair_module"],
        "role_tags": ["industrial", "salvage", "cargo"],
    },
    "medical_ship": {
        "display_name": "Medical Ship",
        "base_hull_hp": 1250,
        "base_shield_capacity": 700,
        "mass": 44.0,
        "cargo_capacity": 16,
        "crew_capacity": 6,
        "power_output": 240,
        "heat_capacity": 160,
        "cooling_capacity": 145,
        "maneuverability": 0.52,
        "max_speed": 175,
        "boost_strength": 0.90,
        "allowed_hardpoint_groups": ["utility", "tractor", "scanner", "cargo", "engine", "countermeasure", "docking"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "crew_module", "repair_module"],
        "role_tags": ["support", "medical", "civilian"],
    },
    "racing_ship": {
        "display_name": "Racing Ship",
        "base_hull_hp": 520,
        "base_shield_capacity": 220,
        "mass": 9.5,
        "cargo_capacity": 0,
        "crew_capacity": 1,
        "power_output": 180,
        "heat_capacity": 90,
        "cooling_capacity": 115,
        "maneuverability": 1.34,
        "max_speed": 390,
        "boost_strength": 1.85,
        "allowed_hardpoint_groups": ["weapon_fixed", "engine", "maneuver_thruster", "countermeasure", "cosmetic"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "avionics"],
        "role_tags": ["civilian", "racing"],
    },
    "luxury_yacht": {
        "display_name": "Luxury Yacht",
        "base_hull_hp": 1100,
        "base_shield_capacity": 850,
        "mass": 40.0,
        "cargo_capacity": 18,
        "crew_capacity": 6,
        "power_output": 260,
        "heat_capacity": 170,
        "cooling_capacity": 155,
        "maneuverability": 0.60,
        "max_speed": 210,
        "boost_strength": 1.02,
        "allowed_hardpoint_groups": ["utility", "scanner", "docking", "cosmetic", "engine", "countermeasure"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "quantum_or_warp_drive", "radar", "scanner", "life_support", "avionics", "crew_module", "stealth_module"],
        "role_tags": ["civilian", "luxury"],
    },
    "boss_capital_ship": {
        "display_name": "Boss Capital Ship",
        "base_hull_hp": 12500,
        "base_shield_capacity": 5600,
        "mass": 620.0,
        "cargo_capacity": 180,
        "crew_capacity": 120,
        "power_output": 1800,
        "heat_capacity": 1260,
        "cooling_capacity": 980,
        "maneuverability": 0.08,
        "max_speed": 72,
        "boost_strength": 0.28,
        "allowed_hardpoint_groups": ["weapon_fixed", "turret", "missile_rack", "torpedo_rack", "utility", "shield", "engine", "countermeasure", "docking"],
        "allowed_component_slots": ["power_plant", "cooler", "shield_generator", "radar", "scanner", "life_support", "avionics", "armor_plating", "cargo_module", "crew_module", "repair_module"],
        "role_tags": ["boss", "capital", "combat"],
    },
}


def resolve_ship_frame(ship_type: str, role: str = "", requested_frame: str = "auto") -> str:
    if requested_frame in VALID_SHIP_FRAMES:
        return requested_frame
    if ship_type == "boss_capital_ship" or role == "boss":
        return "boss_capital_ship" if ship_type == "boss_capital_ship" else SHIP_TYPE_TO_FRAME.get(ship_type, "boss_capital_ship")
    return SHIP_TYPE_TO_FRAME.get(ship_type, "light_raider")


def frame_definition(frame: str) -> dict[str, Any]:
    return deepcopy(FRAME_DEFINITIONS[frame])


def performance_baseline(frame: str) -> dict[str, Any]:
    definition = FRAME_DEFINITIONS[frame]
    keys = (
        "base_hull_hp",
        "base_shield_capacity",
        "mass",
        "cargo_capacity",
        "crew_capacity",
        "power_output",
        "heat_capacity",
        "cooling_capacity",
        "maneuverability",
        "max_speed",
        "boost_strength",
    )
    return {key: deepcopy(definition[key]) for key in keys}


def build_hardpoints(frame: str, dimensions: dict[str, float], preset: str = "frame_default") -> list[dict[str, Any]]:
    hardpoints = [_hardpoint_from_spec(spec, dimensions) for spec in _hardpoint_specs(frame)]
    if preset == "minimal":
        return [hardpoint for hardpoint in hardpoints if hardpoint["required"]]
    if preset == "combat":
        return [
            hardpoint
            for hardpoint in hardpoints
            if hardpoint["required"]
            or hardpoint["type"] in {"weapon_fixed", "weapon_gimbal", "turret", "missile_rack", "torpedo_rack", "countermeasure"}
        ]
    if preset == "industrial":
        return [
            hardpoint
            for hardpoint in hardpoints
            if hardpoint["required"]
            or hardpoint["type"] in {"utility", "mining", "salvage", "tractor", "cargo", "scanner", "docking"}
        ]
    return hardpoints


def build_component_slots(frame: str, preset: str = "frame_default") -> list[dict[str, Any]]:
    slots = deepcopy(_component_slots(frame))
    if preset == "minimal":
        return [slot for slot in slots if slot["required"]]
    if preset == "expanded":
        return slots
    return slots


def build_equipment_recommendations(
    frame: str,
    hardpoints: list[dict[str, Any]],
    component_slots: list[dict[str, Any]],
    *,
    include_loadout: bool,
) -> dict[str, Any]:
    recommendations: dict[str, Any] = {
        "loadout_id": f"{frame}_default",
        "notes": "Starter loadout IDs are Godot-side data references; Blender does not instantiate equipment.",
        "equipment": [],
        "components": [],
    }
    if not include_loadout:
        return recommendations

    for hardpoint in hardpoints:
        equipment_id = _default_equipment_for_hardpoint(hardpoint)
        if equipment_id:
            recommendations["equipment"].append({"hardpoint": hardpoint["name"], "equipment_id": equipment_id})

    for slot in component_slots:
        component_id = _default_component_for_slot(slot)
        if component_id:
            recommendations["components"].append({"slot": slot["id"], "component_id": component_id})
    return recommendations


def build_subsystem_layout(hardpoints: list[dict[str, Any]], component_slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    linked_hardpoints = {
        "engines": [item["name"] for item in hardpoints if item["type"] in {"engine", "maneuver_thruster"}],
        "weapons": [item["name"] for item in hardpoints if item["type"] in {"weapon_fixed", "weapon_gimbal", "turret", "missile_rack", "torpedo_rack"}],
        "shields": [item["name"] for item in hardpoints if item["type"] == "shield"],
        "cargo": [item["name"] for item in hardpoints if item["type"] == "cargo"],
        "scanner": [item["name"] for item in hardpoints if item["type"] == "scanner"],
        "boarding_defense": [item["name"] for item in hardpoints if item["type"] in {"boarding", "docking"}],
    }
    linked_components = {
        "power_plant": [item["id"] for item in component_slots if item["slot_type"] == "power_plant"],
        "cooler": [item["id"] for item in component_slots if item["slot_type"] == "cooler"],
        "shields": [item["id"] for item in component_slots if item["slot_type"] == "shield_generator"],
        "cargo": [item["id"] for item in component_slots if item["slot_type"] == "cargo_module"],
        "life_support": [item["id"] for item in component_slots if item["slot_type"] == "life_support"],
        "scanner": [item["id"] for item in component_slots if item["slot_type"] in {"scanner", "radar"}],
    }
    return [
        _subsystem("DAMAGE_Hull", "hull", 1.0, 0.22, [], []),
        _subsystem("DAMAGE_Engine", "engines", 1.25, 0.35, linked_hardpoints["engines"], []),
        _subsystem("DAMAGE_Weapons", "weapons", 1.15, 0.40, linked_hardpoints["weapons"], []),
        _subsystem("DAMAGE_Shield_Generator", "shields", 1.10, 0.32, linked_hardpoints["shields"], linked_components["shields"]),
        _subsystem("DAMAGE_Cargo", "cargo", 1.00, 0.45, linked_hardpoints["cargo"], linked_components["cargo"]),
        _subsystem("DAMAGE_Bridge", "bridge", 1.35, 0.30, [], []),
        _subsystem("DAMAGE_Power_Plant", "power_plant", 1.25, 0.28, [], linked_components["power_plant"]),
        _subsystem("DAMAGE_Cooler", "cooler", 1.20, 0.34, [], linked_components["cooler"]),
        _subsystem("DAMAGE_Life_Support", "life_support", 1.05, 0.42, [], linked_components["life_support"]),
        _subsystem("DAMAGE_Scanner", "scanner", 1.15, 0.38, linked_hardpoints["scanner"], linked_components["scanner"]),
        _subsystem("DAMAGE_Boarding_Defense", "boarding_defense", 1.20, 0.35, linked_hardpoints["boarding_defense"], []),
    ]


def _subsystem(
    damage_marker: str,
    subsystem: str,
    damage_multiplier: float,
    critical_threshold: float,
    linked_hardpoints: list[str],
    linked_components: list[str],
) -> dict[str, Any]:
    return {
        "name": damage_marker,
        "subsystem": subsystem,
        "damage_multiplier": damage_multiplier,
        "critical_threshold": critical_threshold,
        "linked_hardpoints": linked_hardpoints,
        "linked_components": linked_components,
    }


def _hardpoint_from_spec(spec: dict[str, Any], dimensions: dict[str, float]) -> dict[str, Any]:
    x_factor, y_factor, z_factor = spec["position_factor"]
    position = [
        round(dimensions["width"] * x_factor, 4),
        round(dimensions["length"] * y_factor, 4),
        round(dimensions["height"] * z_factor, 4),
    ]
    name = spec["visual_socket_name"].removeprefix("SOCKET_")
    return {
        "name": name,
        "type": spec["type"],
        "size": spec["size"],
        "position": position,
        "rotation": list(spec.get("rotation", (0.0, 0.0, 0.0))),
        "allowed_equipment_types": list(spec["allowed_equipment_types"]),
        "allowed_mount_modes": list(spec["allowed_mount_modes"]),
        "symmetry_group": spec.get("symmetry_group", ""),
        "required": bool(spec.get("required", False)),
        "optional": not bool(spec.get("required", False)),
        "visual_socket_name": spec["visual_socket_name"],
        "gameplay_socket_name": spec.get("gameplay_socket_name", spec["visual_socket_name"]),
    }


def _hp(
    visual_socket_name: str,
    hardpoint_type: str,
    size: int,
    position_factor: tuple[float, float, float],
    allowed_equipment_types: tuple[str, ...],
    allowed_mount_modes: tuple[str, ...],
    *,
    symmetry_group: str = "",
    required: bool = False,
    gameplay_socket_name: str = "",
) -> dict[str, Any]:
    return {
        "visual_socket_name": visual_socket_name,
        "type": hardpoint_type,
        "size": size,
        "position_factor": position_factor,
        "allowed_equipment_types": allowed_equipment_types,
        "allowed_mount_modes": allowed_mount_modes,
        "symmetry_group": symmetry_group,
        "required": required,
        "gameplay_socket_name": gameplay_socket_name or visual_socket_name,
    }


def _hardpoint_specs(frame: str) -> list[dict[str, Any]]:
    specs = {
        "light_raider": [
            _hp("SOCKET_HP_Weapon_Fixed_Front_01", "weapon_fixed", 2, (-0.08, -0.54, -0.02), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", required=True, gameplay_socket_name="SOCKET_Weapon_Front_01"),
            _hp("SOCKET_HP_Weapon_Fixed_Front_02", "weapon_fixed", 2, (0.08, -0.54, -0.02), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", required=True, gameplay_socket_name="SOCKET_Weapon_Front_02"),
            _hp("SOCKET_HP_Missile_Left_01", "missile_rack", 2, (-0.34, -0.22, -0.08), MISSILES, ("rack",), symmetry_group="missile_pair", gameplay_socket_name="SOCKET_Missile_Left_01"),
            _hp("SOCKET_HP_Missile_Right_01", "missile_rack", 2, (0.34, -0.22, -0.08), MISSILES, ("rack",), symmetry_group="missile_pair", gameplay_socket_name="SOCKET_Missile_Right_01"),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 1, (-0.42, 0.02, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 1, (0.42, 0.02, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 1, (0.0, 0.42, 0.16), ("countermeasure_launcher",), ("internal",)),
        ],
        "interceptor": [
            _hp("SOCKET_HP_Weapon_Gimbal_Front_01", "weapon_gimbal", 3, (0.0, -0.58, -0.02), COMBAT_GUNS, ("gimbal",), required=True, gameplay_socket_name="SOCKET_Weapon_Front_01"),
            _hp("SOCKET_HP_Weapon_Fixed_Front_01", "weapon_fixed", 2, (-0.12, -0.50, -0.03), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", gameplay_socket_name="SOCKET_Weapon_Front_01"),
            _hp("SOCKET_HP_Weapon_Fixed_Front_02", "weapon_fixed", 2, (0.12, -0.50, -0.03), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", gameplay_socket_name="SOCKET_Weapon_Front_02"),
            _hp("SOCKET_HP_Maneuver_Thruster_Left_01", "maneuver_thruster", 2, (-0.44, 0.24, -0.08), (), ("internal",), symmetry_group="thruster_pair"),
            _hp("SOCKET_HP_Maneuver_Thruster_Right_01", "maneuver_thruster", 2, (0.44, 0.24, -0.08), (), ("internal",), symmetry_group="thruster_pair"),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 1, (0.0, 0.46, 0.10), ("countermeasure_launcher",), ("internal",)),
        ],
        "gunship": [
            _hp("SOCKET_HP_Weapon_Fixed_Front_01", "weapon_fixed", 3, (-0.10, -0.50, -0.04), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", required=True, gameplay_socket_name="SOCKET_Weapon_Front_01"),
            _hp("SOCKET_HP_Weapon_Fixed_Front_02", "weapon_fixed", 3, (0.10, -0.50, -0.04), COMBAT_GUNS, ("fixed",), symmetry_group="front_pair", required=True, gameplay_socket_name="SOCKET_Weapon_Front_02"),
            _hp("SOCKET_HP_Turret_Dorsal_01", "turret", 4, (0.0, -0.04, 0.56), COMBAT_GUNS, ("turret",), required=True),
            _hp("SOCKET_HP_Turret_Ventral_01", "turret", 3, (0.0, 0.10, -0.48), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Missile_Left_01", "missile_rack", 3, (-0.40, -0.10, -0.06), MISSILES, ("rack",), symmetry_group="missile_pair", gameplay_socket_name="SOCKET_Missile_Left_01"),
            _hp("SOCKET_HP_Missile_Right_01", "missile_rack", 3, (0.40, -0.10, -0.06), MISSILES, ("rack",), symmetry_group="missile_pair", gameplay_socket_name="SOCKET_Missile_Right_01"),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 2, (-0.48, 0.16, 0.04), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 2, (0.48, 0.16, 0.04), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
        ],
        "boarding_frigate": [
            _hp("SOCKET_HP_Boarding_Grapple_01", "boarding", 4, (0.0, -0.58, -0.06), ("boarding_grapple",), ("external",), required=True, gameplay_socket_name="SOCKET_Boarding_Attach"),
            _hp("SOCKET_HP_Docking_Port_Left_01", "docking", 3, (-0.48, 0.02, 0.02), (), ("external",), symmetry_group="docking_pair"),
            _hp("SOCKET_HP_Docking_Port_Right_01", "docking", 3, (0.48, 0.02, 0.02), (), ("external",), symmetry_group="docking_pair"),
            _hp("SOCKET_HP_Tractor_Front_01", "tractor", 3, (0.0, -0.46, 0.04), ("tractor_beam",), ("external",)),
            _hp("SOCKET_HP_Turret_Dorsal_01", "turret", 4, (0.0, -0.05, 0.58), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 2, (0.0, 0.45, 0.12), ("countermeasure_launcher",), ("internal",)),
        ],
        "missile_corvette": [
            _hp("SOCKET_HP_Missile_Left_01", "missile_rack", 4, (-0.36, -0.12, 0.10), MISSILES, ("rack",), symmetry_group="missile_pair", required=True, gameplay_socket_name="SOCKET_Missile_Left_01"),
            _hp("SOCKET_HP_Missile_Right_01", "missile_rack", 4, (0.36, -0.12, 0.10), MISSILES, ("rack",), symmetry_group="missile_pair", required=True, gameplay_socket_name="SOCKET_Missile_Right_01"),
            _hp("SOCKET_HP_Torpedo_Front_01", "torpedo_rack", 5, (0.0, -0.48, -0.10), TORPEDOES, ("rack",)),
            _hp("SOCKET_HP_Turret_Dorsal_01", "turret", 3, (0.0, 0.02, 0.62), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Turret_Ventral_01", "turret", 3, (0.0, 0.18, -0.52), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 2, (0.0, 0.48, 0.10), ("countermeasure_launcher",), ("internal",)),
        ],
        "freighter": [
            _hp("SOCKET_HP_Cargo_Module_Left_01", "cargo", 5, (-0.38, 0.10, -0.18), ("cargo_pod",), ("external",), symmetry_group="cargo_pair", required=True),
            _hp("SOCKET_HP_Cargo_Module_Right_01", "cargo", 5, (0.38, 0.10, -0.18), ("cargo_pod",), ("external",), symmetry_group="cargo_pair", required=True),
            _hp("SOCKET_HP_Tractor_Front_01", "tractor", 3, (0.0, -0.42, -0.02), ("tractor_beam",), ("external",)),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 2, (-0.44, -0.08, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 2, (0.44, -0.08, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Weapon_Fixed_Front_01", "weapon_fixed", 1, (0.0, -0.50, 0.02), COMBAT_GUNS, ("fixed",), gameplay_socket_name="SOCKET_Weapon_Front_01"),
        ],
        "heavy_cruiser": [
            _hp("SOCKET_HP_Turret_Dorsal_01", "turret", 6, (0.0, -0.18, 0.72), COMBAT_GUNS, ("turret",), required=True),
            _hp("SOCKET_HP_Turret_Dorsal_02", "turret", 6, (0.0, 0.18, 0.70), COMBAT_GUNS, ("turret",), required=True),
            _hp("SOCKET_HP_Turret_Ventral_01", "turret", 5, (0.0, 0.05, -0.60), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Missile_Left_01", "missile_rack", 5, (-0.42, -0.08, 0.06), MISSILES, ("rack",), symmetry_group="missile_pair"),
            _hp("SOCKET_HP_Missile_Right_01", "missile_rack", 5, (0.42, -0.08, 0.06), MISSILES, ("rack",), symmetry_group="missile_pair"),
            _hp("SOCKET_HP_Torpedo_Front_01", "torpedo_rack", 6, (0.0, -0.52, -0.08), TORPEDOES, ("rack",)),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 4, (-0.50, 0.18, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 4, (0.50, 0.18, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
        ],
        "mining_ship": [
            _hp("SOCKET_HP_Mining_Front_01", "mining", 4, (0.0, -0.58, -0.02), ("mining_laser",), ("fixed",), required=True),
            _hp("SOCKET_HP_Tractor_Front_01", "tractor", 3, (0.0, -0.44, 0.04), ("tractor_beam",), ("external",)),
            _hp("SOCKET_HP_Cargo_Module_Left_01", "cargo", 4, (-0.38, 0.14, -0.14), ("cargo_pod",), ("external",), symmetry_group="ore_pair"),
            _hp("SOCKET_HP_Cargo_Module_Right_01", "cargo", 4, (0.38, 0.14, -0.14), ("cargo_pod",), ("external",), symmetry_group="ore_pair"),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 2, (-0.42, -0.08, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 2, (0.42, -0.08, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
        ],
        "salvage_ship": [
            _hp("SOCKET_HP_Salvage_Front_01", "salvage", 4, (0.0, -0.54, -0.02), ("salvage_beam",), ("fixed",), required=True),
            _hp("SOCKET_HP_Tractor_Front_01", "tractor", 3, (0.0, -0.42, 0.02), ("tractor_beam",), ("external",)),
            _hp("SOCKET_HP_Cargo_Module_Left_01", "cargo", 4, (-0.38, 0.16, -0.12), ("cargo_pod",), ("external",), symmetry_group="scrap_pair"),
            _hp("SOCKET_HP_Cargo_Module_Right_01", "cargo", 4, (0.38, 0.16, -0.12), ("cargo_pod",), ("external",), symmetry_group="scrap_pair"),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 2, (-0.42, -0.05, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 2, (0.42, -0.05, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
        ],
        "medical_ship": [
            _hp("SOCKET_HP_Utility_Left_01", "utility", 3, (-0.40, -0.08, 0.04), ("repair_drone_launcher", "tractor_beam", "scanner_array"), ("external",), symmetry_group="support_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 3, (0.40, -0.08, 0.04), ("repair_drone_launcher", "tractor_beam", "scanner_array"), ("external",), symmetry_group="support_pair"),
            _hp("SOCKET_HP_Scanner_Dorsal_01", "scanner", 3, (0.0, -0.18, 0.58), ("scanner_array",), ("external",), required=True),
            _hp("SOCKET_HP_Cargo_Module_Left_01", "cargo", 2, (-0.32, 0.18, -0.12), ("cargo_pod",), ("external",), symmetry_group="medical_pair"),
            _hp("SOCKET_HP_Cargo_Module_Right_01", "cargo", 2, (0.32, 0.18, -0.12), ("cargo_pod",), ("external",), symmetry_group="medical_pair"),
            _hp("SOCKET_HP_Docking_Port_Left_01", "docking", 2, (-0.48, 0.00, 0.03), (), ("external",)),
        ],
        "racing_ship": [
            _hp("SOCKET_HP_Weapon_Fixed_Front_01", "weapon_fixed", 1, (0.0, -0.48, -0.02), COMBAT_GUNS, ("fixed",), gameplay_socket_name="SOCKET_Weapon_Front_01"),
            _hp("SOCKET_HP_Maneuver_Thruster_Left_01", "maneuver_thruster", 3, (-0.44, 0.22, -0.04), (), ("internal",), symmetry_group="thruster_pair", required=True),
            _hp("SOCKET_HP_Maneuver_Thruster_Right_01", "maneuver_thruster", 3, (0.44, 0.22, -0.04), (), ("internal",), symmetry_group="thruster_pair", required=True),
            _hp("SOCKET_HP_Cosmetic_Dorsal_01", "cosmetic", 1, (0.0, 0.04, 0.42), (), ("external",)),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 1, (0.0, 0.42, 0.08), ("countermeasure_launcher",), ("internal",)),
        ],
        "luxury_yacht": [
            _hp("SOCKET_HP_Scanner_Dorsal_01", "scanner", 3, (0.0, -0.16, 0.60), ("scanner_array",), ("external",), required=True),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 2, (-0.36, 0.06, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 2, (0.36, 0.06, 0.02), UTILITY_EQUIPMENT, ("external",), symmetry_group="utility_pair"),
            _hp("SOCKET_HP_Docking_Port_Left_01", "docking", 3, (-0.46, 0.04, 0.03), (), ("external",), symmetry_group="docking_pair"),
            _hp("SOCKET_HP_Docking_Port_Right_01", "docking", 3, (0.46, 0.04, 0.03), (), ("external",), symmetry_group="docking_pair"),
            _hp("SOCKET_HP_Cosmetic_Dorsal_01", "cosmetic", 2, (0.0, 0.12, 0.58), (), ("external",)),
        ],
        "boss_capital_ship": [
            _hp("SOCKET_HP_Turret_Dorsal_01", "turret", 9, (0.0, -0.26, 0.82), COMBAT_GUNS, ("turret",), required=True),
            _hp("SOCKET_HP_Turret_Dorsal_02", "turret", 9, (0.0, 0.02, 0.86), COMBAT_GUNS, ("turret",), required=True),
            _hp("SOCKET_HP_Turret_Dorsal_03", "turret", 8, (0.0, 0.30, 0.78), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Turret_Ventral_01", "turret", 8, (0.0, -0.04, -0.68), COMBAT_GUNS, ("turret",)),
            _hp("SOCKET_HP_Missile_Left_01", "missile_rack", 8, (-0.46, -0.12, 0.08), MISSILES, ("rack",), symmetry_group="capital_missile_pair"),
            _hp("SOCKET_HP_Missile_Right_01", "missile_rack", 8, (0.46, -0.12, 0.08), MISSILES, ("rack",), symmetry_group="capital_missile_pair"),
            _hp("SOCKET_HP_Torpedo_Front_01", "torpedo_rack", 10, (0.0, -0.54, -0.06), TORPEDOES, ("rack",), required=True),
            _hp("SOCKET_HP_Utility_Left_01", "utility", 6, (-0.52, 0.22, 0.04), UTILITY_EQUIPMENT, ("external",), symmetry_group="capital_utility_pair"),
            _hp("SOCKET_HP_Utility_Right_01", "utility", 6, (0.52, 0.22, 0.04), UTILITY_EQUIPMENT, ("external",), symmetry_group="capital_utility_pair"),
            _hp("SOCKET_HP_Countermeasure_Rear_01", "countermeasure", 5, (0.0, 0.52, 0.16), ("countermeasure_launcher",), ("internal",)),
        ],
    }
    return [*_common_engine_hardpoints(frame), *specs.get(frame, specs["light_raider"])]


def _common_engine_hardpoints(frame: str) -> list[dict[str, Any]]:
    size = {
        "boss_capital_ship": 10,
        "heavy_cruiser": 7,
        "boarding_frigate": 5,
        "missile_corvette": 5,
        "freighter": 4,
        "gunship": 4,
        "mining_ship": 4,
        "salvage_ship": 4,
        "medical_ship": 3,
        "luxury_yacht": 3,
        "interceptor": 3,
        "racing_ship": 3,
        "light_raider": 2,
    }.get(frame, 2)
    return [
        _hp("SOCKET_HP_Engine_Main_01", "engine", size, (0.0, 0.54, 0.0), (), ("internal",), required=True, gameplay_socket_name="SOCKET_Engine_Main_01"),
        _hp("SOCKET_HP_Engine_Left_01", "engine", max(1, size - 1), (-0.24, 0.50, -0.04), (), ("internal",), symmetry_group="engine_pair", gameplay_socket_name="SOCKET_Engine_Left_01"),
        _hp("SOCKET_HP_Engine_Right_01", "engine", max(1, size - 1), (0.24, 0.50, -0.04), (), ("internal",), symmetry_group="engine_pair", gameplay_socket_name="SOCKET_Engine_Right_01"),
    ]


def _component_slots(frame: str) -> list[dict[str, Any]]:
    definition = FRAME_DEFINITIONS[frame]
    frame_size = _frame_component_size(frame)
    slots: list[dict[str, Any]] = []
    for slot_type in definition["allowed_component_slots"]:
        required = slot_type in {"power_plant", "cooler", "shield_generator", "radar", "avionics"}
        slots.append(
            {
                "id": f"SLOT_{slot_type.upper()}_{len(slots) + 1:02d}",
                "display_name": slot_type.replace("_", " ").title(),
                "slot_type": slot_type,
                "size": frame_size if required else max(1, frame_size - 1),
                "required": required,
                "optional": not required,
                "role_tags": list(definition["role_tags"]),
            }
        )
    return slots


def _frame_component_size(frame: str) -> int:
    if frame == "boss_capital_ship":
        return 10
    if frame == "heavy_cruiser":
        return 7
    if frame in {"boarding_frigate", "missile_corvette", "freighter"}:
        return 5
    if frame in {"gunship", "mining_ship", "salvage_ship", "medical_ship", "luxury_yacht"}:
        return 4
    if frame == "interceptor":
        return 3
    return 2


def _default_equipment_for_hardpoint(hardpoint: dict[str, Any]) -> str:
    hardpoint_type = hardpoint["type"]
    size = hardpoint["size"]
    if hardpoint_type in {"weapon_fixed", "weapon_gimbal", "turret"}:
        if size >= 5:
            return "eq_railgun_s5"
        if hardpoint_type == "turret":
            return "eq_plasma_repeater_s3"
        return "eq_laser_cannon_s2"
    if hardpoint_type == "missile_rack":
        return "eq_missile_launcher_s3"
    if hardpoint_type == "torpedo_rack":
        return "eq_torpedo_launcher_s5"
    if hardpoint_type == "mining":
        return "eq_mining_laser_s4"
    if hardpoint_type == "salvage":
        return "eq_salvage_beam_s4"
    if hardpoint_type == "tractor":
        return "eq_tractor_beam_s3"
    if hardpoint_type == "utility":
        return "eq_emp_projector_s2" if size <= 2 else "eq_repair_drone_launcher_s3"
    if hardpoint_type == "cargo":
        return "eq_cargo_pod_s4"
    if hardpoint_type == "scanner":
        return "eq_scanner_array_s3"
    if hardpoint_type == "boarding":
        return "eq_boarding_grapple_s4"
    if hardpoint_type == "countermeasure":
        return "eq_countermeasure_launcher_s1"
    return ""


def _default_component_for_slot(slot: dict[str, Any]) -> str:
    slot_type = slot["slot_type"]
    return {
        "power_plant": "cmp_power_plant_industrial_s4",
        "cooler": "cmp_cooler_military_s3",
        "shield_generator": "cmp_shield_generator_military_s4",
        "quantum_or_warp_drive": "cmp_warp_drive_civilian_s3",
        "radar": "cmp_radar_civilian_s2",
        "scanner": "cmp_scanner_industrial_s3",
        "life_support": "cmp_life_support_civilian_s3",
        "avionics": "cmp_avionics_military_s3",
        "armor_plating": "cmp_armor_plating_military_s4",
        "cargo_module": "cmp_cargo_module_industrial_s4",
        "crew_module": "cmp_crew_module_civilian_s3",
        "repair_module": "cmp_repair_module_industrial_s3",
        "stealth_module": "cmp_stealth_module_stealth_s3",
    }.get(slot_type, "")

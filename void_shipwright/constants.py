"""Shared constants for the Void Shipwright Blender add-on."""

ADDON_NAME = "Void Shipwright"
ADDON_ID = "void_shipwright"
SCHEMA_VERSION = "1.0.0"

VALID_ROLES = (
    "player",
    "enemy",
    "ally",
    "neutral",
    "civilian",
    "boss",
    "drone",
    "background_traffic",
)

VALID_FACTIONS = (
    "pirate_clan",
    "sector_navy",
    "trade_consortium",
    "mining_guild",
    "smuggler_network",
    "corporate_security",
    "ancient_relic",
    "independent",
)

VALID_SHIP_TYPES = (
    "light_raider",
    "missile_corvette",
    "interceptor",
    "gunship",
    "freighter",
    "heavy_fighter",
    "bomber",
    "patrol_cutter",
    "explorer",
    "dropship",
    "mining_ship",
    "salvage_ship",
    "medical_ship",
    "racing_ship",
    "luxury_yacht",
)

VALID_HULL_PROFILES = (
    "raider",
    "needle",
    "heavy",
    "cargo",
)

VALID_DETAIL_LEVELS = (
    "low",
    "medium",
    "high",
    "hero",
)

VALID_MATERIAL_STYLES = (
    "gunmetal",
    "worn_steel",
    "dark_titanium",
    "rusted_iron",
    "oxidized_copper",
    "painted_composite",
)

VALID_TEXTURE_WORKFLOWS = (
    "painted",
    "procedural_shader",
)

OBJECT_PREFIXES = (
    "MESH_",
    "SOCKET_",
    "COLLISION_",
    "DAMAGE_",
    "VFX_",
    "CAMERA_",
    "TARGET_",
)

REQUIRED_SOCKETS = (
    "SOCKET_Weapon_Front_01",
    "SOCKET_Weapon_Front_02",
    "SOCKET_Weapon_Left_01",
    "SOCKET_Weapon_Right_01",
    "SOCKET_Missile_Left_01",
    "SOCKET_Missile_Right_01",
    "SOCKET_Engine_Main_01",
    "SOCKET_Engine_Left_01",
    "SOCKET_Engine_Right_01",
    "SOCKET_Camera_Follow",
    "SOCKET_Camera_Look_At",
    "SOCKET_Target_Lock_Center",
    "SOCKET_Loot_Drop",
    "SOCKET_Boarding_Attach",
)

REQUIRED_DAMAGE_MARKERS = (
    "DAMAGE_Hull",
    "DAMAGE_Engine",
    "DAMAGE_Weapons",
    "DAMAGE_Cargo",
    "DAMAGE_Bridge",
    "DAMAGE_Shield_Generator",
)

REQUIRED_COLLISION_PROXIES = (
    "COLLISION_Hull-colonly",
    "COLLISION_Engine-colonly",
    "COLLISION_Cargo-colonly",
    "COLLISION_Bridge-colonly",
)

REQUIRED_VFX_MARKERS = (
    "VFX_Engine_Main",
    "VFX_Engine_Left",
    "VFX_Engine_Right",
    "VFX_Shield_Impact",
    "VFX_Explosion_Core",
)

REQUIRED_CAMERA_MARKERS = (
    "CAMERA_Follow",
    "CAMERA_Look_At",
)

ROLE_PROFILES = {
    "player": {"length": 8.0, "width": 5.0, "height": 1.6, "wing": 1.0, "engine": 1.0},
    "enemy": {"length": 7.4, "width": 4.7, "height": 1.5, "wing": 1.1, "engine": 1.05},
    "ally": {"length": 7.8, "width": 4.8, "height": 1.5, "wing": 1.0, "engine": 1.0},
    "neutral": {"length": 7.2, "width": 4.3, "height": 1.4, "wing": 0.8, "engine": 0.9},
    "civilian": {"length": 9.0, "width": 4.0, "height": 1.8, "wing": 0.55, "engine": 0.75},
    "boss": {"length": 16.0, "width": 10.0, "height": 3.2, "wing": 1.25, "engine": 1.35},
    "drone": {"length": 4.2, "width": 3.0, "height": 0.9, "wing": 0.7, "engine": 0.8},
    "background_traffic": {
        "length": 6.2,
        "width": 3.6,
        "height": 1.2,
        "wing": 0.45,
        "engine": 0.65,
    },
}

FACTION_PROFILES = {
    "pirate_clan": {"color": (0.72, 0.12, 0.08, 1.0), "accent": (0.08, 0.08, 0.08, 1.0)},
    "sector_navy": {"color": (0.12, 0.28, 0.58, 1.0), "accent": (0.82, 0.86, 0.91, 1.0)},
    "trade_consortium": {"color": (0.95, 0.66, 0.18, 1.0), "accent": (0.18, 0.25, 0.28, 1.0)},
    "mining_guild": {"color": (0.78, 0.49, 0.17, 1.0), "accent": (0.16, 0.14, 0.12, 1.0)},
    "smuggler_network": {"color": (0.22, 0.25, 0.29, 1.0), "accent": (0.58, 0.1, 0.48, 1.0)},
    "corporate_security": {"color": (0.8, 0.84, 0.88, 1.0), "accent": (0.08, 0.16, 0.24, 1.0)},
    "ancient_relic": {"color": (0.25, 0.68, 0.55, 1.0), "accent": (0.62, 0.91, 0.76, 1.0)},
    "independent": {"color": (0.36, 0.4, 0.43, 1.0), "accent": (0.2, 0.7, 0.9, 1.0)},
}

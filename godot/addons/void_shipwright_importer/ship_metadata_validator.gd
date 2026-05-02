class_name VoidShipMetadataValidator
extends RefCounted

const VALID_ROLES = {
    "player": true,
    "enemy": true,
    "ally": true,
    "neutral": true,
    "civilian": true,
    "boss": true,
    "drone": true,
    "background_traffic": true,
}

const VALID_FACTIONS = {
    "pirate_clan": true,
    "sector_navy": true,
    "trade_consortium": true,
    "mining_guild": true,
    "smuggler_network": true,
    "corporate_security": true,
    "ancient_relic": true,
    "independent": true,
}

const REQUIRED_SOCKETS = [
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
]

const REQUIRED_DAMAGE_ZONES = [
    "DAMAGE_Hull",
    "DAMAGE_Engine",
    "DAMAGE_Weapons",
    "DAMAGE_Cargo",
    "DAMAGE_Bridge",
    "DAMAGE_Shield_Generator",
]

const REQUIRED_COLLISION_PROXIES = [
    "COLLISION_Hull-colonly",
    "COLLISION_Engine-colonly",
    "COLLISION_Cargo-colonly",
    "COLLISION_Bridge-colonly",
]


func validate(metadata: Dictionary) -> PackedStringArray:
    var errors := PackedStringArray()
    _require_string(metadata, "schema_version", errors)
    _require_string(metadata, "ship_id", errors)
    _require_string(metadata, "role", errors)
    _require_string(metadata, "faction", errors)

    if metadata.has("role") and not VALID_ROLES.has(metadata["role"]):
        errors.append("Unsupported role: %s" % metadata["role"])
    if metadata.has("faction") and not VALID_FACTIONS.has(metadata["faction"]):
        errors.append("Unsupported faction: %s" % metadata["faction"])

    _require_named_entries(metadata, "sockets", REQUIRED_SOCKETS, errors)
    _require_named_entries(metadata, "damage_zones", REQUIRED_DAMAGE_ZONES, errors)
    _require_named_entries(metadata, "collision_proxies", REQUIRED_COLLISION_PROXIES, errors)
    return errors


func _require_string(metadata: Dictionary, key: String, errors: PackedStringArray) -> void:
    if not metadata.has(key) or typeof(metadata[key]) != TYPE_STRING or metadata[key].is_empty():
        errors.append("Metadata field must be a non-empty string: %s" % key)


func _require_named_entries(
    metadata: Dictionary,
    section_name: String,
    required_names: Array,
    errors: PackedStringArray
) -> void:
    if not metadata.has(section_name) or typeof(metadata[section_name]) != TYPE_ARRAY:
        errors.append("Metadata section must be an array: %s" % section_name)
        return

    var names := {}
    for entry in metadata[section_name]:
        if typeof(entry) == TYPE_DICTIONARY and entry.has("name"):
            names[entry["name"]] = true

    for required_name in required_names:
        if not names.has(required_name):
            errors.append("Missing %s entry: %s" % [section_name, required_name])

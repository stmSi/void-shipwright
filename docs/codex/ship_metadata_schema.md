# Ship Metadata Schema

The canonical JSON schema is `schemas/ship_metadata.schema.json`. Example output is `examples/generated/void_ship_example.metadata.json`.

## Top-Level Fields

- `schema_version`: Semantic version for the metadata contract.
- `generator`: Must be `Void Shipwright`.
- `ship_id`: Stable Godot-safe asset ID.
- `role`: One of the supported roles in `AGENTS.md`.
- `faction`: One of the supported factions in `AGENTS.md`.
- `seed`: Non-negative deterministic generation seed.
- `variant`: Variant label.
- `units`: Must be `meters`.
- `source_axis` and `godot_axis`: Axis declarations for importer conversion.

## Required Sections

- `meshes`: Visual mesh objects.
- `sockets`: Gameplay attach points for weapons, engines, cameras, targeting, loot, and boarding.
- `collision_proxies`: Box collision source objects.
- `damage_zones`: Damage routing markers.
- `vfx_markers`: VFX attach points.
- `camera_markers`: Camera rig helper points.
- `target_markers`: Targeting helper points.

The `required_contract` field repeats the mandatory socket, damage-zone, and collision-proxy names so Godot tools can produce clear validation messages.

## Compatibility Rule

When adding a new marker or metadata field, update all of these together:

1. Blender constants and generation code.
2. Godot metadata validator and builder.
3. JSON schema.
4. Example metadata.
5. This documentation.

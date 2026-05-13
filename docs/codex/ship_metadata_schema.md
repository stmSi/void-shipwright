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
- `ship_frame`: Modular frame used for hardpoints, component slots, and performance baseline.
- `ship_frame_definition`: Full frame stats and allowed slot groups exported for tool consumers.
- `units`: Must be `meters`.
- `source_axis` and `godot_axis`: Axis declarations for importer conversion.

## Required Sections

- `meshes`: Visual mesh objects.
- `sockets`: Gameplay attach points for weapons, engines, cameras, targeting, loot, and boarding.
- `collision_proxies`: Box collision source objects. Collision entries include `size` as the full box dimensions Godot should assign to `BoxShape3D.size`; `scale` remains the Blender object transform scale.
- `damage_zones`: Damage routing markers.
- `vfx_markers`: VFX attach points.
- `camera_markers`: Camera rig helper points.
- `target_markers`: Targeting helper points.
- `hardpoints`: Formal equipment attachment schema backed by `SOCKET_HP_*` sockets.
- `component_slots`: Internal component slot schema.
- `equipment_recommendations`: Optional default equipment/component IDs for starter loadouts.
- `performance_baseline`: Frame stats before runtime equipment and component modifiers.
- `subsystem_layout`: Damage routing table linking damage markers to hardpoints and components.

The `required_contract` field repeats the mandatory socket, damage-zone, and collision-proxy names so Godot tools can produce clear validation messages.

Damage-zone entries may also include `subsystem`, `damage_multiplier`, `critical_threshold`, `linked_hardpoints`, and `linked_components`. These fields mirror `subsystem_layout` for consumers that prefer reading damage routing directly from each damage marker entry.

## Compatibility Rule

When adding a new marker or metadata field, update all of these together:

1. Blender constants and generation code.
2. Godot metadata validator and builder.
3. JSON schema.
4. Example metadata.
5. This documentation.

# Modular Ship System

Void Shipwright now exports modular ship metadata for future runtime customization. This phase is Blender-side only: Blender defines source markers and metadata; runtime equipment behavior remains outside Blender.

## Ownership

Blender owns:

- Visual meshes.
- Legacy sockets required by the existing pipeline.
- `SOCKET_HP_*` hardpoint helper sockets.
- Collision proxies.
- Damage markers.
- VFX, camera, and target markers.
- JSON metadata for frames, hardpoints, component slots, performance baseline, loadout recommendations, and subsystem layout.

Godot/runtime ownership is deferred:

- Instantiating equipment scenes.
- Enforcing loadout rules at runtime.
- Movement, power, heat, shields, damage, AI, loot, boarding, spawning, and factions.

## Ship Frames

Supported modular frames:

- `light_raider`
- `interceptor`
- `gunship`
- `boarding_frigate`
- `missile_corvette`
- `freighter`
- `heavy_cruiser`
- `mining_ship`
- `salvage_ship`
- `medical_ship`
- `racing_ship`
- `luxury_yacht`
- `boss_capital_ship`

Each frame defines hull HP, shield capacity, mass, cargo, crew, power, heat, cooling, maneuverability, max speed, boost strength, allowed hardpoint groups, allowed component slots, and role tags.

The Blender UI exposes `Ship Frame`. `Auto From Ship Type` maps visual archetypes to frame metadata while preserving older ship types such as `heavy_fighter` and `bomber`.

## Metadata Sections

New top-level metadata sections:

- `ship_frame`
- `ship_frame_definition`
- `hardpoints`
- `component_slots`
- `equipment_recommendations`
- `performance_baseline`
- `subsystem_layout`

Existing sections remain for compatibility:

- `meshes`
- `sockets`
- `collision_proxies`
- `damage_zones`
- `vfx_markers`
- `camera_markers`
- `target_markers`
- `required_contract`

## Designer Controls

`Hardpoint Preset`:

- `frame_default`: all hardpoints for the selected frame.
- `minimal`: only required hardpoints.
- `combat`: weapons, turrets, missile/torpedo racks, and countermeasures.
- `industrial`: mining, salvage, tractor, scanner, cargo, and utility hardpoints.

`Component Preset`:

- `frame_default`: default frame slots.
- `minimal`: only required component slots.
- `expanded`: all slots for the selected frame.

`Loadout Metadata` controls whether default equipment/component recommendation IDs are included. Blender does not instantiate those items.

`Show Hardpoints` keeps `SOCKET_HP_*` helpers visible even when other technical helpers are hidden.

## Adding A Ship Class

1. Add the visual ship type to `VALID_SHIP_TYPES` if it needs a distinct Blender silhouette.
2. Add a frame to `FRAME_DEFINITIONS` in `void_shipwright/modular.py`.
3. Add hardpoint specs in `_hardpoint_specs`.
4. Add component slots through the frame's `allowed_component_slots`.
5. Add dimensions and base mesh generation in `geometry.py` if the ship needs a new silhouette.
6. Run the Blender modular metadata smoke check.

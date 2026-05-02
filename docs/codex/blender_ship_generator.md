# Blender Ship Generator

Void Shipwright is a Blender 4 add-on that generates procedural spaceship source assets for Godot. Blender owns visual meshes and marker placement only. Gameplay behavior belongs in Godot.

## Add-on Layout

- `void_shipwright/__init__.py` registers the add-on.
- `void_shipwright/properties.py` defines panel settings.
- `void_shipwright/operators.py` exposes generate and metadata export actions.
- `void_shipwright/geometry.py` creates deterministic meshes, sockets, proxies, and markers.
- `void_shipwright/metadata.py` extracts generated objects into JSON.
- `void_shipwright/validation.py` validates roles, factions, seeds, and Godot-safe names.
- `void_shipwright/constants.py` is the shared contract for roles, factions, prefixes, and required markers.

## Generation Contract

Every generated ship must include:

- Visual mesh objects prefixed with `MESH_`.
- Socket empties prefixed with `SOCKET_`.
- Collision proxy meshes prefixed with `COLLISION_` and suffixed with `-colonly`.
- Damage marker empties prefixed with `DAMAGE_`.
- VFX marker empties prefixed with `VFX_`.
- Camera marker empties prefixed with `CAMERA_`.
- Target marker empties prefixed with `TARGET_`.

Names must stay Godot-friendly: ASCII letters, numbers, underscores, and hyphens only.

## Determinism

Generation uses `random.Random(seed)`. The same role, faction, seed, and variant must produce the same dimensions and marker positions. Do not use global random state for generation.

## Blender Usage

1. Install the `void_shipwright` folder as a Blender add-on.
2. Enable `Void Shipwright`.
3. Open `View3D > Sidebar > Void Shipwright`.
4. Choose ship type, role, faction, seed, ship ID, and variant.
5. Click `Generate Ship`.
6. Click `Generate and Export Metadata` to write `*.metadata.json`.

Export the generated mesh collection to a Godot-supported 3D format, then keep the metadata JSON next to that imported asset.

## Designer Controls

`Ship Type` selects the visual/equipment archetype:

- `Light Raider`: sharp attack craft.
- `Missile Corvette`: broad corvette with missile pod banks, ordnance cells, stabilizers, and auxiliary modules.
- `Interceptor`: lean pursuit ship with larger engines and lance details.
- `Gunship`: wider weapons platform with side cannons.
- `Freighter`: utility massing with cargo pods.

`Hull Profile`, `Hull Length`, `Hull Width`, `Hull Height`, `Wing Span`, and `Engine Scale` control silhouette.

`Weapon Density`, `Missile Density`, `Cargo Density`, and `Asymmetry` control visible ship systems. Missile corvettes respond strongly to `Missile Density`; higher values add more pod banks and more cells per bank.

`Armor Density`, `Greeble Density`, `Decal Density`, `Wear Amount`, and `Glow Strength` control surface finish and procedural texture intensity.

Enable `Custom Colors` only when the faction palette should be overridden by the primary, accent, and emissive color pickers.

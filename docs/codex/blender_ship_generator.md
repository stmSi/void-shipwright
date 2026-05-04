# Blender Ship Generator

Void Shipwright is a Blender 4 add-on that generates procedural spaceship source assets for Godot. Blender owns visual meshes and marker placement only. Gameplay behavior belongs in Godot.

## Add-on Layout

- `void_shipwright/__init__.py` registers the add-on.
- `void_shipwright/properties.py` defines panel settings.
- `void_shipwright/operators.py` exposes generate and metadata export actions.
- `void_shipwright/geometry.py` creates deterministic meshes, sockets, proxies, and markers.
- `void_shipwright/textures.py` creates deterministic generated texture-paint maps for exportable materials.
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
- `Missile Corvette`: broad armored hull, blunt prow armor, ordnance deck, missile pod banks, stabilizers, and auxiliary modules.
- `Interceptor`: narrow needle hull, swept wings, canards, oversized engines, and a centerline lance.
- `Gunship`: broad armored hull, stub wings, weapon sponsons, heavy nose cannons, and side cannons.
- `Freighter`: long truss spine, cargo blocks, side rails, bridge cab, and rear engine tug.

`Hull Profile`, `Hull Length`, `Hull Width`, `Hull Height`, `Wing Span`, and `Engine Scale` control silhouette.

`Weapon Density`, `Missile Density`, `Cargo Density`, and `Asymmetry` control visible ship systems. Missile corvettes respond strongly to `Missile Density`; higher values add more pod banks and more cells per bank.

`Decal Density`, `Wear Amount`, and `Glow Strength` control surface finish, texture-painted livery, chipped edges, and emissive detail. Extra armor shell, top panel, accent spine, panel seam, armor tile, micro vent, raider spike, greeble, wing decal, hull livery stripe, and faction insignia mesh layers are not generated; the add-on keeps surface complexity in nose chevrons, scuffs, lighting strips, and generated texture paint.

`Texture Workflow` controls how ship surface materials are built. `Painted Textures` is the default and creates packed Base Color, Roughness, and Normal image maps for each part family. `Procedural Shader` keeps the older Blender shader-node workflow available for comparison.

`Texture Resolution` controls the generated image map size per material family. The default is `64` for responsive iteration. Higher values cost more Blender memory and generation time, but export cleaner texture detail to Godot. Painted material maps are generated lazily only for material families used by the current ship, and identical seed/settings reuse existing maps.

`Material Style` selects the metal family. Current styles are `Gunmetal`, `Worn Steel`, `Dark Titanium`, `Rusted Iron`, `Oxidized Copper`, and `Painted Composite`.

`Rust`, `Scratches`, and `Texture Scale` control oxide coverage, bright scratched edges, painted panel-line frequency, sparse angular corrosion, roughness breakup, chipped micro scratches, and normal-map strength. The painted texture workflow avoids broad directional bands and brown base-color grain so surfaces read as painted or treated metal rather than wood.

Generated ships use separate material families per part role instead of one shared hull material. `Material Style` controls the primary body shell, while wing skins, livery edges, top armor, dark inset armor, underbody structure, heat-stained engine shells, blued weapon metal, cargo pods, system bays, dark inset detail, chipped edge wear, and painted trim use role-specific internal profiles so the model reads like layered hard-surface construction.

Every generated mesh receives a `VS_PaintedUV` box-projected UV map so generated image textures can export through glTF/GLB and remain usable in Godot. Painted panel lines and chips are texture data, not extra floating mesh layers.

Enable `Custom Colors` only when the faction palette should be overridden by the primary, accent, and emissive color pickers.

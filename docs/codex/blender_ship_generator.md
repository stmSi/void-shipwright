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

- `Light Raider`: fast attack craft with clipped hard-surface wings and compact nose guns.
- `Missile Corvette`: broad reinforced hull, blunt prow, ordnance deck, missile pod banks, stabilizers, and auxiliary modules.
- `Interceptor`: narrow pursuit hull, clipped swept wings, canards, oversized engines, and compact cannons.
- `Gunship`: broad weapons platform with stub wings, weapon sponsons, heavy nose cannons, and side cannons.
- `Freighter`: long truss spine, cargo blocks, side rails, bridge cab, and rear engine tug.
- `Heavy Fighter`: twin-engine combat craft with broad shoulders, clipped swept wings, and heavy nose guns.
- `Bomber`: long strike craft with reinforced keel, ordnance doors, and low stabilizers.
- `Patrol Cutter`: compact security/naval cutter with command deck, mission racks, and cutter prow.
- `Explorer`: long-range survey ship with sensor masts, fuel pods, and dorsal survey module.
- `Dropship`: reinforced troop transport with side doors, belly ramp, and lift engines.
- `Mining Ship`: industrial extractor with cutter boom, ore canisters, and processing bay.
- `Salvage Ship`: asymmetrical recovery craft with grappler arms, processing bay, and scrap canister.
- `Medical Ship`: rescue craft with triage module, life-support pods, rescue lights, and quieter engines.
- `Racing Ship`: slim racing hull with clipped side wings and oversized thrust pods.
- `Luxury Yacht`: sleek touring hull with panoramic observation lounge, trim spine, and integrated nacelles.

`Hull Profile`, `Hull Length`, `Hull Width`, `Hull Height`, `Wing Span`, and `Engine Scale` control silhouette.

`Structure Density` controls attached hard-surface massing: beveled shoulder blocks, side chine structures, recessed side frames, and aft engine buttresses. These are structural hull pieces rather than floating detail meshes, so higher values make ships read more engineered and corner-rich.

`Variant` now controls visual construction, not only metadata. `default` derives a repeatable variation from ship type, role, faction, and seed. Named presets force a specific silhouette family: `blade`, `fork`, `hammerhead`, `outrigger`, `twinboom`, `keel`, `broadwing`, `carrier`, `compact`, and `asymmetric`. These presets change hull proportions and add connected silhouette modules such as split prongs, outrigger engines, deep keels, cargo bays, VLS batteries, tug engines, and wide stabilizers.

`Weapon Density`, `Missile Density`, `Cargo Density`, and `Asymmetry` control visible ship systems. Missile corvettes respond strongly to `Missile Density`; higher values add more pod banks and more cells per bank.

`Decal Density`, `Wear Amount`, and `Glow Strength` control surface finish, texture-painted livery, chipped edges, and emissive detail. Extra armor shell, top panel, accent spine, panel seam, armor tile, micro vent, raider spike, greeble, wing decal, hull livery stripe, faction insignia, light-slit, nose-chevron, paint-scuff, winglet, and mining-manipulator mesh layers are not generated; the add-on keeps surface complexity in lighting strips, engine cable runs, and generated texture paint.

`Texture Workflow` controls how ship surface materials are built. `Painted Textures` is the default and creates Base Color, glTF-packed Metallic-Roughness, and Normal image maps for each part family. `Procedural Shader` keeps the older Blender shader-node workflow available for comparison.

`Texture Resolution` controls the exported image map size per material family. The default is `256`; for performance, the CPU-heavy painted mask pass samples at `128` internally and upscales to the exported `256` image. `64` and `128` paint at native resolution. The supported range is `64` to `256`.

`Material Style` selects the metal family. Current styles are `Gunmetal`, `Worn Steel`, `Dark Titanium`, `Rusted Iron`, `Oxidized Copper`, and `Painted Composite`.

`Rust`, `Scratches`, and `Texture Scale` control oxide coverage, bright scratched edges, painted panel-line frequency, sparse angular corrosion, roughness breakup, metallic variation, chipped micro scratches, service markings, warning stripes, machined rib/detail lines, fastener/cavity normal detail, and normal-map strength. The painted texture workflow avoids broad directional bands and brown base-color grain so surfaces read as painted or treated metal rather than wood.

Generated ships use separate material families per part role instead of one shared hull material. `Material Style` controls the primary body shell, while wing skins, livery edges, upper plating, dark inset metal, underbody structure, heat-stained engine shells, blued weapon metal, cargo pods, system bays, dark inset detail, chipped edge wear, and painted trim use role-specific internal profiles so the model reads like layered hard-surface construction.

Every generated mesh receives a `VS_PaintedUV` box-projected UV map so generated image textures can export through glTF/GLB and remain usable in Godot. Painted panel lines and chips are texture data, not extra floating mesh layers.

Enable `Custom Colors` only when the faction palette should be overridden by the primary, accent, and emissive color pickers.

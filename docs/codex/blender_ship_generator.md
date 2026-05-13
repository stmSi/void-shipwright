# Blender Ship Generator

Void Shipwright is a Blender 4 add-on that generates procedural spaceship source assets for Godot. Blender owns visual meshes and marker placement only. Gameplay behavior belongs in Godot.

## Add-on Layout

- `void_shipwright/__init__.py` registers the add-on.
- `void_shipwright/properties.py` defines panel settings.
- `void_shipwright/operators.py` exposes generate and metadata export actions.
- `void_shipwright/geometry.py` creates deterministic meshes, sockets, proxies, and markers.
- `void_shipwright/design_language.py` defines the art-direction grammar used by visual quality, silhouette, faction geometry, and class-specific shape language.
- `void_shipwright/modular.py` defines ship frames, hardpoint layouts, component slots, default recommendations, and subsystem layout metadata.
- `void_shipwright/material_library.py` defines premium PBR material categories, material presets, texture quality levels, and faction/class material language.
- `void_shipwright/textures.py` creates deterministic generated texture-paint PBR maps and premium glass/emissive shader materials.
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
- `Boarding Frigate`: reinforced boarding craft with docking collars, grapple rails, and boarding hardpoints.
- `Freighter`: long truss spine, cargo blocks, side rails, bridge cab, and rear engine tug.
- `Heavy Cruiser`: large combat hull with command tower, weapons deck, side batteries, and cruiser engines.
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
- `Boss Capital Ship`: oversized multi-section boss hull with capital hardpoints and additional damage routing.

`Ship Frame` controls modular metadata. `Auto From Ship Type` maps visual ship types to frame data, while direct frame choices let a designer generate a visual hull with a different runtime frame contract.

`Visual Quality` controls the geometry hierarchy. `Draft` keeps a fast silhouette pass, `Standard` adds balanced secondary forms, `Hero` is the default screenshot-grade mode, and `Cinematic` generates the densest connected hard-surface geometry.

`Design Language` controls art direction. `Auto` chooses from the ship type and faction. Direct choices include `Military`, `Pirate`, `Industrial`, `Luxury`, `Ancient`, `Racing`, and `Cargo`.

`Silhouette Bias` adjusts the primary read: `Balanced`, `Sleek`, `Broad`, `Tall`, `Asymmetric`, or `Capital`.

`Hull Profile`, `Hull Length`, `Hull Width`, `Hull Height`, `Wing Span`, and `Engine Scale` control base silhouette.

`Structure Density` controls attached hard-surface massing: beveled shoulder blocks, side chine structures, recessed side frames, aft engine buttresses, command tower tiers, bridge window bands, sensor mast bases, cargo latches, and module hatches. These are structural hull pieces rather than floating detail meshes, so higher values make ships read more engineered and corner-rich.

`Surface Geometry`, `Armor Layers`, `Panel Geometry`, `Engine Complexity`, `Bridge Complexity`, and `Faction Geometry` control the art-quality geometry pass. These settings create actual mesh detail: armor terraces, recessed service panels, side bays, hangar frames, vents, radiator fins, engine nacelles, heat rings, turret bases, cockpit/bridge strips, docking structures, and faction-specific modules.

Visual meshes receive automatic hard-surface beveling and weighted normals. Hero/cinematic ships use higher segment counts on engines, pods, torus rings, canopies, barrels, antennae, and cable curves so parts do not read as low-poly blocks. Collision proxies remain simple and are not affected by the visual bevel pass.

`Avoid Boxy Shapes` enables a Blender-side quality check. If a generated ship lacks enough silhouette hierarchy, connected panels, engine architecture, bridge/cockpit structure, or class-critical features, the generator adds deterministic rescue geometry before metadata export. Boss capital ships have stricter checks for armor terraces, hangar/side bays, turret decks, engine clusters, command citadel, and ventral keel.

`Hardpoint Preset`, `Component Preset`, `Loadout Metadata`, and `Show Hardpoints` control exported modular metadata and `SOCKET_HP_*` helper visibility. Blender creates marker sockets and JSON only; equipment behavior is deferred to runtime systems.

`Variant` now controls visual construction, not only metadata. `default` derives a repeatable variation from ship type, role, faction, and seed. Named presets force a specific silhouette family: `blade`, `fork`, `hammerhead`, `outrigger`, `twinboom`, `keel`, `broadwing`, `carrier`, `compact`, `asymmetric`, `arrowhead`, `manta`, `split_nose`, `forked_prow`, `crescent`, `needle`, `dagger`, `hammerhead_refined`, `cathedral_capital`, `carrier_spine`, `luxury_swan`, `military_wedge`, `industrial_frame`, `asym_salvage`, `ring_engine`, `tri_engine`, `wide_nacelle`, `blade_wing`, `deep_keel`, `armored_citadel`, and `railgun_spine`. These presets change hull proportions and add connected silhouette modules such as split prongs, crescent wings, ring engines, capital citadels, hangar spine bays, deep keels, cargo frames, VLS batteries, tug engines, and wide stabilizers.

`Weapon Density`, `Missile Density`, `Cargo Density`, and `Asymmetry` control visible ship systems. Missile corvettes respond strongly to `Missile Density`; higher values add more pod banks and more cells per bank.

`Decal Density`, `Wear Amount`, and `Glow Strength` control surface finish, texture-painted livery, chipped edges, and emissive detail. Extra armor shell, top panel, accent spine, panel seam, armor tile, micro vent, raider spike, greeble, wing decal, hull livery stripe, faction insignia, light-slit, nose-chevron, paint-scuff, winglet, and mining-manipulator mesh layers are not generated; the add-on keeps surface complexity in attached command/module structures, lighting strips, engine cable runs, and generated texture paint.

`Texture Workflow` controls how ship surface materials are built. `Painted Textures` is the default and creates export-friendly image maps for each part family. `Procedural Shader` keeps the older Blender shader-node workflow available for comparison.

`Texture Quality` sets the PBR map target: `Low 256`, `Standard 512`, `Hero 1024`, or `Cinematic 2048`. The CPU-heavy mask pass samples at a lower internal resolution and upscales to the exported map so `512` remains practical. Use `1024` or `2048` for screenshots, not every iteration.

`Texture Resolution` is a custom map size override. It supports `64` to `2048`; the effective output uses at least the `Texture Quality` target, and raising this value can request larger maps for close screenshots.

`Material Style` selects the PBR surface language. `Auto From Class/Faction` is the default and resolves to class/faction presets such as `Naval Ceramic Armor`, `Corporate White Composite`, `Dark Military Titanium`, `Black Ops Stealth`, `Luxury Pearl Alloy`, `Racing Carbon Composite`, `Industrial Hazard Plating`, `Pirate Salvaged Metal`, `Ancient Iridescent Alloy`, `Mining Worn Industrial`, `Medical Rescue Composite`, and `Trade Consortium Cargo Paint`. Legacy styles remain available for compatibility: `Gunmetal`, `Worn Steel`, `Dark Titanium`, `Rusted Iron`, `Oxidized Copper`, and `Painted Composite`.

`Material Complexity`, `Paint Layer`, `Roughness Variation`, `Metallic Variation`, `Edge Wear`, `Cavity Dirt`, `Heat Stain`, `Soot`, `Decals`, `Livery`, `Emissive Density`, `Glass Tint`, `Engine Heat`, and `Faction Material` control the layered manufactured surface response. These values drive masks for base metal/composite, paint, exposed metal, cavity dirt, panel seams, heat discoloration, warning markings, abstract faction markings, and emissive accents. The material system avoids broad brown grain and uncontrolled noise so ships do not read as wood, stone, or muddy camouflage.

Generated painted materials always create Base Color, glTF-packed Metallic-Roughness, Normal, Emissive, and AO maps when the relevant toggles are enabled. `Ultra` material complexity or explicit debug toggles can also create Height, Curvature/Edge Wear, Dirt, Paint, Heat, Decal, and Material ID masks. These maps are generated procedurally and packed into the Blender file for export-friendly workflows.

Generated ships use separate material families per part role instead of one shared hull material. The primary body shell, wing skins, livery edges, upper plating, dark inset metal, underbody structure, heat-stained engine shells, blued weapon metal, cargo pods, system bays, missile bay interiors, dark inset detail, chipped edge wear, premium glass, controlled emissive strips, and painted trim use role-specific internal profiles so the model reads like layered hard-surface construction.

Faction material language affects more than color. Pirates get salvaged mixed plates and patched wear; navy and corporate ships get cleaner ceramic/titanium plating; trade ships get cargo labels and warning stripes; mining ships get dust, grime, and industrial paint; smugglers get matte stealth panels; ancient relic ships get clean iridescent alloy and glowing seams.

Every generated mesh receives a `VS_PaintedUV` box-projected UV map so generated image textures can export through glTF/GLB and remain usable in Godot. Painted panel lines and chips are texture data, not extra floating mesh layers.

Enable `Custom Colors` only when the faction palette should be overridden by the primary, accent, and emissive color pickers.

## Blender Visual Smoke Test

Run this from the repository root to generate the major classes with cinematic settings and validate the visual hierarchy:

```bash
blender --background --python scripts/visual_quality_smoke.py
```

The script checks light raider, interceptor, gunship, missile corvette, boarding frigate, freighter, heavy cruiser, mining ship, salvage ship, medical ship, racing ship, luxury yacht, and boss capital ship.

## Blender Material Smoke Test

Run this from the repository root to validate the premium PBR material pipeline:

```bash
blender --background --python scripts/material_quality_smoke.py
```

The script generates light raider, interceptor, missile corvette, freighter, heavy cruiser, mining ship, medical ship, racing ship, luxury yacht, and boss capital ship. It checks material assignment, PBR value ranges, required Base Color/Metallic-Roughness/Normal/Emissive/AO maps, glass materials, emissive materials, faction identity, and over-dirty clean-faction materials.

## Recommended Cinematic Settings

For the current best-looking boss/capital outputs:

- Ship Type: `Boss Capital Ship`
- Role: `Boss` or `Enemy`
- Faction: `Sector Navy`, `Corporate Security`, `Ancient Relic`, or `Pirate Clan`
- Detail: `Hero`
- Visual Quality: `Cinematic`
- Design Language: `Auto` or `Military`
- Silhouette Bias: `Capital`
- Avoid Boxy Shapes: enabled
- Structure Density: `0.85`
- Surface Geometry: `0.85`
- Armor Layers: `0.75`
- Panel Geometry: `0.75`
- Engine Complexity: `0.90`
- Bridge Complexity: `0.85`
- Texture Quality: `Hero` or `Cinematic`
- Texture Resolution: `1024` or `2048`
- Material Style: `Auto`, `Dark Military Titanium`, `Naval Ceramic Armor`, `Corporate White Composite`, or `Ancient Iridescent Alloy`
- Material Complexity: `High`
- Roughness Variation: `0.65`
- Metallic Variation: `0.45`
- Edge Wear: `0.25` to `0.45`
- Cavity Dirt: `0.35` to `0.55`
- Decals: `0.45`
- Emissive Density: `0.40`
- Engine Heat: `0.75`

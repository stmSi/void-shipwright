# Material Texture Pipeline

Void Shipwright generates original procedural PBR materials for Blender source assets. The material pipeline is export-friendly first: generated image maps are assigned through Blender nodes so GLB/glTF workflows can carry the important surface data forward.

## Ownership

Blender owns:

- Visual material assignment.
- Procedural PBR image map generation.
- Glass, emissive, engine heat, decal, paint, dirt, and material ID masks.
- Faction and ship-class material identity.

Godot owns runtime interpretation:

- Damage, shield, heat, power, AI, spawning, loot, and equipment behavior.
- Any runtime material swapping, gameplay highlights, or damage-state effects.

## Material Presets

Legacy styles remain available: `gunmetal`, `worn_steel`, `dark_titanium`, `rusted_iron`, `oxidized_copper`, and `painted_composite`.

Premium presets add stronger PBR intent:

- `naval_ceramic_armor`
- `corporate_white_composite`
- `dark_military_titanium`
- `black_ops_stealth`
- `luxury_pearl_alloy`
- `racing_carbon_composite`
- `industrial_hazard_plating`
- `pirate_salvaged_metal`
- `ancient_iridescent_alloy`
- `mining_worn_industrial`
- `medical_rescue_composite`
- `trade_consortium_cargo_paint`

`auto` resolves a preset from ship class and faction. This is the recommended default.

## Generated Maps

The painted texture workflow creates:

- Base Color / Albedo
- glTF-packed Metallic-Roughness
- Normal
- Emissive
- Ambient Occlusion

Optional/debug maps can also be generated:

- Height / Bump
- Curvature / Edge Wear
- Dirt / Grime
- Decal
- Paint
- Heat Stain
- Material ID

The maps are procedural. No paid or external texture assets are required.

## Texture Quality

Texture quality targets:

- `low`: 256
- `standard`: 512
- `hero`: 1024
- `cinematic`: 2048

The generator samples expensive masks at a lower internal resolution and upscales to the target map size. Use `standard` for iteration. Use `hero` or `cinematic` for screenshots or close hero ships.

## Layer Model

The material generator builds masks for:

- Base metal or composite substrate.
- Paint layer.
- Exposed metal edge wear.
- Cavity dirt and panel seam darkening.
- Oil streaks and controlled grime.
- Heat discoloration and soot on engine/weapon parts.
- Warning stripes and abstract generated decals.
- Faction livery and accent overlays.
- Emissive light strips, windows, engine cores, and ancient seams.

The intent is manufactured aerospace surfacing, not random noise or broad rust.

## Faction Identity

Faction material identity affects palette, wear, dirt, decals, and glow:

- `pirate_clan`: salvaged mixed plates, patched paint, exposed metal, warm reactor glow.
- `sector_navy`: clean ceramic/titanium plating, organized trim, controlled scratches.
- `trade_consortium`: cargo paint, labels, loading scuffs, warning stripes.
- `mining_guild`: industrial yellow/orange, dust, grime, worn ore hardware.
- `smuggler_network`: matte stealth panels, low-visibility markings, subtle lights.
- `corporate_security`: polished tactical white/black/blue, low rust, precise decals.
- `ancient_relic`: iridescent alloy, glowing seams, minimal human-industrial dirt.
- `independent`: practical mixed civilian materials with moderate wear.

## Class Identity

Class material presets reinforce ship purpose:

- Interceptors and racers use clean titanium/carbon and strong engine glow.
- Gunships and cruisers use military armor, dark insets, and worn weapon metals.
- Missile corvettes emphasize bay interiors, warning stripes, and ordnance labels.
- Freighters use cargo paint, loading marks, and industrial scuffs.
- Mining and salvage ships use grime, dust, oil, and worn utility materials.
- Medical ships use clean rescue composite and emergency strobes.
- Luxury yachts use pearl composite, brushed trim, and panoramic glass.
- Boss capital ships use multi-zone armor, command glass, hangar lights, heat zones, turret wear, and scale-readable paneling.

## Validation

`scripts/material_quality_smoke.py` checks:

- Meshes have assigned materials.
- PBR values stay in valid ranges.
- Base Color, Metallic-Roughness, Normal, Emissive, and AO maps exist.
- Glass exists on cockpit/bridge ships.
- Emissive materials exist without becoming giant glow slabs.
- Clean factions are not over-rusted or over-dirtied.
- Faction material identity is represented.

Run:

```bash
blender --background --python scripts/material_quality_smoke.py
```

## Recommended Screenshot Settings

- Visual Quality: `Cinematic`
- Texture Quality: `Hero` or `Cinematic`
- Material Style: `Auto`, `Dark Military Titanium`, `Naval Ceramic Armor`, `Corporate White Composite`, or `Ancient Iridescent Alloy`
- Material Complexity: `High`
- Roughness Variation: `0.65`
- Metallic Variation: `0.45`
- Edge Wear: `0.25` to `0.45`
- Cavity Dirt: `0.35` to `0.55`
- Decals: `0.45`
- Emissive Density: `0.40`
- Engine Heat: `0.75`
- Texture Resolution: `1024` or `2048`
- Glow Strength: `0.8` to `1.2`


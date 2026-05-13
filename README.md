# Blender Spaceship Generator

## Made By OpenAI Chatgpts Codex AI Assistence

This repository contains the first pass of the `Void Shipwright` pipeline:

## Sample

![Void Shipwright generated spaceship sample](screenshot.png)

- A modular Blender 4 add-on in `void_shipwright/`.
- Deterministic premium PBR material generation with Base Color, glTF-packed Metallic-Roughness, Normal, Emissive, AO, layered paint, roughness/metallic variation, glass, engine heat, decals, and faction/class material identity.
- A Blender-side art-direction grammar for cinematic silhouettes, class-specific ship architecture, connected armor/panel/engine geometry, and visual-quality validation.
- A Godot 4 editor helper in `godot/addons/void_shipwright_importer/`.
- A JSON metadata contract in `schemas/ship_metadata.schema.json`.
- Example generated metadata in `examples/generated/void_ship_example.metadata.json`.

Read `AGENTS.md` first, then the docs in `docs/codex/` before changing generation behavior.
For material work, start with `docs/codex/material_texture_pipeline.md`.

## Blender Visual Smoke Test

```bash
blender --background --python scripts/visual_quality_smoke.py
```

This generates the major ship classes with cinematic visual settings and fails if the geometry hierarchy is too weak.

## Blender Material Smoke Test

```bash
blender --background --python scripts/material_quality_smoke.py
```

This validates the premium material pipeline across major ship classes, including PBR maps, glass, emissive materials, and faction/class material identity.

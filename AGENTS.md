# AGENTS.md

## Project Context

This project is a space combat game using:

- Godot 4 for the game engine
- Blender for procedural spaceship asset generation
- A custom Blender add-on named Void Shipwright
- A Godot-side ship importer / ship factory system

The spaceship generator must support all ship types, not only the player ship.

Supported roles:
- player
- enemy
- ally
- neutral
- civilian
- boss
- drone
- background traffic

Supported factions:
- pirate_clan
- sector_navy
- trade_consortium
- mining_guild
- smuggler_network
- corporate_security
- ancient_relic
- independent

## Core Rule

Blender generates:

- visual mesh
- sockets
- collision proxies
- damage-zone markers
- VFX markers
- camera markers
- JSON metadata

Godot handles:

- node scene structure
- movement
- AI
- weapons
- damage
- shields
- loot
- boarding
- spawning
- faction behavior

Do not create a Blender-only solution.
Every generated ship must be compatible with Godot's node-based scene system.

## Important Docs

Before working on the ship generator, read:

- docs/codex/blender_ship_generator.md
- docs/codex/godot_ship_node_pipeline.md
- docs/codex/ship_metadata_schema.md

## Coding Standards

- Keep the Blender add-on modular.
- Do not put all logic inside `__init__.py`.
- Do not use unsafe `eval` or `exec`.
- Validate enum values.
- Use deterministic generation based on seed.
- Use clear object prefixes:
  - MESH_
  - SOCKET_
  - COLLISION_
  - DAMAGE_
  - VFX_
  - CAMERA_
  - TARGET_

## Godot Compatibility

Generated Blender objects must use Godot-friendly names.

Required sockets include:

- SOCKET_Weapon_Front_01
- SOCKET_Weapon_Front_02
- SOCKET_Weapon_Left_01
- SOCKET_Weapon_Right_01
- SOCKET_Missile_Left_01
- SOCKET_Missile_Right_01
- SOCKET_Engine_Main_01
- SOCKET_Engine_Left_01
- SOCKET_Engine_Right_01
- SOCKET_Camera_Follow
- SOCKET_Camera_Look_At
- SOCKET_Target_Lock_Center
- SOCKET_Loot_Drop
- SOCKET_Boarding_Attach

Required damage markers include:

- DAMAGE_Hull
- DAMAGE_Engine
- DAMAGE_Weapons
- DAMAGE_Cargo
- DAMAGE_Bridge
- DAMAGE_Shield_Generator

Required collision proxy names include:

- COLLISION_Hull-colonly
- COLLISION_Engine-colonly
- COLLISION_Cargo-colonly
- COLLISION_Bridge-colonly

## Expected Output

When implementing features, update both sides when needed:

1. Blender add-on code
2. Godot importer / builder code
3. Metadata schema
4. Example generated ship metadata
5. Documentation

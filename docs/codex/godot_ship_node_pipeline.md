# Godot Ship Node Pipeline

Godot turns a Void Shipwright export into a gameplay-ready scene. Blender does not create movement, AI, weapons, damage, shields, loot, boarding, spawning, or faction behavior.

## Expected Scene Shape

The builder creates this node shape:

```text
ShipRoot (Node3D)
  Visuals (Node3D)
    MESH_* imported visual nodes
  Sockets (Node3D)
    SOCKET_* Marker3D nodes
  Collision (Node3D)
    COLLISION_* StaticBody3D nodes
      CollisionShape3D
  DamageZones (Node3D)
    DAMAGE_* Marker3D nodes
  VFX (Node3D)
    VFX_* Marker3D nodes
  CAMERA_* Marker3D nodes
```

Gameplay systems should query marker names or metadata, then attach weapons, engines, camera rigs, loot drops, boarding interactions, target locks, and VFX emitters.

## Import Flow

1. Export the generated Blender asset and metadata JSON from Blender.
2. Import the mesh asset into Godot.
3. Enable `addons/void_shipwright_importer`.
4. Select the imported ship root.
5. Run `Project > Tools > Void Shipwright/Build Ship Scene`.
6. Save the generated scene as a reusable `.tscn`.

## Axis Conversion

Metadata records Blender source axes and Godot target axes. The included builder converts positions from Blender `(X, Y, Z)` into Godot `(X, Z, -Y)`.

If a project uses a different export axis configuration, update `ship_builder.gd` and document that conversion here.

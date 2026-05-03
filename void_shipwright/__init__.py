"""Void Shipwright Blender add-on entry point."""

from __future__ import annotations

bl_info = {
    "name": "Void Shipwright",
    "author": "Void Shipwright Contributors",
    "version": (0, 2, 5),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Void Shipwright",
    "description": "Procedural Godot-compatible spaceship asset generator",
    "category": "Object",
}

try:
    import bpy as _bpy  # noqa: F401
except ModuleNotFoundError:
    operators = None
    panel = None
    properties = None
else:
    from . import operators, panel, properties


def register() -> None:
    if properties is None or operators is None or panel is None:
        raise RuntimeError("Void Shipwright can only be registered inside Blender.")
    properties.register()
    operators.register()
    panel.register()


def unregister() -> None:
    if properties is None or operators is None or panel is None:
        return
    panel.unregister()
    operators.unregister()
    properties.unregister()

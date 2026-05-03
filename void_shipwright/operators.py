"""Blender operators exposed by the Void Shipwright add-on."""

from __future__ import annotations

import bpy
from bpy.props import StringProperty

from .geometry import ShipGenerationConfig, generate_ship
from .metadata import write_metadata


class VOID_SHIPWRIGHT_OT_generate_ship(bpy.types.Operator):
    bl_idname = "void_shipwright.generate_ship"
    bl_label = "Generate Godot Ship"
    bl_description = "Generate a deterministic Godot-compatible spaceship"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.void_shipwright_settings
        metadata = generate_ship(
            ShipGenerationConfig(
                role=settings.role,
                faction=settings.faction,
                seed=settings.seed,
                ship_type=settings.ship_type,
                ship_id=settings.ship_id,
                variant=settings.variant,
                clear_existing=settings.clear_existing,
                detail_level=settings.detail_level,
                hull_profile=settings.hull_profile,
                wing_span=settings.wing_span,
                engine_scale=settings.engine_scale,
                hull_length=settings.hull_length,
                hull_width=settings.hull_width,
                hull_height=settings.hull_height,
                armor_density=settings.armor_density,
                greeble_density=settings.greeble_density,
                decal_density=settings.decal_density,
                wear_amount=settings.wear_amount,
                glow_strength=settings.glow_strength,
                material_style=settings.material_style,
                rust_amount=settings.rust_amount,
                scratch_amount=settings.scratch_amount,
                texture_scale=settings.texture_scale,
                weapon_density=settings.weapon_density,
                missile_density=settings.missile_density,
                cargo_density=settings.cargo_density,
                asymmetry=settings.asymmetry,
                use_custom_colors=settings.use_custom_colors,
                primary_hue=tuple(settings.primary_hue),
                accent_hue=tuple(settings.accent_hue),
                emissive_hue=tuple(settings.emissive_hue),
                show_helpers=settings.show_helpers,
                presentation_scene=settings.presentation_scene,
            )
        )
        context.scene.void_shipwright_last_metadata = str(metadata)
        self.report({"INFO"}, f"Generated {settings.ship_id} for {settings.role}/{settings.faction}")
        return {"FINISHED"}


class VOID_SHIPWRIGHT_OT_export_metadata(bpy.types.Operator):
    bl_idname = "void_shipwright.export_metadata"
    bl_label = "Export Ship Metadata"
    bl_description = "Generate a ship and export its JSON metadata"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context: bpy.types.Context) -> set[str]:
        settings = context.scene.void_shipwright_settings
        metadata = generate_ship(
            ShipGenerationConfig(
                role=settings.role,
                faction=settings.faction,
                seed=settings.seed,
                ship_type=settings.ship_type,
                ship_id=settings.ship_id,
                variant=settings.variant,
                clear_existing=settings.clear_existing,
                detail_level=settings.detail_level,
                hull_profile=settings.hull_profile,
                wing_span=settings.wing_span,
                engine_scale=settings.engine_scale,
                hull_length=settings.hull_length,
                hull_width=settings.hull_width,
                hull_height=settings.hull_height,
                armor_density=settings.armor_density,
                greeble_density=settings.greeble_density,
                decal_density=settings.decal_density,
                wear_amount=settings.wear_amount,
                glow_strength=settings.glow_strength,
                material_style=settings.material_style,
                rust_amount=settings.rust_amount,
                scratch_amount=settings.scratch_amount,
                texture_scale=settings.texture_scale,
                weapon_density=settings.weapon_density,
                missile_density=settings.missile_density,
                cargo_density=settings.cargo_density,
                asymmetry=settings.asymmetry,
                use_custom_colors=settings.use_custom_colors,
                primary_hue=tuple(settings.primary_hue),
                accent_hue=tuple(settings.accent_hue),
                emissive_hue=tuple(settings.emissive_hue),
                show_helpers=settings.show_helpers,
                presentation_scene=settings.presentation_scene,
            )
        )
        output_path = bpy.path.abspath(settings.metadata_path)
        write_metadata(output_path, metadata)
        self.report({"INFO"}, f"Exported metadata to {output_path}")
        return {"FINISHED"}


CLASSES = (
    VOID_SHIPWRIGHT_OT_generate_ship,
    VOID_SHIPWRIGHT_OT_export_metadata,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.void_shipwright_last_metadata = StringProperty(
        name="Last Ship Metadata",
        description="Last metadata payload generated by Void Shipwright",
        default="",
    )


def unregister() -> None:
    if hasattr(bpy.types.Scene, "void_shipwright_last_metadata"):
        del bpy.types.Scene.void_shipwright_last_metadata
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

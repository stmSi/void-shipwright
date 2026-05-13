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
                ship_frame=settings.ship_frame,
                ship_id=settings.ship_id,
                variant=settings.variant,
                clear_existing=settings.clear_existing,
                detail_level=settings.detail_level,
                visual_quality=settings.visual_quality,
                design_language=settings.design_language,
                silhouette_bias=settings.silhouette_bias,
                hull_profile=settings.hull_profile,
                wing_span=settings.wing_span,
                engine_scale=settings.engine_scale,
                hull_length=settings.hull_length,
                hull_width=settings.hull_width,
                hull_height=settings.hull_height,
                structure_density=settings.structure_density,
                surface_geometry_density=settings.surface_geometry_density,
                armor_layer_density=settings.armor_layer_density,
                panel_geometry_density=settings.panel_geometry_density,
                engine_complexity=settings.engine_complexity,
                cockpit_bridge_complexity=settings.cockpit_bridge_complexity,
                faction_geometry_influence=settings.faction_geometry_influence,
                avoid_boxy_shapes=settings.avoid_boxy_shapes,
                hardpoint_preset=settings.hardpoint_preset,
                component_slot_preset=settings.component_slot_preset,
                generate_loadout_metadata=settings.generate_loadout_metadata,
                decal_density=settings.decal_density,
                wear_amount=settings.wear_amount,
                glow_strength=settings.glow_strength,
                texture_workflow=settings.texture_workflow,
                texture_quality=settings.texture_quality,
                texture_resolution=settings.texture_resolution,
                material_style=settings.material_style,
                material_complexity=settings.material_complexity,
                paint_layer_strength=settings.paint_layer_strength,
                roughness_variation=settings.roughness_variation,
                metallic_variation=settings.metallic_variation,
                edge_wear_amount=settings.edge_wear_amount,
                cavity_dirt_amount=settings.cavity_dirt_amount,
                heat_stain_amount=settings.heat_stain_amount,
                soot_amount=settings.soot_amount,
                decal_amount=settings.decal_amount,
                livery_amount=settings.livery_amount,
                emissive_density=settings.emissive_density,
                glass_tint=settings.glass_tint,
                engine_heat_intensity=settings.engine_heat_intensity,
                faction_material_influence=settings.faction_material_influence,
                generate_emissive_map=settings.generate_emissive_map,
                generate_ao_map=settings.generate_ao_map,
                generate_decal_mask=settings.generate_decal_mask,
                generate_material_id_mask=settings.generate_material_id_mask,
                export_texture_maps=settings.export_texture_maps,
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
                show_hardpoint_helpers=settings.show_hardpoint_helpers,
                show_design_helpers=settings.show_design_helpers,
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
                ship_frame=settings.ship_frame,
                ship_id=settings.ship_id,
                variant=settings.variant,
                clear_existing=settings.clear_existing,
                detail_level=settings.detail_level,
                visual_quality=settings.visual_quality,
                design_language=settings.design_language,
                silhouette_bias=settings.silhouette_bias,
                hull_profile=settings.hull_profile,
                wing_span=settings.wing_span,
                engine_scale=settings.engine_scale,
                hull_length=settings.hull_length,
                hull_width=settings.hull_width,
                hull_height=settings.hull_height,
                structure_density=settings.structure_density,
                surface_geometry_density=settings.surface_geometry_density,
                armor_layer_density=settings.armor_layer_density,
                panel_geometry_density=settings.panel_geometry_density,
                engine_complexity=settings.engine_complexity,
                cockpit_bridge_complexity=settings.cockpit_bridge_complexity,
                faction_geometry_influence=settings.faction_geometry_influence,
                avoid_boxy_shapes=settings.avoid_boxy_shapes,
                hardpoint_preset=settings.hardpoint_preset,
                component_slot_preset=settings.component_slot_preset,
                generate_loadout_metadata=settings.generate_loadout_metadata,
                decal_density=settings.decal_density,
                wear_amount=settings.wear_amount,
                glow_strength=settings.glow_strength,
                texture_workflow=settings.texture_workflow,
                texture_quality=settings.texture_quality,
                texture_resolution=settings.texture_resolution,
                material_style=settings.material_style,
                material_complexity=settings.material_complexity,
                paint_layer_strength=settings.paint_layer_strength,
                roughness_variation=settings.roughness_variation,
                metallic_variation=settings.metallic_variation,
                edge_wear_amount=settings.edge_wear_amount,
                cavity_dirt_amount=settings.cavity_dirt_amount,
                heat_stain_amount=settings.heat_stain_amount,
                soot_amount=settings.soot_amount,
                decal_amount=settings.decal_amount,
                livery_amount=settings.livery_amount,
                emissive_density=settings.emissive_density,
                glass_tint=settings.glass_tint,
                engine_heat_intensity=settings.engine_heat_intensity,
                faction_material_influence=settings.faction_material_influence,
                generate_emissive_map=settings.generate_emissive_map,
                generate_ao_map=settings.generate_ao_map,
                generate_decal_mask=settings.generate_decal_mask,
                generate_material_id_mask=settings.generate_material_id_mask,
                export_texture_maps=settings.export_texture_maps,
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
                show_hardpoint_helpers=settings.show_hardpoint_helpers,
                show_design_helpers=settings.show_design_helpers,
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

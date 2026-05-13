"""User interface panel for Void Shipwright."""

from __future__ import annotations

import bpy


class VOID_SHIPWRIGHT_PT_generator(bpy.types.Panel):
    bl_label = "Void Shipwright"
    bl_idname = "VOID_SHIPWRIGHT_PT_generator"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Void Shipwright"

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        settings = context.scene.void_shipwright_settings

        layout.prop(settings, "ship_id")
        layout.prop(settings, "variant")
        layout.prop(settings, "ship_type")
        layout.prop(settings, "ship_frame")
        layout.prop(settings, "role")
        layout.prop(settings, "faction")
        layout.prop(settings, "seed")
        layout.prop(settings, "clear_existing")

        action_row = layout.row(align=True)
        action_row.scale_y = 1.25
        action_row.operator("void_shipwright.generate_ship", text="Generate Ship")
        action_row.operator("void_shipwright.export_metadata", text="Generate + Export")

        layout.separator()
        layout.label(text="Silhouette")
        layout.prop(settings, "detail_level")
        layout.prop(settings, "visual_quality")
        layout.prop(settings, "design_language")
        layout.prop(settings, "silhouette_bias")
        layout.prop(settings, "hull_profile")
        layout.prop(settings, "hull_length", slider=True)
        layout.prop(settings, "hull_width", slider=True)
        layout.prop(settings, "hull_height", slider=True)
        layout.prop(settings, "wing_span", slider=True)
        layout.prop(settings, "engine_scale", slider=True)
        layout.prop(settings, "structure_density", slider=True)
        layout.prop(settings, "surface_geometry_density", slider=True)
        layout.prop(settings, "armor_layer_density", slider=True)
        layout.prop(settings, "panel_geometry_density", slider=True)
        layout.prop(settings, "engine_complexity", slider=True)
        layout.prop(settings, "cockpit_bridge_complexity", slider=True)
        layout.prop(settings, "faction_geometry_influence", slider=True)
        layout.prop(settings, "avoid_boxy_shapes")
        layout.prop(settings, "hardpoint_preset")
        layout.prop(settings, "component_slot_preset")
        layout.prop(settings, "generate_loadout_metadata")

        layout.separator()
        layout.label(text="Systems")
        layout.prop(settings, "weapon_density", slider=True)
        layout.prop(settings, "missile_density", slider=True)
        layout.prop(settings, "cargo_density", slider=True)
        layout.prop(settings, "asymmetry", slider=True)

        layout.separator()
        layout.label(text="Surface Detail")
        layout.prop(settings, "decal_density", slider=True)
        layout.prop(settings, "wear_amount", slider=True)
        layout.prop(settings, "glow_strength", slider=True)
        layout.prop(settings, "texture_workflow")
        layout.prop(settings, "texture_quality")
        layout.prop(settings, "material_style")
        layout.prop(settings, "material_complexity")
        layout.prop(settings, "texture_resolution")
        layout.prop(settings, "paint_layer_strength", slider=True)
        layout.prop(settings, "roughness_variation", slider=True)
        layout.prop(settings, "metallic_variation", slider=True)
        layout.prop(settings, "edge_wear_amount", slider=True)
        layout.prop(settings, "cavity_dirt_amount", slider=True)
        layout.prop(settings, "heat_stain_amount", slider=True)
        layout.prop(settings, "soot_amount", slider=True)
        layout.prop(settings, "decal_amount", slider=True)
        layout.prop(settings, "livery_amount", slider=True)
        layout.prop(settings, "emissive_density", slider=True)
        layout.prop(settings, "glass_tint", slider=True)
        layout.prop(settings, "engine_heat_intensity", slider=True)
        layout.prop(settings, "faction_material_influence", slider=True)
        layout.prop(settings, "generate_emissive_map")
        layout.prop(settings, "generate_ao_map")
        layout.prop(settings, "generate_decal_mask")
        layout.prop(settings, "generate_material_id_mask")
        layout.prop(settings, "export_texture_maps")
        layout.prop(settings, "rust_amount", slider=True)
        layout.prop(settings, "scratch_amount", slider=True)
        layout.prop(settings, "texture_scale", slider=True)

        layout.separator()
        layout.label(text="Palette")
        layout.prop(settings, "use_custom_colors")
        color_column = layout.column()
        color_column.enabled = settings.use_custom_colors
        color_column.prop(settings, "primary_hue")
        color_column.prop(settings, "accent_hue")
        color_column.prop(settings, "emissive_hue")

        layout.separator()
        layout.prop(settings, "show_helpers")
        layout.prop(settings, "show_hardpoint_helpers")
        layout.prop(settings, "show_design_helpers")
        layout.prop(settings, "presentation_scene")
        layout.separator()
        layout.operator("void_shipwright.generate_ship", text="Generate Ship")
        layout.prop(settings, "metadata_path")
        layout.operator("void_shipwright.export_metadata", text="Generate and Export Metadata")


CLASSES = (VOID_SHIPWRIGHT_PT_generator,)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

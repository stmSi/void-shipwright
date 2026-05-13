"""Deterministic generated texture-paint materials for Void Shipwright."""

from __future__ import annotations

from array import array
import hashlib
from math import floor, sqrt
from typing import Any, Iterable

import bpy


def painted_metal_material(
    name: str,
    color: tuple[float, float, float, float],
    profile: dict[str, Any],
    *,
    part_name: str,
    seed: int,
    resolution: int,
    rust_amount: float,
    scratch_amount: float,
    wear_amount: float,
    decal_density: float,
    texture_scale: float,
    role_scale: float,
    accent_color: tuple[float, float, float, float],
    metallic: float | None = None,
    roughness: float | None = None,
    emission_color: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
    material_style: str = "gunmetal",
    material_complexity: str = "high",
    paint_layer_strength: float = 0.82,
    roughness_variation: float = 0.65,
    metallic_variation: float = 0.45,
    edge_wear_amount: float = 0.34,
    cavity_dirt_amount: float = 0.42,
    heat_stain_amount: float = 0.62,
    soot_amount: float = 0.28,
    decal_amount: float = 0.45,
    livery_amount: float = 0.50,
    emissive_density: float = 0.40,
    engine_heat_intensity: float = 0.75,
    faction_material_influence: float = 0.85,
    faction: str = "independent",
    ship_type: str = "light_raider",
    generate_emissive_map: bool = True,
    generate_ao_map: bool = True,
    generate_decal_mask: bool = False,
    generate_material_id_mask: bool = False,
    export_texture_maps: bool = True,
) -> bpy.types.Material:
    """Create an image-textured metal material with painted PBR maps."""
    rust_amount = _clamp(rust_amount)
    scratch_amount = _clamp(scratch_amount)
    wear_amount = _clamp(wear_amount)
    decal_density = _clamp(decal_density)
    paint_layer_strength = _clamp(paint_layer_strength)
    roughness_variation = _clamp(roughness_variation)
    metallic_variation = _clamp(metallic_variation)
    edge_wear_amount = _clamp(edge_wear_amount)
    cavity_dirt_amount = _clamp(cavity_dirt_amount)
    heat_stain_amount = _clamp(heat_stain_amount)
    soot_amount = _clamp(soot_amount)
    decal_amount = _clamp(decal_amount)
    livery_amount = _clamp(livery_amount)
    emissive_density = _clamp(emissive_density)
    engine_heat_intensity = _clamp(engine_heat_intensity)
    faction_material_influence = _clamp(faction_material_influence)
    texture_scale = max(texture_scale, 0.1)
    resolution = max(64, min(int(resolution), 2048))
    sample_resolution = _paint_sample_resolution(resolution)
    metallic_value = _clamp(profile["metallic"] if metallic is None else metallic)
    roughness_value = _clamp(profile["roughness"] if roughness is None else roughness, 0.08, 0.95)

    paint_seed = _stable_seed("void_shipwright_texture", seed, name, part_name, resolution)
    fingerprint = _texture_fingerprint(
        name,
        part_name,
        paint_seed,
        resolution,
        color,
        rust_amount,
        scratch_amount,
        wear_amount,
        decal_density,
        texture_scale,
        role_scale,
        accent_color,
        metallic_value,
        roughness_value,
        material_style,
        material_complexity,
        paint_layer_strength,
        roughness_variation,
        metallic_variation,
        edge_wear_amount,
        cavity_dirt_amount,
        heat_stain_amount,
        soot_amount,
        decal_amount,
        livery_amount,
        emissive_density,
        engine_heat_intensity,
        faction_material_influence,
        faction,
        ship_type,
        generate_emissive_map,
        generate_ao_map,
        generate_decal_mask,
        generate_material_id_mask,
        export_texture_maps,
    )
    material = bpy.data.materials.get(name)
    if _material_matches_texture_fingerprint(material, fingerprint):
        return material

    texture_maps = _paint_metal_maps(
        resolution,
        color,
        profile,
        part_name=part_name,
        seed=paint_seed,
        rust_amount=rust_amount,
        scratch_amount=scratch_amount,
        wear_amount=wear_amount,
        decal_density=decal_density,
        texture_scale=texture_scale,
        role_scale=role_scale,
        accent_color=accent_color,
        roughness_value=roughness_value,
        metallic_value=metallic_value,
        material_style=material_style,
        material_complexity=material_complexity,
        paint_layer_strength=paint_layer_strength,
        roughness_variation=roughness_variation,
        metallic_variation=metallic_variation,
        edge_wear_amount=edge_wear_amount,
        cavity_dirt_amount=cavity_dirt_amount,
        heat_stain_amount=heat_stain_amount,
        soot_amount=soot_amount,
        decal_amount=decal_amount,
        livery_amount=livery_amount,
        emissive_density=emissive_density,
        engine_heat_intensity=engine_heat_intensity,
        faction_material_influence=faction_material_influence,
        faction=faction,
        ship_type=ship_type,
        generate_emissive_map=generate_emissive_map,
        generate_ao_map=generate_ao_map,
        generate_decal_mask=generate_decal_mask,
        generate_material_id_mask=generate_material_id_mask,
    )

    safe_name = _safe_image_name(name)
    base_image = _image_from_pixels(f"{safe_name}_Paint_BaseColor", resolution, texture_maps["base_color"], colorspace="sRGB")
    metallic_roughness_image = _image_from_pixels(f"{safe_name}_Paint_MetallicRoughness", resolution, texture_maps["metallic_roughness"], colorspace="Non-Color")
    normal_image = _image_from_pixels(f"{safe_name}_Paint_Normal", resolution, texture_maps["normal"], colorspace="Non-Color")
    emissive_image = _image_from_pixels(f"{safe_name}_Paint_Emissive", resolution, texture_maps["emissive"], colorspace="sRGB") if generate_emissive_map else None
    ao_image = _image_from_pixels(f"{safe_name}_Paint_AO", resolution, texture_maps["ao"], colorspace="Non-Color") if generate_ao_map else None
    high_quality_masks = material_complexity == "ultra"
    height_image = _image_from_pixels(f"{safe_name}_Paint_Height", resolution, texture_maps["height"], colorspace="Non-Color") if high_quality_masks else None
    curvature_image = _image_from_pixels(f"{safe_name}_Paint_CurvatureWear", resolution, texture_maps["curvature"], colorspace="Non-Color") if high_quality_masks else None
    dirt_image = _image_from_pixels(f"{safe_name}_Paint_DirtMask", resolution, texture_maps["dirt"], colorspace="Non-Color") if high_quality_masks else None
    paint_image = _image_from_pixels(f"{safe_name}_Paint_PaintMask", resolution, texture_maps["paint"], colorspace="Non-Color") if high_quality_masks else None
    heat_image = _image_from_pixels(f"{safe_name}_Paint_HeatMask", resolution, texture_maps["heat"], colorspace="Non-Color") if high_quality_masks else None
    decal_image = _image_from_pixels(f"{safe_name}_Paint_DecalMask", resolution, texture_maps["decal"], colorspace="Non-Color") if generate_decal_mask else None
    material_id_image = _image_from_pixels(f"{safe_name}_Paint_MaterialID", resolution, texture_maps["material_id"], colorspace="Non-Color") if generate_material_id_mask else None

    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    material["void_shipwright_material"] = "painted_layered_metal"
    material["void_shipwright_texture_workflow"] = "procedural_texture_paint"
    material["void_shipwright_texture_resolution"] = resolution
    material["void_shipwright_texture_sample_resolution"] = sample_resolution
    material["void_shipwright_texture_fingerprint"] = fingerprint
    material["void_shipwright_rust_amount"] = round(rust_amount, 4)
    material["void_shipwright_scratch_amount"] = round(scratch_amount, 4)
    material["void_shipwright_material_style"] = material_style
    material["void_shipwright_material_complexity"] = material_complexity
    material["void_shipwright_has_emissive_map"] = bool(emissive_image)
    material["void_shipwright_has_ao_map"] = bool(ao_image)
    material["void_shipwright_has_height_map"] = bool(height_image)
    material["void_shipwright_has_decal_mask"] = bool(decal_image)
    material["void_shipwright_has_material_id_mask"] = bool(material_id_image)
    material["void_shipwright_export_texture_maps"] = bool(export_texture_maps)

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        return material

    for node in list(nodes):
        if node.name not in {"Principled BSDF", "Material Output"}:
            nodes.remove(node)

    _set_input(bsdf, "Metallic", metallic_value)
    _set_input(bsdf, "Roughness", roughness_value)
    _set_input(bsdf, "Base Color", color)
    if emission_color is not None:
        _set_input(bsdf, "Emission Color", emission_color)
        _set_input(bsdf, "Emission Strength", emission_strength)

    base_node = nodes.new("ShaderNodeTexImage")
    base_node.name = "VS_Painted_BaseColor"
    base_node.image = base_image
    metallic_roughness_node = nodes.new("ShaderNodeTexImage")
    metallic_roughness_node.name = "VS_Painted_MetallicRoughness"
    metallic_roughness_node.image = metallic_roughness_image
    separate_mr = nodes.new("ShaderNodeSeparateColor")
    separate_mr.name = "VS_Painted_Separate_MetallicRoughness"
    normal_node = nodes.new("ShaderNodeTexImage")
    normal_node.name = "VS_Painted_Normal"
    normal_node.image = normal_image
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "VS_Painted_NormalMap"
    _set_input(normal_map, "Strength", 0.38 + scratch_amount * 0.24 + edge_wear_amount * 0.20 + cavity_dirt_amount * 0.12)

    links.new(base_node.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(metallic_roughness_node.outputs["Color"], separate_mr.inputs["Color"])
    if "Green" in separate_mr.outputs:
        links.new(separate_mr.outputs["Green"], bsdf.inputs["Roughness"])
    else:
        links.new(separate_mr.outputs[1], bsdf.inputs["Roughness"])
    if "Blue" in separate_mr.outputs:
        links.new(separate_mr.outputs["Blue"], bsdf.inputs["Metallic"])
    else:
        links.new(separate_mr.outputs[2], bsdf.inputs["Metallic"])
    links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    if emissive_image is not None:
        emissive_node = nodes.new("ShaderNodeTexImage")
        emissive_node.name = "VS_Painted_Emissive"
        emissive_node.image = emissive_image
        links.new(emissive_node.outputs["Color"], bsdf.inputs["Emission Color"])
        _set_input(bsdf, "Emission Strength", max(emission_strength, emissive_density * 1.4))
    if ao_image is not None:
        ao_node = nodes.new("ShaderNodeTexImage")
        ao_node.name = "VS_Painted_AO"
        ao_node.image = ao_image
    if height_image is not None:
        height_node = nodes.new("ShaderNodeTexImage")
        height_node.name = "VS_Painted_Height"
        height_node.image = height_image
    if curvature_image is not None:
        curvature_node = nodes.new("ShaderNodeTexImage")
        curvature_node.name = "VS_Painted_CurvatureWear"
        curvature_node.image = curvature_image
    if dirt_image is not None:
        dirt_node = nodes.new("ShaderNodeTexImage")
        dirt_node.name = "VS_Painted_DirtMask"
        dirt_node.image = dirt_image
    if paint_image is not None:
        paint_node = nodes.new("ShaderNodeTexImage")
        paint_node.name = "VS_Painted_PaintMask"
        paint_node.image = paint_image
    if heat_image is not None:
        heat_node = nodes.new("ShaderNodeTexImage")
        heat_node.name = "VS_Painted_HeatMask"
        heat_node.image = heat_image
    if decal_image is not None:
        decal_node = nodes.new("ShaderNodeTexImage")
        decal_node.name = "VS_Painted_DecalMask"
        decal_node.image = decal_image
    if material_id_image is not None:
        material_id_node = nodes.new("ShaderNodeTexImage")
        material_id_node.name = "VS_Painted_MaterialID"
        material_id_node.image = material_id_image

    material.blend_method = "OPAQUE"
    return material


def premium_glass_material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    tint_strength: float,
    emission_color: tuple[float, float, float, float],
    emission_strength: float,
    reinforced: bool = False,
    luxury: bool = False,
    ancient: bool = False,
) -> bpy.types.Material:
    """Create a controlled cockpit/canopy glass material for Blender preview and export."""
    tint_strength = _clamp(tint_strength)
    alpha = _clamp(0.42 + tint_strength * 0.38, 0.25, 0.86)
    base = _mix_color(color, (0.02, 0.06, 0.08, alpha), tint_strength * 0.50)
    if luxury:
        base = _mix_color(base, (0.28, 0.45, 0.55, alpha), 0.30)
    if ancient:
        base = _mix_color(base, (0.12, 0.60, 0.48, alpha), 0.36)

    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = base
    material.use_nodes = True
    material["void_shipwright_material"] = "premium_reinforced_glass" if reinforced else "premium_cockpit_glass"
    material["void_shipwright_glass_tint"] = round(tint_strength, 4)
    material["void_shipwright_has_glass_shader"] = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        for node in list(nodes):
            if node.name not in {"Principled BSDF", "Material Output"}:
                nodes.remove(node)
        _set_input(bsdf, "Base Color", base)
        _set_input(bsdf, "Alpha", alpha)
        _set_input(bsdf, "Metallic", 0.0)
        _set_input(bsdf, "Roughness", 0.045 if luxury else 0.08 + (0.04 if reinforced else 0.0))
        _set_input(bsdf, "IOR", 1.46)
        _set_input(bsdf, "Transmission Weight", 0.24 if not reinforced else 0.10)
        _set_input(bsdf, "Coat Weight", 0.55)
        _set_input(bsdf, "Coat Roughness", 0.05)
        _set_input(bsdf, "Emission Color", emission_color)
        _set_input(bsdf, "Emission Strength", emission_strength)
        if reinforced or ancient:
            wave = nodes.new("ShaderNodeTexWave")
            wave.name = "VS_Glass_Reinforcement_Lines"
            if "Scale" in wave.inputs:
                wave.inputs["Scale"].default_value = 18.0 if reinforced else 10.0
            if "Distortion" in wave.inputs:
                wave.inputs["Distortion"].default_value = 3.0 if ancient else 0.8
            bump = nodes.new("ShaderNodeBump")
            bump.name = "VS_Glass_Fine_Line_Normal"
            _set_input(bump, "Strength", 0.030 if reinforced else 0.018)
            _set_input(bump, "Distance", 0.010)
            links.new(wave.outputs["Color"], bump.inputs["Height"])
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material.blend_method = "BLEND"
    if hasattr(material, "use_screen_refraction"):
        material.use_screen_refraction = True
    return material


def emissive_pbr_material(
    name: str,
    color: tuple[float, float, float, float],
    *,
    strength: float,
    alpha: float = 1.0,
    pulse_bias: float = 0.0,
) -> bpy.types.Material:
    """Create a contained emissive material for engines, windows, and small light strips."""
    strength = max(strength, 0.0)
    alpha = _clamp(alpha)
    material = bpy.data.materials.get(name)
    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = (color[0], color[1], color[2], alpha)
    material.use_nodes = True
    material["void_shipwright_material"] = "premium_emissive_strip"
    material["void_shipwright_emission_strength"] = round(strength, 4)

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is not None:
        for node in list(nodes):
            if node.name not in {"Principled BSDF", "Material Output"}:
                nodes.remove(node)
        base = _mix_color(color, (0.02, 0.04, 0.06, alpha), 0.35)
        _set_input(bsdf, "Base Color", base)
        _set_input(bsdf, "Alpha", alpha)
        _set_input(bsdf, "Metallic", 0.0)
        _set_input(bsdf, "Roughness", 0.24)
        _set_input(bsdf, "Emission Color", color)
        _set_input(bsdf, "Emission Strength", strength)
        if pulse_bias > 0.0:
            noise = nodes.new("ShaderNodeTexNoise")
            noise.name = "VS_Emission_Core_Breakup"
            noise.inputs["Scale"].default_value = 18.0 + pulse_bias * 18.0
            noise.inputs["Detail"].default_value = 7.0
            ramp = nodes.new("ShaderNodeValToRGB")
            ramp.name = "VS_Emission_Breakup_Ramp"
            ramp.color_ramp.elements[0].position = 0.18
            ramp.color_ramp.elements[0].color = _scale_color(color, 0.62)
            ramp.color_ramp.elements[1].position = 1.0
            ramp.color_ramp.elements[1].color = _mix_color(color, (1.0, 1.0, 1.0, alpha), 0.34)
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
            links.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
    material.blend_method = "BLEND" if alpha < 1.0 else "OPAQUE"
    return material


def evaluate_material_quality(materials: Iterable[bpy.types.Material]) -> dict[str, Any]:
    """Return a compact material quality report for Blender-side smoke tests."""
    material_list = [material for material in materials if material is not None]
    painted = [material for material in material_list if material.get("void_shipwright_material") == "painted_layered_metal"]
    glass = [material for material in material_list if material.get("void_shipwright_has_glass_shader")]
    emissive = [material for material in material_list if "emissive" in str(material.get("void_shipwright_material", "")) or material.get("void_shipwright_emission_strength", 0.0) > 0.0]
    image_nodes = []
    for material in material_list:
        if not material.use_nodes:
            continue
        image_nodes.extend(node for node in material.node_tree.nodes if node.bl_idname == "ShaderNodeTexImage" and getattr(node, "image", None) is not None)
    map_names = {node.name for node in image_nodes}
    score = 0.0
    score += 0.20 if material_list else 0.0
    score += 0.20 if painted else 0.0
    score += 0.15 if {"VS_Painted_BaseColor", "VS_Painted_MetallicRoughness", "VS_Painted_Normal"}.issubset(map_names) else 0.0
    score += 0.10 if "VS_Painted_Emissive" in map_names else 0.0
    score += 0.10 if "VS_Painted_AO" in map_names else 0.0
    score += 0.10 if glass else 0.0
    score += 0.10 if emissive else 0.0
    score += 0.05 if validate_no_flat_plastic_materials(material_list) else 0.0
    return {
        "score": round(_clamp(score), 4),
        "material_count": len(material_list),
        "painted_materials": len(painted),
        "glass_materials": len(glass),
        "emissive_materials": len(emissive),
        "image_texture_nodes": len(image_nodes),
        "map_names": sorted(map_names),
    }


def validate_pbr_ranges(materials: Iterable[bpy.types.Material]) -> bool:
    for material in materials:
        if material is None or not material.use_nodes:
            continue
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        if bsdf is None:
            continue
        for input_name in ("Metallic", "Roughness", "Alpha", "Emission Strength"):
            if input_name in bsdf.inputs:
                value = bsdf.inputs[input_name].default_value
                if input_name == "Emission Strength":
                    if value < 0.0 or value > 20.0:
                        return False
                elif value < 0.0 or value > 1.0:
                    return False
    return True


def validate_texture_resolution(materials: Iterable[bpy.types.Material], *, minimum: int = 64, maximum: int = 2048) -> bool:
    for material in materials:
        resolution = material.get("void_shipwright_texture_resolution")
        if resolution is None:
            continue
        if int(resolution) < minimum or int(resolution) > maximum:
            return False
    return True


def validate_material_assignment(objects: Iterable[bpy.types.Object]) -> bool:
    visual_meshes = [obj for obj in objects if obj.name.startswith("MESH_") and getattr(obj, "type", "") == "MESH"]
    if not visual_meshes:
        return False
    return all(obj.data.materials for obj in visual_meshes)


def validate_no_flat_plastic_materials(materials: Iterable[bpy.types.Material]) -> bool:
    painted_count = 0
    for material in materials:
        if material is None:
            continue
        if material.get("void_shipwright_material") == "painted_layered_metal":
            painted_count += 1
            if not material.get("void_shipwright_has_ao_map") and not material.get("void_shipwright_has_emissive_map"):
                return False
        if material.use_nodes:
            nodes = material.node_tree.nodes
            if nodes.get("VS_Painted_MetallicRoughness") is not None and nodes.get("VS_Painted_Normal") is None:
                return False
    return painted_count > 0


def validate_no_overdirty_materials(materials: Iterable[bpy.types.Material]) -> bool:
    for material in materials:
        rust = float(material.get("void_shipwright_rust_amount", 0.0))
        if material.get("void_shipwright_material_style") in {"corporate_white_composite", "medical_rescue_composite", "luxury_pearl_alloy", "ancient_iridescent_alloy"} and rust > 0.25:
            return False
    return True


def validate_emissive_is_not_overused(materials: Iterable[bpy.types.Material]) -> bool:
    material_list = list(materials)
    emissive_count = 0
    for material in material_list:
        if material.get("void_shipwright_has_emissive_map") or material.get("void_shipwright_emission_strength", 0.0) > 0.0:
            emissive_count += 1
    return emissive_count <= max(3, len(material_list))


def validate_faction_material_identity(materials: Iterable[bpy.types.Material], faction: str) -> bool:
    material_list = list(materials)
    styles = {str(material.get("void_shipwright_material_style", "")) for material in material_list}
    if faction == "ancient_relic":
        return "ancient_iridescent_alloy" in styles or any(material.get("void_shipwright_has_emissive_map") for material in material_list)
    if faction == "corporate_security":
        return not any(float(material.get("void_shipwright_rust_amount", 0.0)) > 0.35 for material in material_list)
    if faction == "pirate_clan":
        return any(float(material.get("void_shipwright_scratch_amount", 0.0)) >= 0.35 for material in material_list)
    return True


def _paint_metal_maps(
    resolution: int,
    color: tuple[float, float, float, float],
    profile: dict[str, Any],
    *,
    part_name: str,
    seed: int,
    rust_amount: float,
    scratch_amount: float,
    wear_amount: float,
    decal_density: float,
    texture_scale: float,
    role_scale: float,
    accent_color: tuple[float, float, float, float],
    roughness_value: float,
    metallic_value: float,
    material_style: str,
    material_complexity: str,
    paint_layer_strength: float,
    roughness_variation: float,
    metallic_variation: float,
    edge_wear_amount: float,
    cavity_dirt_amount: float,
    heat_stain_amount: float,
    soot_amount: float,
    decal_amount: float,
    livery_amount: float,
    emissive_density: float,
    engine_heat_intensity: float,
    faction_material_influence: float,
    faction: str,
    ship_type: str,
    generate_emissive_map: bool,
    generate_ao_map: bool,
    generate_decal_mask: bool,
    generate_material_id_mask: bool,
) -> dict[str, array]:
    sample_resolution = _paint_sample_resolution(resolution)
    texture_maps = _paint_metal_maps_at_resolution(
        sample_resolution,
        color,
        profile,
        part_name=part_name,
        seed=seed,
        rust_amount=rust_amount,
        scratch_amount=scratch_amount,
        wear_amount=wear_amount,
        decal_density=decal_density,
        texture_scale=texture_scale,
        role_scale=role_scale,
        accent_color=accent_color,
        roughness_value=roughness_value,
        metallic_value=metallic_value,
        material_style=material_style,
        material_complexity=material_complexity,
        paint_layer_strength=paint_layer_strength,
        roughness_variation=roughness_variation,
        metallic_variation=metallic_variation,
        edge_wear_amount=edge_wear_amount,
        cavity_dirt_amount=cavity_dirt_amount,
        heat_stain_amount=heat_stain_amount,
        soot_amount=soot_amount,
        decal_amount=decal_amount,
        livery_amount=livery_amount,
        emissive_density=emissive_density,
        engine_heat_intensity=engine_heat_intensity,
        faction_material_influence=faction_material_influence,
        faction=faction,
        ship_type=ship_type,
        generate_emissive_map=generate_emissive_map,
        generate_ao_map=generate_ao_map,
        generate_decal_mask=generate_decal_mask,
        generate_material_id_mask=generate_material_id_mask,
    )
    if sample_resolution == resolution:
        return texture_maps
    return {
        key: _resize_pixels_nearest(pixels, sample_resolution, resolution)
        for key, pixels in texture_maps.items()
    }


def _paint_sample_resolution(resolution: int) -> int:
    if resolution <= 128:
        return resolution
    if resolution <= 512:
        return 128
    return 256


def _paint_metal_maps_at_resolution(
    resolution: int,
    color: tuple[float, float, float, float],
    profile: dict[str, Any],
    *,
    part_name: str,
    seed: int,
    rust_amount: float,
    scratch_amount: float,
    wear_amount: float,
    decal_density: float,
    texture_scale: float,
    role_scale: float,
    accent_color: tuple[float, float, float, float],
    roughness_value: float,
    metallic_value: float,
    material_style: str,
    material_complexity: str,
    paint_layer_strength: float,
    roughness_variation: float,
    metallic_variation: float,
    edge_wear_amount: float,
    cavity_dirt_amount: float,
    heat_stain_amount: float,
    soot_amount: float,
    decal_amount: float,
    livery_amount: float,
    emissive_density: float,
    engine_heat_intensity: float,
    faction_material_influence: float,
    faction: str,
    ship_type: str,
    generate_emissive_map: bool,
    generate_ao_map: bool,
    generate_decal_mask: bool,
    generate_material_id_mask: bool,
) -> dict[str, array]:
    count = resolution * resolution
    base_pixels = array("f", [0.0]) * (count * 4)
    metallic_roughness_pixels = array("f", [0.0]) * (count * 4)
    emissive_pixels = array("f", [0.0]) * (count * 4)
    ao_pixels = array("f", [1.0]) * (count * 4)
    height_pixels = array("f", [0.5]) * (count * 4)
    curvature_pixels = array("f", [0.0]) * (count * 4)
    dirt_pixels = array("f", [0.0]) * (count * 4)
    decal_pixels = array("f", [0.0]) * (count * 4)
    paint_pixels = array("f", [0.0]) * (count * 4)
    heat_pixels = array("f", [0.0]) * (count * 4)
    material_id_pixels = array("f", [0.0]) * (count * 4)
    height_values = array("f", [0.0]) * count

    columns, rows, diagonal_bias, paint_strength, dirt_strength = _layout_for_part(part_name)
    complexity_multiplier = {"low": 0.55, "medium": 0.78, "high": 1.0, "ultra": 1.18}.get(material_complexity, 1.0)
    scale = max(texture_scale * max(role_scale, 0.35), 0.12)
    panel_line_width = _clamp(0.0048 + (1.0 / resolution) * 1.35, 0.0045, 0.014)
    trim = profile["trim"]
    edge = profile["edge"]
    rust = _mix_color(profile["rust"], profile["oxide"], 0.45 + rust_amount * 0.28)
    oxide = profile["oxide"]
    dark = _scale_color(color, 0.46)
    paint_tint = _mix_color(accent_color, color, 0.28)
    warning_tint = (0.95, 0.64, 0.16, 1.0)
    service_tint = _mix_color(edge, (0.86, 0.88, 0.80, 1.0), 0.38)
    bare_metal = _mix_color(edge, (0.98, 0.96, 0.86, 1.0), 0.24)
    alpha = color[3]
    base_metallic = metallic_value
    cavity_dirt_amount *= complexity_multiplier
    roughness_variation *= complexity_multiplier
    metallic_variation *= complexity_multiplier
    decal_amount *= complexity_multiplier
    livery_amount *= complexity_multiplier

    for y in range(resolution):
        v = y / max(resolution - 1, 1)
        for x in range(resolution):
            u = x / max(resolution - 1, 1)
            index = y * resolution + x
            offset = index * 4

            broad = _value_noise(u, v, 5.5 * scale, seed + 11)
            mid = _value_noise(u, v, 22.0 * scale, seed + 23)
            fine = _value_noise(u, v, 120.0 * scale, seed + 37)
            panel_tone = _panel_tone(u, v, columns, rows, seed + 181, part_name)
            metal_variation = (broad - 0.5) * 0.050 + (mid - 0.5) * 0.036 + (fine - 0.5) * 0.010 + panel_tone

            panel_mask = _panel_line_mask(u, v, columns, rows, panel_line_width)
            bevel_mask = _panel_line_mask(u + 0.006, v + 0.004, columns, rows, panel_line_width * 0.58)
            inset_mask = _inset_panel_mask(u, v, columns, rows, panel_line_width * 0.72)
            sub_panel_mask = _sub_panel_line_mask(u, v, columns, rows, seed + 193, part_name)
            rib_mask = _recessed_rib_mask(u, v, columns, rows, seed + 199, part_name)
            corner_wear_mask = _corner_wear_mask(u, v, columns, rows, seed + 211, wear_amount)
            machined_mask = _machined_line_mask(u, v, seed + 223, texture_scale, part_name)
            plate_mask = _painted_plate_mask(u, v, columns, rows, seed + 43, decal_density, part_name)
            diagonal_mask = _diagonal_livery_mask(u, v, diagonal_bias, seed + 53) * decal_density * paint_strength
            hatch_mask = _angular_hatch_mask(u, v, columns, rows, seed + 71, decal_density, part_name)
            warning_mask = _warning_stripe_mask(u, v, columns, rows, seed + 79, decal_density, part_name)
            service_mask = _service_marking_mask(u, v, columns, rows, seed + 83, decal_density, part_name)
            fastener_mask = _fastener_mask(u, v, columns, rows, seed + 97, part_name)

            chip_mask = _chip_mask(u, v, panel_mask, seed + 89, scratch_amount, wear_amount, texture_scale)
            scratch_mask = _scratch_mask(u, v, seed + 107, scratch_amount, wear_amount, texture_scale)
            oxide_mask = _oxide_mask(u, v, panel_mask, chip_mask, seed + 131, rust_amount, texture_scale)
            grime_mask = _grime_mask(u, v, panel_mask, seed + 149, dirt_strength, texture_scale)
            streak_mask = _streak_mask(u, v, seed + 157, dirt_strength, texture_scale, part_name)
            heat_mask = _heat_stain_mask(u, v, seed + 167, part_name)
            cavity_mask = _clamp(panel_mask * 0.82 + sub_panel_mask * 0.38 + inset_mask * 0.28 + rib_mask * 0.42 + fastener_mask * 0.34)
            chip_mask = _clamp(chip_mask * (0.35 + edge_wear_amount * 1.35))
            scratch_mask = _clamp(scratch_mask * (0.40 + edge_wear_amount * 1.10))
            grime_mask = _clamp(grime_mask * (0.35 + cavity_dirt_amount * 1.45))
            streak_mask = _clamp(streak_mask * (0.25 + cavity_dirt_amount * 1.20))
            oxide_mask = _clamp(oxide_mask * (0.35 + cavity_dirt_amount * 0.45))
            heat_mask = _clamp(heat_mask * heat_stain_amount * (0.35 + engine_heat_intensity))
            soot_mask = _clamp(heat_mask * soot_amount * (0.4 + cavity_mask))
            diagonal_mask = _clamp(diagonal_mask * (0.25 + livery_amount * 1.25))
            hatch_mask = _clamp(hatch_mask * (0.20 + decal_amount * 1.30))
            warning_mask = _clamp(warning_mask * (0.20 + decal_amount * 1.45))
            service_mask = _clamp(service_mask * (0.18 + decal_amount * 1.30))
            plate_mask = _clamp(plate_mask * (0.30 + paint_layer_strength * 1.15))
            paint_mask = _clamp(plate_mask + diagonal_mask + hatch_mask + warning_mask + service_mask)
            decal_mask = _clamp(hatch_mask + warning_mask + service_mask)
            emissive_mask = _emissive_mask(u, v, columns, rows, seed + 241, part_name, emissive_density, ship_type, faction)

            rgb = _scale_color(color, 0.86 + metal_variation)
            rgb = _mix_color(rgb, _scale_color(color, 0.76), plate_mask * 0.18)
            rgb = _mix_color(rgb, _scale_color(color, 1.16), bevel_mask * 0.18 + corner_wear_mask * 0.22)
            rgb = _mix_color(rgb, trim, panel_mask * 0.68 + sub_panel_mask * 0.34)
            rgb = _mix_color(rgb, _scale_color(trim, 0.64), inset_mask * 0.32 + rib_mask * 0.40)
            rgb = _mix_color(rgb, _scale_color(edge, 0.84), machined_mask * 0.08)
            rgb = _mix_color(rgb, dark, grime_mask * 0.30 + streak_mask * 0.18)
            rgb = _mix_color(rgb, paint_tint, diagonal_mask * 0.42)
            rgb = _mix_color(rgb, paint_tint, hatch_mask * 0.30)
            rgb = _mix_color(rgb, warning_tint, warning_mask * 0.44)
            rgb = _mix_color(rgb, service_tint, service_mask * 0.40)
            rgb = _mix_color(rgb, bare_metal, chip_mask * 0.62 + corner_wear_mask * 0.48)
            rgb = _mix_color(rgb, bare_metal, scratch_mask * 0.38)
            rgb = _mix_color(rgb, rust, oxide_mask * 0.46)
            rgb = _mix_color(rgb, oxide, oxide_mask * rust_amount * 0.16)
            rgb = _mix_color(rgb, (0.22, 0.30, 0.42, alpha), heat_mask * 0.22)
            rgb = _mix_color(rgb, (0.70, 0.42, 0.18, alpha), heat_mask * 0.12)
            rgb = _mix_color(rgb, (0.015, 0.012, 0.010, alpha), soot_mask * 0.42)
            if faction == "ancient_relic":
                rgb = _mix_color(rgb, (0.30, 0.78, 0.66, alpha), emissive_mask * 0.18)
            elif ship_type == "medical_ship":
                rgb = _mix_color(rgb, (0.92, 0.96, 0.98, alpha), paint_mask * 0.14)

            rough = roughness_value
            rough += (mid - 0.5) * (0.040 + roughness_variation * 0.105)
            rough += cavity_mask * (0.05 + cavity_dirt_amount * 0.14) + grime_mask * 0.14 + streak_mask * 0.06 + oxide_mask * 0.34
            rough += plate_mask * 0.030 + warning_mask * 0.045 + service_mask * 0.022 + machined_mask * 0.040
            rough += soot_mask * 0.14
            rough -= scratch_mask * (0.055 + metallic_variation * 0.085) + chip_mask * 0.08 + corner_wear_mask * 0.06 + heat_mask * 0.04
            rough = _clamp(rough, 0.08, 0.96)

            metal = base_metallic
            metal += (panel_tone + broad - 0.5) * 0.025 * metallic_variation
            metal -= (diagonal_mask + hatch_mask + warning_mask + service_mask + plate_mask) * (0.08 + paint_layer_strength * 0.16)
            metal -= oxide_mask * 0.38 + grime_mask * 0.06
            metal += chip_mask * (0.08 + metallic_variation * 0.18) + scratch_mask * (0.04 + metallic_variation * 0.10) + corner_wear_mask * 0.12
            if part_name in {"glass", "window"}:
                metal = 0.0
            metal = _clamp(metal, 0.02, 0.98)

            height = 0.50
            height -= panel_mask * 0.20
            height -= sub_panel_mask * 0.085
            height -= inset_mask * 0.085
            height -= rib_mask * 0.075
            height -= fastener_mask * 0.045
            height -= grime_mask * 0.025
            height -= oxide_mask * 0.070
            height -= soot_mask * 0.030
            height += bevel_mask * 0.070
            height += plate_mask * 0.022
            height += chip_mask * 0.12
            height += corner_wear_mask * 0.065
            height += scratch_mask * 0.040
            height += service_mask * 0.018
            height -= machined_mask * 0.012
            height += (fine - 0.5) * 0.014
            height = _clamp(height, 0.18, 0.82)

            base_pixels[offset] = _clamp(rgb[0])
            base_pixels[offset + 1] = _clamp(rgb[1])
            base_pixels[offset + 2] = _clamp(rgb[2])
            base_pixels[offset + 3] = alpha
            metallic_roughness_pixels[offset] = 1.0
            metallic_roughness_pixels[offset + 1] = rough
            metallic_roughness_pixels[offset + 2] = metal
            metallic_roughness_pixels[offset + 3] = 1.0
            height_values[index] = height
            emissive_value = _clamp(emissive_mask + heat_mask * emissive_density * engine_heat_intensity)
            emissive_rgb = _emissive_color_for(accent_color, faction, ship_type, part_name)
            emissive_pixels[offset] = emissive_rgb[0] * emissive_value
            emissive_pixels[offset + 1] = emissive_rgb[1] * emissive_value
            emissive_pixels[offset + 2] = emissive_rgb[2] * emissive_value
            emissive_pixels[offset + 3] = 1.0
            ao_value = _clamp(1.0 - cavity_mask * (0.25 + cavity_dirt_amount * 0.35) - grime_mask * 0.16 - soot_mask * 0.18, 0.18, 1.0)
            _write_grey_pixel(ao_pixels, offset, ao_value)
            _write_grey_pixel(height_pixels, offset, height)
            _write_grey_pixel(curvature_pixels, offset, _clamp(chip_mask + scratch_mask * 0.55 + corner_wear_mask * 0.62 + bevel_mask * 0.28))
            _write_grey_pixel(dirt_pixels, offset, _clamp(grime_mask + streak_mask + oxide_mask * 0.62 + soot_mask))
            _write_grey_pixel(decal_pixels, offset, decal_mask)
            _write_grey_pixel(paint_pixels, offset, _clamp(paint_mask + plate_mask * 0.38))
            _write_grey_pixel(heat_pixels, offset, _clamp(heat_mask + soot_mask * 0.55))
            material_id_pixels[offset] = _clamp(0.18 + paint_mask * 0.28)
            material_id_pixels[offset + 1] = _clamp(metal * 0.74 + heat_mask * 0.22)
            material_id_pixels[offset + 2] = _clamp(cavity_mask * 0.45 + emissive_value)
            material_id_pixels[offset + 3] = 1.0

    normal_pixels = _normal_pixels_from_height(height_values, resolution, strength=6.5)
    return {
        "base_color": base_pixels,
        "metallic_roughness": metallic_roughness_pixels,
        "normal": normal_pixels,
        "emissive": emissive_pixels,
        "ao": ao_pixels,
        "height": height_pixels,
        "curvature": curvature_pixels,
        "dirt": dirt_pixels,
        "decal": decal_pixels,
        "paint": paint_pixels,
        "heat": heat_pixels,
        "material_id": material_id_pixels,
    }


def _layout_for_part(part_name: str) -> tuple[int, int, float, float, float]:
    if part_name in {"body", "hull", "body_panel"}:
        return 5, 9, 0.40, 0.55, 0.70
    if part_name in {"wing", "wing_edge"}:
        return 7, 4, 1.0, 0.80, 0.52
    if part_name in {"armor", "armor_top", "armor_dark"}:
        return 4, 6, 0.18, 0.28, 0.82
    if part_name in {"engine_shell", "weapon", "ordnance"}:
        return 3, 10, 0.62, 0.18, 0.46
    if part_name in {"cargo", "system_bay"}:
        return 6, 6, 0.24, 0.45, 0.92
    if part_name in {"wear", "red_decal", "accent"}:
        return 5, 5, 0.75, 1.0, 0.35
    return 5, 7, 0.35, 0.45, 0.62


def _panel_line_mask(u: float, v: float, columns: int, rows: int, width: float) -> float:
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    du = min(cell_u, 1.0 - cell_u)
    dv = min(cell_v, 1.0 - cell_v)
    line = max(_edge_falloff(du, width), _edge_falloff(dv, width))
    return _clamp(line)


def _inset_panel_mask(u: float, v: float, columns: int, rows: int, width: float) -> float:
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    left = _edge_falloff(abs(cell_u - 0.16), width)
    right = _edge_falloff(abs(cell_u - 0.84), width)
    lower = _edge_falloff(abs(cell_v - 0.18), width)
    upper = _edge_falloff(abs(cell_v - 0.82), width)
    side_gate = _smoothstep(_clamp((cell_v - 0.10) / 0.18)) * _smoothstep(_clamp((0.90 - cell_v) / 0.18))
    cap_gate = _smoothstep(_clamp((cell_u - 0.10) / 0.18)) * _smoothstep(_clamp((0.90 - cell_u) / 0.18))
    return _clamp(max(left, right) * side_gate + max(lower, upper) * cap_gate)


def _panel_tone(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    part_name: str,
) -> float:
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    cell_value = _hash01(cell_x, cell_y, seed)
    if part_name in {"wing_edge", "weapon", "ordnance"}:
        amount = 0.040
    elif part_name in {"cargo", "system_bay", "armor", "armor_top", "armor_dark"}:
        amount = 0.070
    else:
        amount = 0.055
    return (cell_value - 0.5) * amount


def _sub_panel_line_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    part_name: str,
) -> float:
    if part_name in {"wear", "red_decal", "accent"}:
        return 0.0
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.54:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    line_u = _edge_falloff(abs(cell_u - (0.34 + _hash01(cell_x, cell_y, seed + 7) * 0.30)), 0.006)
    line_v = _edge_falloff(abs(cell_v - (0.32 + _hash01(cell_x, cell_y, seed + 11) * 0.34)), 0.006)
    gate_u = _smoothstep(_clamp((cell_v - 0.16) / 0.16)) * _smoothstep(_clamp((0.84 - cell_v) / 0.16))
    gate_v = _smoothstep(_clamp((cell_u - 0.16) / 0.16)) * _smoothstep(_clamp((0.84 - cell_u) / 0.16))
    return max(line_u * gate_u, line_v * gate_v) * 0.62


def _recessed_rib_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    part_name: str,
) -> float:
    if part_name not in {"engine_shell", "weapon", "ordnance", "cargo", "system_bay", "underbody", "panel"}:
        return 0.0
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.66:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    gate = _rect_mask(cell_u, cell_v, 0.18, 0.18, 0.82, 0.82)
    phase = _hash01(cell_x, cell_y, seed + 5)
    if part_name in {"engine_shell", "weapon", "ordnance"}:
        rib = abs(((cell_v * 6.0 + phase) % 1.0) - 0.5)
    else:
        rib = abs(((cell_u * 5.0 + phase) % 1.0) - 0.5)
    return _edge_falloff(rib, 0.050) * gate * 0.72


def _corner_wear_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    wear_amount: float,
) -> float:
    if wear_amount <= 0.0:
        return 0.0
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.34 + wear_amount * 0.34:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    corner_distance = min(
        max(abs(cell_u - 0.08), abs(cell_v - 0.08)),
        max(abs(cell_u - 0.92), abs(cell_v - 0.08)),
        max(abs(cell_u - 0.08), abs(cell_v - 0.92)),
        max(abs(cell_u - 0.92), abs(cell_v - 0.92)),
    )
    broken = _value_noise(u, v, 96.0, seed + 17)
    return _edge_falloff(corner_distance + (broken - 0.5) * 0.020, 0.060) * (0.32 + wear_amount * 0.60)


def _machined_line_mask(
    u: float,
    v: float,
    seed: int,
    texture_scale: float,
    part_name: str,
) -> float:
    if part_name in {"glass", "window", "red_decal"}:
        return 0.0
    frequency = (80.0 if part_name in {"weapon", "engine_shell", "ordnance"} else 58.0) * max(texture_scale, 0.35)
    phase = _hash01(seed, 13, 37)
    coord = v if part_name in {"weapon", "engine_shell", "ordnance"} else u
    lane = abs(((coord * frequency + phase) % 1.0) - 0.5)
    gate = _value_noise(u, v, 12.0 * max(texture_scale, 0.35), seed + 19)
    return _edge_falloff(lane, 0.030) * _smoothstep(_clamp((gate - 0.42) / 0.36)) * 0.34


def _painted_plate_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    density: float,
    part_name: str,
) -> float:
    if density <= 0.0:
        return 0.0
    if part_name in {"panel", "wear", "weapon", "engine_shell", "ordnance"}:
        density *= 0.35
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.18 + density * 0.30:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    pad_x = 0.12 + _hash01(cell_x, cell_y, seed + 9) * 0.12
    pad_y = 0.14 + _hash01(cell_x, cell_y, seed + 17) * 0.10
    inside_x = _smoothstep(_clamp((cell_u - pad_x) / 0.08)) * _smoothstep(_clamp((1.0 - pad_x - cell_u) / 0.08))
    inside_y = _smoothstep(_clamp((cell_v - pad_y) / 0.08)) * _smoothstep(_clamp((1.0 - pad_y - cell_v) / 0.08))
    split = _edge_falloff(abs(cell_u - 0.50), 0.010) * 0.18
    return _clamp(inside_x * inside_y * density - split)


def _diagonal_livery_mask(u: float, v: float, bias: float, seed: int) -> float:
    if bias <= 0.05:
        return 0.0
    phase = _hash01(seed, 17, 29)
    band = (u * (1.8 + bias) + v * (0.75 + bias * 0.52) + phase) % 1.0
    core = _edge_falloff(abs(band - 0.50), 0.030 + bias * 0.012)
    gate = _value_noise(u, v, 3.0 + bias * 2.0, seed + 31)
    return core * _smoothstep(_clamp((gate - 0.42) / 0.36)) * 0.72


def _warning_stripe_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    density: float,
    part_name: str,
) -> float:
    if density <= 0.0 or part_name in {"panel", "wear"}:
        return 0.0
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.06 + density * 0.13:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    region = _smoothstep(_clamp((cell_u - 0.08) / 0.06)) * _smoothstep(_clamp((0.48 - cell_u) / 0.08))
    region *= _smoothstep(_clamp((cell_v - 0.58) / 0.06)) * _smoothstep(_clamp((0.88 - cell_v) / 0.06))
    stripe = ((cell_u * 8.0 + cell_v * 5.0 + _hash01(cell_x, cell_y, seed + 2) * 2.0) % 1.0)
    return region * _smoothstep(_clamp((0.34 - abs(stripe - 0.5)) / 0.18)) * density * 0.82


def _service_marking_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    density: float,
    part_name: str,
) -> float:
    if density <= 0.0 or part_name in {"panel", "wear", "engine_shell"}:
        return 0.0
    cell_x = floor(u * columns * 1.2)
    cell_y = floor(v * rows * 1.1)
    if _hash01(cell_x, cell_y, seed) > 0.09 + density * 0.14:
        return 0.0
    cell_u = (u * columns * 1.2) % 1.0
    cell_v = (v * rows * 1.1) % 1.0
    block = _rect_mask(cell_u, cell_v, 0.18, 0.58, 0.64, 0.72)
    bars = 0.0
    for bar in range(4):
        x0 = 0.22 + bar * 0.10
        bars = max(bars, _rect_mask(cell_u, cell_v, x0, 0.38, x0 + 0.052, 0.48))
    tail = _rect_mask(cell_u, cell_v, 0.22, 0.28, 0.46, 0.32)
    return max(block, bars, tail) * density * 0.82


def _angular_hatch_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    density: float,
    part_name: str,
) -> float:
    if density <= 0.0:
        return 0.0
    cell_x = floor(u * columns * 1.4)
    cell_y = floor(v * rows * 1.2)
    if _hash01(cell_x, cell_y, seed) < 1.0 - density * 0.28:
        return 0.0
    local_u = (u * columns * 1.4) % 1.0
    local_v = (v * rows * 1.2) % 1.0
    slant = abs((local_u + local_v * 0.38) - 0.58)
    mask = _edge_falloff(slant, 0.045)
    if part_name in {"cargo", "system_bay"}:
        mask = max(mask, _edge_falloff(abs(local_v - 0.28), 0.028))
    return mask * density * 0.78


def _fastener_mask(u: float, v: float, columns: int, rows: int, seed: int, part_name: str) -> float:
    if part_name in {"wear", "red_decal"}:
        return 0.0
    cell_x = floor(u * columns)
    cell_y = floor(v * rows)
    if _hash01(cell_x, cell_y, seed) > 0.72:
        return 0.0
    cell_u = (u * columns) % 1.0
    cell_v = (v * rows) % 1.0
    mask = 0.0
    for px, py in ((0.18, 0.20), (0.82, 0.20), (0.18, 0.80), (0.82, 0.80)):
        distance = max(abs(cell_u - px), abs(cell_v - py))
        mask = max(mask, _edge_falloff(distance, 0.025))
    return mask * 0.65


def _chip_mask(
    u: float,
    v: float,
    panel_mask: float,
    seed: int,
    scratch_amount: float,
    wear_amount: float,
    texture_scale: float,
) -> float:
    grid = 42.0 * max(texture_scale, 0.3)
    cell_x = floor(u * grid)
    cell_y = floor(v * grid)
    chance = _hash01(cell_x, cell_y, seed)
    threshold = 0.985 - wear_amount * 0.042 - scratch_amount * 0.014
    if chance < threshold and panel_mask < 0.20:
        return 0.0
    local_u = (u * grid) % 1.0
    local_v = (v * grid) % 1.0
    jagged = _value_noise(u, v, grid * 0.8, seed + 5)
    corner = min(local_u, local_v, 1.0 - local_u, 1.0 - local_v)
    shape = _edge_falloff(corner + (jagged - 0.5) * 0.09, 0.18)
    edge_bias = 0.35 + panel_mask * 0.85
    return _clamp(shape * edge_bias * (0.24 + wear_amount * 0.62))


def _scratch_mask(
    u: float,
    v: float,
    seed: int,
    scratch_amount: float,
    wear_amount: float,
    texture_scale: float,
) -> float:
    if scratch_amount <= 0.0:
        return 0.0
    grid = 30.0 * max(texture_scale, 0.4)
    cell_x = floor(u * grid)
    cell_y = floor(v * grid)
    chance = _hash01(cell_x, cell_y, seed)
    if chance < 0.92 - scratch_amount * 0.10:
        return 0.0
    local_u = (u * grid) % 1.0
    local_v = (v * grid) % 1.0
    angle_shift = _hash01(cell_x, cell_y, seed + 19) * 0.34
    scratch_center = _hash01(cell_x, cell_y, seed + 41)
    distance = abs((local_v + local_u * angle_shift) - scratch_center)
    length_gate = _smoothstep(_clamp((0.78 - abs(local_u - 0.45)) / 0.78))
    return _edge_falloff(distance, 0.014) * length_gate * (0.24 + scratch_amount * 0.68 + wear_amount * 0.18)


def _oxide_mask(
    u: float,
    v: float,
    panel_mask: float,
    chip_mask: float,
    seed: int,
    rust_amount: float,
    texture_scale: float,
) -> float:
    if rust_amount <= 0.0:
        return 0.0
    oxide_noise = _value_noise(u, v, 48.0 * max(texture_scale, 0.35), seed)
    pits = _value_noise(u, v, 130.0 * max(texture_scale, 0.35), seed + 13)
    threshold = 0.91 - rust_amount * 0.13
    mask = _smoothstep(_clamp((oxide_noise - threshold) / max(1.0 - threshold, 0.001)))
    mask *= 0.20 + panel_mask * 0.72 + chip_mask * 0.55
    mask += _smoothstep(_clamp((pits - 0.965) / 0.035)) * rust_amount * 0.18
    return _clamp(mask * rust_amount)


def _grime_mask(
    u: float,
    v: float,
    panel_mask: float,
    seed: int,
    dirt_strength: float,
    texture_scale: float,
) -> float:
    grime = _value_noise(u, v, 18.0 * max(texture_scale, 0.35), seed)
    directional = _clamp((v - 0.18) / 0.78)
    mask = _smoothstep(_clamp((grime - 0.62) / 0.32))
    return _clamp(mask * (0.10 + panel_mask * 0.54 + directional * 0.14) * dirt_strength)


def _streak_mask(
    u: float,
    v: float,
    seed: int,
    dirt_strength: float,
    texture_scale: float,
    part_name: str,
) -> float:
    if part_name in {"wear", "red_decal"}:
        return 0.0
    grid = 18.0 * max(texture_scale, 0.35)
    cell_x = floor(u * grid)
    if _hash01(cell_x, 0, seed) > 0.24:
        return 0.0
    lane = (u * grid) % 1.0
    streak_core = _edge_falloff(abs(lane - _hash01(cell_x, 4, seed + 3)), 0.045)
    start = _hash01(cell_x, 8, seed + 5) * 0.55
    fade = _smoothstep(_clamp((v - start) / 0.45))
    breakup = _value_noise(u, v, 50.0 * max(texture_scale, 0.35), seed + 7)
    return _clamp(streak_core * fade * breakup * dirt_strength * 0.22)


def _heat_stain_mask(u: float, v: float, seed: int, part_name: str) -> float:
    if part_name not in {"engine_shell", "weapon", "ordnance"}:
        return 0.0
    band = _smoothstep(_clamp((v - 0.48) / 0.42))
    noise = _value_noise(u, v, 14.0, seed)
    ripple = abs(((v * 12.0 + noise * 1.8) % 1.0) - 0.5)
    return band * _edge_falloff(ripple, 0.30) * 0.85


def _emissive_mask(
    u: float,
    v: float,
    columns: int,
    rows: int,
    seed: int,
    part_name: str,
    emissive_density: float,
    ship_type: str,
    faction: str,
) -> float:
    if emissive_density <= 0.0 or part_name in {"wear", "red_decal"}:
        return 0.0
    allowed_parts = {"body", "body_panel", "armor", "armor_top", "system_bay", "engine_shell", "ordnance", "cargo"}
    if part_name not in allowed_parts:
        return 0.0
    density_bonus = 0.12 if faction == "ancient_relic" else 0.0
    density_bonus += 0.08 if ship_type in {"boss_capital_ship", "medical_ship", "luxury_yacht"} else 0.0
    cell_x = floor(u * columns * 1.25)
    cell_y = floor(v * rows * 1.15)
    if _hash01(cell_x, cell_y, seed) > 0.055 + emissive_density * 0.12 + density_bonus:
        return 0.0
    cell_u = (u * columns * 1.25) % 1.0
    cell_v = (v * rows * 1.15) % 1.0
    if faction == "ancient_relic":
        seam = abs((cell_u + cell_v * 0.45) - 0.52)
        return _edge_falloff(seam, 0.018) * emissive_density
    if part_name == "engine_shell":
        band = _edge_falloff(abs(cell_v - 0.62), 0.040)
        gate = _rect_mask(cell_u, cell_v, 0.16, 0.52, 0.84, 0.72)
        return band * gate * emissive_density
    strip = _edge_falloff(abs(cell_v - 0.50), 0.015)
    gate = _rect_mask(cell_u, cell_v, 0.18, 0.42, 0.72, 0.58)
    return strip * gate * emissive_density


def _emissive_color_for(
    accent_color: tuple[float, float, float, float],
    faction: str,
    ship_type: str,
    part_name: str,
) -> tuple[float, float, float, float]:
    if faction == "ancient_relic":
        return (0.34, 1.0, 0.78, 1.0)
    if ship_type == "medical_ship":
        return (0.42, 0.78, 1.0, 1.0)
    if part_name in {"engine_shell", "ordnance"}:
        return (
            min(accent_color[0] * 0.28 + 0.08, 1.0),
            min(accent_color[1] * 0.35 + 0.62, 1.0),
            min(accent_color[2] * 0.45 + 0.95, 1.0),
            1.0,
        )
    return (
        min(accent_color[0] * 0.55 + 0.08, 1.0),
        min(accent_color[1] * 0.55 + 0.38, 1.0),
        min(accent_color[2] * 0.65 + 0.48, 1.0),
        1.0,
    )


def _write_grey_pixel(pixels: array, offset: int, value: float) -> None:
    value = _clamp(value)
    pixels[offset] = value
    pixels[offset + 1] = value
    pixels[offset + 2] = value
    pixels[offset + 3] = 1.0


def _rect_mask(u: float, v: float, x0: float, y0: float, x1: float, y1: float) -> float:
    feather = 0.012
    inside_x = _smoothstep(_clamp((u - x0) / feather)) * _smoothstep(_clamp((x1 - u) / feather))
    inside_y = _smoothstep(_clamp((v - y0) / feather)) * _smoothstep(_clamp((y1 - v) / feather))
    return inside_x * inside_y


def _normal_pixels_from_height(height_values: array, resolution: int, *, strength: float) -> array:
    normal_pixels = array("f", [0.0]) * (resolution * resolution * 4)
    for y in range(resolution):
        ym = max(y - 1, 0)
        yp = min(y + 1, resolution - 1)
        for x in range(resolution):
            xm = max(x - 1, 0)
            xp = min(x + 1, resolution - 1)
            center = y * resolution + x
            dx = (height_values[y * resolution + xp] - height_values[y * resolution + xm]) * strength
            dy = (height_values[yp * resolution + x] - height_values[ym * resolution + x]) * strength
            nx = -dx
            ny = -dy
            nz = 1.0
            length = sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            offset = center * 4
            normal_pixels[offset] = nx / length * 0.5 + 0.5
            normal_pixels[offset + 1] = ny / length * 0.5 + 0.5
            normal_pixels[offset + 2] = nz / length * 0.5 + 0.5
            normal_pixels[offset + 3] = 1.0
    return normal_pixels


def _resize_pixels_nearest(pixels: array, source_resolution: int, target_resolution: int) -> array:
    if source_resolution == target_resolution:
        return pixels
    if target_resolution % source_resolution == 0:
        factor = target_resolution // source_resolution
        resized = array("f")
        for source_y in range(source_resolution):
            source_row_start = source_y * source_resolution * 4
            expanded_row = array("f")
            for source_x in range(source_resolution):
                pixel_start = source_row_start + source_x * 4
                pixel = pixels[pixel_start : pixel_start + 4]
                for _ in range(factor):
                    expanded_row.extend(pixel)
            for _ in range(factor):
                resized.extend(expanded_row)
        return resized

    resized = array("f", [0.0]) * (target_resolution * target_resolution * 4)
    for target_y in range(target_resolution):
        source_y = min(source_resolution - 1, int(target_y * source_resolution / target_resolution))
        source_row_start = source_y * source_resolution * 4
        target_row_start = target_y * target_resolution * 4
        for target_x in range(target_resolution):
            source_x = min(source_resolution - 1, int(target_x * source_resolution / target_resolution))
            source_offset = source_row_start + source_x * 4
            target_offset = target_row_start + target_x * 4
            resized[target_offset : target_offset + 4] = pixels[source_offset : source_offset + 4]
    return resized


def _image_from_pixels(name: str, resolution: int, pixels: array, *, colorspace: str) -> bpy.types.Image:
    image = bpy.data.images.get(name)
    if image is not None and (image.size[0] != resolution or image.size[1] != resolution):
        bpy.data.images.remove(image)
        image = None
    if image is None:
        image = bpy.data.images.new(name, width=resolution, height=resolution, alpha=True)
    try:
        image.colorspace_settings.name = colorspace
    except TypeError:
        pass
    image.pixels.foreach_set(pixels)
    image.update()
    try:
        image.pack()
    except RuntimeError:
        pass
    return image


def _texture_fingerprint(
    name: str,
    part_name: str,
    seed: int,
    resolution: int,
    color: tuple[float, float, float, float],
    rust_amount: float,
    scratch_amount: float,
    wear_amount: float,
    decal_density: float,
    texture_scale: float,
    role_scale: float,
    accent_color: tuple[float, float, float, float],
    metallic_value: float,
    roughness_value: float,
    material_style: str,
    material_complexity: str,
    paint_layer_strength: float,
    roughness_variation: float,
    metallic_variation: float,
    edge_wear_amount: float,
    cavity_dirt_amount: float,
    heat_stain_amount: float,
    soot_amount: float,
    decal_amount: float,
    livery_amount: float,
    emissive_density: float,
    engine_heat_intensity: float,
    faction_material_influence: float,
    faction: str,
    ship_type: str,
    generate_emissive_map: bool,
    generate_ao_map: bool,
    generate_decal_mask: bool,
    generate_material_id_mask: bool,
    export_texture_maps: bool,
) -> str:
    values = (
        "painted_texture_v7_premium_pbr",
        name,
        part_name,
        seed,
        resolution,
        _paint_sample_resolution(resolution),
        tuple(round(component, 5) for component in color),
        round(rust_amount, 5),
        round(scratch_amount, 5),
        round(wear_amount, 5),
        round(decal_density, 5),
        round(texture_scale, 5),
        round(role_scale, 5),
        tuple(round(component, 5) for component in accent_color),
        round(metallic_value, 5),
        round(roughness_value, 5),
        material_style,
        material_complexity,
        round(paint_layer_strength, 5),
        round(roughness_variation, 5),
        round(metallic_variation, 5),
        round(edge_wear_amount, 5),
        round(cavity_dirt_amount, 5),
        round(heat_stain_amount, 5),
        round(soot_amount, 5),
        round(decal_amount, 5),
        round(livery_amount, 5),
        round(emissive_density, 5),
        round(engine_heat_intensity, 5),
        round(faction_material_influence, 5),
        faction,
        ship_type,
        bool(generate_emissive_map),
        bool(generate_ao_map),
        bool(generate_decal_mask),
        bool(generate_material_id_mask),
        bool(export_texture_maps),
    )
    return hashlib.sha256(repr(values).encode("utf-8")).hexdigest()


def _material_matches_texture_fingerprint(material: bpy.types.Material | None, fingerprint: str) -> bool:
    if material is None or not material.use_nodes:
        return False
    if material.get("void_shipwright_texture_fingerprint") != fingerprint:
        return False
    nodes = material.node_tree.nodes
    return (
        nodes.get("VS_Painted_BaseColor") is not None
        and nodes.get("VS_Painted_MetallicRoughness") is not None
        and nodes.get("VS_Painted_Separate_MetallicRoughness") is not None
        and nodes.get("VS_Painted_Normal") is not None
        and nodes.get("VS_Painted_NormalMap") is not None
    )


def _set_input(node: bpy.types.Node, name: str, value: Any) -> None:
    if name in node.inputs:
        node.inputs[name].default_value = value


def _value_noise(u: float, v: float, frequency: float, seed: int) -> float:
    x = u * frequency
    y = v * frequency
    ix = floor(x)
    iy = floor(y)
    fx = x - ix
    fy = y - iy
    sx = fx * fx * (3.0 - 2.0 * fx)
    sy = fy * fy * (3.0 - 2.0 * fy)
    a = _hash01(ix, iy, seed)
    b = _hash01(ix + 1, iy, seed)
    c = _hash01(ix, iy + 1, seed)
    d = _hash01(ix + 1, iy + 1, seed)
    return _lerp(_lerp(a, b, sx), _lerp(c, d, sx), sy)


def _hash01(x: int, y: int, seed: int) -> float:
    value = (x * 374761393 + y * 668265263 + seed * 2246822519) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    value = (value ^ (value >> 16)) & 0xFFFFFFFF
    return value / 0xFFFFFFFF


def _stable_seed(*parts: object) -> int:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big")


def _safe_image_name(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)
    return f"VS_Tex_{safe}"


def _edge_falloff(distance: float, width: float) -> float:
    return _smoothstep(_clamp((width - distance) / max(width, 0.0001)))


def _smoothstep(value: float) -> float:
    value = _clamp(value)
    return value * value * (3.0 - 2.0 * value)


def _lerp(a: float, b: float, amount: float) -> float:
    return a * (1.0 - amount) + b * amount


def _mix_color(
    a: tuple[float, float, float, float],
    b: tuple[float, float, float, float],
    amount: float,
) -> tuple[float, float, float, float]:
    amount = _clamp(amount)
    return (
        _lerp(a[0], b[0], amount),
        _lerp(a[1], b[1], amount),
        _lerp(a[2], b[2], amount),
        _lerp(a[3], b[3], amount),
    )


def _scale_color(color: tuple[float, float, float, float], scale: float) -> tuple[float, float, float, float]:
    return (_clamp(color[0] * scale), _clamp(color[1] * scale), _clamp(color[2] * scale), color[3])


def _clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return min(max(value, minimum), maximum)

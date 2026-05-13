"""Deterministic generated texture-paint materials for Void Shipwright."""

from __future__ import annotations

from array import array
import hashlib
from math import floor, sqrt
from typing import Any

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
) -> bpy.types.Material:
    """Create an image-textured metal material with painted PBR maps."""
    rust_amount = _clamp(rust_amount)
    scratch_amount = _clamp(scratch_amount)
    wear_amount = _clamp(wear_amount)
    decal_density = _clamp(decal_density)
    texture_scale = max(texture_scale, 0.1)
    resolution = max(64, min(int(resolution), 256))
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
    )
    material = bpy.data.materials.get(name)
    if _material_matches_texture_fingerprint(material, fingerprint):
        return material

    base_pixels, metallic_roughness_pixels, normal_pixels = _paint_metal_maps(
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
    )

    safe_name = _safe_image_name(name)
    base_image = _image_from_pixels(f"{safe_name}_Paint_BaseColor", resolution, base_pixels, colorspace="sRGB")
    metallic_roughness_image = _image_from_pixels(f"{safe_name}_Paint_MetallicRoughness", resolution, metallic_roughness_pixels, colorspace="Non-Color")
    normal_image = _image_from_pixels(f"{safe_name}_Paint_Normal", resolution, normal_pixels, colorspace="Non-Color")

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
    _set_input(normal_map, "Strength", 0.46 + scratch_amount * 0.36 + rust_amount * 0.18)

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

    material.blend_method = "OPAQUE"
    return material


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
) -> tuple[array, array, array]:
    sample_resolution = _paint_sample_resolution(resolution)
    base_pixels, metallic_roughness_pixels, normal_pixels = _paint_metal_maps_at_resolution(
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
    )
    if sample_resolution == resolution:
        return base_pixels, metallic_roughness_pixels, normal_pixels
    return (
        _resize_pixels_nearest(base_pixels, sample_resolution, resolution),
        _resize_pixels_nearest(metallic_roughness_pixels, sample_resolution, resolution),
        _resize_pixels_nearest(normal_pixels, sample_resolution, resolution),
    )


def _paint_sample_resolution(resolution: int) -> int:
    if resolution <= 128:
        return resolution
    return max(64, resolution // 2)


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
) -> tuple[array, array, array]:
    count = resolution * resolution
    base_pixels = array("f", [0.0]) * (count * 4)
    metallic_roughness_pixels = array("f", [0.0]) * (count * 4)
    height_values = array("f", [0.0]) * count

    columns, rows, diagonal_bias, paint_strength, dirt_strength = _layout_for_part(part_name)
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
    base_metallic = _clamp(profile.get("metallic", 0.7))

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

            rough = roughness_value
            rough += (mid - 0.5) * 0.080 + cavity_mask * 0.12 + grime_mask * 0.14 + streak_mask * 0.06 + oxide_mask * 0.34
            rough += plate_mask * 0.030 + warning_mask * 0.045 + service_mask * 0.022 + machined_mask * 0.040
            rough -= scratch_mask * 0.11 + chip_mask * 0.08 + corner_wear_mask * 0.06 + heat_mask * 0.04
            rough = _clamp(rough, 0.08, 0.96)

            metal = base_metallic
            metal -= (diagonal_mask + hatch_mask + warning_mask + service_mask + plate_mask) * 0.18
            metal -= oxide_mask * 0.38 + grime_mask * 0.06
            metal += chip_mask * 0.16 + scratch_mask * 0.08 + corner_wear_mask * 0.12
            metal = _clamp(metal, 0.02, 0.98)

            height = 0.50
            height -= panel_mask * 0.20
            height -= sub_panel_mask * 0.085
            height -= inset_mask * 0.085
            height -= rib_mask * 0.075
            height -= fastener_mask * 0.045
            height -= grime_mask * 0.025
            height -= oxide_mask * 0.070
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

    normal_pixels = _normal_pixels_from_height(height_values, resolution, strength=6.5)
    return base_pixels, metallic_roughness_pixels, normal_pixels


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
) -> str:
    values = (
        "painted_texture_v6_sampled_256",
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

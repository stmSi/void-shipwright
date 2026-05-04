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
    resolution = max(64, min(int(resolution), 1024))
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

    base_pixels, roughness_pixels, normal_pixels = _paint_metal_maps(
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
    roughness_image = _image_from_pixels(f"{safe_name}_Paint_Roughness", resolution, roughness_pixels, colorspace="Non-Color")
    normal_image = _image_from_pixels(f"{safe_name}_Paint_Normal", resolution, normal_pixels, colorspace="Non-Color")

    if material is None:
        material = bpy.data.materials.new(name)
    material.diffuse_color = color
    material.use_nodes = True
    material["void_shipwright_material"] = "painted_layered_metal"
    material["void_shipwright_texture_workflow"] = "procedural_texture_paint"
    material["void_shipwright_texture_resolution"] = resolution
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
    roughness_node = nodes.new("ShaderNodeTexImage")
    roughness_node.name = "VS_Painted_Roughness"
    roughness_node.image = roughness_image
    normal_node = nodes.new("ShaderNodeTexImage")
    normal_node.name = "VS_Painted_Normal"
    normal_node.image = normal_image
    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "VS_Painted_NormalMap"
    _set_input(normal_map, "Strength", 0.46 + scratch_amount * 0.36 + rust_amount * 0.18)

    links.new(base_node.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(roughness_node.outputs["Color"], bsdf.inputs["Roughness"])
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
    count = resolution * resolution
    base_pixels = array("f", [0.0]) * (count * 4)
    roughness_pixels = array("f", [0.0]) * (count * 4)
    height_values = array("f", [0.0]) * count

    columns, rows, diagonal_bias, paint_strength, dirt_strength = _layout_for_part(part_name)
    scale = max(texture_scale * max(role_scale, 0.35), 0.12)
    panel_line_width = _clamp(0.008 + (1.0 / resolution) * 1.35, 0.006, 0.020)
    trim = profile["trim"]
    edge = profile["edge"]
    rust = _mix_color(profile["rust"], profile["oxide"], 0.45 + rust_amount * 0.28)
    oxide = profile["oxide"]
    dark = _scale_color(color, 0.46)
    alpha = color[3]

    for y in range(resolution):
        v = y / max(resolution - 1, 1)
        for x in range(resolution):
            u = x / max(resolution - 1, 1)
            index = y * resolution + x
            offset = index * 4

            broad = _value_noise(u, v, 7.0 * scale, seed + 11)
            mid = _value_noise(u, v, 28.0 * scale, seed + 23)
            fine = _value_noise(u, v, 108.0 * scale, seed + 37)
            metal_variation = (broad - 0.5) * 0.13 + (mid - 0.5) * 0.06 + (fine - 0.5) * 0.025

            panel_mask = _panel_line_mask(u, v, columns, rows, panel_line_width)
            bevel_mask = _panel_line_mask(u + 0.006, v + 0.004, columns, rows, panel_line_width * 0.58)
            diagonal_mask = _diagonal_livery_mask(u, v, diagonal_bias, seed + 53) * decal_density * paint_strength
            hatch_mask = _angular_hatch_mask(u, v, columns, rows, seed + 71, decal_density, part_name)

            chip_mask = _chip_mask(u, v, panel_mask, seed + 89, scratch_amount, wear_amount, texture_scale)
            scratch_mask = _scratch_mask(u, v, seed + 107, scratch_amount, wear_amount, texture_scale)
            oxide_mask = _oxide_mask(u, v, panel_mask, chip_mask, seed + 131, rust_amount, texture_scale)
            grime_mask = _grime_mask(u, v, panel_mask, seed + 149, dirt_strength, texture_scale)

            rgb = _scale_color(color, 0.86 + metal_variation)
            rgb = _mix_color(rgb, _scale_color(color, 1.12), bevel_mask * 0.16)
            rgb = _mix_color(rgb, trim, panel_mask * 0.58)
            rgb = _mix_color(rgb, dark, grime_mask * 0.42)
            rgb = _mix_color(rgb, accent_color, diagonal_mask * 0.48)
            rgb = _mix_color(rgb, accent_color, hatch_mask * 0.38)
            rgb = _mix_color(rgb, edge, chip_mask * 0.72)
            rgb = _mix_color(rgb, edge, scratch_mask * 0.46)
            rgb = _mix_color(rgb, rust, oxide_mask * 0.76)
            rgb = _mix_color(rgb, oxide, oxide_mask * rust_amount * 0.20)

            rough = roughness_value
            rough += (mid - 0.5) * 0.12 + panel_mask * 0.10 + grime_mask * 0.18 + oxide_mask * 0.26
            rough -= scratch_mask * 0.13 + chip_mask * 0.08
            rough = _clamp(rough, 0.08, 0.96)

            height = 0.50
            height -= panel_mask * 0.16
            height -= grime_mask * 0.04
            height -= oxide_mask * 0.08
            height += chip_mask * 0.14
            height += scratch_mask * 0.05
            height += (fine - 0.5) * 0.030
            height = _clamp(height, 0.18, 0.82)

            base_pixels[offset] = _clamp(rgb[0])
            base_pixels[offset + 1] = _clamp(rgb[1])
            base_pixels[offset + 2] = _clamp(rgb[2])
            base_pixels[offset + 3] = alpha
            roughness_pixels[offset] = rough
            roughness_pixels[offset + 1] = rough
            roughness_pixels[offset + 2] = rough
            roughness_pixels[offset + 3] = 1.0
            height_values[index] = height

    normal_pixels = _normal_pixels_from_height(height_values, resolution, strength=6.0)
    return base_pixels, roughness_pixels, normal_pixels


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


def _diagonal_livery_mask(u: float, v: float, bias: float, seed: int) -> float:
    if bias <= 0.05:
        return 0.0
    phase = _hash01(seed, 17, 29)
    band = (u * (1.8 + bias) + v * (0.75 + bias * 0.52) + phase) % 1.0
    core = _edge_falloff(abs(band - 0.50), 0.030 + bias * 0.012)
    gate = _value_noise(u, v, 3.0 + bias * 2.0, seed + 31)
    return core * _smoothstep(_clamp((gate - 0.34) / 0.36))


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
    if _hash01(cell_x, cell_y, seed) < 1.0 - density * 0.42:
        return 0.0
    local_u = (u * columns * 1.4) % 1.0
    local_v = (v * rows * 1.2) % 1.0
    slant = abs((local_u + local_v * 0.38) - 0.58)
    mask = _edge_falloff(slant, 0.045)
    if part_name in {"cargo", "system_bay"}:
        mask = max(mask, _edge_falloff(abs(local_v - 0.28), 0.028))
    return mask * density


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
    threshold = 0.975 - wear_amount * 0.050 - scratch_amount * 0.018
    if chance < threshold and panel_mask < 0.20:
        return 0.0
    local_u = (u * grid) % 1.0
    local_v = (v * grid) % 1.0
    jagged = _value_noise(u, v, grid * 0.8, seed + 5)
    corner = min(local_u, local_v, 1.0 - local_u, 1.0 - local_v)
    shape = _edge_falloff(corner + (jagged - 0.5) * 0.09, 0.18)
    edge_bias = 0.35 + panel_mask * 0.85
    return _clamp(shape * edge_bias * (0.35 + wear_amount * 0.80))


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
    if chance < 0.88 - scratch_amount * 0.12:
        return 0.0
    local_u = (u * grid) % 1.0
    local_v = (v * grid) % 1.0
    angle_shift = _hash01(cell_x, cell_y, seed + 19) * 0.34
    scratch_center = _hash01(cell_x, cell_y, seed + 41)
    distance = abs((local_v + local_u * angle_shift) - scratch_center)
    length_gate = _smoothstep(_clamp((0.78 - abs(local_u - 0.45)) / 0.78))
    return _edge_falloff(distance, 0.018) * length_gate * (0.30 + scratch_amount * 0.82 + wear_amount * 0.25)


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
    threshold = 0.86 - rust_amount * 0.16
    mask = _smoothstep(_clamp((oxide_noise - threshold) / max(1.0 - threshold, 0.001)))
    mask *= 0.35 + panel_mask * 0.70 + chip_mask * 0.65
    mask += _smoothstep(_clamp((pits - 0.94) / 0.06)) * rust_amount * 0.28
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
    mask = _smoothstep(_clamp((grime - 0.56) / 0.38))
    return _clamp(mask * (0.18 + panel_mask * 0.60 + directional * 0.24) * dirt_strength)


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
        "painted_texture_v2_colorspace_before_pixels",
        name,
        part_name,
        seed,
        resolution,
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
    return nodes.get("VS_Painted_BaseColor") is not None and nodes.get("VS_Painted_Roughness") is not None and nodes.get("VS_Painted_Normal") is not None


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

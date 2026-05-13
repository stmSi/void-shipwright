"""Blender-side material quality smoke test for Void Shipwright."""

from __future__ import annotations

import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from void_shipwright.geometry import ShipGenerationConfig, generate_ship  # noqa: E402
from void_shipwright.textures import (  # noqa: E402
    evaluate_material_quality,
    validate_emissive_is_not_overused,
    validate_faction_material_identity,
    validate_material_assignment,
    validate_no_flat_plastic_materials,
    validate_no_overdirty_materials,
    validate_pbr_ranges,
    validate_texture_resolution,
)


TEST_CASES = (
    ("light_raider", "pirate_clan", 7301, "standard"),
    ("interceptor", "corporate_security", 7302, "standard"),
    ("missile_corvette", "sector_navy", 7303, "standard"),
    ("freighter", "trade_consortium", 7304, "standard"),
    ("heavy_cruiser", "sector_navy", 7305, "standard"),
    ("mining_ship", "mining_guild", 7306, "standard"),
    ("medical_ship", "independent", 7307, "standard"),
    ("racing_ship", "corporate_security", 7308, "standard"),
    ("luxury_yacht", "independent", 7309, "hero"),
    ("boss_capital_ship", "ancient_relic", 7310, "hero"),
)


def _collection_objects() -> list[bpy.types.Object]:
    collection = bpy.data.collections.get("Void Shipwright Generated")
    return list(collection.objects) if collection else []


def _materials_for(objects: list[bpy.types.Object]) -> list[bpy.types.Material]:
    materials: list[bpy.types.Material] = []
    seen: set[str] = set()
    for obj in objects:
        if getattr(obj, "type", "") != "MESH":
            continue
        for material in obj.data.materials:
            if material and material.name not in seen:
                materials.append(material)
                seen.add(material.name)
    return materials


def main() -> None:
    failures: list[str] = []
    for ship_type, faction, seed, texture_quality in TEST_CASES:
        role = "boss" if ship_type == "boss_capital_ship" else "enemy"
        generate_ship(
            ShipGenerationConfig(
                role=role,
                faction=faction,
                seed=seed,
                ship_type=ship_type,
                ship_id=f"material_test_{ship_type}",
                variant="default",
                visual_quality="hero",
                texture_quality=texture_quality,
                texture_resolution=512 if texture_quality == "standard" else 1024,
                material_style="auto",
                material_complexity="high",
                paint_layer_strength=0.82,
                roughness_variation=0.65,
                metallic_variation=0.45,
                edge_wear_amount=0.34,
                cavity_dirt_amount=0.42,
                heat_stain_amount=0.62,
                soot_amount=0.28,
                decal_amount=0.45,
                livery_amount=0.50,
                emissive_density=0.42,
                engine_heat_intensity=0.75,
                faction_material_influence=0.85,
                generate_emissive_map=True,
                generate_ao_map=True,
                generate_decal_mask=ship_type in {"missile_corvette", "freighter", "boss_capital_ship"},
                generate_material_id_mask=ship_type == "boss_capital_ship",
                clear_existing=True,
                presentation_scene=False,
            )
        )
        objects = _collection_objects()
        materials = _materials_for(objects)
        report = evaluate_material_quality(materials)
        print(
            f"{ship_type}: quality={texture_quality} materials={report['material_count']} "
            f"painted={report['painted_materials']} glass={report['glass_materials']} "
            f"emissive={report['emissive_materials']} images={report['image_texture_nodes']} score={report['score']}",
            flush=True,
        )
        required_maps = {"VS_Painted_BaseColor", "VS_Painted_MetallicRoughness", "VS_Painted_Normal", "VS_Painted_Emissive", "VS_Painted_AO"}
        map_names = set(report["map_names"])
        checks = {
            "material_assignment": validate_material_assignment(objects),
            "pbr_ranges": validate_pbr_ranges(materials),
            "texture_resolution": validate_texture_resolution(materials, minimum=256, maximum=2048),
            "required_maps": required_maps.issubset(map_names),
            "flat_plastic": validate_no_flat_plastic_materials(materials),
            "overdirty": validate_no_overdirty_materials(materials),
            "emissive_budget": validate_emissive_is_not_overused(materials),
            "faction_identity": validate_faction_material_identity(materials, faction),
            "glass_present": report["glass_materials"] > 0,
            "emissive_present": report["emissive_materials"] > 0,
            "quality_score": report["score"] >= 0.75,
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            failures.append(f"{ship_type}: {', '.join(failed)}")

    if failures:
        raise SystemExit("VOID_SHIPWRIGHT_MATERIAL_SMOKE_FAILED\n" + "\n".join(failures))
    print("VOID_SHIPWRIGHT_MATERIAL_QUALITY_SMOKE_OK")


if __name__ == "__main__":
    main()

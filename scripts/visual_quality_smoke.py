"""Generate major ship classes in Blender and print visual-quality scores.

Run from the repository root:
blender --background --python scripts/visual_quality_smoke.py
"""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from void_shipwright.geometry import ShipGenerationConfig, evaluate_visual_quality, generate_ship  # noqa: E402


SHIP_TYPES = (
    "light_raider",
    "interceptor",
    "gunship",
    "missile_corvette",
    "boarding_frigate",
    "freighter",
    "heavy_cruiser",
    "mining_ship",
    "salvage_ship",
    "medical_ship",
    "racing_ship",
    "luxury_yacht",
    "boss_capital_ship",
)


def main() -> None:
    for index, ship_type in enumerate(SHIP_TYPES, start=1):
        role = "boss" if ship_type == "boss_capital_ship" else "enemy"
        faction = "sector_navy" if ship_type in {"gunship", "missile_corvette", "heavy_cruiser", "boss_capital_ship"} else "independent"
        config = ShipGenerationConfig(
            role=role,
            faction=faction,
            seed=2400 + index,
            ship_type=ship_type,
            ship_id=f"visual_quality_{ship_type}",
            detail_level="hero",
            visual_quality="cinematic",
            structure_density=0.85,
            surface_geometry_density=0.85,
            armor_layer_density=0.75,
            panel_geometry_density=0.75,
            engine_complexity=0.90,
            cockpit_bridge_complexity=0.85,
            texture_workflow="procedural_shader",
            presentation_scene=False,
        )
        metadata = generate_ship(config)
        mesh_names = [mesh["name"] for mesh in metadata["meshes"]]
        objects = [obj for obj in __import__("bpy").data.objects if obj.name in mesh_names]
        dimensions = {
            "length": max(abs(mesh["position"][1]) for mesh in metadata["meshes"]) * 1.60,
            "width": max(abs(mesh["position"][0]) for mesh in metadata["meshes"]) * 1.60,
            "height": max(abs(mesh["position"][2]) for mesh in metadata["meshes"]) * 1.60,
        }
        report = evaluate_visual_quality(objects, dimensions, config)
        if not report["passes"]:
            raise RuntimeError(f"{ship_type} failed visual quality: {report}")
        print(f"{ship_type}: meshes={len(mesh_names)} score={report['score']:.3f} features={report['feature_counts']}")
    print("VOID_SHIPWRIGHT_VISUAL_QUALITY_SMOKE_OK")


if __name__ == "__main__":
    main()


# Component Schema

Component slots are internal ship systems. They are exported in metadata separately from visual hardpoints.

## Slot Types

- `power_plant`
- `cooler`
- `shield_generator`
- `quantum_or_warp_drive`
- `radar`
- `scanner`
- `life_support`
- `avionics`
- `armor_plating`
- `cargo_module`
- `crew_module`
- `repair_module`
- `stealth_module`

## Slot Fields

- `id`: Stable slot ID.
- `display_name`: Designer-facing name.
- `slot_type`: Required component category.
- `size`: Integer from `1` to `10`.
- `required`: Whether a valid runtime loadout should fill this slot.
- `optional`: Convenience inverse of `required`.
- `role_tags`: Frame role tags inherited by the slot.

## Component Definition Fields

Starter component definitions live in `data/components/starter_components.json`.

- `id`
- `display_name`
- `slot_type`
- `size`
- `grade`
- `manufacturer_tag`
- `power_draw`
- `heat_generation`
- `cooling_bonus`
- `shield_bonus`
- `mass`
- `reliability`
- `price`
- `rarity`
- `role_tags`
- `stat_modifiers`

## Grades

- `civilian`
- `industrial`
- `military`
- `competition`
- `stealth`
- `pirate`
- `ancient`

## Validation Intent

Runtime validation should reject oversized components and wrong slot types. Power, heat, shield, mass, cargo, crew, and maneuverability modifiers are exported as data so a future runtime can calculate final ship stats from the frame baseline plus component and equipment loadout.

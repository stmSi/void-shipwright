class_name VoidShipBuilder
extends RefCounted

const MetadataValidator = preload("res://addons/void_shipwright_importer/ship_metadata_validator.gd")

var validator := MetadataValidator.new()


func load_metadata(path: String) -> Dictionary:
    if not FileAccess.file_exists(path):
        push_error("Void Shipwright metadata does not exist: %s" % path)
        return {}

    var file := FileAccess.open(path, FileAccess.READ)
    if file == null:
        push_error("Could not open Void Shipwright metadata: %s" % path)
        return {}

    var parsed = JSON.parse_string(file.get_as_text())
    if typeof(parsed) != TYPE_DICTIONARY:
        push_error("Void Shipwright metadata is not a JSON object: %s" % path)
        return {}

    var errors := validator.validate(parsed)
    if not errors.is_empty():
        for error in errors:
            push_error(error)
        return {}

    return parsed


func build_ship(imported_root: Node3D, metadata: Dictionary) -> Node3D:
    var ship := Node3D.new()
    ship.name = _node_name(metadata.get("ship_id", "VoidShip"))
    ship.set_meta("void_shipwright_role", metadata["role"])
    ship.set_meta("void_shipwright_faction", metadata["faction"])
    ship.set_meta("void_shipwright_seed", metadata.get("seed", 0))

    var visual_root := Node3D.new()
    visual_root.name = "Visuals"
    ship.add_child(visual_root)

    var sockets_root := Node3D.new()
    sockets_root.name = "Sockets"
    ship.add_child(sockets_root)

    var collisions_root := Node3D.new()
    collisions_root.name = "Collision"
    ship.add_child(collisions_root)

    var damage_root := Node3D.new()
    damage_root.name = "DamageZones"
    ship.add_child(damage_root)

    var vfx_root := Node3D.new()
    vfx_root.name = "VFX"
    ship.add_child(vfx_root)

    _clone_visual_meshes(imported_root, visual_root)
    _build_markers(sockets_root, metadata.get("sockets", []))
    _build_markers(damage_root, metadata.get("damage_zones", []))
    _build_markers(vfx_root, metadata.get("vfx_markers", []))
    _build_markers(ship, metadata.get("camera_markers", []))
    _build_collision_shapes(collisions_root, metadata.get("collision_proxies", []))
    return ship


func _clone_visual_meshes(source: Node, target_parent: Node) -> void:
    for child in source.get_children():
        if child.name.begins_with("MESH_"):
            var copy := child.duplicate()
            target_parent.add_child(copy)
        elif child.get_child_count() > 0:
            _clone_visual_meshes(child, target_parent)


func _build_markers(parent: Node, entries: Array) -> void:
    for entry in entries:
        if typeof(entry) != TYPE_DICTIONARY:
            continue
        var marker := Marker3D.new()
        marker.name = entry.get("name", "Marker")
        marker.transform = _transform_from_metadata(entry)
        for key in entry.keys():
            if not ["name", "position", "rotation_euler", "scale"].has(key):
                marker.set_meta(key, entry[key])
        parent.add_child(marker)


func _build_collision_shapes(parent: Node, entries: Array) -> void:
    for entry in entries:
        if typeof(entry) != TYPE_DICTIONARY:
            continue

        var body := StaticBody3D.new()
        body.name = entry.get("name", "Collision")
        body.transform = _transform_from_metadata(entry, false)

        var shape := CollisionShape3D.new()
        shape.name = "%s_Shape" % body.name
        var box := BoxShape3D.new()
        var scale := _blender_to_godot_scale(_vec3(entry.get("scale", [1.0, 1.0, 1.0])))
        box.size = scale * 2.0
        shape.shape = box
        body.add_child(shape)
        parent.add_child(body)


func _transform_from_metadata(entry: Dictionary, include_scale: bool = true) -> Transform3D:
    var basis := Basis.from_euler(_vec3(entry.get("rotation_euler", [0.0, 0.0, 0.0])))
    if include_scale:
        basis = basis.scaled(_blender_to_godot_scale(_vec3(entry.get("scale", [1.0, 1.0, 1.0]))))
    return Transform3D(basis, _blender_to_godot_position(_vec3(entry.get("position", [0.0, 0.0, 0.0]))))


func _vec3(values: Array) -> Vector3:
    return Vector3(float(values[0]), float(values[1]), float(values[2]))


func _blender_to_godot_position(value: Vector3) -> Vector3:
    return Vector3(value.x, value.z, -value.y)


func _blender_to_godot_scale(value: Vector3) -> Vector3:
    return Vector3(value.x, value.z, value.y)


func _node_name(value: String) -> String:
    var safe := ""
    for index in range(value.length()):
        var code := value.unicode_at(index)
        var character := value.substr(index, 1)
        var is_digit := code >= 48 and code <= 57
        var is_upper := code >= 65 and code <= 90
        var is_lower := code >= 97 and code <= 122
        if is_digit or is_upper or is_lower or character == "_" or character == "-":
            safe += character
        else:
            safe += "_"
    return safe

@tool
extends EditorPlugin

const ShipBuilder = preload("res://addons/void_shipwright_importer/ship_builder.gd")

var _builder: ShipBuilder


func _enter_tree() -> void:
    _builder = ShipBuilder.new()
    add_tool_menu_item("Void Shipwright/Build Ship Scene", _build_selected_ship_scene)


func _exit_tree() -> void:
    remove_tool_menu_item("Void Shipwright/Build Ship Scene")
    _builder = null


func _build_selected_ship_scene() -> void:
    var selection := get_editor_interface().get_selection().get_selected_nodes()
    if selection.is_empty():
        push_warning("Select an imported ship root before building a Void Shipwright scene.")
        return

    var root := selection[0]
    if not root is Node3D:
        push_warning("Selected node must be a Node3D imported from Blender.")
        return

    var metadata_path := "%s.metadata.json" % root.scene_file_path.get_basename()
    if not FileAccess.file_exists(metadata_path):
        push_warning("Missing metadata file: %s" % metadata_path)
        return

    var metadata := _builder.load_metadata(metadata_path)
    if metadata.is_empty():
        return

    var ship_scene := _builder.build_ship(root as Node3D, metadata)
    root.add_sibling(ship_scene)
    ship_scene.owner = root.owner
    get_editor_interface().edit_node(ship_scene)

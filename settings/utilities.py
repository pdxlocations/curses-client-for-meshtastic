from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2
from save_to_radio import settings_reboot, settings_factory_reset, settings_reset_nodedb, settings_set_owner, settings_shutdown
import logging, traceback

# Function to generate the menu structure from protobuf messages
def generate_menu_from_protobuf(interface):

    def extract_fields(message_instance, current_config=None):
        if isinstance(current_config, dict):  # Handle dictionaries
            return {key: (None, current_config.get(key, "Not Set")) for key in current_config}
        
        if not hasattr(message_instance, "DESCRIPTOR"):
            return {}
        
        menu = {}
        fields = message_instance.DESCRIPTOR.fields
        for field in fields:
            if field.name == "sessionkey":
                continue
            if field.message_type:  # Nested message
                nested_instance = getattr(message_instance, field.name)
                nested_config = getattr(current_config, field.name, None) if current_config else None
                menu[field.name] = extract_fields(nested_instance, nested_config)
            else:
                # Fetch the current value if available
                current_value = getattr(current_config, field.name, "Not Set") if current_config else "Not Set"
                menu[field.name] = (field, current_value)
        return menu

    menu_structure = {"Main Menu": {}}

    # Add Radio Settings
    radio = config_pb2.Config()
    current_radio_config = interface.localNode.localConfig if interface else None
    menu_structure["Main Menu"]["Radio Settings"] = extract_fields(radio, current_radio_config)

    # Add Module Settings
    module = module_config_pb2.ModuleConfig()
    current_module_config = interface.localNode.moduleConfig if interface else None
    menu_structure["Main Menu"]["Module Settings"] = extract_fields(module, current_module_config)

    # Add User Settings
    current_node_info = interface.getMyNodeInfo() if interface else None

    if current_node_info:
        print("Node Info:", current_node_info)
        current_user_config = current_node_info.get("user", None)
        if current_user_config and isinstance(current_user_config, dict):
            # Only include longName and shortName
            menu_structure["Main Menu"]["User Settings"] = {
                "longName": (None, current_user_config.get("longName", "Not Set")),
                "shortName": (None, current_user_config.get("shortName", "Not Set"))
            }
        else:
            logging.info("User settings not found in Node Info")
            menu_structure["Main Menu"]["User Settings"] = "No user settings available"
    else:
        logging.info("Node Info not available")
        menu_structure["Main Menu"]["User Settings"] = "Node Info not available"

    # Add Channels
    channel = channel_pb2.ChannelSettings()
    menu_structure["Main Menu"]["Channels"] = {}
    if interface:
        for i in range(8):
            current_channel = interface.localNode.getChannelByChannelIndex(i)
            if current_channel:
                channel_config = extract_fields(channel, current_channel.settings)
                menu_structure["Main Menu"]["Channels"][f"Channel {i + 1}"] = channel_config

    # Add additional settings options
    menu_structure["Main Menu"]["Reboot"] = settings_reboot
    menu_structure["Main Menu"]["Reset Node DB"] = settings_reset_nodedb
    menu_structure["Main Menu"]["Shutdown"] = settings_shutdown
    menu_structure["Main Menu"]["Factory Reset"] = settings_factory_reset

    # Add Exit option
    menu_structure["Main Menu"]["Exit"] = None

    return menu_structure
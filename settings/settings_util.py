from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2
from settings_save_to_radio import settings_reboot, settings_factory_reset, settings_reset_nodedb, settings_set_owner, settings_shutdown


# Function to generate the menu structure from protobuf messages
def generate_menu_from_protobuf(interface):
    def extract_fields(message_instance, current_config=None):
        if not hasattr(message_instance, "DESCRIPTOR"):
            return {}
        menu = {}
        fields = message_instance.DESCRIPTOR.fields
        for field in fields:
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
    user = mesh_pb2.User()
    current_user_config = interface.getMyNodeInfo()["user"] if interface else None
    menu_structure["Main Menu"]["User Settings"] = extract_fields(user, current_user_config)

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
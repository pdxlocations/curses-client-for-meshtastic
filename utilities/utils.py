import globals
from meshtastic.protobuf import config_pb2
import re

def get_channels():
    """Retrieve channels from the node and update globals.channel_list and globals.all_messages."""
    node = globals.interface.getNode('^local')
    device_channels = node.channels

    # Clear and rebuild channel list
    globals.channel_list = []

    for device_channel in device_channels:
        if device_channel.role:
            # Use the channel name if available, otherwise use the modem preset
            if device_channel.settings.name:
                channel_name = device_channel.settings.name
            else:
                # If channel name is blank, use the modem preset
                lora_config = node.localConfig.lora
                modem_preset_enum = lora_config.modem_preset
                modem_preset_string = config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[modem_preset_enum].name
                channel_name = convert_to_camel_case(modem_preset_string)

            # Add channel to globals.channel_list if not already present
            if channel_name not in globals.channel_list:
                globals.channel_list.append(channel_name)

            # Initialize globals.all_messages[channel_name] if it doesn't exist
            if channel_name not in globals.all_messages:
                globals.all_messages[channel_name] = []


    return globals.channel_list

def get_node_list():
    node_list = []
    if globals.interface.nodes:
        for node in globals.interface.nodes.values():
            node_list.append(node['num'])
    return node_list

def get_nodeNum():
    myinfo = globals.interface.getMyNodeInfo()
    myNodeNum = myinfo['num']
    return myNodeNum

def decimal_to_hex(decimal_number):
    return f"!{decimal_number:08x}"

def convert_to_camel_case(string):
    words = string.split('_')
    camel_case_string = ''.join(word.capitalize() for word in words)
    return camel_case_string

def get_name_from_number(number, type='long'):
    name = ""
    for node in globals.interface.nodes.values():
        if number == node['num']:
            if type == 'long':
                name = node['user']['longName']
                return name
            elif type == 'short':
                name = node['user']['shortName']
                return name
            else:
                pass
        else:
            name = str(decimal_to_hex(number))  # If long name not found, use the ID as string
    return name

def sanitize_string(input_str: str) -> str:
    """Check if the string starts with a letter (a-z, A-Z) or an underscore (_), and replace all non-alpha/numeric/underscore characters with underscores."""

    if not re.match(r'^[a-zA-Z_]', input_str):
        # If not, add "_"
        input_str = '_' + input_str

    # Replace special characters with underscores (for database tables)
    sanitized_str: str = re.sub(r'[^a-zA-Z0-9_]', '_', input_str)
    return sanitized_str
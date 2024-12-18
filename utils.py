
import globals
from meshtastic.protobuf import config_pb2


def get_nodeNum(interface):
    myinfo = interface.getMyNodeInfo()
    myNodeNum = myinfo['num']
    return myNodeNum

def get_channels():
    node = globals.interface.getNode('^local')
    device_channels = node.channels

    channel_output = []
    for device_channel in device_channels:
        if device_channel.role:
            if device_channel.settings.name:
                channel_output.append(device_channel.settings.name)
                globals.all_messages[device_channel.settings.name] = []

            else:
                # If channel name is blank, use the modem preset
                lora_config = node.localConfig.lora
                modem_preset_enum = lora_config.modem_preset
                modem_preset_string = config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[modem_preset_enum].name
                channel_output.append(convert_to_camel_case(modem_preset_string))
                globals.all_messages[convert_to_camel_case(modem_preset_string)] = []

    globals.channel_list = list(globals.all_messages.keys())



def get_node_list():
    node_list = []
    if globals.interface.nodes:
        for node in globals.interface.nodes.values():
            node_list.append(node['num'])
    return node_list

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
            name =  str(decimal_to_hex(number))  # If long name not found, use the ID as string
    return name
        
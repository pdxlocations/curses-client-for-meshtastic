from meshtastic.protobuf import channel_pb2
import logging
import base64

def settings_reboot(interface):
    interface.localNode.reboot()

def settings_reset_nodedb(interface):
    interface.localNode.resetNodeDb()

def settings_shutdown(interface):
    interface.localNode.shutdown()

def settings_factory_reset(interface):
    interface.localNode.factoryReset()

def settings_set_owner(interface, long_name=None, short_name=None, is_licensed=False):
    if isinstance(is_licensed, str):
        is_licensed = is_licensed.lower() == 'true'
    interface.localNode.setOwner(long_name, short_name, is_licensed)



def save_changes(interface, menu_path, modified_settings):
    """
    Save changes to the device based on modified settings.
    :param interface: Meshtastic interface instance
    :param menu_path: Current menu path
    :param modified_settings: Dictionary of modified settings
    """
    try:
        if not modified_settings:
            logging.info("No changes to save. modified_settings is empty.")
            return
        
        node = interface.getNode('^local')

        if menu_path[1] ==  "Radio Settings" or menu_path[1] == "Module Settings":
            config_category = menu_path[2].lower() # for radio and module configs

        elif menu_path[1] == "User Settings": # for user configs
            config_category = "User Settings" 
            long_name = modified_settings.get("longName", None)
            short_name = modified_settings.get("shortName", None)
            #TODO add is_licensed
            node.setOwner(long_name, short_name, is_licensed=False)
            logging.info(f"Updated {config_category} with Long Name: {long_name} and Short Name {short_name}")
            return
        

        elif menu_path[1] == "Channels":    # for channel configs
            config_category = "Channels"

            try:
                channel = menu_path[-1]
                channel_num = int(channel.split()[-1])
            except (IndexError, ValueError) as e:
                channel_num = None

            channel = node.channels[channel_num]
            for key, value in modified_settings.items():
                if key == 'psk':  # Special case: decode Base64 for psk
                    channel.settings.psk = base64.b64decode(value)
                elif key == 'position_precision':  # Special case: module_settings
                    channel.settings.module_settings.position_precision = value
                else:
                    setattr(channel.settings, key, value)  # Use setattr for other fields

            if channel_num == 0:
                channel.role = channel_pb2.Channel.Role.PRIMARY
            else:
                channel.role = channel_pb2.Channel.Role.SECONDARY

            node.writeChannel(channel_num)

            logging.info(f"Updated Channel {channel_num} in {config_category}")
            logging.info(node.channels)
            return

        else:
            config_category = None

        for config_item, new_value in modified_settings.items():
            if hasattr(node.localConfig, config_category):
                config_subcategory = getattr(node.localConfig, config_category)
                if hasattr(config_subcategory, config_item):
                    setattr(config_subcategory, config_item, new_value)
                    logging.info(f"Updated {config_category}.{config_item} to {new_value}")
                else:
                    logging.warning(f"config item '{config_item}' not found in config category '{config_category}'")

            elif hasattr(node.moduleConfig, config_category):
                config_subcategory = getattr(node.moduleConfig, config_category)
                if hasattr(config_subcategory, config_item):
                    setattr(config_subcategory, config_item, new_value)
                    logging.info(f"Updated {config_category}.{config_item} to {new_value}")
                else:
                    logging.warning(f"config item '{config_item}' not found in config category '{config_category}'")

            else:
                logging.warning(f"config category '{config_category}' not found in config")


        node.writeConfig(config_category)

        logging.info(f"Changes written to config category: {config_category}")

    except Exception as e:
        logging.error(f"Error saving changes: {e}")

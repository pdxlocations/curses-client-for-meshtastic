import logging

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
        node = interface.getNode('^local')
        if len(menu_path) > 2:
            config_category = menu_path[2].lower()
        else:    
            config_category = menu_path[-1].lower()

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

            elif config_category == 'user settings':
                long_name = modified_settings.get("longName", None)
                short_name = modified_settings.get("shortName", None)
                node.setOwner(long_name, short_name, is_licensed=False)
                logging.info(f"Updated {config_category} with Long Name: {long_name} and Short Name {short_name}")
                return
            
            elif menu_path[1] == 'Channels':

                #TODO

                logging.info(f"Updated {config_category} ")
                return

            else:
                logging.warning(f"config category '{config_category}' not found in config")


        node.writeConfig(config_category)

        logging.info(f"Changes written to config category: {config_category}")

    except Exception as e:
        logging.error(f"Error saving changes: {e}")

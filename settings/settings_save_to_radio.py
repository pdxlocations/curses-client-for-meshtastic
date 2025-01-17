import meshtastic.serial_interface
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
    Save changes to the Meshtastic device based on modified settings.
    :param interface: Meshtastic interface instance
    :param menu_path: Current menu path
    :param modified_settings: Dictionary of modified settings
    """
    try:
        # Get the node configuration
        node = interface.getNode('^local')

        # Apply the changes to the localConfig dynamically
        for option, new_value in modified_settings.items():
        # for option, (field, new_value) in modified_settings.items():
            section = menu_path[-1].lower()  # Determine the configuration section (e.g., 'device')
            if hasattr(node.localConfig, section):
                section_config = getattr(node.localConfig, section)
                if hasattr(section_config, option):
                    setattr(section_config, option, new_value)
                    logging.info(f"Updated {section}.{option} to {new_value}")
                else:
                    logging.warning(f"Option '{option}' not found in section '{section}'")

            elif hasattr(node.moduleConfig, section):
                section_config = getattr(node.moduleConfig, section)
                if hasattr(section_config, option):
                    setattr(section_config, option, new_value)
                    logging.info(f"Updated {section}.{option} to {new_value}")
                else:
                    logging.warning(f"Option '{option}' not found in section '{section}'")
            else:
                logging.warning(f"Section '{section}' not found in localConfig")

        # Write the changes for the relevant section
        section_name = menu_path[-1].lower()


        node.writeConfig(section_name)



        logging.info(f"Changes written to section: {section_name}")
        print("Configuration successfully updated and saved!")
    except Exception as e:
        logging.error(f"Error saving changes: {e}")
        print(f"Failed to save changes: {e}")


   

def new_func():
    print('')

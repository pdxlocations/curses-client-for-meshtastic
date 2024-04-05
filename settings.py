import curses
from meshtastic import config_pb2, module_config_pb2
import meshtastic.serial_interface, meshtastic.tcp_interface


def generate_menu_from_protobuf(message_instance):
    if not hasattr(message_instance, "DESCRIPTOR"):
        return  # This is not a protobuf message instance, exit
    
    menu = {}
    field_names = message_instance.DESCRIPTOR.fields_by_name.keys()
    for field_name in field_names:
        field_descriptor = message_instance.DESCRIPTOR.fields_by_name[field_name]

        if field_descriptor is not None:
            nested_message_instance = getattr(message_instance, field_name)
            menu[field_name] = generate_menu_from_protobuf(nested_message_instance)

    return menu


def nested_menu(stdscr, menu, interface):
    menu_item = 0
    current_menu = menu
    prev_menu = []
    menu_index = 0

    while True:
        stdscr.clear()
        stdscr.border()

        # Display current menu
        if current_menu is not None:
            for i, key in enumerate(current_menu.keys(), start=0):
                if i == menu_item:
                    if key in ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]:
                        stdscr.addstr(i+1, 1, key, curses.color_pair(5))
                    else:
                        stdscr.addstr(i+1, 1, key, curses.A_REVERSE)
                else:
                    stdscr.addstr(i+1, 1, key)

            # Get user input
            char = stdscr.getch()

            if char == curses.KEY_DOWN:
                menu_item = min(len(current_menu) - 1, menu_item + 1)
            elif char == curses.KEY_UP:
                menu_item = max(0, menu_item - 1)
            elif char == curses.KEY_RIGHT:
                selected_key = list(current_menu.keys())[menu_item]
                selected_value = current_menu[selected_key]
                if isinstance(selected_value, dict):
                    # If the selected item is a submenu, navigate to it
                    if 0 <= menu_index < len(prev_menu):
                        prev_menu[menu_index] = current_menu
                    else:
                        prev_menu.append(current_menu)
                    menu_index += 1
                    current_menu = selected_value
                    menu_item = 0

            elif char == curses.KEY_LEFT:
                if menu_index > 0:
                    current_menu = prev_menu[menu_index-1]
                    menu_index -= 1
                menu_item = 0

            elif char == ord('\n'):
                # If user presses enter, display the selected value if it's not a submenu
                selected_key = list(current_menu.keys())[menu_item]
                selected_value = current_menu[selected_key]

                if selected_key == "Reboot":
                    settings_reboot(interface)
                elif selected_key == "Reset NodeDB":
                    settings_reset_nodedb(interface)
                elif selected_key == "Shutdown":
                    settings_shutdown(interface)
                elif selected_key == "Factory Reset":
                    settings_factory_reset(interface)

                elif selected_value is not None:
                    stdscr.refresh()
                    stdscr.getch()  # Wait for user input before continuing
            # escape to exit menu        
            elif char == 27:
                break
        else:
            break  # Exit loop if current_menu is None


def settings(stdscr, interface):
    popup_height = 20
    popup_width = 50
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2
    popup_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    popup_win.border()
    popup_win.keypad(True)
    
    # Generate menu from protobuf for both radio and module settings
    radio = config_pb2.Config()
    radio_config = generate_menu_from_protobuf(radio)

    module = module_config_pb2.ModuleConfig()
    module_config = generate_menu_from_protobuf(module)

    # Add top-level menu items
    top_level_menu = {
        "Radio Settings": radio_config,
        "Module Settings": module_config,
        "Reboot": None,
        "Reset NodeDB": None,
        "Shutdown": None,
        "Factory Reset": None
    }

    # Call nested_menu function to display and handle the nested menu
    nested_menu(popup_win, top_level_menu, interface)

    # Close the popup window
    popup_win.clear()
    popup_win.refresh()
    del popup_win  # Delete the window object to free up memory


def settings_reboot(interface):
    interface.getNode('^local').reboot()

def settings_reset_nodedb(interface):
    interface.getNode('^local').resetNodeDb()

def settings_shutdown(interface):
    interface.getNode('^local').shutdown()

def settings_factory_reset(interface):
    interface.getNode('^local').factory_reset()

    # ourNode = interface.getNode('^local')
    # ourNode.localConfig.lora.modem_preset = 'LONG_FAST'
    # ourNode.writeConfig("lora")

if __name__ == "__main__": 
    interface = meshtastic.serial_interface.SerialInterface()
    radio = config_pb2.Config()
    module = module_config_pb2.ModuleConfig()
    print(generate_menu_from_protobuf(radio))
    print(generate_menu_from_protobuf(module))
    
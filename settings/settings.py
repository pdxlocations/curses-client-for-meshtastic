import curses
from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2
import meshtastic.serial_interface
from settings_util import settings_factory_reset, settings_reboot, settings_reset_nodedb, settings_set_owner, settings_shutdown, generate_menu_from_protobuf
from setting_input_handlers import get_bool_selection, get_repeated_input, get_user_input, get_enum_input
from settings_save_to_radio import save_changes


import logging
import traceback
# Configure logging
# Run `tail -f client.log` in another terminal to view live
logging.basicConfig(
    filename="settings.log",
    level=logging.INFO
    ,  # DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"
)



def display_menu(stdscr, current_menu, menu_path, selected_index, show_save_option):
    # Calculate the dynamic height based on the number of menu items
    num_items = len(current_menu) + (1 if show_save_option else 0)  # Add 1 for the "Save Changes" option if applicable
    height = min(curses.LINES - 2, num_items + 5)  # Ensure the menu fits within the terminal height
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a new curses window with dynamic dimensions
    menu_win = curses.newwin(height, width, start_y, start_x)
    menu_win.clear()
    menu_win.border()

    # Display the current menu path as a header
    header = " > ".join(menu_path)
    if len(header) > width - 4:
        header = header[:width - 7] + "..."
    menu_win.addstr(1, 2, header, curses.A_BOLD)

    # Display the menu options
    for idx, option in enumerate(current_menu):
        field_info = current_menu[option]
        current_value = field_info[1] if isinstance(field_info, tuple) else ""
        display_option = f"{option}"[:width // 2 - 2]  # Truncate option name if too long
        display_value = f"{current_value}"[:width // 2 - 4]  # Truncate value if too long

        try:
            if idx == selected_index:
                menu_win.addstr(idx + 3, 4, f"{display_option:<{width // 2 - 2}} {display_value}", curses.A_REVERSE)
            else:
                menu_win.addstr(idx + 3, 4, f"{display_option:<{width // 2 - 2}} {display_value}")
        except curses.error:
            pass

    # Show save option if applicable
    if show_save_option:
        save_option = "Save Changes"
        save_position = height - 2
        if selected_index == len(current_menu):
            menu_win.addstr(save_position, (width - len(save_option)) // 2, save_option, curses.A_REVERSE)
        else:
            menu_win.addstr(save_position, (width - len(save_option)) // 2, save_option)

    menu_win.refresh()

def nested_menu(stdscr, menu, interface):
    current_menu = menu["Main Menu"]
    menu_path = ["Main Menu"]
    selected_index = 0
    modified_settings = {}

    while True:
        # Extract keys of the current menu
        options = list(current_menu.keys())

        show_save_option = "Radio Settings" in menu_path or "Module Settings" in menu_path or "User Settings" in menu_path

        # Display the menu
        display_menu(stdscr, current_menu, menu_path, selected_index, show_save_option)

        # Capture user input
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) if not show_save_option else len(options) + 1 - 1, selected_index + 1)
        elif key == curses.KEY_RIGHT or key == ord('\n'):
            if show_save_option and selected_index == len(options):

                # Save changes
                save_changes(interface, menu_path, modified_settings)

                stdscr.addstr(1, 2, "Changes saved! Press any key to continue.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                continue

            selected_option = options[selected_index]

            if selected_option == "Exit":
                break
            elif selected_option == "Reboot":
                settings_reboot(interface)
                stdscr.addstr(1, 2, "Rebooting... Press any key to continue.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                break
            elif selected_option == "Reset Node DB":
                settings_reset_nodedb(interface)
                stdscr.addstr(1, 2, "Node DB reset. Press any key to continue.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
            elif selected_option == "Shutdown":
                settings_shutdown(interface)
                stdscr.addstr(1, 2, "Shutting down... Press any key to exit.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                break
            elif selected_option == "Factory Reset":
                settings_factory_reset(interface)
                stdscr.addstr(1, 2, "Factory reset complete. Press any key to continue.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()

            field_info = current_menu.get(selected_option)

            if isinstance(field_info, tuple):
                field, current_value = field_info

                if field.type == 8:  # Handle boolean type
                    new_value = get_bool_selection(stdscr, str(current_value))
                    try:
                        # Convert the input into a valid boolean
                        if isinstance(new_value, str):
                            # Handle string representations of booleans
                            new_value = new_value.lower() in ("true", "yes", "1", "on")
                        else:
                            # Convert other types directly to bool
                            new_value = bool(new_value)
                        isbool = True
                    except ValueError:
                        stdscr.addstr(1, 2, "Invalid input for boolean. Please try again.", curses.A_BOLD)
                        stdscr.refresh()
                        stdscr.getch()

                elif field.label == field.LABEL_REPEATED:  # Handle repeated field
                    new_value = get_repeated_input(stdscr, current_value)
                    isrepeated = True

                elif field.enum_type:  # Enum field
                    enum_options = [v.name for v in field.enum_type.values]
                    new_value = get_enum_input(stdscr, enum_options, current_value)
                    isemnum = True

                elif field.type == 13: # Field type 13 corresponds to UINT32
                    new_value = get_user_input(stdscr, f"Current value for {selected_option}: {current_value}")
                    new_value = int(new_value)
                    isint = True

                else:  # Handle other field types
                    new_value = get_user_input(stdscr, f"Current value for {selected_option}: {current_value}")
                    isother = True

                # Update the modified settings and current menu
                modified_settings[selected_option] = (new_value)
                # modified_settings[selected_option] = (field, new_value)
                current_menu[selected_option] = (field, new_value)
            else:
                current_menu = current_menu[selected_option]
                menu_path.append(selected_option)
                selected_index = 0


        elif key == curses.KEY_LEFT:
            # Navigate back to the previous menu
            if len(menu_path) > 1:
                menu_path.pop()
                current_menu = menu["Main Menu"]
                for step in menu_path[1:]:
                    current_menu = current_menu.get(step, {})
                selected_index = 0
        elif key == 27:  # Escape key
            break

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)

    # Initialize Meshtastic interface
    interface = meshtastic.serial_interface.SerialInterface()

    # Generate menu structure from protobuf
    menu_structure = generate_menu_from_protobuf(interface)
    stdscr.clear()
    stdscr.refresh()
    nested_menu(stdscr, menu_structure, interface)

if __name__ == "__main__":
    curses.wrapper(main)
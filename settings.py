import curses
import logging

from save_to_radio import settings_factory_reset, settings_reboot, settings_reset_nodedb, settings_shutdown, save_changes
from ui.menus import generate_menu_from_protobuf
from input_handlers import get_bool_selection, get_repeated_input, get_user_input, get_enum_input, get_fixed32_input
from ui.colors import setup_colors, get_color
from utilities.arg_parser import setup_parser
from utilities.interfaces import initialize_interface
import globals

width = 60
save_option = "Save Changes"
sensitive_settings = ["Reboot", "Reset Node DB", "Shutdown", "Factory Reset"]

def display_menu(current_menu, menu_path, selected_index, show_save_option):
    global menu_win

    # Calculate the dynamic height based on the number of menu items
    num_items = len(current_menu) + (1 if show_save_option else 0)  # Add 1 for the "Save Changes" option if applicable
    height = min(curses.LINES - 2, num_items + 5)  # Ensure the menu fits within the terminal height
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a new curses window with dynamic dimensions
    menu_win = curses.newwin(height, width, start_y, start_x)
    menu_win.clear()
    menu_win.attrset((get_color("window_frame")))
    menu_win.border()
    menu_win.keypad(True)

    # Display the current menu path as a header
    header = " > ".join(word.title() for word in menu_path)
    if len(header) > width - 4:
        header = header[:width - 7] + "..."
    menu_win.addstr(1, 2, header, get_color("settings_breadcrumbs", bold=True))

    # Display the menu options
    for idx, option in enumerate(current_menu):
        field_info = current_menu[option]
        current_value = field_info[1] if isinstance(field_info, tuple) else ""
        display_option = f"{option}"[:width // 2 - 2]  # Truncate option name if too long``
        display_value = f"{current_value}"[:width // 2 - 4]  # Truncate value if too long

        try:
            # Use red color for "Reboot" or "Shutdown"
            color = get_color("settings_sensitive" if option in sensitive_settings else "default", reverse = (idx == selected_index))
            menu_win.addstr(idx + 3, 4, f"{display_option:<{width // 2 - 2}} {display_value}".ljust(width - 8), color)
        except curses.error:
            pass

    # Show save option if applicable
    if show_save_option:
        save_position = height - 2
        menu_win.addstr(save_position, (width - len(save_option)) // 2, save_option, get_color("settings_save", reverse = (selected_index == len(current_menu))))

    menu_win.refresh()

def move_highlight(old_idx, new_idx, options, show_save_option, menu_win):

    if(old_idx == new_idx): # no-op
        return

    max_index = len(options) + (1 if show_save_option else 0) - 1

    if show_save_option and old_idx == max_index: # special case un-highlight "Save" option
        menu_win.chgat(max_index + 4, (width - len(save_option)) // 2, len(save_option), get_color("settings_save"))
    else:
        menu_win.chgat(old_idx + 3, 4, width - 8, get_color("settings_sensitive" if options[old_idx] in sensitive_settings else "default"))

    if show_save_option and new_idx == max_index: # special case highlight "Save" option
        menu_win.chgat(max_index + 4, (width - len(save_option)) // 2, len(save_option), get_color("settings_save", reverse = True))
    else:
       menu_win.chgat(new_idx + 3, 4, width - 8, get_color("settings_sensitive" if options[new_idx] in sensitive_settings else "default", reverse = True))

    menu_win.refresh()

def settings_menu(stdscr, interface):

    menu = generate_menu_from_protobuf(interface)
    current_menu = menu["Main Menu"]
    menu_path = ["Main Menu"]
    selected_index = 0
    modified_settings = {}
    
    need_redraw = True
    show_save_option = False

    while True:
        if(need_redraw):
            options = list(current_menu.keys())

            show_save_option = (
                len(menu_path) > 2 and ("Radio Settings" in menu_path or "Module Settings" in menu_path)
            ) or (
                len(menu_path) == 2 and "User Settings" in menu_path 
            ) or (
                len(menu_path) == 3 and "Channels" in menu_path
            )

            # Display the menu
            display_menu(current_menu, menu_path, selected_index, show_save_option)

            need_redraw = False

        # Capture user input
        key = menu_win.getch()

        if key == curses.KEY_UP:
            old_selected_index = selected_index
            selected_index = max(0, selected_index - 1)
            move_highlight(old_selected_index, selected_index, options, show_save_option, menu_win)
            
        elif key == curses.KEY_DOWN:
            old_selected_index = selected_index
            max_index = len(options) + (1 if show_save_option else 0) - 1
            selected_index = min(max_index, selected_index + 1)
            move_highlight(old_selected_index, selected_index, options, show_save_option, menu_win)

        elif key == curses.KEY_RIGHT or key == ord('\n'):
            need_redraw = True
            menu_win.clear()
            menu_win.refresh()
            if show_save_option and selected_index == len(options):
                save_changes(interface, menu_path, modified_settings)
                modified_settings.clear()
                logging.info("Changes Saved")

                if len(menu_path) > 1:
                    menu_path.pop()
                    current_menu = menu["Main Menu"]
                    for step in menu_path[1:]:
                        current_menu = current_menu.get(step, {})
                    selected_index = 0

                continue

            selected_option = options[selected_index]

            if selected_option == "Exit":
                break
            elif selected_option == "Reboot":
                confirmation = get_bool_selection("Are you sure you want to Reboot?", 0)
                if confirmation == "True":
                    settings_reboot(interface)
                    logging.info(f"Node Reboot Requested by menu")
                    break
            elif selected_option == "Reset Node DB":
                confirmation = get_bool_selection("Are you sure you want to Reset Node DB?", 0)
                if confirmation == "True":
                    settings_reset_nodedb(interface)
                    logging.info(f"Node DB Reset Requested by menu")
                    break
            elif selected_option == "Shutdown":
                confirmation = get_bool_selection("Are you sure you want to Shutdown?", 0)
                if confirmation == "True":
                    settings_shutdown(interface)
                    logging.info(f"Node Shutdown Requested by menu")
                    break
            elif selected_option == "Factory Reset":
                confirmation = get_bool_selection("Are you sure you want to Factory Reset?", 0)
                if confirmation == "True":
                    settings_factory_reset(interface)
                    logging.info(f"Factory Reset Requested by menu")
                    break

            field_info = current_menu.get(selected_option)
            if isinstance(field_info, tuple):
                field, current_value = field_info

                if selected_option in ['longName', 'shortName', 'isLicensed']:
                    if selected_option in ['longName', 'shortName']:
                        new_value = get_user_input(f"Current value for {selected_option}: {current_value}")
                        current_menu[selected_option] = (field, new_value)

                    elif selected_option == 'isLicensed':
                        new_value = get_bool_selection(f"Current value for {selected_option}: {current_value}", str(current_value))
                        new_value = new_value == "True"
                        current_menu[selected_option] = (field, new_value)

                    for option, (field, value) in current_menu.items():
                        modified_settings[option] = value

                elif field.type == 8:  # Handle boolean type
                    new_value = get_bool_selection(selected_option, str(current_value))
                    new_value = new_value == "True"

                elif field.label == field.LABEL_REPEATED:  # Handle repeated field
                    new_value = get_repeated_input(current_value)
                    new_value = current_value if new_value is None else [int(item) for item in new_value]

                elif field.enum_type:  # Enum field
                    enum_options = [v.name for v in field.enum_type.values]
                    new_value = get_enum_input(enum_options, current_value)

                elif field.type == 7: # Field type 7 corresponds to FIXED32
                    new_value = get_fixed32_input(current_value)

                elif field.type == 13: # Field type 13 corresponds to UINT32
                    new_value = get_user_input(f"Current value for {selected_option}: {current_value}")
                    new_value = current_value if new_value is None else int(new_value)

                elif field.type == 2: # Field type 13 corresponds to INT64
                    new_value = get_user_input(f"Current value for {selected_option}: {current_value}")
                    new_value = current_value if new_value is None else float(new_value)

                else:  # Handle other field types
                    new_value = get_user_input(f"Current value for {selected_option}: {current_value}")
                    new_value = current_value if new_value is None else new_value
                
                for key in menu_path[3:]:  # Skip "Main Menu"
                    modified_settings = modified_settings.setdefault(key, {})

                # Add the new value to the appropriate level
                modified_settings[selected_option] = new_value

                current_menu[selected_option] = (field, new_value)
            else:
                current_menu = current_menu[selected_option]
                menu_path.append(selected_option)
                selected_index = 0

        elif key == curses.KEY_LEFT:
            need_redraw = True

            menu_win.clear()
            menu_win.refresh()

            modified_settings.clear()

            # Navigate back to the previous menu
            if len(menu_path) > 1:
                menu_path.pop()
                current_menu = menu["Main Menu"]
                for step in menu_path[1:]:
                    current_menu = current_menu.get(step, {})
                selected_index = 0

        elif key == 27:  # Escape key
            menu_win.clear()
            menu_win.refresh()
            break


def main(stdscr):
    logging.basicConfig( # Run `tail -f client.log` in another terminal to view live
        filename="settings.log",
        level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    setup_colors()
    curses.curs_set(0)
    stdscr.keypad(True)

    parser = setup_parser()
    args = parser.parse_args()
    globals.interface = initialize_interface(args)

    settings_menu(stdscr, globals.interface)

if __name__ == "__main__":
    curses.wrapper(main)

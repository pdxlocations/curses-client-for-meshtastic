import curses
from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2
import meshtastic.serial_interface


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

def get_user_input(stdscr, prompt):
    # Calculate the dynamic height and width for the input window
    height = 7  # Fixed height for input prompt
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a new window for user input
    input_win = curses.newwin(height, width, start_y, start_x)
    input_win.clear()
    input_win.border()

    # Display the prompt
    input_win.addstr(1, 2, prompt, curses.A_BOLD)
    input_win.addstr(3, 2, "Enter value: ")
    input_win.refresh()

    # Enable user input
    curses.echo()
    curses.curs_set(1)
    user_input = input_win.getstr(3, 15).decode("utf-8")
    curses.curs_set(0)
    curses.noecho()

    # Clear the input window
    input_win.clear()
    input_win.refresh()

    return user_input

def get_bool_selection(stdscr, current_value):
    options = ["True", "False"]
    selected_index = 0 if current_value == "True" else 1

    # Set dimensions and position to match other windows
    height = 7
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a curses window for boolean selection
    bool_win = curses.newwin(height, width, start_y, start_x)
    bool_win.keypad(True)

    while True:
        bool_win.clear()
        bool_win.border()
        bool_win.addstr(1, 2, "Select True or False:", curses.A_BOLD)

        # Display options
        for idx, option in enumerate(options):
            if idx == selected_index:
                bool_win.addstr(idx + 3, 4, option, curses.A_REVERSE)
            else:
                bool_win.addstr(idx + 3, 4, option)

        bool_win.refresh()
        key = bool_win.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) - 1, selected_index + 1)
        elif key == ord('\n'):  # Enter key to select
            return options[selected_index]
        elif key == 27:  # Escape key to cancel
            return current_value

def get_repeated_input(stdscr, current_value):
    height = 10
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    repeated_win = curses.newwin(height, width, start_y, start_x)
    repeated_win.clear()
    repeated_win.border()

    curses.echo()
    repeated_win.addstr(1, 2, "Enter comma-separated values:", curses.A_BOLD)
    repeated_win.addstr(3, 2, f"Current: {current_value}")
    repeated_win.addstr(5, 2, "New value: ")
    repeated_win.refresh()

    user_input = repeated_win.getstr(5, 13).decode("utf-8")
    curses.noecho()

    repeated_win.clear()
    repeated_win.refresh()

    return user_input.split(",")

def select_enum_option(stdscr, options, current_value):
    selected_index = options.index(current_value) if current_value in options else 0

    # Set dimensions and position to match other windows
    height = min(len(options) + 4, curses.LINES - 2)  # Dynamic height based on options
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a curses window for enum selection
    enum_win = curses.newwin(height, width, start_y, start_x)
    enum_win.keypad(True)

    while True:
        enum_win.clear()
        enum_win.border()
        enum_win.addstr(1, 2, "Select an option:", curses.A_BOLD)

        # Display options
        for idx, option in enumerate(options):
            if idx == selected_index:
                enum_win.addstr(idx + 2, 4, option, curses.A_REVERSE)
            else:
                enum_win.addstr(idx + 2, 4, option)

        enum_win.refresh()
        key = enum_win.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) - 1, selected_index + 1)
        elif key == ord('\n'):  # Enter key to select
            return options[selected_index]
        elif key == 27:  # Escape key to cancel
            return current_value
        
def save_changes(interface, menu_path, settings):
    try:
        # Determine the specific subcategory (config_name) based on the menu path
        if menu_path[1] == "Radio Settings":
            config_name = menu_path[2]  # The second level in the menu specifies the subcategory
        elif menu_path[1] == "Module Settings":
            config_name = menu_path[2]  # Similarly, handle module settings subcategories
        elif menu_path[1] == "User Settings":
            config_name = menu_path[1]  # Similarly, handle user settings subcategories
        else:
            print("Unsupported config path for saving changes.")
            return

        # Apply modified settings to the corresponding config object
        for key, value in settings.items():
            if isinstance(value, tuple):
                field, new_value = value
                # Update the relevant field in localConfig
                if hasattr(interface.localNode.localConfig, key):
                    setattr(interface.localNode.localConfig, key, new_value)
                    print(f"Updated {key} to {new_value}")  # Debugging log

        # Write the changes back to the radio for the specific config_name
        if config_name == "User Settings":
            # Extract values for settings_set_owner
            long_name = settings.get("long_name", "")
            short_name = settings.get("short_name", "")
            is_licensed = settings.get("is_licensed", False)

            # Call settings_set_owner with extracted values
            settings_set_owner(interface, long_name=long_name, short_name=short_name, is_licensed=is_licensed)
            print("User settings saved.")
        else:
            interface.localNode.writeConfig(config_name)
            print(f"Changes saved to {config_name}.")

    except Exception as e:
        print(f"Error saving changes: {e}")

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

                if field.type == field.TYPE_BOOL:  # Handle boolean type
                    new_value = get_bool_selection(stdscr, str(current_value))

                    # Update the modified settings and current menu
                    modified_settings[selected_option] = (field, new_value)
                    current_menu[selected_option] = (field, new_value)
                elif field.label == field.LABEL_REPEATED:
                    new_value = get_repeated_input(stdscr, current_value)
                elif field.enum_type:  # Enum field
                    enum_options = [v.name for v in field.enum_type.values]
                    new_value = select_enum_option(stdscr, enum_options, current_value)

                    modified_settings[selected_option] = (field, new_value)
                    current_menu[selected_option] = (field, new_value)
                else:
                    new_value = get_user_input(stdscr, f"Current value for {selected_option}: {current_value}")

                modified_settings[selected_option] = (field, new_value)
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
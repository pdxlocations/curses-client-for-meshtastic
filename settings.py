import curses
from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2
import meshtastic.serial_interface

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

    # Add Channels (example with 8 channels)
    channel = channel_pb2.ChannelSettings()
    menu_structure["Main Menu"]["Channels"] = {}
    if interface:
        for i in range(8):
            current_channel = interface.localNode.getChannelByChannelIndex(i)
            if current_channel:
                channel_config = extract_fields(channel, current_channel.settings)
                menu_structure["Main Menu"]["Channels"][f"Channel {i + 1}"] = channel_config

    # Add Exit option
    menu_structure["Main Menu"]["Exit"] = None

    return menu_structure

def display_menu(stdscr, current_menu, menu_path, selected_index, show_save_option):
    stdscr.clear()
    stdscr.border()

    # Get screen dimensions
    height, width = stdscr.getmaxyx()

    # Display the current menu path as a header
    header = " > ".join(menu_path)
    if len(header) > width - 4:
        header = header[:width - 7] + "..."
    stdscr.addstr(1, 2, header, curses.A_BOLD)

    # Display the menu options
    for idx, option in enumerate(current_menu):
        field_info = current_menu[option]
        current_value = field_info[1] if isinstance(field_info, tuple) else ""
        display_option = f"{option}"[:width // 2 - 2]  # Truncate option name if too long
        display_value = f"{current_value}"[:width // 2 - 4]  # Truncate value if too long

        try:
            if idx == selected_index:
                stdscr.addstr(idx + 3, 4, f"{display_option:<{width // 2 - 2}} {display_value}", curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 3, 4, f"{display_option:<{width // 2 - 2}} {display_value}")
        except curses.error:
            pass

    # Show save option if applicable
    if show_save_option:
        save_option = "Save Changes"
        save_position = height - 2
        if selected_index == len(current_menu):
            stdscr.addstr(save_position, (width - len(save_option)) // 2, save_option, curses.A_REVERSE)
        else:
            stdscr.addstr(save_position, (width - len(save_option)) // 2, save_option)

    stdscr.refresh()

def get_user_input(stdscr, prompt):
    curses.echo()
    stdscr.clear()
    stdscr.addstr(1, 2, prompt, curses.A_BOLD)
    stdscr.addstr(3, 2, "Enter value: ")
    curses.curs_set(1)
    user_input = stdscr.getstr(3, 15).decode("utf-8")
    curses.curs_set(0)
    curses.noecho()
    return user_input

def get_bool_selection(stdscr, current_value):
    options = ["True", "False"]
    selected_index = 0 if current_value == "True" else 1

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "Select True or False:", curses.A_BOLD)

        for idx, option in enumerate(options):
            if idx == selected_index:
                stdscr.addstr(idx + 3, 4, option, curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 3, 4, option)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) - 1, selected_index + 1)
        elif key == ord('\n'):
            return options[selected_index]
        elif key == 27:  # Escape key
            return current_value

def get_repeated_input(stdscr, current_value):
    stdscr.clear()
    curses.echo()
    stdscr.addstr(1, 2, "Enter comma-separated values:", curses.A_BOLD)
    stdscr.addstr(3, 2, f"Current: {current_value}")
    stdscr.addstr(5, 2, "New value: ")
    curses.curs_set(1)
    user_input = stdscr.getstr(5, 13).decode("utf-8")
    curses.curs_set(0)
    curses.noecho()
    return user_input.split(",")

def select_enum_option(stdscr, options, current_value):
    selected_index = options.index(current_value) if current_value in options else 0

    while True:
        stdscr.clear()
        stdscr.addstr(1, 2, "Select an option:", curses.A_BOLD)

        for idx, option in enumerate(options):
            if idx == selected_index:
                stdscr.addstr(idx + 3, 4, option, curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 3, 4, option)

        stdscr.refresh()
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) - 1, selected_index + 1)
        elif key == ord('\n'):
            return options[selected_index]
        elif key == 27:  # Escape key
            return current_value

def save_changes(interface, menu_path, settings):
    try:
        # Traverse and update the corresponding settings in the radio
        if menu_path[1] == "Radio Settings":
            config = interface.localNode.localConfig
        elif menu_path[1] == "Module Settings":
            config = interface.localNode.moduleConfig
        else:
            return

        for key, value in settings.items():
            if isinstance(value, tuple):
                field, new_value = value
                if hasattr(config, key):
                    setattr(config, key, new_value)

        # Write changes back to the radio
        interface.localNode.writeConfig()
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
        show_save_option = "Radio Settings" in menu_path or "Module Settings" in menu_path

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

            field_info = current_menu.get(selected_option)

            if isinstance(field_info, tuple):
                field, current_value = field_info

                if field.type == field.TYPE_BOOL:
                    new_value = get_bool_selection(stdscr, str(current_value))
                elif field.label == field.LABEL_REPEATED:
                    new_value = get_repeated_input(stdscr, current_value)
                elif field.enum_type:  # Enum field
                    enum_options = [v.name for v in field.enum_type.values]
                    new_value = select_enum_option(stdscr, enum_options, current_value)
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
    nested_menu(stdscr, menu_structure, interface)

if __name__ == "__main__":
    curses.wrapper(main)

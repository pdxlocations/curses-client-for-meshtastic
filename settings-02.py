import curses
from meshtastic.protobuf import config_pb2, module_config_pb2, mesh_pb2, channel_pb2

# Function to generate the menu structure from protobuf messages
def generate_menu_from_protobuf():
    def extract_fields(message_instance):
        if not hasattr(message_instance, "DESCRIPTOR"):
            return {}
        menu = {}
        fields = message_instance.DESCRIPTOR.fields
        for field in fields:
            if field.message_type:  # Nested message
                nested_instance = getattr(message_instance, field.name)
                menu[field.name] = extract_fields(nested_instance)
            else:
                menu[field.name] = None
        return menu

    menu_structure = {"Main Menu": {}}

    # Add Radio Settings
    radio = config_pb2.Config()
    menu_structure["Main Menu"]["Radio Settings"] = extract_fields(radio)

    # Add Module Settings
    module = module_config_pb2.ModuleConfig()
    menu_structure["Main Menu"]["Module Settings"] = extract_fields(module)

    # Add User Settings
    user = mesh_pb2.User()
    menu_structure["Main Menu"]["User Settings"] = extract_fields(user)

    # Add Channels (example with 8 channels)
    channel = channel_pb2.ChannelSettings()
    channel_config = extract_fields(channel)
    menu_structure["Main Menu"]["Channels"] = {f"Channel {i + 1}": channel_config for i in range(8)}

    # Add Exit option
    menu_structure["Main Menu"]["Exit"] = None

    return menu_structure

def display_menu(stdscr, current_menu, menu_path, selected_index):
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
        # Ensure the text fits within the screen width
        display_option = option[:width - 6]  # Leave space for borders
        try:
            if idx == selected_index:
                stdscr.addstr(idx + 3, 4, display_option, curses.A_REVERSE)
            else:
                stdscr.addstr(idx + 3, 4, display_option)
        except curses.error as e:
            # If there's an error, log the issue (optional)
            pass

    stdscr.refresh()

def nested_menu(stdscr, menu):
    current_menu = menu["Main Menu"]
    menu_path = ["Main Menu"]
    selected_index = 0

    while True:
        # Extract keys of the current menu
        options = list(current_menu.keys())

        # Display the menu
        display_menu(stdscr, options, menu_path, selected_index)

        # Capture user input
        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(options) - 1, selected_index + 1)
        elif key == curses.KEY_RIGHT or key == ord('\n'):
            selected_option = options[selected_index]

            if selected_option == "Exit":
                break

            # Navigate to the selected submenu
            if isinstance(current_menu.get(selected_option), dict):
                current_menu = current_menu[selected_option]
                menu_path.append(selected_option)
                selected_index = 0
            else:
                stdscr.addstr(1, 2, f"No submenu for {selected_option}")
                stdscr.refresh()
                stdscr.getch()
        elif key == curses.KEY_LEFT:
            # Navigate back to the previous menu
            if len(menu_path) > 1:
                menu_path.pop()
                current_menu = menu["Main Menu"]
                for step in menu_path[1:]:
                    try:
                        current_menu = current_menu[step]
                    except KeyError:
                        curses.endwin()
                        print(f"Invalid menu path: {step} not found")
                        return
                selected_index = 0
        elif key == 27:  # Escape key
            break

def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)

    # Generate menu structure from protobuf
    menu_structure = generate_menu_from_protobuf()
    nested_menu(stdscr, menu_structure)

if __name__ == "__main__":
    curses.wrapper(main)
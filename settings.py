import curses
from meshtastic import config_pb2, module_config_pb2
import meshtastic.serial_interface, meshtastic.tcp_interface
import ipaddress


def display_enum_menu(stdscr, enum_values, menu_item):
    menu_height = len(enum_values) + 2
    menu_width = max(len(option) for option in enum_values) + 4
    y_start = (curses.LINES - menu_height) // 2
    x_start = (curses.COLS - menu_width) // 2

    # Maximum number of rows to display
    max_rows = 10

    # Calculate popup window dimensions and position
    popup_height = min(len(enum_values), max_rows) + 2
    popup_width = max(len(option) for option in enum_values) + 6
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    # Create the popup window
    try:
        popup_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    # Enable keypad mode
    popup_win.keypad(True)

    # Display enum values in the popup window
    start_index = 0  # Starting index of displayed items
    while True:
        popup_win.clear()
        popup_win.border()

        # Calculate the starting index based on the menu item and window size
        if menu_item >= start_index + max_rows:
            start_index += 1
        elif menu_item < start_index:
            start_index -= 1

        # Display enum values within the window height
        for i in range(min(len(enum_values) - start_index, max_rows)):
            option_index = start_index + i
            if option_index == menu_item:
                popup_win.addstr(i + 1, 2, enum_values[option_index], curses.A_REVERSE)
            else:
                popup_win.addstr(i + 1, 2, enum_values[option_index])

        popup_win.refresh()

        char = popup_win.getch()
        if char == curses.KEY_DOWN:
            if menu_item < len(enum_values) - 1:
                menu_item += 1
        elif char == curses.KEY_UP:
            if menu_item > 0:
                menu_item -= 1
        elif char == ord('\n'):
            selected_option = enum_values[menu_item]
            popup_win.clear()
            popup_win.refresh()
            return selected_option, True
        elif char == 27 or char == curses.KEY_LEFT:  # Check if escape key is pressed
            curses.curs_set(0)
            popup_win.refresh()
            return None, False

def get_string_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    input_win.addstr(1, 1, str(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    # Get user input
    curses.curs_set(1)
    input_text = ""

    while True:
        # Display the current input text
        input_win.addstr(1, 1, input_text)
        input_win.border()
        input_win.refresh()

        # Get a character from the user
        key = stdscr.getch()

        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            curses.curs_set(0)
            input_win.clear()
            input_win.refresh()
            return input_text, True
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
            # Delete the last character from input_text
            input_text = input_text[:-1]
        elif 32 <= key <= 126:  # Printable ASCII characters
            # Append the character to input_text
            input_text += chr(key)
        elif key == 27:  # Check if escape key is pressed
            curses.curs_set(0)
            input_win.refresh()
            return None, False
            
        input_win.clear()
        input_win.refresh()


def get_uint_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    input_win.addstr(1, 1, str(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    curses.curs_set(1)
    input_text = ""

    while True:
        # Display the current input text
        input_win.addstr(1, 1, input_text)
        input_win.border()
        input_win.refresh()

        # Get a character from the user
        key = stdscr.getch()

        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            curses.curs_set(0)
            input_win.clear()
            input_win.refresh()
            return int(input_text), True
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
            # Delete the last character from input_text
            input_text = input_text[:-1]
        elif 48 <= key <= 57:  # Numbers(ASCII range)
            # Append the character to input_text
            input_text += chr(key)
        elif key == 27 or key == curses.KEY_LEFT:  # Check if escape key is pressed
            curses.curs_set(0)
            input_win.refresh()
            return None, False
            
        input_win.clear()
        input_win.refresh()


def get_uint32_list_input(stdscr, setting_string):
    setting_string = [str(num) for num in setting_string]

    popup_height = 8  # Increased height to accommodate three lines
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    input_text = setting_string[:]  # Copy the input strings
    curses.curs_set(0)

    while True:
        # Display the current input text for each line
        for i, line in enumerate(input_text):
            input_win.addstr(1 + i, 1, line)

        input_win.border()
        input_win.refresh()

        # Get a character from the user
        key = stdscr.getch()

        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            input_win.clear()
            input_win.refresh()
            return None, False  # TODO allow setting this
        #     return input_text, True
        # elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
        #     # Delete the last character from the current line's input_text
        #     current_y, current_x = input_win.getyx()
        #     input_text[current_y - 1] = input_text[current_y - 1][:-1]
        # elif (48 <= key <= 57) or key == 44:  # Numbers and comma (ASCII range)
        #     # Append the character to the current line's input_text
        #     current_y, current_x = input_win.getyx()
        #     input_text[current_y - 1] += chr(key)
        elif key == 27 or key == curses.KEY_LEFT:  # Check if escape key is pressed
            curses.curs_set(0)
            input_win.refresh()
            return None, False
            
        input_win.clear()
        input_win.refresh()

def get_float_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    input_win.addstr(1, 1, str(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    curses.curs_set(1)
    input_text = ""

    while True:
        # Display the current input text
        input_win.addstr(1, 1, input_text)
        input_win.border()
        input_win.refresh()

        # Get a character from the user
        key = stdscr.getch()

        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            curses.curs_set(0)
            input_win.clear()
            input_win.refresh()
            return float(input_text), True
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
            # Delete the last character from input_text
            input_text = input_text[:-1]
        elif (48 <= key <= 57) or key == 46:  # Numbers and decimal point (ASCII range)
            # Append the character to input_text
            input_text += chr(key)
        elif key == 27 or key == curses.KEY_LEFT:  # Check if escape key is pressed
            curses.curs_set(0)
            input_win.refresh()
            return None, False
            
        input_win.clear()
        input_win.refresh()


def ip_to_fixed32(ip):
    # Parse the IP address
    ip_obj = ipaddress.ip_address(ip)
    # Convert IP address to 32-bit integer
    return int(ip_obj)

def fixed32_to_ip(fixed32):
    # Convert 32-bit integer to IPv4Address object
    ip_obj = ipaddress.IPv4Address(fixed32)
    # Convert IPv4Address object to string representation
    return str(ip_obj)

def get_fixed32_input(stdscr, setting_string):
    popup_height = 5
    popup_width = 40
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    try:
        input_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    input_win.border()
    input_win.keypad(True)
    input_win.refresh()

    input_win.addstr(1, 1, fixed32_to_ip(setting_string))  # Prepopulate input field with the setting value
    input_win.refresh()
    curses.curs_set(1)
    input_text = ""

    while True:
        # Display the current input text
        input_win.addstr(1, 1, input_text)
        input_win.border()
        input_win.refresh()

        # Get a character from the user
        key = stdscr.getch()

        if key == curses.KEY_ENTER or key == 10 or key == 13:  # Enter key
            curses.curs_set(0)
            input_win.clear()
            input_win.refresh()
            return ip_to_fixed32(input_text), True
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace key
            # Delete the last character from input_text
            input_text = input_text[:-1]
        elif 48 <= key <= 57 or key == 46:  # Numbers + period (ASCII range)
            # Append the character to input_text
            input_text += chr(key)
        elif key == 27 or key == curses.KEY_LEFT:  # Check if escape key is pressed
            curses.curs_set(0)
            input_win.refresh()
            return None, False
            
        input_win.clear()
        input_win.refresh()   


def display_bool_menu(stdscr, setting_value):
    bool_options = ["False", "True"]
    return display_enum_menu(stdscr, bool_options, setting_value)


def generate_menu_from_protobuf(message_instance, interface):
    if not hasattr(message_instance, "DESCRIPTOR"):
        return  # This is not a protobuf message instance, exit
    menu = {}

    field_names = message_instance.DESCRIPTOR.fields_by_name.keys()
    for field_name in field_names:
        field_descriptor = message_instance.DESCRIPTOR.fields_by_name[field_name]
        if field_descriptor is not None:
            nested_message_instance = getattr(message_instance, field_name)
            menu[field_name] = generate_menu_from_protobuf(nested_message_instance, interface)
    return menu


def change_setting(stdscr, interface, menu_path):
    node = interface.localNode
    field_descriptor = None
    setting_value = 0
    
    stdscr.clear()
    stdscr.border()
    stdscr.refresh()
    menu_header(stdscr, f"{menu_path[-1]}")

    

    # Determine the level of nesting based on the length of menu_path

    if menu_path[1] == "User Settings":
        n = interface.getMyNodeInfo()
        
        try:
            setting_string = n['user'][snake_to_camel(menu_path[2])]
        except:
            setting_string = 0

        if menu_path[2] == "is_licensed":
            setting_value, do_change_setting = display_bool_menu(stdscr, setting_string)
        else:
            setting_value, do_change_setting = get_string_input(stdscr, setting_string)

        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        
        if menu_path[2] == "long_name":
            settings_set_owner(interface, long_name=setting_value)
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        elif menu_path[2] == "short_name":
            if len(setting_value) > 4:
                setting_value = setting_value[:4]
            settings_set_owner(interface, short_name=setting_value)
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        elif menu_path[2] == "is_licensed":
            ln = n['user']['longName']
            settings_set_owner(interface, long_name=ln, is_licensed=setting_value)
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        else:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        
    if len(menu_path) == 4:
        if menu_path[1] == "Radio Settings":
            setting_string = getattr(getattr(node.localConfig, str(menu_path[2])), menu_path[3])
            field_descriptor = getattr(node.localConfig, menu_path[2]).DESCRIPTOR.fields_by_name[menu_path[3]]

        elif menu_path[1] == "Module Settings":
            setting_string = getattr(getattr(node.moduleConfig, str(menu_path[2])), menu_path[3])
            field_descriptor = getattr(node.moduleConfig, menu_path[2]).DESCRIPTOR.fields_by_name[menu_path[3]]

    elif len(menu_path) == 5:
        if menu_path[1] == "Radio Settings":
            setting_string = getattr(getattr(getattr(node.localConfig, str(menu_path[2])), menu_path[3]), menu_path[4])
            field_descriptor = getattr(getattr(node.localConfig, menu_path[2]), menu_path[3]).DESCRIPTOR.fields_by_name[menu_path[4]]

        elif menu_path[1] == "Module Settings":
            setting_string = getattr(getattr(getattr(node.moduleConfig, str(menu_path[2])), menu_path[3]), menu_path[4])
            field_descriptor = getattr(getattr(node.moduleConfig, menu_path[2]), menu_path[3]).DESCRIPTOR.fields_by_name[menu_path[3]]


    if field_descriptor.enum_type is not None:
        enum_values = [enum_value.name for enum_value in field_descriptor.enum_type.values]
        enum_option, do_change_setting = display_enum_menu(stdscr, enum_values, setting_string)
        setting_value = enum_option
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return

    elif field_descriptor.type == 8:  # Field type 8 corresponds to BOOL
        setting_value, do_change_setting = display_bool_menu(stdscr, setting_string)
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return

    elif field_descriptor.type == 9:  # Field type 9 corresponds to STRING
        setting_value, do_change_setting = get_string_input(stdscr, setting_string)
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return

    elif field_descriptor.type == 2:  # Field type 2 corresponds to FLOAT
        setting_value, do_change_setting = get_float_input(stdscr, setting_string)
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return

    elif field_descriptor.type == 13:  # Field type 13 corresponds to UINT32
        if field_descriptor.label == field_descriptor.LABEL_REPEATED:
            setting_value, do_change_setting = get_uint32_list_input(stdscr, setting_string)
        else:
            setting_value, do_change_setting = get_uint_input(stdscr, setting_string)
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
        
    elif field_descriptor.type == 7:  # Field type 7 corresponds to FIXED32
        setting_value, do_change_setting = get_fixed32_input(stdscr, setting_string)
        if not do_change_setting:
            stdscr.clear()
            stdscr.border()
            menu_path.pop()
            return
    else:
        menu_path.pop()
        return
        
    # formatted_text = f"{menu_path[2]}.{menu_path[3]} = {setting_value}"
    # menu_header(stdscr,formatted_text,2)

    ourNode = interface.localNode
    
    # Convert "true" to 1, "false" to 0, leave other values as they are
    if setting_value == "True" or setting_value == "1":
        setting_value_int = 1
    elif setting_value == "False" or setting_value == "0":
        setting_value_int = 0
    else:
        # If setting_value is not "true" or "false", keep it as it is
        setting_value_int = setting_value

    # if isinstance(setting_value_int, list):
    #     value_string = ', '.join(str(item) for item in setting_value_int)
    #     setting_value_int = value_string

    try:
        if len(menu_path) == 4:
            if menu_path[1] == "Radio Settings":
                setattr(getattr(ourNode.localConfig, menu_path[2]), menu_path[3], setting_value_int)
            elif menu_path[1] == "Module Settings":
                setattr(getattr(ourNode.moduleConfig, menu_path[2]), menu_path[3], setting_value_int)

        elif len(menu_path) == 5:
            if menu_path[1] == "Radio Settings":
                setattr(getattr(getattr(ourNode.localConfig, menu_path[2]), menu_path[3]), menu_path[4], setting_value_int)
            elif menu_path[1] == "Module Settings":
                setattr(getattr(getattr(ourNode.moduleConfig, menu_path[2]), menu_path[3]), menu_path[4], setting_value_int)

    except AttributeError as e:
        print("Error setting attribute:", e)


    ourNode.writeConfig(menu_path[2])
    menu_path.pop()

def snake_to_camel(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


def display_values(stdscr, interface, key_list, menu_path):
    node = interface.localNode
    user_settings = ["long_name", "short_name", "is_licensed"]
    for i, key in enumerate(key_list):

        if len(menu_path) == 2:
            if menu_path[1] == 'User Settings':
                n = interface.getMyNodeInfo()
                try:
                    setting = n['user'][snake_to_camel(key_list[i])]
                except:
                    setting = None
                if key_list[i] in user_settings:
                    stdscr.addstr(i+3, 40, str(setting))

        if len(menu_path) == 3:
            if menu_path[1] == "Radio Settings":
                setting = getattr(getattr(node.localConfig, menu_path[2]), key_list[i])  
            if menu_path[1] == "Module Settings":
                setting = getattr(getattr(node.moduleConfig, menu_path[2]), key_list[i])
            stdscr.addstr(i+3, 40, str(setting)[:14])

        if len(menu_path) == 4:
            if menu_path[1] == "Radio Settings":
                setting = getattr(getattr(getattr(node.localConfig, menu_path[2]), menu_path[3]), key_list[i])  
            if menu_path[1] == "Module Settings":
                setting = getattr(getattr(getattr(node.moduleConfig, menu_path[2]), menu_path[3]), key_list[i])
            stdscr.addstr(i+3, 40, str(setting)[:14])
        
    stdscr.refresh()

def menu_header(window, text, start_y=1):
    window.clear()
    window.box()
    window.refresh()
    _, window_width = window.getmaxyx()
    start_x = (window_width - len(text)) // 2
    formatted_text = text.replace('_', ' ').title()
    window.addstr(start_y, start_x, formatted_text)
    window.refresh()

def nested_menu(stdscr, menu, interface):
    menu_item = 0
    current_menu = menu
    prev_menu = []
    menu_index = 0
    next_key = None

    key_list = []
    menu_path = ["Main Menu"]

    last_menu_level = False

    while True:
        
        if current_menu is not None:
            menu_header(stdscr, f"{menu_path[menu_index]}")

            # Display current menu
            for i, key in enumerate(current_menu.keys(), start=0):
                if i == menu_item:
                    if key in ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]:
                        stdscr.addstr(i+3, 1, key, curses.color_pair(5))
                    else:
                        stdscr.addstr(i+3, 1, key, curses.A_REVERSE)
                else:
                    stdscr.addstr(i+3, 1, key)

            # Display current values
            display_values(stdscr, interface, key_list, menu_path)

            char = stdscr.getch()

            selected_key = list(current_menu.keys())[menu_item]
            selected_value = current_menu[selected_key]

            if char == curses.KEY_DOWN:
                if last_menu_level == True:
                    last_menu_level = False
                menu_item = min(len(current_menu) - 1, menu_item + 1)

            elif char == curses.KEY_UP:
                if last_menu_level == True:
                    last_menu_level = False
                menu_item = max(0, menu_item - 1)

            elif char == curses.KEY_RIGHT:
                # if selected_key == "Region":
                #     settings_region(interface)
                #     break
                if selected_key not in ["Reboot", "Reset NodeDB", "Shutdown", "Factory Reset"]:
                    menu_path.append(selected_key)

                    if isinstance(selected_value, dict):
                        # If the selected item is a submenu, navigate to it
                        prev_menu.append(current_menu)
                        menu_index += 1
                        current_menu = selected_value
                        menu_item = 0
                        last_menu_level = False
                    else:
                        last_menu_level = True
                        
                
            elif char == curses.KEY_LEFT:
                if last_menu_level == True:
                    last_menu_level = False
                if len(menu_path) > 1:
                    menu_path.pop()
                    current_menu = prev_menu[menu_index-1]
                    del prev_menu[menu_index-1]
                    menu_index -= 1
                    menu_item = 0

            elif char == ord('\n'):
                # if selected_key == "Region":
                #     settings_region(interface)
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
                    stdscr.getch()
                 
            elif char == 27:  # escape to exit menu 
                break

            if char:
                stdscr.clear()
                stdscr.border()

            next_key = list(current_menu.keys())[menu_item]
            key_list = list(current_menu.keys())

        else:
            break  # Exit loop if current_menu is None

        if last_menu_level == True:
            if not isinstance(current_menu.get(next_key), dict):
                change_setting(stdscr, interface, menu_path)


def settings(stdscr, interface):
    popup_height = 20
    popup_width = 60
    popup_win = None
    y_start = (curses.LINES - popup_height) // 2
    x_start = (curses.COLS - popup_width) // 2

    curses.curs_set(0)
    try:
        popup_win = curses.newwin(popup_height, popup_width, y_start, x_start)
    except curses.error as e:
        print("Error occurred while initializing curses window:", e)

    popup_win.border()
    popup_win.keypad(True)
    
    # Generate menu from protobuf for both radio and module settings
    from meshtastic import mesh_pb2

    user = mesh_pb2.User()
    user_settings = ["long_name", "short_name", "is_licensed"]
    user_config = generate_menu_from_protobuf(user, interface)
    user_config = {key: value for key, value in user_config.items() if key in user_settings}


    radio = config_pb2.Config()
    radio_config = generate_menu_from_protobuf(radio, interface)

    module = module_config_pb2.ModuleConfig()
    module_config = generate_menu_from_protobuf(module, interface)

    # Add top-level menu items
    top_level_menu = {
        # "Region": None,
        "User Settings": user_config,
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

# def settings_region(interface):
#     selected_option, do_set = set_region(interface)
#     if do_set:
#         ourNode = interface.localNode
#         setattr(ourNode.localConfig.lora, "region", selected_option)
#         ourNode.writeConfig("lora")

def settings_reboot(interface):
    interface.localNode.reboot()

def settings_reset_nodedb(interface):
    interface.localNode.resetNodeDb()

def settings_shutdown(interface):
    interface.localNode.shutdown()

def settings_factory_reset(interface):
    interface.localNode.factoryReset()

def settings_set_owner(interface, long_name=None, short_name=None, is_licensed=False):
    if is_licensed == 'True':
        is_licensed = True
    elif is_licensed == 'False':
        is_licensed = False
    interface.localNode.setOwner(long_name, short_name, is_licensed)


if __name__ == "__main__":

    interface = meshtastic.serial_interface.SerialInterface()

    # radio = config_pb2.Config()
    # module = module_config_pb2.ModuleConfig()
    # print(generate_menu_from_protobuf(radio, interface))
    # print(generate_menu_from_protobuf(module, interface))

    def main(stdscr):
        stdscr.keypad(True)
        while True:
            settings(stdscr, interface)
        
    curses.wrapper(main)
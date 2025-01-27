import curses
import json
import os
from ui.colors import get_color, setup_colors
from default_config import format_json_single_line_arrays

width = 60

def select_color_from_list(window, prompt, current_color, colors):
    """
    Displays a list of colors for the user to choose from.
    """
    curses.curs_set(0)
    selected_index = colors.index(current_color) if current_color in colors else 0

    while True:
        window.clear()
        window.addstr(0, 2, prompt, get_color("settings_default"))
        window.addstr(2, 2, "Use UP/DOWN to navigate, ENTER to confirm, ESC to cancel.", get_color("settings_default"))

        # Display all available colors
        for i, color in enumerate(colors):
            if i == selected_index:
                window.addstr(i + 4, 4, color, get_color("settings_default", reverse=True))
            else:
                window.addstr(i + 4, 4, color, get_color("settings_default"))

        window.refresh()
        key = window.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(colors) - 1, selected_index + 1)
        elif key == ord("\n"):  # Confirm selection
            return colors[selected_index]
        elif key == 27:  # ESC key to cancel
            return current_color

def edit_value(parent_window, key, current_value):
    width = 60
    height = 8
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a centered window
    edit_win = curses.newwin(height, width, start_y, start_x)
    edit_win.bkgd(get_color("background"))
    edit_win.attrset(get_color("window_frame"))
    edit_win.border()

    # Display instructions and current value
    edit_win.addstr(1, 2, f"Editing {key}:", get_color("settings_default", bold=True))
    edit_win.addstr(2, 2, "Press Enter to save or ESC to cancel.", get_color("settings_default"))
    edit_win.addstr(4, 2, f"Current Value: {current_value}", get_color("settings_default"))
    edit_win.addstr(6, 2, "New Value: ", get_color("settings_default"))
    edit_win.refresh()

    curses.curs_set(1)  # Show the cursor for input
    curses.echo()

    new_value = None  # Default to None if ESC is pressed
    input_buffer = []  # To build the input dynamically

    while True:
        char = edit_win.getch()

        if char == 27:  # ESC key
            break
        elif char == curses.KEY_BACKSPACE or char == 127:  # Handle backspace
            if input_buffer:
                input_buffer.pop()
                edit_win.addstr(6, 13, " " * (width - 15))  # Clear the line
                edit_win.addstr(6, 13, "".join(input_buffer))  # Reprint the buffer
                edit_win.refresh()
        elif char == ord("\n"):  # Enter key
            new_value = "".join(input_buffer)  # Save the input
            break
        else:
            if len(input_buffer) < (width - 15):  # Prevent overflow
                input_buffer.append(chr(char))
                edit_win.addstr(6, 13 + len(input_buffer) - 1, chr(char))
                edit_win.refresh()

    curses.noecho()
    curses.curs_set(0)

    # Return the new value, or None if ESC was pressed
    return current_value if new_value is None else new_value

def edit_color_pair(window, key, current_value):
    """
    Allows the user to select a foreground and background color for a key.
    """
    colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]

    # Foreground color selection
    fg_color = select_color_from_list(window, f"Select Foreground Color for {key}", current_value[0], colors)

    # Background color selection
    bg_color = select_color_from_list(window, f"Select Background Color for {key}", current_value[1], colors)

    return [fg_color, bg_color]


def render_menu(current_data, menu_path, selected_index):
    # Determine the menu items based on the type of current_data
    if isinstance(current_data, dict):
        keys = list(current_data.keys())
    elif isinstance(current_data, list):
        keys = [f"[{i}]" for i in range(len(current_data))]
    else:
        keys = []  # Fallback in case of unexpected data types

    # Calculate the dynamic height based on menu items + 1 for "Save" button
    num_items = len(keys) + 1  # Add 1 for the "Save" button
    height = min(curses.LINES - 2, num_items + 5)
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create window
    menu_win = curses.newwin(height, width, start_y, start_x)
    menu_win.clear()
    menu_win.bkgd(get_color("background"))
    menu_win.attrset(get_color("window_frame"))
    menu_win.border()
    menu_win.keypad(True)

    # Display the menu path
    header = " > ".join(menu_path)
    if len(header) > width - 4:
        header = header[:width - 7] + "..."
    menu_win.addstr(1, 2, header, get_color("settings_breadcrumbs", bold=True))

    # Display menu options
    menu_pad = curses.newpad(num_items + 1, width - 8)
    for idx, key in enumerate(keys):
        value = current_data[key] if isinstance(current_data, dict) else current_data[idx]

        # Truncate long keys and values
        max_key_len = width // 2 - 4  # Allow space for padding
        max_value_len = width // 2 - 6
        display_key = f"{key}"[:max_key_len]
        display_value = f"{value}"[:max_value_len] if not isinstance(value, (dict, list)) else "[...]"

        color = get_color("settings_default", reverse=(idx == selected_index))
        try:
            menu_pad.addstr(
                idx,
                0,
                f"{display_key:<{max_key_len}} {display_value}".ljust(width - 8),
                color,
            )
        except curses.error:
            pass  # Safeguard against edge cases

    # Add "Save" button
    save_color = get_color("settings_save", reverse=(selected_index == len(keys)))
    menu_pad.addstr(len(keys), 0, "Save".center(width - 8), save_color)

    # Refresh window and pad
    menu_win.refresh()
    menu_pad.refresh(0, 0, start_y + 3, start_x + 4, start_y + height - 3, start_x + width - 4)

    return menu_win, menu_pad, keys



def json_editor(stdscr):
    menu_path = ["App Settings"]
    selected_index = 0  # Track selected option

    file_path = "config.json"

    # Ensure the file exists
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)

    # Load JSON data
    with open(file_path, "r") as f:
        original_data = json.load(f)

    data = original_data  # Reference to the original data
    current_data = data  # Track the current level of the menu

    while True:
        # Render menu
        menu_win, menu_pad, keys = render_menu(current_data, menu_path, selected_index)

        # Handle user input
        key = menu_win.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(keys), selected_index + 1)  # Include "Save" button
        elif key in (curses.KEY_RIGHT, ord("\n")):
            if selected_index < len(keys):  # Handle key selection
                selected_key = keys[selected_index]

                # Handle nested data
                if isinstance(current_data, dict):
                    selected_data = current_data[selected_key]
                elif isinstance(current_data, list):
                    selected_data = current_data[int(selected_key.strip("[]"))]

                # Check if the selected data is a color pair
                if (
                    isinstance(selected_data, list)
                    and len(selected_data) == 2
                    and all(color in [" ", "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"] for color in selected_data)
                ):
                    # Edit the color pair
                    new_value = edit_color_pair(stdscr, selected_key, selected_data)
                    if isinstance(current_data, dict):
                        current_data[selected_key] = new_value
                    elif isinstance(current_data, list):
                        current_data[int(selected_key.strip("[]"))] = new_value
                elif isinstance(selected_data, (dict, list)):
                    # Navigate into nested data
                    menu_path.append(str(selected_key))
                    current_data = selected_data
                    selected_index = 0
                else:
                    # General value editing
                    new_value = edit_value(stdscr, selected_key, selected_data)
                    if isinstance(current_data, dict):
                        current_data[selected_key] = new_value
                    elif isinstance(current_data, list):
                        current_data[int(selected_key.strip("[]"))] = new_value
            else:
                # Save button selected
                save_json(file_path, data)
                stdscr.addstr(curses.LINES - 2, 2, "Settings saved! Press any key to continue...", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                break  # Exit App Settings and return to the main menu
        elif key in (27, curses.KEY_LEFT):  # ESC or Left Arrow
            if len(menu_path) > 1:
                # Go back one level
                menu_path.pop()
                current_data = data
                for path in menu_path[1:]:
                    if isinstance(current_data, dict):
                        current_data = current_data[path]
                    elif isinstance(current_data, list):
                        current_data = current_data[int(path.strip("[]"))]
                selected_index = 0
            else:
                # Exit App Settings and return to the main menu
                menu_win.clear()
                menu_win.refresh()
                break

    # No auto-save; save only when the "Save" button is selected
    menu_win.clear()
    menu_win.refresh()

def save_json(file_path, data):
    formatted_json = format_json_single_line_arrays(data)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)
    setup_colors()
    json_editor(stdscr)


if __name__ == "__main__":
    curses.wrapper(main)
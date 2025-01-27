import curses
import json
import os
from ui.colors import get_color, setup_colors
from default_config import format_json_single_line_arrays


def select_color(window, current_color):
    curses.curs_set(0)
    colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    selected_index = colors.index(current_color) if current_color in colors else 0

    while True:
        window.clear()
        window.addstr(0, 2, "Select a color (Enter to confirm, ESC to cancel):", get_color("settings_default"))

        for i, color in enumerate(colors):
            if i == selected_index:
                window.addstr(i + 2, 4, color, get_color("settings_default", reverse=True))
            else:
                window.addstr(i + 2, 4, color, get_color("settings_default"))

        window.refresh()
        key = window.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(colors) - 1, selected_index + 1)
        elif key == ord("\n"):
            return colors[selected_index]
        elif key == 27 or key == curses.KEY_LEFT:  # ESC or Left Arrow
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
    curses.curs_set(0)
    window.clear()
    window.addstr(1, 2, f"Editing {key} (foreground/background):", get_color("settings_default"))
    window.refresh()

    fg_color = select_color(window, current_value[0])
    bg_color = select_color(window, current_value[1])

    return [fg_color, bg_color]


width = 60

def render_menu(current_data, menu_path, selected_index):
        # Calculate the dynamic height based on menu items
        num_items = len(current_data)
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
        for idx, key in enumerate(current_data):
            value = current_data[key] if isinstance(current_data, dict) else key

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

        # Refresh window and pad
        menu_win.refresh()
        menu_pad.refresh(0, 0, start_y + 3, start_x + 4, start_y + height - 3, start_x + width - 4)

        return menu_win, menu_pad

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
        data = json.load(f)

    while True:
        # Render menu
        keys = list(data.keys()) if isinstance(data, dict) else range(len(data))
        menu_win, menu_pad = render_menu(data, menu_path, selected_index)

        # Handle user input
        key = menu_win.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(keys) - 1, selected_index + 1)
        elif key in (curses.KEY_RIGHT, ord("\n")):
            selected_key = keys[selected_index]
            if isinstance(data[selected_key], (dict, list)):
                menu_path.append(str(selected_key))
                data = data[selected_key]
                selected_index = 0
            else:
                # Edit the value
                new_value = edit_value(stdscr, selected_key, data[selected_key])
                data[selected_key] = new_value
        elif key in (27, curses.KEY_LEFT):  # ESC or Left Arrow
            if len(menu_path) > 1:
                # Go back one level
                menu_path.pop()
                with open(file_path, "r") as f:
                    data = json.load(f)
                for path in menu_path[1:]:
                    data = data[path]
                selected_index = 0
            else:
                # Exit App Settings and return to the main menu
                menu_win.clear()
                menu_win.refresh()
                break
        elif key == ord("s"):
            save_json(file_path, data)
            stdscr.addstr(curses.LINES - 2, 2, "Changes saved! Press any key to continue...", curses.A_BOLD)
            stdscr.refresh()
            stdscr.getch()


    # Save changes on exit
    save_json(file_path, data)

def save_json(file_path, data):
    formatted_json = format_json_single_line_arrays(data)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)


def main(stdscr):
    curses.curs_set(0)
    stdscr.keypad(True)

    # Initialize colors
    # setup_colors()

    # Launch JSON editor
    json_editor(stdscr)


if __name__ == "__main__":
    curses.wrapper(main)
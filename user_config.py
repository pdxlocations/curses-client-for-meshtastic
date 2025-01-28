import curses
import json
import os
from ui.colors import get_color, setup_colors
from default_config import format_json_single_line_arrays

width = 60
save_option_text = "Save Changes"

def edit_color_pair(key, current_value):

    """
    Allows the user to select a foreground and background color for a key.
    """
    colors = ["black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"]
    fg_color = select_color_from_list(f"Select Foreground Color for {key}", current_value[0], colors)
    bg_color = select_color_from_list(f"Select Background Color for {key}", current_value[1], colors)

    return [fg_color, bg_color]


def select_color_from_list(prompt, current_color, colors):
    """
    Displays a scrollable list of colors for the user to choose from using a pad.
    """
    selected_index = colors.index(current_color) if current_color in colors else 0

    height = min(len(colors) + 5, curses.LINES - 2)
    width = 60
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    color_win = curses.newwin(height, width, start_y, start_x)
    color_win.bkgd(get_color("background"))
    color_win.attrset(get_color("window_frame"))
    color_win.keypad(True)

    color_pad = curses.newpad(len(colors) + 1, width - 8)

    # Render header
    color_win.clear()
    color_win.border()
    color_win.addstr(1, 2, prompt, get_color("settings_default", bold=True))
    # color_win.addstr(2, 2, "Use UP/DOWN to navigate, ENTER to confirm, ESC to cancel.", get_color("settings_default"))

    # Render color options on the pad
    for idx, color in enumerate(colors):
        if idx == selected_index:
            color_pad.addstr(idx, 0, color.ljust(width - 8), get_color("settings_default", reverse=True))
        else:
            color_pad.addstr(idx, 0, color.ljust(width - 8), get_color("settings_default"))

    # Initial refresh
    color_win.refresh()
    color_pad.refresh(0, 0,
                    color_win.getbegyx()[0] + 3, color_win.getbegyx()[1] + 4,
                    color_win.getbegyx()[0] + color_win.getmaxyx()[0] - 2, color_win.getbegyx()[1] + color_win.getmaxyx()[1] - 4)

    while True:
        key = color_win.getch()

        if key == curses.KEY_UP:

            if selected_index > 0:
                selected_index -= 1

        elif key == curses.KEY_DOWN:
            if selected_index < len(colors) - 1:
                selected_index += 1

        elif key == curses.KEY_RIGHT or key == ord('\n'):
            return colors[selected_index]
        
        elif key == curses.KEY_LEFT or key == 27:  # ESC key
            return current_color

        # Refresh the pad with updated selection and scroll offset
        for idx, color in enumerate(colors):
            if idx == selected_index:
                color_pad.addstr(idx, 0, color.ljust(width - 8), get_color("settings_default", reverse=True))
            else:
                color_pad.addstr(idx, 0, color.ljust(width - 8), get_color("settings_default"))


        color_win.refresh()
        color_pad.refresh(0, 0,
                        color_win.getbegyx()[0] + 3, color_win.getbegyx()[1] + 4,
                        color_win.getbegyx()[0] + color_win.getmaxyx()[0] - 2, color_win.getbegyx()[1] + color_win.getmaxyx()[1] - 4)



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


    curses.curs_set(1)

    user_input = ""
    while True:
        key = edit_win.getch(6, 13 + len(user_input))  # Adjust cursor position dynamically
        if key == 27 or key == curses.KEY_LEFT:  # ESC or Left Arrow
            curses.curs_set(0)
            return None  # Exit without returning a value
        elif key == ord('\n'):  # Enter key
            break
        elif key == curses.KEY_BACKSPACE or key == 127:  # Backspace
            user_input = user_input[:-1]
            edit_win.addstr(6, 13, " " * (len(user_input) + 1), get_color("settings_default"))  # Clear the line
            edit_win.addstr(6, 13, user_input, get_color("settings_default"))
        else:
            user_input += chr(key)
            edit_win.addstr(6, 13, user_input, get_color("settings_default"))

    curses.curs_set(0)

    # Return the new value, or None if ESC was pressed
    return current_value if user_input is None else user_input


def render_menu(current_data, menu_path, selected_index):
    """
    Render the configuration menu with a Save button directly added to the window.
    """
    # Determine menu items based on the type of current_data
    if isinstance(current_data, dict):
        options = list(current_data.keys())
    elif isinstance(current_data, list):
        options = [f"[{i}]" for i in range(len(current_data))]
    else:
        options = []  # Fallback in case of unexpected data types


    # Calculate dynamic dimensions for the menu
    num_items = len(options)
    height = min(curses.LINES - 2, num_items + 6)  # Include space for borders and Save button
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create the window
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

    # Create the pad for scrolling
    menu_pad = curses.newpad(num_items + 1, width - 8)

    # Populate the pad with menu options
    for idx, key in enumerate(options):
        value = current_data[key] if isinstance(current_data, dict) else current_data[int(key.strip("[]"))]
        display_key = f"{key}"[:width // 2 - 2]
        display_value = (
            f"{value}"[:width // 2 - 8]
        )

        color = get_color("settings_default", reverse=(idx == selected_index))
        menu_pad.addstr(idx, 0, f"{display_key:<{width // 2 - 2}} {display_value}".ljust(width - 8), color)

    # Add Save button to the main window
    save_button_position = height - 2
    menu_win.addstr(
        save_button_position,
        (width - len(save_option_text)) // 2,
        save_option_text,
        get_color("settings_save", reverse=(selected_index == len(options))),
    )

    return menu_win, menu_pad, options

def move_highlight(old_idx, new_idx, menu_win, enum_pad):
    if old_idx == new_idx:
        return # no-op

    enum_pad.chgat(old_idx, 0, enum_pad.getmaxyx()[1], get_color("settings_default"))
    enum_pad.chgat(new_idx, 0, enum_pad.getmaxyx()[1], get_color("settings_default", reverse = True))

    menu_win.refresh()

    start_index = max(0, new_idx - (menu_win.getmaxyx()[0] - 6))

    menu_win.refresh()
    enum_pad.refresh(start_index, 0,
                     menu_win.getbegyx()[0] + 3,
                     menu_win.getbegyx()[1] + 4,
                     menu_win.getbegyx()[0] + menu_win.getmaxyx()[0] - 3,
                     menu_win.getbegyx()[1] + 4 + menu_win.getmaxyx()[1] - 4)


def json_editor(stdscr):
    menu_path = ["App Settings"]
    selected_index = 0  # Track the selected option

    file_path = "config.json"
    show_save_option = True  # Always show the Save button

    # Ensure the file exists
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)

    # Load JSON data
    with open(file_path, "r") as f:
        original_data = json.load(f)

    data = original_data  # Reference to the original data
    current_data = data  # Track the current level of the menu

    # Render the menu
    menu_win, menu_pad, options = render_menu(current_data, menu_path, selected_index)

    # Refresh menu and pad
    menu_win.refresh()
    menu_pad.refresh(
        0,
        0,
        menu_win.getbegyx()[0] + 3,
        menu_win.getbegyx()[1] + 4,
        
        menu_win.getbegyx()[0] + menu_win.getmaxyx()[0] - 3,
        menu_win.getbegyx()[1] + menu_win.getmaxyx()[1] - 4,
    )

    need_redraw = True
    while True:
        key = menu_win.getch()
        max_index = len(options) + (1 if show_save_option else 0) - 1
        if(need_redraw):
            menu_win, menu_pad, options = render_menu(current_data, menu_path, selected_index)
            need_redraw = False








        if key == curses.KEY_UP:

            old_selected_index = selected_index
            # selected_index = max(0, selected_index - 1)
            selected_index = max_index if selected_index == 0 else selected_index - 1
            move_highlight(old_selected_index, selected_index, menu_win, menu_pad)

        elif key == curses.KEY_DOWN:


            old_selected_index = selected_index
            # selected_index = min(len(options) - 1, selected_index + 1)
            selected_index = 0 if selected_index == max_index else selected_index + 1
            move_highlight(old_selected_index, selected_index, menu_win, menu_pad)










        elif key in (curses.KEY_RIGHT, ord("\n")):

            need_redraw = True
            menu_win.erase()
            menu_win.refresh()

            if selected_index < len(options):  # Handle selection of a menu item
                selected_key = options[selected_index]

                # Handle nested data
                if isinstance(current_data, dict):
                    if selected_key in current_data:
                        selected_data = current_data[selected_key]
                    else:
                        continue  # Skip invalid key
                elif isinstance(current_data, list):
                    selected_data = current_data[int(selected_key.strip("[]"))]

                if isinstance(selected_data, list) and len(selected_data) == 2:
                    # Edit color pair
                    new_value = edit_color_pair(
                        selected_key, selected_data)
                    current_data[selected_key] = new_value

                elif isinstance(selected_data, (dict, list)):
                    # Navigate into nested data
                    menu_path.append(str(selected_key))
                    current_data = selected_data
                    selected_index = 0  # Reset the selected index

                else:
                    # General value editing
                    new_value = edit_value(stdscr, selected_key, selected_data)
                    current_data[selected_key] = new_value
            else:
                # Save button selected
                save_json(file_path, data)
                stdscr.refresh()
                # stdscr.getch()
                continue

        elif key in (27, curses.KEY_LEFT):  # Escape or Left Arrow

            need_redraw = True
            menu_win.erase()
            menu_win.refresh()

            # Navigate back in the menu
            if len(menu_path) > 1:
                menu_path.pop()
                current_data = data
                for path in menu_path[1:]:
                    current_data = current_data[path] if isinstance(current_data, dict) else current_data[int(path.strip("[]"))]
                selected_index = 0
            else:
                # Exit the editor
                menu_win.clear()
                menu_win.refresh()
                break

    # Final cleanup
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
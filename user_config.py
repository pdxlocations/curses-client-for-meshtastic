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
    height = 10
    input_width = width - 16  # Allow space for "New Value: "
    start_y = (curses.LINES - height) // 2
    start_x = (curses.COLS - width) // 2

    # Create a centered window
    edit_win = curses.newwin(height, width, start_y, start_x)
    edit_win.bkgd(get_color("background"))
    edit_win.attrset(get_color("window_frame"))
    edit_win.border()

    # Display instructions
    edit_win.addstr(1, 2, f"Editing {key}", get_color("settings_default", bold=True))
    # edit_win.addstr(2, 2, "Press Enter when done or ESC to cancel.", get_color("settings_default"))

    # Properly wrap `current_value` by characters
    wrap_width = width - 4  # Account for border and padding
    wrapped_lines = [current_value[i:i+wrap_width] for i in range(0, len(current_value), wrap_width)]

    edit_win.addstr(3, 2, "Current Value: ", get_color("settings_default"))

    for i, line in enumerate(wrapped_lines[:4]):  # Limit display to fit the window height
        edit_win.addstr(4 + i, 2, line, get_color("settings_default"))

    edit_win.addstr(7, 2, "New Value: ", get_color("settings_default"))
    edit_win.refresh()

    curses.curs_set(1)

    # User input handling with scrolling
    user_input = ""
    scroll_offset = 0  # Determines which part of the text is visible

    while True:
        visible_text = user_input[scroll_offset:scroll_offset + input_width]  # Only show what fits
        edit_win.addstr(7, 13, " " * input_width, get_color("settings_default"))  # Clear previous text
        edit_win.addstr(7, 13, visible_text, get_color("settings_default"))  # Display text
        edit_win.refresh()

        edit_win.move(7, 13 + min(len(user_input) - scroll_offset, input_width))  # Adjust cursor position

        # key = edit_win.getch()
        key = edit_win.get_wch()

        if key in (chr(27), curses.KEY_LEFT):  # ESC or Left Arrow
            curses.curs_set(0)
            return current_value  # Exit without returning a value
        elif key in (chr(curses.KEY_ENTER), chr(10), chr(13)):
            break
        elif key in (curses.KEY_BACKSPACE, chr(127)):  # Backspace
            if user_input:  # Only process if there's something to delete
                user_input = user_input[:-1]
                if scroll_offset > 0 and len(user_input) < scroll_offset + input_width:
                    scroll_offset -= 1  # Move back if text is shorter than scrolled area
        else:
            # Append typed character to input text
            if(isinstance(key, str)):
                user_input += key
            else:
                user_input += chr(key)

            if len(user_input) > input_width:  # Scroll if input exceeds visible area
                scroll_offset += 1

    curses.curs_set(0)

    return user_input if user_input else current_value


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

    return menu_win, menu_pad, options


def move_highlight(old_idx, new_idx, options, menu_win, menu_pad):
    if old_idx == new_idx:
        return # no-op

    show_save_option = True

    max_index = len(options) + (1 if show_save_option else 0) - 1

    if show_save_option and old_idx == max_index: # special case un-highlight "Save" option
        menu_win.chgat(menu_win.getmaxyx()[0] - 2, (width - len(save_option_text)) // 2, len(save_option_text), get_color("settings_save"))
    else:
        menu_pad.chgat(old_idx, 0, menu_pad.getmaxyx()[1], get_color("settings_default"))

    if show_save_option and new_idx == max_index: # special case highlight "Save" option
        menu_win.chgat(menu_win.getmaxyx()[0] - 2, (width - len(save_option_text)) // 2, len(save_option_text), get_color("settings_save", reverse = True))
    else:
       menu_pad.chgat(new_idx, 0,menu_pad.getmaxyx()[1], get_color("settings_default", reverse = True))

    start_index = max(0, new_idx - (menu_win.getmaxyx()[0] - 6))

    menu_win.refresh()
    menu_pad.refresh(start_index, 0,
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

    need_redraw = True


    while True:

        if(need_redraw):
            
            menu_win, menu_pad, options = render_menu(current_data, menu_path, selected_index)
            menu_win.refresh()
            need_redraw = False
            

        max_index = len(options) + (1 if show_save_option else 0) - 1
        key = menu_win.getch()


        if key == curses.KEY_UP:

            old_selected_index = selected_index
            selected_index = max_index if selected_index == 0 else selected_index - 1
            move_highlight(old_selected_index, selected_index, options, menu_win, menu_pad)

        elif key == curses.KEY_DOWN:

            old_selected_index = selected_index
            selected_index = 0 if selected_index == max_index else selected_index + 1
            move_highlight(old_selected_index, selected_index, options, menu_win, menu_pad)


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
                    need_redraw = True


            else:
                # Save button selected
                save_json(file_path, data)
                stdscr.refresh()
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
    # menu_win.clear()
    # menu_win.refresh()

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
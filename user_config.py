import curses
import json
import os
from ui.colors import get_color, setup_colors
from default_config import format_json_single_line_arrays



def display_menu(window, items, selected_index, title, show_save):
    window.clear()
    height, width = window.getmaxyx()

    window.addstr(0, (width - len(title)) // 2, title, get_color("settings_default"))

    for i, (key, value) in enumerate(items.items()):
        value_display = str(value)[:width // 2 - 4]  # Truncate if too long
        key_display = key[:width // 2 - 4]  # Truncate if too long

        if i == selected_index:
            window.addstr(i + 2, 2, f"{key_display:<{width // 2 - 2}}: {value_display}", get_color("settings_default")| curses.A_REVERSE)
        else:
            window.addstr(i + 2, 2, f"{key_display:<{width // 2 - 2}}: {value_display}", get_color("settings_default"))

    if show_save:
        save_text = "Save Changes"
        if selected_index == len(items):
            window.addstr(height - 2, (width - len(save_text)) // 2, save_text, get_color("settings_default") | curses.A_REVERSE)
        else:
            window.addstr(height - 2, (width - len(save_text)) // 2, save_text, get_color("settings_default"))

    window.refresh()

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
        elif key == 27:  # ESC key
            return current_color

def edit_value(window, key, current_value):
    curses.curs_set(1)
    window.clear()
    window.addstr(1, 2, f"Editing {key}: (Press Enter to save, ESC to cancel)", get_color("settings_default"))
    window.addstr(3, 2, f"Current Value: {current_value}", get_color("settings_default"))
    window.addstr(5, 2, "New Value: ", get_color("settings_default"))
    window.refresh()

    curses.echo()
    new_value = window.getstr(5, 14, 50).decode("utf-8")
    curses.noecho()
    curses.curs_set(0)

    return new_value

def edit_color_pair(window, key, current_value):
    curses.curs_set(0)
    window.clear()
    window.addstr(1, 2, f"Editing {key} (foreground/background):", get_color("settings_default"))
    window.refresh()

    fg_color = select_color(window, current_value[0])
    bg_color = select_color(window, current_value[1])

    return [fg_color, bg_color]

def save_json(file_path, data):
    formatted_json = format_json_single_line_arrays(data)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(formatted_json)

def nested_menu(stdscr, data, menu_path, file_path):

    curses.curs_set(0)

    selected_index = 0
    keys = list(data.keys())

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        title = f"{' > '.join(menu_path)} - Use Arrow Keys to Navigate, Enter to Edit, ESC to Go Back"
        display_menu(stdscr, {key: data[key] for key in keys}, selected_index, title, show_save=True)

        key = stdscr.getch()

        if key == curses.KEY_UP:
            selected_index = max(0, selected_index - 1)
        elif key == curses.KEY_DOWN:
            selected_index = min(len(keys), selected_index + 1)  # Include save option
        elif key == ord("\n"):
            if selected_index == len(keys):  # Save option selected
                save_json(file_path, data)
                stdscr.addstr(height - 4, 2, "Changes saved successfully!", get_color("settings_default"))
                stdscr.refresh()
                curses.napms(1500)
            else:
                selected_key = keys[selected_index]
                if isinstance(data[selected_key], dict):
                    nested_menu(stdscr, data[selected_key], menu_path + [selected_key], file_path)
                elif isinstance(data[selected_key], list) and len(data[selected_key]) == 2:
                    data[selected_key] = edit_color_pair(stdscr, selected_key, data[selected_key])
                else:
                    new_value = edit_value(stdscr, selected_key, data[selected_key])
                    data[selected_key] = new_value
        elif key == 27:  # ESC key
            break

def json_editor(stdscr, file_path):
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            json.dump({}, f)

    with open(file_path, "r") as f:
        data = json.load(f)

    nested_menu(stdscr, data, ["App Settings"], file_path)

def main_menu_handler(stdscr, menu_structure, file_path):
    if "App Settings" in menu_structure["Main Menu"]:
        json_editor(stdscr, file_path)


def main():

    curses.wrapper(json_editor, "config.json")
    setup_colors()

if __name__ == "__main__":
    main()

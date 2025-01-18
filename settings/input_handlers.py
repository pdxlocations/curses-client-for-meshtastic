
import curses


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

def get_enum_input(stdscr, options, current_value):
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
        
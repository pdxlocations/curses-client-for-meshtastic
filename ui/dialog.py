import curses

def dialog(stdscr, title, message):
    height, width = stdscr.getmaxyx()

    # Calculate dialog dimensions
    max_line_lengh = 0
    message_lines = message.splitlines()
    for l in message_lines:
        max_line_length = max(len(l), max_line_lengh)
    dialog_width = max(len(title) + 4, max_line_length + 4)
    dialog_height = len(message_lines) + 4
    x = (width - dialog_width) // 2
    y = (height - dialog_height) // 2

    # Create dialog window
    win = curses.newwin(dialog_height, dialog_width, y, x)
    win.border(0)

    # Add title
    win.addstr(0, 2, title)

    # Add message
    for i, l in enumerate(message_lines):
        win.addstr(2 + i, 2, l)

    # Add button
    win.addstr(dialog_height - 2, (dialog_width - 4) // 2, " Ok ", curses.color_pair(3))

    # Refresh dialog window
    win.refresh()

    # Get user input
    while True:
        char = win.getch()
        # Close dialog with enter, space, or esc
        if char in(curses.KEY_ENTER, 10, 13, 32, 27):
            win.clear()
            win.refresh()
            return

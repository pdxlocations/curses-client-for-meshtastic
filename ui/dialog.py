import curses

def dialog(stdscr, title, message):
    height, width = stdscr.getmaxyx()

    # Calculate dialog dimensions
    dialog_width = max(len(title) + 4, len(message) + 4)
    dialog_height = 5
    x = (width - dialog_width) // 2
    y = (height - dialog_height) // 2

    # Create dialog window
    win = curses.newwin(dialog_height, dialog_width, y, x)
    win.border(0)

    # Add title
    win.addstr(0, 2, title)

    # Add message
    win.addstr(2, 2, message)

    # Add button
    win.addstr(dialog_height - 2, (dialog_width - 4) // 2, " Ok ")

    # Refresh dialog window
    win.refresh()

    # Get user input
    while True:
        char = win.getch()
        if char == curses.KEY_ENTER or char == 10 or char == 13:
            win.clear()
            win.refresh()
            return

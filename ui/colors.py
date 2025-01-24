import curses
import globals
# def setup_colors():
#     curses.start_color()
#     curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
#     curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK) 
#     curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
#     curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)
#     curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)



# # Configuration dictionary for text categories
# COLOR_CONFIG = {
#     "default_text": {"foreground": "white", "background": "black"},
#     "rx_messages": {"foreground": "green", "background": "black"},
#     "tx_messages": {"foreground": "cyan", "background": "black"},
#     "timestamps": {"foreground": "yellow", "background": "black"}
# }

# Map color names to curses constants
COLOR_MAP = {
    "black": curses.COLOR_BLACK,
    "red": curses.COLOR_RED,
    "green": curses.COLOR_GREEN,
    "yellow": curses.COLOR_YELLOW,
    "blue": curses.COLOR_BLUE,
    "magenta": curses.COLOR_MAGENTA,
    "cyan": curses.COLOR_CYAN,
    "white": curses.COLOR_WHITE
}

def setup_colors():
    curses.start_color()
    # Dynamically create color pairs based on the configuration
    for idx, (category, colors) in enumerate(globals.COLOR_CONFIG.items(), start=1):
        fg = COLOR_MAP.get(colors["foreground"].lower(), curses.COLOR_WHITE)
        bg = COLOR_MAP.get(colors["background"].lower(), curses.COLOR_BLACK)
        curses.init_pair(idx, fg, bg)
        colors["pair_id"] = idx  # Store the pair ID for later use



# def main(stdscr):
#     # Setup colors based on the configuration
#     setup_colors()

#     # Use the configured color pairs
#     stdscr.addstr(0, 0, "This is default text.", curses.color_pair(COLOR_CONFIG["default_text"]["pair_id"]))
#     stdscr.addstr(1, 0, "This is an RX message.", curses.color_pair(COLOR_CONFIG["rx_messages"]["pair_id"]))
#     stdscr.addstr(2, 0, "This is a TX message.", curses.color_pair(COLOR_CONFIG["tx_messages"]["pair_id"]))
#     stdscr.addstr(3, 0, "This is a timestamp.", curses.color_pair(COLOR_CONFIG["timestamps"]["pair_id"]))

#     stdscr.refresh()
#     stdscr.getch()

# if __name__ == "__main__":
#     curses.wrapper(main)
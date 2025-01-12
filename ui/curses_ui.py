import curses
import textwrap
import globals
from utilities.utils import get_node_list, get_name_from_number, get_channels
from settings import settings
from message_handlers.tx_handler import send_message

# def handle_notification(channel_number, add=True):
#     global channel_win
#     _, win_width = channel_win.getmaxyx()  # Get the width of the channel window

#     # Get the channel name
#     if isinstance(globals.channel_list[channel_number], str):  # Channels
#         channel_name = globals.channel_list[channel_number]
#     elif isinstance(globals.channel_list[channel_number], int):  # DM's
#         channel_name = get_name_from_number(globals.channel_list[channel_number])
#     else:
#         return

#     # Truncate the channel name if it's too long to fit in the window
#     truncated_channel_name = channel_name[:win_width - 5] + '-' if len(channel_name) > win_width - 5 else channel_name

#     # Add or remove the notification indicator
#     notification = " *" if add else "  "
#     channel_win.addstr(channel_number + 1, len(truncated_channel_name) + 1, notification, curses.color_pair(4))
#     channel_win.refresh()

# def handle_notification(channel_number, add=True):
#     # Modify the channel name in globals.channel_list to include or remove the notification
#     if add:
#         # Avoid adding multiple `*` notifications
#         if not globals.channel_list[channel_number].endswith(" *"):
#             globals.channel_list[channel_number] += " *"
#     else:
#         # Remove the `*` notification if it exists
#         if globals.channel_list[channel_number].endswith(" *"):
#             globals.channel_list[channel_number] = globals.channel_list[channel_number][:-2]

#     # Redraw the channel list to reflect the changes
#     # draw_channel_list()

def handle_notification(channel_number, add=True):
    if add:
        globals.notifications.add(channel_number)  # Add the channel to the notification tracker
    else:
        globals.notifications.discard(channel_number)  # Remove the channel from the notification tracker

    # Redraw the channel list to reflect the notification state
    # draw_channel_list()



def add_notification(channel_number):
    handle_notification(channel_number, add=True)

def remove_notification(channel_number):
    handle_notification(channel_number, add=False)
    channel_win.box()
    channel_win.refresh()

def update_messages_window():
    global messages_win
    messages_win.clear()

    # Calculate how many messages can fit in the window
    max_messages = messages_win.getmaxyx()[0] - 2  # Subtract 2 for the top and bottom border

    # Determine the starting index for displaying messages
    if globals.channel_list[globals.selected_channel] in globals.all_messages:
        start_index = max(0, len(globals.all_messages[globals.channel_list[globals.selected_channel]]) - max_messages)
    else:
        # Handle the case where selected_channel does not exist
        start_index = 0  # Set start_index to 0 or any other appropriate value

    # Display messages starting from the calculated start index
    # Check if selected_channel exists in all_messages before accessing it
    if globals.channel_list[globals.selected_channel] in globals.all_messages:
        row = 1
        for _, (prefix, message) in enumerate(globals.all_messages[globals.channel_list[globals.selected_channel]][start_index:], start=1):
            full_message = f"{prefix}{message}"
            wrapped_messages = textwrap.wrap(full_message, messages_win.getmaxyx()[1] - 2)

            for wrapped_message in wrapped_messages:
                messages_win.addstr(row, 1, wrapped_message, curses.color_pair(1) if prefix.startswith(">> Sent:") else curses.color_pair(2))
                row += 1

    messages_win.box()
    messages_win.refresh()
    update_packetlog_win()

def update_packetlog_win():
    if globals.display_log:
        packetlog_win.clear()
        packetlog_win.box()
        # Get the dimensions of the packet log window
        height, width = packetlog_win.getmaxyx()
        
        columns = [10,10,15,30]
        span = 0
        for column in columns[:-1]:
            span += column

        # Add headers
        headers = f"{'From':<{columns[0]}} {'To':<{columns[1]}} {'Port':<{columns[2]}} {'Payload':<{width-span}}"
        packetlog_win.addstr(1, 1, headers[:width - 2],curses.A_UNDERLINE)  # Truncate headers if they exceed window width

        for i, packet in enumerate(reversed(globals.packet_buffer)):
            if i >= height - 3:  # Skip if exceeds the window height
                break
            
            # Format each field

            from_id = get_name_from_number(packet['from'], 'short').ljust(columns[0])
            to_id = (
                "BROADCAST".ljust(columns[1]) if str(packet['to']) == "4294967295"
                else get_name_from_number(packet['to'], 'short').ljust(columns[1])
            )
            if 'decoded' in packet:
                port = packet['decoded']['portnum'].ljust(columns[2])
                payload = (packet['decoded']['payload']).ljust(columns[3])
            else:
                port = "NO KEY".ljust(columns[2])
                payload = "NO KEY".ljust(columns[3])

            # Combine and truncate if necessary
            logString = f"{from_id} {to_id} {port} {payload}"
            logString = logString[:width - 3]

            # Add to the window
            packetlog_win.addstr(i + 2, 1, logString)

        packetlog_win.refresh()

def draw_text_field(win, text):
    win.border()
    win.addstr(1, 1, text)

def draw_centered_text_field(win, text, y_offset = 0):
    height, width = win.getmaxyx()
    x = (width - len(text)) // 2
    y = (height // 2) + y_offset
    
    win.addstr(y, x, text)
    win.refresh()

def draw_splash(stdscr):
    curses.start_color()
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Green text on black background
    curses.curs_set(0)

    stdscr.clear()
    height, width = stdscr.getmaxyx()
    message_1 = "/ Λ"
    message_2 = "/ / \\"
    message_3 = "P W R D"
    message_4 = "connecting..."

    start_x = width // 2 - len(message_1) // 2
    start_x2 = width // 2 - len(message_4) // 2
    start_y = height // 2 - 1
    stdscr.addstr(start_y, start_x, message_1, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(start_y+1, start_x-1, message_2, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(start_y+2, start_x-2, message_3, curses.color_pair(1) | curses.A_BOLD)
    stdscr.addstr(start_y+4, start_x2, message_4)
    stdscr.box()
    stdscr.refresh()


def draw_channel_list():

    channel_win.clear() 
    win_height, win_width = channel_win.getmaxyx()
    start_index = max(0, globals.selected_channel - (win_height - 3))  # Leave room for borders

    for i, (channel, _) in enumerate(list(globals.all_messages.items())[start_index:], start=0):
        # Convert node number to long name if it's an integer
        if isinstance(channel, int):
            channel = get_name_from_number(channel, type='long')

        # Determine whether to add the notification
        notification = " " + globals.notification_symbol if start_index + i in globals.notifications else ""

        # Truncate the channel name if it's too long to fit in the window
        truncated_channel = channel[:win_width - 5] + '-' if len(channel) > win_width - 5 else channel
        if i < win_height - 2   :  # Check if there is enough space in the window
            if start_index + i == globals.selected_channel and not globals.direct_message:
                channel_win.addstr(i + 1, 1, truncated_channel + notification, curses.color_pair(3))
                remove_notification(globals.selected_channel)
            else:
                channel_win.addstr(i + 1, 1, truncated_channel + notification, curses.color_pair(4))
    channel_win.box()
    channel_win.refresh()


def draw_node_list():

    nodes_win.clear()                 
    win_height, _ = nodes_win.getmaxyx()
    start_index = max(0, globals.selected_node - (win_height - 3))  # Calculate starting index based on selected node and window height

    for i, node in enumerate(get_node_list()[start_index:], start=1):
        if i < win_height - 1   :  # Check if there is enough space in the window
            if globals.selected_node + 1 == start_index + i and globals.direct_message:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(3))
            else:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(4))

    nodes_win.box()
    nodes_win.refresh()

def draw_debug(value):
    function_win.addstr(1, 100, f"debug: {value}    ")
    function_win.refresh()

def select_channels(direction):
    channel_list_length = len(globals.channel_list)
    globals.selected_channel += direction

    if globals.selected_channel < 0:
        globals.selected_channel = channel_list_length - 1
    elif globals.selected_channel >= channel_list_length:
        globals.selected_channel = 0

    draw_channel_list()
    update_messages_window()

def select_nodes(direction):
    node_list_length = len(get_node_list())
    globals.selected_node += direction

    if globals.selected_node < 0:
        globals.selected_node = node_list_length - 1
    elif globals.selected_node >= node_list_length:
        globals.selected_node = 0

    draw_node_list()

def main_ui(stdscr):
    global messages_win, nodes_win, channel_win, function_win, packetlog_win
    stdscr.keypad(True)
    get_channels()

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_RED, curses.COLOR_BLACK)

    # Calculate window max dimensions
    height, width = stdscr.getmaxyx()

    # Define window dimensions and positions
    entry_win = curses.newwin(3, width, 0, 0)
    channel_width = 3 * (width // 16)
    nodes_width = 5 * (width // 16)
    messages_width = width - channel_width - nodes_width

    channel_win = curses.newwin(height - 6, channel_width, 3, 0)
    messages_win = curses.newwin(height - 6, messages_width, 3, channel_width)
    packetlog_win = curses.newwin(int(height / 3), messages_width, height - int(height / 3) - 3, channel_width)
    nodes_win = curses.newwin(height - 6, nodes_width, 3, channel_width + messages_width)
    function_win = curses.newwin(3, width, height - 3, 0)

    draw_centered_text_field(function_win, f"↑→↓← = Select    ENTER = Send    ` = Settings    / = Toggle Log    ESC = Quit")

    # Enable scrolling for messages and nodes windows
    messages_win.scrollok(True)
    nodes_win.scrollok(True)
    channel_win.scrollok(True)

    draw_channel_list()
    draw_node_list()
    update_messages_window()

    # Draw boxes around windows
    channel_win.box()
    entry_win.box()
    messages_win.box()
    nodes_win.box()
    function_win.box() 

    # Refresh all windows
    entry_win.refresh()
    messages_win.refresh()
    nodes_win.refresh()
    channel_win.refresh()
    function_win.refresh()

    input_text = ""
    globals.direct_message = False

    entry_win.keypad(True)
    curses.curs_set(1)

    while True:
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.getch()

        # draw_debug(f"Keypress: {char}")

        if char == curses.KEY_UP:
            if globals.direct_message:
                draw_channel_list()
                select_nodes(-1)
            else:
                select_channels(-1)
        elif char == curses.KEY_DOWN:
            if globals.direct_message:
                draw_channel_list()
                select_nodes(1)
            else:
                select_channels(1)
            
        elif char == curses.KEY_LEFT:
            if globals.direct_message == False:
                pass
            else:
                globals.direct_message = False
                draw_channel_list()
                draw_node_list()

        elif char == curses.KEY_RIGHT:
            if globals.direct_message == False:
                globals.direct_message = True
                draw_channel_list()
                draw_node_list()
            else:
                pass

        # Check for Esc
        elif char == 27:
            break
            
        elif char == curses.KEY_ENTER or char == 10 or char == 13:
            if globals.direct_message:
                node_list = get_node_list()
                if node_list[globals.selected_node] not in globals.channel_list:
                    globals.channel_list.append(node_list[globals.selected_node])
                    globals.all_messages[node_list[globals.selected_node]] = []

                globals.selected_channel = globals.channel_list.index(node_list[globals.selected_node])
                globals.selected_node = 0
                globals.direct_message = False
                draw_node_list()
                draw_channel_list()
                update_messages_window()

            else:
                # Enter key pressed, send user input as message
                send_message(input_text, channel=globals.selected_channel)
                update_messages_window()
                messages_win.refresh()

                # Clear entry window and reset input text
                input_text = ""
                entry_win.clear()       
                entry_win.refresh()

        elif char == curses.KEY_BACKSPACE or char == 127:
            if input_text:
                input_text = input_text[:-1]
                y, x = entry_win.getyx()
                entry_win.move(y, x - 1)
                entry_win.addch(' ')  #
                entry_win.move(y, x - 1)
            entry_win.refresh()
            
        elif char == 96:
            curses.curs_set(0)  # Hide cursor
            settings(stdscr)
            curses.curs_set(1)  # Show cursor again
        
        elif char == 47:
            # Display packet log
            if globals.display_log is False:
                globals.display_log = True
                update_messages_window()
            else:
                globals.display_log = False
                packetlog_win.clear()
                update_messages_window()
        else:
            # Append typed character to input text
            input_text += chr(char)

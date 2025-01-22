import curses
import textwrap
import globals
from utilities.utils import get_name_from_number, get_channels
from settings import settings_menu
from message_handlers.tx_handler import send_message, send_traceroute
import ui.dialog
from ui.colors import setup_colors

def add_notification(channel_number):
    handle_notification(channel_number, add=True)

def remove_notification(channel_number):
    handle_notification(channel_number, add=False)
    channel_win.box()

def handle_notification(channel_number, add=True):
    if add:
        globals.notifications.add(channel_number)  # Add the channel to the notification tracker
    else:
        globals.notifications.discard(channel_number)  # Remove the channel from the notification tracker

def draw_text_field(win, text):
    win.border()
    win.addstr(1, 1, text)

def draw_centered_text_field(win, text, y_offset = 0):
    height, width = win.getmaxyx()
    x = (width - len(text)) // 2
    y = (height // 2) + y_offset
    win.addstr(y, x, text)
    win.refresh()

def draw_debug(value):
    function_win.addstr(1, 1, f"debug: {value}    ")
    function_win.refresh()

def draw_splash(stdscr):
    setup_colors()
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
    stdscr.addstr(start_y, start_x, message_1, curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(start_y+1, start_x-1, message_2, curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(start_y+2, start_x-2, message_3, curses.color_pair(2) | curses.A_BOLD)
    stdscr.addstr(start_y+4, start_x2, message_4)
    stdscr.box()
    stdscr.refresh()
    curses.napms(500)


def draw_channel_list():

    channel_win.clear() 
    win_height, win_width = channel_win.getmaxyx()
    start_index = max(0, globals.selected_channel - (win_height - 3))  # Leave room for borders

    for i, channel in enumerate(list(globals.all_messages.keys())[start_index:], start=0):

        # Convert node number to long name if it's an integer
        if isinstance(channel, int):
            channel = get_name_from_number(channel, type='long')

        # Determine whether to add the notification
        notification = " " + globals.notification_symbol if start_index + i in globals.notifications else ""

        # Truncate the channel name if it's too long to fit in the window
        truncated_channel = channel[:win_width - 5] + '-' if len(channel) > win_width - 5 else channel
        if i < win_height - 2   :  # Check if there is enough space in the window
            if start_index + i == globals.selected_channel and globals.current_window == 0:
                channel_win.addstr(i + 1, 1, truncated_channel + notification, curses.color_pair(1) | curses.A_REVERSE)
                remove_notification(globals.selected_channel)
            else:
                channel_win.addstr(i + 1, 1, truncated_channel + notification, curses.color_pair(1))
    channel_win.box()
    channel_win.refresh()

def draw_messages_window(scroll_to_bottom = False):
    """Update the messages window based on the selected channel and scroll position."""
    messages_pad.clear()

    channel = globals.channel_list[globals.selected_channel]

    if channel in globals.all_messages:
        messages = globals.all_messages[channel]

        msg_line_count = 0

        row = 0
        for (prefix, message) in messages:
            full_message = f"{prefix}{message}"
            wrapped_lines = textwrap.wrap(full_message, messages_box.getmaxyx()[1] - 2)
            msg_line_count += len(wrapped_lines)
            messages_pad.resize(msg_line_count, messages_box.getmaxyx()[1])

            for line in wrapped_lines:
                color = curses.color_pair(1) if prefix.startswith(globals.sent_message_prefix) else curses.color_pair(2)
                messages_pad.addstr(row, 1, line, color)
                row += 1

    messages_box.box()
    messages_box.refresh()

    if(scroll_to_bottom):
        globals.selected_message = max(msg_line_count - get_msg_window_lines(), 0)
    else:
        globals.selected_message = max(min(globals.selected_message, msg_line_count - get_msg_window_lines()), 0)

    # Adjust for packetlog height if log is visible
    packetlog_height = packetlog_win.getmaxyx()[0] if globals.display_log else 0
    messages_pad.refresh(globals.selected_message, 0,
                         messages_box.getbegyx()[0] + 1, messages_box.getbegyx()[1] + 1,
                         messages_box.getbegyx()[0] + get_msg_window_lines(), messages_box.getbegyx()[1] + messages_box.getmaxyx()[1] - 2)

    draw_packetlog_win()

def draw_node_list():
    nodes_win.clear()                 
    win_height = nodes_win.getmaxyx()[0]
    start_index = max(0, globals.selected_node - (win_height - 3))  # Calculate starting index based on selected node and window height

    for i, node in enumerate(globals.node_list[start_index:], start=1):
        if i < win_height - 1   :  # Check if there is enough space in the window
            if globals.selected_node + 1 == start_index + i and globals.current_window == 2:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(1) | curses.A_REVERSE)
            else:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(1))

    nodes_win.box()
    nodes_win.refresh()

def select_channels(direction):
    channel_list_length = len(globals.channel_list)
    globals.selected_channel += direction

    if globals.selected_channel < 0:
        globals.selected_channel = channel_list_length - 1
    elif globals.selected_channel >= channel_list_length:
        globals.selected_channel = 0

    draw_channel_list()
    draw_messages_window(True)

def select_messages(direction):
    globals.selected_message += direction

    msg_line_count = messages_pad.getmaxyx()[0]
    if globals.selected_message < 0:
        globals.selected_message = max(msg_line_count - get_msg_window_lines(), 0)
    elif globals.selected_message > (msg_line_count - get_msg_window_lines()):
        globals.selected_message = 0

    messages_pad.refresh(globals.selected_message, 0,
                         messages_box.getbegyx()[0] + 1, messages_box.getbegyx()[1] + 1,
                         messages_box.getbegyx()[0] + get_msg_window_lines(), messages_box.getbegyx()[1] + messages_box.getmaxyx()[1] - 2)

def select_nodes(direction):
    node_list_length = len(globals.node_list)
    globals.selected_node += direction

    if globals.selected_node < 0:
        globals.selected_node = node_list_length - 1
    elif globals.selected_node >= node_list_length:
        globals.selected_node = 0

    draw_node_list()


def draw_packetlog_win():

    columns = [10,10,15,30]
    span = 0

    if globals.display_log:
        packetlog_win.clear()
        height, width = packetlog_win.getmaxyx()
        
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

        packetlog_win.box()
        packetlog_win.refresh()


def main_ui(stdscr):
    global messages_pad, messages_box, nodes_win, channel_win, function_win, packetlog_win
    stdscr.keypad(True)
    get_channels()

    # Calculate window max dimensions
    height, width = stdscr.getmaxyx()

    # Define window dimensions and positions
    entry_win = curses.newwin(3, width, 0, 0)
    channel_width = 3 * (width // 16)
    nodes_width = 5 * (width // 16)
    messages_width = width - channel_width - nodes_width

    channel_win = curses.newwin(height - 6, channel_width, 3, 0)
    messages_box = curses.newwin(height - 6, messages_width, 3, channel_width)

    # Will be resized to what we need when drawn
    messages_pad = curses.newpad(1, 1)
    packetlog_win = curses.newwin(int(height / 3), messages_width, height - int(height / 3) - 3, channel_width)
    nodes_win = curses.newwin(height - 6, nodes_width, 3, channel_width + messages_width)
    function_win = curses.newwin(3, width, height - 3, 0)

    draw_centered_text_field(function_win, f"↑→↓← = Select    ENTER = Send    ` = Settings    ^P = Packet Log    ESC = Quit")

    # Draw boxes around windows
    channel_win.box()
    entry_win.box()
    nodes_win.box()
    messages_box.box()
    function_win.box() 

    # Refresh all windows
    entry_win.refresh()

    nodes_win.refresh()
    channel_win.refresh()
    function_win.refresh()
    messages_box.refresh()
    input_text = ""

    entry_win.keypad(True)
    curses.curs_set(1)

    draw_channel_list()
    draw_node_list()
    draw_messages_window(True)

    while True:
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.get_wch()

        # draw_debug(f"Keypress: {char}")

        if char == curses.KEY_UP:
            if globals.current_window == 0:
                select_channels(-1)
            elif globals.current_window == 1:
                select_messages(-1)
            elif globals.current_window == 2:
                select_nodes(-1)

        elif char == curses.KEY_DOWN:
            if globals.current_window == 0:
                select_channels(1)
            elif globals.current_window == 1:
                select_messages(1)
            elif globals.current_window == 2:
                select_nodes(1)

        elif char == curses.KEY_LEFT or char == curses.KEY_RIGHT:
            delta = -1 if char == curses.KEY_LEFT else 1

            old_window = globals.current_window
            globals.current_window = (globals.current_window + delta) % 3

            if old_window == 0 or globals.current_window == 0:
                draw_channel_list()
            if old_window == 1 or globals.current_window == 1:
                draw_messages_window()
            if old_window == 2 or globals.current_window == 2:
                draw_node_list()

        # Check for Esc
        elif char == chr(27):
            break

        # Check for Ctrl + t
        elif char == chr(20):
            send_traceroute()
            curses.curs_set(0)  # Hide cursor
            ui.dialog.dialog(stdscr, "Traceroute Sent", "Results will appear in messages window.\nNote: Traceroute is limited to once every 30 seconds.")
            curses.curs_set(1)  # Show cursor again

        elif char in (chr(curses.KEY_ENTER), chr(10), chr(13)):
            if globals.current_window == 2:
                node_list = globals.node_list
                if node_list[globals.selected_node] not in globals.channel_list:
                    globals.channel_list.append(node_list[globals.selected_node])
                    globals.all_messages[node_list[globals.selected_node]] = []

                globals.selected_channel = globals.channel_list.index(node_list[globals.selected_node])
                globals.selected_node = 0
                globals.current_window = 0

                draw_node_list()
                draw_channel_list()
                draw_messages_window(True)

            else:
                # Enter key pressed, send user input as message
                send_message(input_text, channel=globals.selected_channel)
                draw_messages_window(True)

                # Clear entry window and reset input text
                input_text = ""
                entry_win.clear()       
                # entry_win.refresh()

        elif char in (curses.KEY_BACKSPACE, chr(127)):
            if input_text:
                input_text = input_text[:-1]
                y, x = entry_win.getyx()
                entry_win.move(y, x - 1)
                entry_win.addch(' ')  #
                entry_win.move(y, x - 1)
            entry_win.refresh()
            
        elif char == "`": # ` Launch the settings interface
            curses.curs_set(0)
            settings_menu(stdscr, globals.interface)
            curses.curs_set(1)
        
        elif char == chr(16):
            # Display packet log
            if globals.display_log is False:
                globals.display_log = True
                draw_messages_window(True)
            else:
                globals.display_log = False
                packetlog_win.clear()
                draw_messages_window(True)
        else:
            # Append typed character to input text
            if(isinstance(char, str)):
                input_text += char
            else:
                input_text += chr(char)

def get_msg_window_lines():
    packetlog_height = packetlog_win.getmaxyx()[0] if globals.display_log else 0
    return messages_box.getmaxyx()[0] - 2 - packetlog_height

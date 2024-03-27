import curses
import meshtastic.serial_interface
from pubsub import pub

# Initialize Meshtastic interface
interface = meshtastic.serial_interface.SerialInterface()

messages_win = None
nodes_win = None
message_row = 1


node_list = []
if interface.nodes:
    for node in interface.nodes.values():
        node_list.append(node["user"]["longName"])


def on_receive(packet, interface):
    global message_row  # Access the global message_row variable
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
            # Add received message to the messages window
            messages_win.addstr(message_row, 1, ">> Received: ", curses.color_pair(1))
            messages_win.addstr(message_row, 14, message_string + '\n')
            messages_win.box()
            messages_win.refresh()
            message_row += 1  # Increment message row
    except KeyError as e:
        print(f"Error processing packet: {e}")

pub.subscribe(on_receive, 'meshtastic.receive')

def send_message(message):
    global message_row 
    interface.sendText(message)
    # Add sent message to the messages window
    messages_win.addstr(message_row, 1, ">> Sent: ", curses.color_pair(2))
    messages_win.addstr(message_row, 10, message + '\n')

    messages_win.box()
    messages_win.refresh()
    message_row += 1  # Increment message row

def draw_text_field(win, text):
    win.clear()
    win.border()
    win.addstr(1, 1, text)

def main(stdscr):
    global messages_win, nodes_win 

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    # Turn off cursor blinking
    curses.curs_set(1)

    # Calculate window dimensions
    height, width = stdscr.getmaxyx()

    # Define window dimensions and positions
    entry_win = curses.newwin(3, width, 0, 0)
    messages_win = curses.newwin(height - 6, 2*(width // 3), 3, 0)
    nodes_win = curses.newwin(height - 6, width // 3, 3, 2*(width // 3))

    # Enable scrolling for messages and nodes windows
    messages_win.scrollok(True)
    nodes_win.scrollok(True)

    # Draw boxes around windows
    entry_win.box()
    messages_win.box()
    nodes_win.box()

    # Display initial content in nodes window
    for i, node in enumerate(node_list, start=1):
        if i < height - 6 - 1:  # Check if there is enough space in the window
            nodes_win.addstr(i, 1, node)

    # Refresh all windows
    stdscr.refresh()
    entry_win.refresh()
    messages_win.refresh()
    nodes_win.refresh()

    input_text = ""
    while True:
        # Draw text field
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.getch()

        if char == curses.KEY_ENTER or char == 10 or char == 13:
            # Enter key pressed, send user input as message
            send_message(input_text)

            # Clear entry window and reset input text
            input_text = ""
            entry_win.clear()
            entry_win.refresh()
        elif char == curses.KEY_BACKSPACE or char == 127:
            # Backspace key pressed, remove last character from input text
            input_text = input_text[:-1]
        else:
            # Append typed character to input text
            input_text += chr(char)


if __name__ == "__main__":
    curses.wrapper(main)

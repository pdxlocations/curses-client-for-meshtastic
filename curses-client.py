import curses
import meshtastic.serial_interface
from pubsub import pub
from meshtastic import config_pb2  # Import config_pb2 for accessing modem presets

# Initialize Meshtastic interface
interface = meshtastic.serial_interface.SerialInterface()

messages_win = None
nodes_win = None
channel_win = None  # Added channel_win variable
message_row = 1
selected_channel = 0
number_of_channels=0
BROADCAST_ADDR = 4294967295

node_list = []
if interface.nodes:
    for node in interface.nodes.values():
        node_list.append(node["user"]["longName"])

def decimal_to_hex(decimal_number):
    return "!" + hex(decimal_number)[2:]

def convert_to_camel_case(string):
    words = string.split('_')
    camel_case_string = ''.join(word.capitalize() for word in words)
    return camel_case_string

def on_receive(packet, interface):
    global message_row
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')

            # Add received message to the messages window
            message_from_id = packet['from']
            message_from_string =""
            for node in interface.nodes.values():

                if message_from_id == node['num']:
                    message_from_string = node["user"]["longName"]  # Get the long name using the node ID
                    break
                else:
                    message_from_string = str(decimal_to_hex(message_from_id))  # If long name not found, use the ID as string

            messages_win.addstr(message_row, 1, f">> {message_from_string}", curses.color_pair(1))
            messages_win.addstr(message_row, 3 + len(message_from_string) + 2, message_string + '\n')
            messages_win.box()
            messages_win.refresh()
            message_row += 1  # Increment message row
    except KeyError as e:
        print(f"Error processing packet: {e}")


def send_message(message, destination=BROADCAST_ADDR, channel=0):
    global message_row 
    
    interface.sendText(
        text=message,
        destinationId=destination,
        wantAck=False,
        wantResponse=False,
        onResponse=None,
        channelIndex=channel,
    )

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

def draw_channel_list():
    global number_of_channels
     # Get node information and display it in the channel_win
    node = interface.getNode('^local')
    device_channels = node.channels

    channel_output = []
    number_of_channels = 0
    for device_channel in device_channels:
        if device_channel.role:
            number_of_channels += 1
            if device_channel.settings.name:
                channel_output.append(device_channel.settings.name)
            else:
                # If channel name is blank, use the modem preset
                lora_config = node.localConfig.lora
                modem_preset_enum = lora_config.modem_preset
                modem_preset_string = config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[modem_preset_enum].name
                channel_output.append(convert_to_camel_case(modem_preset_string))

    for i, channel in enumerate(channel_output):
        if selected_channel == i:
            channel_win.addstr(i+1, 1, channel, curses.color_pair(3))
        else:
            channel_win.addstr(i+1, 1, channel, curses.color_pair(4))


def main(stdscr):
    global messages_win, nodes_win, channel_win, selected_channel, function_win

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Turn off cursor blinking
    curses.curs_set(1)

    # Calculate window dimensions
    height, width = stdscr.getmaxyx()

    # Define window dimensions and positions
    entry_win = curses.newwin(3, width, 0, 0)  # Positioned at the top, spans entire width
    
    # Define window dimensions and positions
    channel_width = width // 8  # ⅛ of the width
    messages_width = 4 * (width // 8)  # 4/8 of the width
    nodes_width = 3 * (width // 8)  # ⅜ of the width

    channel_win = curses.newwin(height - 6, channel_width, 3, 0)  # Left column
    messages_win = curses.newwin(height - 6, messages_width, 3, channel_width)  # Middle column
    nodes_win = curses.newwin(height - 6, nodes_width, 3, channel_width + messages_width)  # Right column
    function_win = curses.newwin(3, width, height - 3, 0)  # Bottom row window

    draw_text_field(function_win, f"TAB = Switch Channels   ENTER = Send Message")

    # Enable scrolling for messages and nodes windows
    messages_win.scrollok(True)
    nodes_win.scrollok(True)
    channel_win.scrollok(True)

    draw_channel_list()

    # Display initial content in nodes window
    for i, node in enumerate(node_list, start=1):
        if i < height - 8   :  # Check if there is enough space in the window
            nodes_win.addstr(i, 1, node)

    # Draw boxes around windows
    channel_win.box()
    entry_win.box()
    messages_win.box()
    nodes_win.box()
    function_win.box()

    # Refresh all windows
    stdscr.refresh()
    entry_win.refresh()
    messages_win.refresh()
    nodes_win.refresh()
    channel_win.refresh()
    function_win.refresh()

    input_text = ""

    while True:
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.getch()

        if char == ord('\t'):
            if selected_channel < number_of_channels-1:
                selected_channel += 1
            else:
                selected_channel = 0

            draw_channel_list()
            channel_win.refresh()   
            
        elif char == curses.KEY_ENTER or char == 10 or char == 13:
            # Enter key pressed, send user input as message
            send_message(input_text, channel=selected_channel)

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

pub.subscribe(on_receive, 'meshtastic.receive')

if __name__ == "__main__":
    curses.wrapper(main)

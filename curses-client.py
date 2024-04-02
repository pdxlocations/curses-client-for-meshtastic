#!/usr/bin/env python3

'''
Curses Client for Meshtastic by http://github.com/pdxlocations
Powered by Meshtastic.org
V 0.1.2
'''

import curses
import meshtastic.serial_interface, meshtastic.tcp_interface
from pubsub import pub
from meshtastic import config_pb2, BROADCAST_NUM
import textwrap  # Import the textwrap module

from settings import settings

# Initialize Meshtastic interface
interface = meshtastic.serial_interface.SerialInterface()
# interface = meshtastic.tcp_interface.TCPInterface(hostname='192.168.xx.xx')

myinfo = interface.getMyNodeInfo()

myNodeNum = myinfo['num']
all_messages = {}
channel_list = []
selected_channel = 0
selected_node = 0
direct_message = False

def get_channels():
    global channel_list

    node = interface.getNode('^local')
    device_channels = node.channels

    channel_output = []
    for device_channel in device_channels:
        if device_channel.role:
            if device_channel.settings.name:
                channel_output.append(device_channel.settings.name)
                all_messages[device_channel.settings.name] = []

            else:
                # If channel name is blank, use the modem preset
                lora_config = node.localConfig.lora
                modem_preset_enum = lora_config.modem_preset
                modem_preset_string = config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[modem_preset_enum].name
                channel_output.append(convert_to_camel_case(modem_preset_string))
                all_messages[convert_to_camel_case(modem_preset_string)] = []

    channel_list = list(all_messages.keys())

def get_node_list():
    node_list = []
    if interface.nodes:
        for node in interface.nodes.values():
            node_list.append(node['num'])
    return node_list

def decimal_to_hex(decimal_number):
    return f"!{decimal_number:08x}"

def convert_to_camel_case(string):
    words = string.split('_')
    camel_case_string = ''.join(word.capitalize() for word in words)
    return camel_case_string

def get_name_from_number(number, type='long'):
    name = ""
    for node in interface.nodes.values():
        if number == node['num']:
            if type == 'long':
                name = node['user']['longName']
                return name
            elif type == 'short':
                name = node['user']['shortName']
                return name
            else:
                pass
        else:
            name =  str(decimal_to_hex(number))  # If long name not found, use the ID as string
    return name
        

def on_receive(packet, interface):
    global all_messages, selected_channel, channel_list
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'NODEINFO_APP':
            get_node_list()
            draw_node_list()

        elif 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
            if packet.get('channel'):
                channel_number = packet['channel']
            else:
                channel_number = 0

            if packet['to'] == myNodeNum:
                if packet['from'] in channel_list:
                    pass
                else:
                    channel_list.append(packet['from'])
                    all_messages[packet['from']] = []
                    draw_channel_list()

                channel_number = channel_list.index(packet['from'])

            if channel_list[channel_number] != channel_list[selected_channel]:
                add_notification(channel_number)

            # Add received message to the messages list
            message_from_id = packet['from']
            message_from_string = ""
            for node in interface.nodes.values():
                if message_from_id == node['num']:
                    message_from_string = node["user"]["longName"]  # Get the long name using the node ID
                    break
                else:
                    message_from_string = str(decimal_to_hex(message_from_id))  # If long name not found, use the ID as string
        
            if channel_list[channel_number] in all_messages:
                all_messages[channel_list[channel_number]].append((f">> {message_from_string} ", message_string))
            else:
                all_messages[channel_list[channel_number]] = [(f">> {message_from_string} ", message_string)]
                draw_channel_list()
            update_messages_window()

    except KeyError as e:
        print(f"Error processing packet: {e}")


def send_message(message, destination=BROADCAST_NUM, channel=0):
    global all_messages, channel_list
    
    # FIXME if sending a DM, always send on channel 0
    send_on_channel = 0
    if isinstance(channel_list[channel], int):
        send_on_channel = 0
        destination = channel_list[channel]
    elif isinstance(channel_list[channel], str):
        send_on_channel = channel

    interface.sendText(
        text=message,
        destinationId=destination,
        wantAck=False,
        wantResponse=False,
        onResponse=None,
        channelIndex=send_on_channel,
    )

    # Add sent message to the messages dictionary
    if channel_list[channel] in all_messages:
        all_messages[channel_list[channel]].append((">> Sent: ", message))
    else:
        all_messages[channel_list[channel]] = [(">> Sent: ", message)]

    update_messages_window()
    messages_win.refresh()

def add_notification(channel_number):
    global channel_win
    _, win_width = channel_win.getmaxyx()  # Get the width of the channel window

    if isinstance(channel_list[channel_number], str):
        channel_name = channel_list[channel_number]
    elif isinstance(channel_list[channel_number], int):
        channel_name = get_name_from_number(channel_list[channel_number])

    # Truncate the channel name if it's too long to fit in the window
    truncated_channel_name = channel_name[:win_width - 5] + '-' if len(channel_name) > win_width - 5 else channel_name

    channel_win.addstr(channel_number + 1, len(str(truncated_channel_name))+1, " *", curses.color_pair(4))
    channel_win.refresh()

def remove_notification(channel_number):
    global channel_win
    _, win_width = channel_win.getmaxyx()  # Get the width of the channel window

    if isinstance(channel_list[channel_number], str):
        channel_name = channel_list[channel_number]
    elif isinstance(channel_list[channel_number], int):
        channel_name = get_name_from_number(channel_list[channel_number])

    # Truncate the channel name if it's too long to fit in the window
    truncated_channel_name = channel_name[:win_width - 5] + '-' if len(channel_name) > win_width - 5 else channel_name

    channel_win.addstr(channel_number + 1, len(str(truncated_channel_name))+1, "  ", curses.color_pair(4))
    channel_win.refresh()

def update_messages_window():
    global all_messages, selected_channel, messages_win

    messages_win.clear()

    # Calculate how many messages can fit in the window
    max_messages = messages_win.getmaxyx()[0] - 2  # Subtract 2 for the top and bottom border

    # Determine the starting index for displaying messages
    if channel_list[selected_channel] in all_messages:
        start_index = max(0, len(all_messages[channel_list[selected_channel]]) - max_messages)
    else:
        # Handle the case where selected_channel does not exist
        start_index = 0  # Set start_index to 0 or any other appropriate value

    # Display messages starting from the calculated start index
    # Check if selected_channel exists in all_messages before accessing it
    if channel_list[selected_channel] in all_messages:
        row = 1
        for _, (prefix, message) in enumerate(all_messages[channel_list[selected_channel]][start_index:], start=1):
            full_message = f"{prefix}{message}"
            wrapped_messages = textwrap.wrap(full_message, messages_win.getmaxyx()[1] - 2)

            for wrapped_message in wrapped_messages:
                messages_win.addstr(row, 1, wrapped_message, curses.color_pair(1) if prefix.startswith(">> Sent:") else curses.color_pair(2))
                row += 1

    messages_win.box()
    messages_win.refresh()



def draw_text_field(win, text):
    win.clear()
    win.border()
    win.addstr(1, 1, text)


def draw_channel_list():
    global direct_message

    # Get the dimensions of the channel window
    _, win_width = channel_win.getmaxyx()

    for i, (channel, message_list) in enumerate(all_messages.items()):
        # Convert node number to long name if it's an integer
        if isinstance(channel, int):
            channel = get_name_from_number(channel, type='long')

        # Truncate the channel name if it's too long to fit in the window
        truncated_channel = channel[:win_width - 5] + '-' if len(channel) > win_width - 5 else channel

        if selected_channel == i and not direct_message:
            channel_win.addstr(i + 1, 1, truncated_channel, curses.color_pair(3))
            remove_notification(selected_channel)
        else:
            channel_win.addstr(i + 1, 1, truncated_channel, curses.color_pair(4))

    channel_win.refresh()


def draw_node_list():
    global selected_node, direct_message
    nodes_win.clear()                 
    height, width = nodes_win.getmaxyx()
    start_index = max(0, selected_node - (height - 3))  # Calculate starting index based on selected node and window height

    for i, node in enumerate(get_node_list()[start_index:], start=1):

        if i < height - 1   :  # Check if there is enough space in the window
            if selected_node + 1 == start_index + i and direct_message:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(3))
            else:
                nodes_win.addstr(i, 1, get_name_from_number(node, "long"), curses.color_pair(4))

    nodes_win.box()
    nodes_win.refresh()



def draw_debug(value):
    function_win.addstr(1, 100, f"debug: {value}    ")
    function_win.refresh()

def select_channels(direction):
    global selected_channel
    channel_list_length = len(channel_list)

    selected_channel += direction

    if selected_channel < 0:
        selected_channel = channel_list_length - 1
    elif selected_channel >= channel_list_length:
        selected_channel = 0

    draw_channel_list()
    update_messages_window()

def select_nodes(direction):
    global selected_node
    node_list_length = len(get_node_list())

    selected_node += direction

    if selected_node < 0:
        selected_node = node_list_length - 1
    elif selected_node >= node_list_length:
        selected_node = 0

    draw_node_list()



def main(stdscr):
    global messages_win, nodes_win, channel_win, function_win, selected_node, selected_channel, direct_message

    stdscr.keypad(True)

    # Initialize colors
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    # Calculate window max dimensions
    height, width = stdscr.getmaxyx()

    # Define window dimensions and positions
    entry_win = curses.newwin(3, width, 0, 0)
    channel_width = 3 * (width // 16)
    nodes_width = 5 * (width // 16)
    messages_width = width - channel_width - nodes_width

    channel_win = curses.newwin(height - 6, channel_width, 3, 0)
    messages_win = curses.newwin(height - 6, messages_width, 3, channel_width)
    nodes_win = curses.newwin(height - 6, nodes_width, 3, channel_width + messages_width)
    function_win = curses.newwin(3, width, height - 3, 0)

    draw_text_field(function_win, f"↑↓ = Switch Channels   ← → = Channels/Nodes   ENTER = Send / Select DM    ESC = Quit  ` = Settings")

    # Enable scrolling for messages and nodes windows
    messages_win.scrollok(True)
    nodes_win.scrollok(True)
    channel_win.scrollok(True)

    get_channels()
    channel_win.refresh()
    draw_channel_list()
    draw_node_list()

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
    direct_message = False

    entry_win.keypad(True)

    while True:
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.getch()

        # draw_debug(f"Keypress: {char}")

        if char == curses.KEY_UP:
            if direct_message:
                draw_channel_list()
                select_nodes(-1)
            else:
                select_channels(-1)
        elif char == curses.KEY_DOWN:
            if direct_message:
                draw_channel_list()
                select_nodes(1)
            else:
                select_channels(1)
            
        elif char == curses.KEY_LEFT:
            if direct_message == False:
                pass
            else:
                direct_message = False
                draw_channel_list()
                draw_node_list()

        elif char == curses.KEY_RIGHT:
            if direct_message == False:
                direct_message = True
                draw_channel_list()
                draw_node_list()
            else:
                pass

        # Check for Esc
        elif char == 27:
            break
            
        elif char == curses.KEY_ENTER or char == 10 or char == 13:
            if direct_message:
                node_list = get_node_list()
                if node_list[selected_node] not in channel_list:
                    channel_list.append(node_list[selected_node])
                    all_messages[node_list[selected_node]] = []

                selected_channel = channel_list.index(node_list[selected_node])
                selected_node = 0
                direct_message = False
                draw_node_list()
                draw_channel_list()
                update_messages_window()

            else:
                # Enter key pressed, send user input as message
                send_message(input_text, channel=selected_channel)

                # Clear entry window and reset input text
                input_text = ""
                entry_win.clear()       
                entry_win.refresh()

        elif char == curses.KEY_BACKSPACE or char == 127:
            input_text = input_text[:-1]
            
        elif char == 96:
            curses.curs_set(0)  # Hide cursor
            settings(stdscr, interface)
            curses.curs_set(1)  # Show cursor again
            
        else:
            # Append typed character to input text
            input_text += chr(char)

        # draw_debug(char)
pub.subscribe(on_receive, 'meshtastic.receive')

if __name__ == "__main__":
    curses.wrapper(main)
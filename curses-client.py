#!/usr/bin/env python3

import curses
import meshtastic.serial_interface
from pubsub import pub
from meshtastic import config_pb2, BROADCAST_NUM

# Initialize Meshtastic interface
interface = meshtastic.serial_interface.SerialInterface()

myinfo = interface.getMyNodeInfo()

myNodeNum = myinfo['num']
all_messages = {}
is_dm = False
selected_channel = 0

def get_node_list():
    node_list = []
    if interface.nodes:
        for node in interface.nodes.values():
            node_list.append(node["user"]["longName"])
    return node_list

def decimal_to_hex(decimal_number):
    return f"!{decimal_number:08x}"

def convert_to_camel_case(string):
    words = string.split('_')
    camel_case_string = ''.join(word.capitalize() for word in words)
    return camel_case_string

def get_number_of_channels():
    node = interface.getNode('^local')
    device_channels = node.channels
    number_of_channels = 0
    for device_channel in device_channels:
        if device_channel.role:
            number_of_channels += 1
    return number_of_channels 

def get_channel_name(channel_num):
    channel_name = ""
    node = interface.getNode('^local')
    device_channels = node.channels

    if device_channels[channel_num].settings.name:
        channel_name = device_channels[channel_num].settings.name
    else:
        # If channel name is blank, use the modem preset
        lora_config = node.localConfig.lora
        modem_preset_enum = lora_config.modem_preset
        modem_preset_string = config_pb2._CONFIG_LORACONFIG_MODEMPRESET.values_by_number[modem_preset_enum].name
        channel_name = convert_to_camel_case(modem_preset_string)
    
    return channel_name



def on_receive(packet, interface):
    global all_messages, selected_channel
    try:
        if 'decoded' in packet and packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
            if packet.get('channel'):
                channel_number = packet['channel']
            else:
                channel_number = 0

            if packet['to'] == myNodeNum:
                draw_debug(f"is dm on ch:{channel_number}")
                is_dm = True


            if channel_number != selected_channel:
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

            if channel_number in all_messages:
                all_messages[channel_number].append((f">> {message_from_string} ", message_string))
            else:
                all_messages[channel_number] = [(f">> {message_from_string} ", message_string)]

            update_messages_window()
    except KeyError as e:
        print(f"Error processing packet: {e}")

def send_message(message, destination=BROADCAST_NUM, channel=0):
    global all_messages, selected_channel

    interface.sendText(
        text=message,
        destinationId=destination,
        wantAck=False,
        wantResponse=False,
        onResponse=None,
        channelIndex=channel,
    )

    # Add sent message to the messages dictionary
    if selected_channel in all_messages:
        all_messages[selected_channel].append((">> Sent: ", message))
    else:
        all_messages[selected_channel] = [(">> Sent: ", message)]


    update_messages_window()
    messages_win.refresh()

def add_notification(channel_number):
    channel_win.addstr(channel_number+1, len(get_channel_name(channel_number))+1, " *", curses.color_pair(4))
    channel_win.refresh()

def remove_notification(channel_number):
    channel_win.addstr(channel_number+1, len(get_channel_name(channel_number))+1, "  ", curses.color_pair(4))
    channel_win.refresh()

def update_messages_window():
    global all_messages, selected_channel

    messages_win.clear()

    # Calculate how many messages can fit in the window
    max_messages = messages_win.getmaxyx()[0] - 2  # Subtract 2 for the top and bottom border

    # Determine the starting index for displaying messages
    if selected_channel in all_messages:
        start_index = max(0, len(all_messages[selected_channel]) - max_messages)
    else:
        # Handle the case where selected_channel does not exist
        start_index = 0  # Set start_index to 0 or any other appropriate value


    # Display messages starting from the calculated start index
    # Check if selected_channel exists in all_messages before accessing it
    if selected_channel in all_messages:
        for row, (prefix, message) in enumerate(all_messages[selected_channel][start_index:], start=1):
            messages_win.addstr(row, 1, prefix, curses.color_pair(1) if prefix.startswith(">> Sent:") else curses.color_pair(2))
            messages_win.addstr(row, len(prefix) + 1, message + '\n')
    else:
        # Handle the case where selected_channel does not exist
        pass

    messages_win.box()
    messages_win.refresh()

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
            remove_notification(selected_channel)
        else:
            channel_win.addstr(i+1, 1, channel, curses.color_pair(4))

def draw_node_list(height):
    for i, node in enumerate(get_node_list(), start=1):
        if i < height - 8   :  # Check if there is enough space in the window
            nodes_win.addstr(i, 1, node)

def draw_debug(value):
    function_win.addstr(1, 70, f"debug: {value}    ")
    function_win.refresh()
    

def main(stdscr):
    global messages_win, nodes_win, channel_win, selected_channel, function_win

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
    channel_width = width // 8
    messages_width = 4 * (width // 8)
    nodes_width = 3 * (width // 8)

    channel_win = curses.newwin(height - 6, channel_width, 3, 0)
    messages_win = curses.newwin(height - 6, messages_width, 3, channel_width)
    nodes_win = curses.newwin(height - 6, nodes_width, 3, channel_width + messages_width)
    function_win = curses.newwin(3, width, height - 3, 0)

    draw_text_field(function_win, f"TAB = Switch Channels   ENTER = Send Message   ESC = Quit")

    # Enable scrolling for messages and nodes windows
    messages_win.scrollok(True)
    nodes_win.scrollok(True)
    channel_win.scrollok(True)

    draw_channel_list()
    draw_node_list(height)


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

    while True:
        draw_text_field(entry_win, f"Input: {input_text}")

        # Get user input from entry window
        entry_win.move(1, len(input_text) + 8)
        char = entry_win.getch()

        draw_debug(str(char))

        # Check for Esc
        if char == 27:
            break
            
        # Check for Ctrl-D
        elif char == 4:
            if direct_message == False:
                direct_message = True
            else:
                direct_message = False
            draw_debug(f"dm = {direct_message}")

        # Check for Tab
        elif char == ord('\t'):
            if selected_channel < number_of_channels-1:
                selected_channel += 1
            else:
                selected_channel = 0

            draw_channel_list()
            channel_win.refresh()  
            update_messages_window()
            
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

from meshtastic import BROADCAST_NUM
from utilities.utils import get_node_list, decimal_to_hex, get_name_from_number
import globals
from ui.curses_ui import draw_packetlog_win, draw_node_list, draw_messages_window, draw_channel_list, add_notification
from db_handler import save_message_to_db, maybe_store_nodeinfo_in_db
import time
import default_config as config


from datetime import datetime

def on_receive(packet, interface):
    global nodes_win

    # Update packet log
    globals.packet_buffer.append(packet)
    if len(globals.packet_buffer) > 20:
        # Trim buffer to 20 packets
        globals.packet_buffer = globals.packet_buffer[-20:]
        
    if globals.display_log:
        draw_packetlog_win()
    try:
        if 'decoded' not in packet:
            return

        # Assume any incoming packet could update the last seen time for a node
        new_node_list = get_node_list()
        if new_node_list != globals.node_list:
            globals.node_list = new_node_list
            draw_node_list()

        if packet['decoded']['portnum'] == 'NODEINFO_APP':
            if "user" in packet['decoded'] and "longName" in packet['decoded']["user"]: 
                maybe_store_nodeinfo_in_db(packet)

        elif packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')

            refresh_channels = False
            refresh_messages = False

            if packet.get('channel'):
                channel_number = packet['channel']
            else:
                channel_number = 0

            if packet['to'] == globals.myNodeNum:
                if packet['from'] in globals.channel_list:
                    pass
                else:
                    globals.channel_list.append(packet['from'])
                    globals.all_messages[packet['from']] = []
                    refresh_channels = True

                channel_number = globals.channel_list.index(packet['from'])

            if globals.channel_list[channel_number] != globals.channel_list[globals.selected_channel]:
                add_notification(channel_number)
                refresh_channels = True
            else:
                refresh_messages = True

            # Add received message to the messages list
            message_from_id = packet['from']
            message_from_string = get_name_from_number(message_from_id, type='short') + ":"

            if globals.channel_list[channel_number] not in globals.all_messages:
                globals.all_messages[globals.channel_list[channel_number]] = []

            # Timestamp handling
            current_timestamp = time.time() 
            current_hour = datetime.fromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:00')

            # Retrieve the last timestamp if available
            channel_messages = globals.all_messages[globals.channel_list[channel_number]]
            if channel_messages:
                # Check the last entry for a timestamp
                for entry in reversed(channel_messages):
                    if entry[0].startswith("--"):
                        last_hour = entry[0].strip("- ").strip()
                        break
                else:
                    last_hour = None
            else:
                last_hour = None

            # Add a new timestamp if it's a new hour
            if last_hour != current_hour:
                globals.all_messages[globals.channel_list[channel_number]].append((f"-- {current_hour} --", ""))

            globals.all_messages[globals.channel_list[channel_number]].append((f"{config.message_prefix} {message_from_string} ", message_string))

            if refresh_channels:
                draw_channel_list()
            if refresh_messages:
                draw_messages_window(True)

            save_message_to_db(globals.channel_list[channel_number], message_from_id, message_string)

    except KeyError as e:
        print(f"Error processing packet: {e}")
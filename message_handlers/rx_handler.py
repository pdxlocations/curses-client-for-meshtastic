from meshtastic import BROADCAST_NUM
from utilities.utils import get_node_list, decimal_to_hex, get_nodeNum
import globals
from ui.curses_ui import draw_packetlog_win, draw_node_list, draw_messages_window, draw_channel_list, add_notification
from db_handler import save_message_to_db, maybe_store_nodeinfo_in_db


def on_receive(packet, interface):
    global nodes_win

    # update packet log
    globals.packet_buffer.append(packet)
    if len(globals.packet_buffer) > 20:
        # trim buffer to 20 packets
        globals.packet_buffer = globals.packet_buffer[-20:]
        
    if globals.display_log:
        draw_packetlog_win()
    try:
        if 'decoded' not in packet:
            return

        # Assume any incoming packet could update the last seen time for a node, so we
        # may need to reorder the list. This could probably be limited to specific packets.
        globals.node_list = get_node_list()
        draw_node_list()

        if packet['decoded']['portnum'] == 'NODEINFO_APP':
            if "user" in packet['decoded'] and "longName" in packet['decoded']["user"]: 
                maybe_store_nodeinfo_in_db(packet)

        elif packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message_bytes = packet['decoded']['payload']
            message_string = message_bytes.decode('utf-8')
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
                    draw_channel_list()

                channel_number = globals.channel_list.index(packet['from'])

            if globals.channel_list[channel_number] != globals.channel_list[globals.selected_channel]:
                add_notification(channel_number)

            # Add received message to the messages list
            message_from_id = packet['from']
            message_from_string = ""
            for node in globals.interface.nodes.values():
                if message_from_id == node['num']:
                    message_from_string = node["user"]["shortName"] + ":" # Get the name using the node ID
                    break
                else:
                    message_from_string = str(decimal_to_hex(message_from_id))  # If long name not found, use the ID as string
        
            if globals.channel_list[channel_number] in globals.all_messages:
                globals.all_messages[globals.channel_list[channel_number]].append((f"{globals.message_prefix} {message_from_string} ", message_string))
            else:
                globals.all_messages[globals.channel_list[channel_number]] = [(f"{globals.message_prefix} {message_from_string} ", message_string)]

            draw_channel_list()
            draw_messages_window()
            save_message_to_db(globals.channel_list[channel_number], message_from_id, message_string)

    except KeyError as e:
        print(f"Error processing packet: {e}")


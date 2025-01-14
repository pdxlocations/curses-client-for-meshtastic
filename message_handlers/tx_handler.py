from meshtastic import BROADCAST_NUM
from db_handler import save_message_to_db
from utilities.utils import get_nodeNum
import globals

ack_naks = {}

# Note "onAckNak" has special meaning to the API, thus the nonstandard naming convention
# See https://github.com/meshtastic/python/blob/master/meshtastic/mesh_interface.py#L462
def onAckNak(packet):
    from ui.curses_ui import draw_messages_window
    request = packet['decoded']['requestId']
    if(request not in ack_naks):
        return

    acknak = ack_naks.pop(request)
    message = globals.all_messages[acknak['channel']][acknak['messageIndex']][1]

    confirm_string = " "
    if(packet['decoded']['routing']['errorReason'] == "NONE"):
        if(packet['from'] == get_nodeNum()): # Ack "from" ourself means implicit ACK
            confirm_string = "[◌]"
        else:
            confirm_string = "[✓]"
    else:
        confirm_string = "[x]"

    globals.all_messages[acknak['channel']][acknak['messageIndex']] = (globals.sent_message_prefix + confirm_string + ": ", message)

    draw_messages_window()

def send_message(message, destination=BROADCAST_NUM, channel=0):

    myid = get_nodeNum()
    send_on_channel = 0
    channel_id = globals.channel_list[channel]
    if isinstance(channel_id, int):
        send_on_channel = 0
        destination = channel_id
    elif isinstance(channel_id, str):
        send_on_channel = channel

    sent_message_data = globals.interface.sendText(
        text=message,
        destinationId=destination,
        wantAck=True,
        wantResponse=False,
        onResponse=onAckNak,
        channelIndex=send_on_channel,
    )

    # Add sent message to the messages dictionary
    if channel_id in globals.all_messages:
        globals.all_messages[channel_id].append((globals.sent_message_prefix + "[…]: ", message))
    else:
        globals.all_messages[channel_id] = [(globals.sent_message_prefix + "[…]: ", message)]

    ack_naks[sent_message_data.id] = {'channel' : channel_id, 'messageIndex' : len(globals.all_messages[channel_id]) - 1 }


    save_message_to_db(channel_id, myid, message)

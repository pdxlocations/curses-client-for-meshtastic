from meshtastic import BROADCAST_NUM
from database import save_message_to_db
from utilities.utils import get_nodeNum
import globals


def send_message(message, destination=BROADCAST_NUM, channel=0):

    myid = get_nodeNum()
    send_on_channel = 0
    if isinstance(globals.channel_list[channel], int):
        send_on_channel = 0
        destination = globals.channel_list[channel]
    elif isinstance(globals.channel_list[channel], str):
        send_on_channel = channel

    globals.interface.sendText(
        text=message,
        destinationId=destination,
        wantAck=False,
        wantResponse=False,
        onResponse=None,
        channelIndex=send_on_channel,
    )

    # Add sent message to the messages dictionary
    if globals.channel_list[channel] in globals.all_messages:
        globals.all_messages[globals.channel_list[channel]].append((globals.sent_message_prefix + " ", message))
    else:
        globals.all_messages[globals.channel_list[channel]] = [(globals.sent_message_prefix + " ", message)]

    save_message_to_db(globals.channel_list[channel], myid, message)
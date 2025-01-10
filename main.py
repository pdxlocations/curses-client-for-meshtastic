#!/usr/bin/env python3

'''
Curses Client for Meshtastic by http://github.com/pdxlocations
Powered by Meshtastic.org
V 0.2.0
'''

import curses
from pubsub import pub

from utilities.arg_parser import setup_parser
from utilities.interfaces import initialize_interface
from message_handlers.rx_handler import on_receive
from ui.curses_ui import main_ui
from utilities.utils import get_channels
from database import initialize_database
import globals

if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    globals.interface = initialize_interface(args)
    globals.channel_list = get_channels()
    initialize_database()
    pub.subscribe(on_receive, 'meshtastic.receive')
    curses.wrapper(main_ui)
#!/usr/bin/env python3

'''
Curses Client for Meshtastic by http://github.com/pdxlocations
Powered by Meshtastic.org
V 0.2.0
'''

import curses
from pubsub import pub

from parsers import setup_parser
from interfaces import initialize_interface
from rx_handlers import on_receive
from curses_ui import main_ui
from utils import get_channels
import globals

if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    globals.interface = initialize_interface(args)
    globals.channel_list = get_channels()
    pub.subscribe(on_receive, 'meshtastic.receive')
    curses.wrapper(main_ui)
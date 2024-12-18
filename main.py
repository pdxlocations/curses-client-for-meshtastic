#!/usr/bin/env python3

'''
Curses Client for Meshtastic by http://github.com/pdxlocations
Powered by Meshtastic.org
V 0.1.8
'''

import curses
from pubsub import pub

import meshtastic.serial_interface, meshtastic.tcp_interface, meshtastic.ble_interface

from parsers import setup_parser
from interfaces import initialize_interface
from utils import get_channels, get_node_list, get_name_from_number, get_nodeNum
from handlers import on_receive
from curses_ui import main_ui
import globals




if __name__ == "__main__":
    parser = setup_parser()
    args = parser.parse_args()
    interface = initialize_interface(args)

    globals.myNodeNum = get_nodeNum(globals.interface)
    get_channels()
    pub.subscribe(on_receive, 'meshtastic.receive')
    curses.wrapper(main_ui)
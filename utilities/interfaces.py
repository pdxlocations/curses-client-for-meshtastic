import logging
import meshtastic.serial_interface, meshtastic.tcp_interface, meshtastic.ble_interface
import globals

def initialize_interface(args):
    if args.ble:
        return meshtastic.ble_interface.BLEInterface(args.ble if args.ble != "any" else None)
    elif args.host:
        return meshtastic.tcp_interface.TCPInterface(args.host)
    else:
        try:
            return meshtastic.serial_interface.SerialInterface(args.port)
        except PermissionError as ex:
            logging.error("You probably need to add yourself to the `dialout` group to use a serial connection.")
        if globals.interface.devPath is None:
            return meshtastic.tcp_interface.TCPInterface("meshtastic.local")
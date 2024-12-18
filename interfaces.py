import meshtastic.serial_interface
import meshtastic.tcp_interface
import meshtastic.ble_interface
import globals

def initialize_interface(args):
    if args.ble:
        globals.interface = meshtastic.ble_interface.BLEInterface(args.ble if args.ble != "any" else None)
    elif args.host:
        globals.interface = meshtastic.tcp_interface.TCPInterface(args.host)
    else:
        try:
            globals.interface = meshtastic.serial_interface.SerialInterface(args.port)
        except PermissionError as ex:
            print("You probably need to add yourself to the `dialout` group to use a serial connection.")
        if globals.interface.devPath is None:
            globals.interface = meshtastic.tcp_interface.TCPInterface("meshtastic.local")


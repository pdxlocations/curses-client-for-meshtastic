import logging
from pubsub import pub
import meshtastic.serial_interface, meshtastic.tcp_interface, meshtastic.ble_interface
import globals

def on_connection(interface, topic=pub.AUTO_TOPIC) -> None:  # pylint: disable=W0613
    """Callback invoked when we connect/disconnect from a radio"""
    logging.info(f"Connection changed: {topic.getName()}")

def initialize_interface(args):
    try:
        if args.ble:
            return meshtastic.ble_interface.BLEInterface(args.ble if args.ble != "any" else None)
        elif args.host:
            return meshtastic.tcp_interface.TCPInterface(args.host)
        else:
            try:
                return meshtastic.serial_interface.SerialInterface(args.port)
            except PermissionError as ex:
                logging.error(f"You probably need to add yourself to the `dialout` group to use a serial connection. {ex}")
            except Exception as ex:
                logging.error(f"Unexpected error initializing interface: {ex}")
            if globals.interface.devPath is None:
                return meshtastic.tcp_interface.TCPInterface("meshtastic.local")
    
    except Exception as ex:
        logging.critical(f"Fatal error initializing interface: {ex}")
    
import meshtastic.serial_interface
import base64

# Initialize Meshtastic interface
interface = meshtastic.serial_interface.SerialInterface()

# Get node information
node = interface.getNode('^local')
channels = node.channels
print (channels)
if channels:
    print("Channels:")
    for channel in channels:
        if channel.role:
            psk_base64 = base64.b64encode(channel.settings.psk).decode('utf-8')
            print(f"Index: {channel.index}, Role: {channel.role}, PSK (Base64): {psk_base64}, Name: {channel.settings.name}")
else:
    print("No channels found.")


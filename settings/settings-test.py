import meshtastic.serial_interface
import time

# Define the configuration dictionary
configurations = {
    "device": {
        "role": "CLIENT_MUTE",
        "node_info_broadcast_secs": 10801,
        "serial_enabled": False
    }
}

# Initialize the Meshtastic serial interface
interface = meshtastic.serial_interface.SerialInterface()
ourNode = interface.getNode('^local')

# Get the single config from the configurations dictionary
for config, params in configurations.items():
    if hasattr(ourNode.localConfig, config):  # Check if the config exists
        config_config = getattr(ourNode.localConfig, config)
        for param, value in params.items():
            if hasattr(config_config, param):  # Check if the parameter exists in the config
                setattr(config_config, param, value)  # Set the value dynamically
            else:
                print(f"Parameter '{param}' not found in config '{config}'")
        
        ourNode.writeConfig(config)  # Pass the config name as the config_name argument  

        # Write the updated configuration for the current config
        print(f"Updated and wrote configuration for config: {config}")
    else:
        print(f"config '{config}' not found in localConfig")


print("Configuration updated successfully")

# Keep the script running
while True:
    time.sleep(1)
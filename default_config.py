import os
import json


def initialize_config():
    app_directory = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(app_directory, "config.json")

    # Default configuration variables
    default_config_variables = {
        "db_file_path": os.path.join(app_directory, "client.db"),
        "log_file_path": os.path.join(app_directory, "client.log"),
        "message_prefix": ">>",
        "sent_message_prefix": ">> Sent",
        "notification_symbol": "*",
        "ack_implicit_str": "[◌]",
        "ack_str": "[✓]",
        "nak_str": "[x]",
        "ack_unknown_str": "[…]",
        "COLOR_CONFIG": {
            "default": ["white", "black"],
            "splash_logo": ["green", "black"],
            "splash_text": ["white", "black"],
            "input": ["white", "black"],
            "node_list": ["white", "black"],
            "channel_list": ["white", "black"],
            "channel_selected": ["green", "black"],
            "rx_messages": ["cyan", "black"],
            "tx_messages": ["green", "black"],
            "timestamps": ["white", "black"],
            "commands": ["white", "black"],
            "window_frame": ["white", "black"],
            "window_frame_selected": ["green", "black"],
            "log_header": ["blue", "black"],
            "log": ["green", "black"],
        },
    }

    # Step 1: Check if the JSON file exists; if not, create it
    if not os.path.exists(json_file_path):
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(default_config_variables, json_file, indent=4, ensure_ascii=False)
        print(f"JSON file created at {json_file_path} with default variables.")

    # Step 2: Ensure all default variables exist in the JSON file
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        loaded_config = json.load(json_file)

    # Check and add missing variables
    updated = False
    for key, value in default_config_variables.items():
        if key not in loaded_config:
            loaded_config[key] = value
            updated = True

    # Update the JSON file if any variables were missing
    if updated:
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(loaded_config, json_file, indent=4, ensure_ascii=False)
        print(f"JSON file updated with missing default variables.")

    return loaded_config


# Call the function when the script is imported
loaded_config = initialize_config()

# Assign values to local variables
db_file_path = loaded_config["db_file_path"]
log_file_path = loaded_config["log_file_path"]
message_prefix = loaded_config["message_prefix"]
sent_message_prefix = loaded_config["sent_message_prefix"]
notification_symbol = loaded_config["notification_symbol"]
ack_implicit_str = loaded_config["ack_implicit_str"]
ack_str = loaded_config["ack_str"]
nak_str = loaded_config["nak_str"]
ack_unknown_str = loaded_config["ack_unknown_str"]
COLOR_CONFIG = loaded_config["COLOR_CONFIG"]

# Example of using the loaded variables
if __name__ == "__main__":
    print("\nLoaded Configuration:")
    print(f"Database File Path: {db_file_path}")
    print(f"Log File Path: {log_file_path}")
    print(f"Message Prefix: {message_prefix}")
    print(f"Sent Message Prefix: {sent_message_prefix}")
    print(f"Notification Symbol: {notification_symbol}")
    print(f"ACK Implicit String: {ack_implicit_str}")
    print(f"ACK String: {ack_str}")
    print(f"NAK String: {nak_str}")
    print(f"ACK Unknown String: {ack_unknown_str}")
    print(f"Color Config: {COLOR_CONFIG}")

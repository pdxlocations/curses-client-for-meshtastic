import os
import json
import logging

def format_json_single_line_arrays(data, indent=4):
    """
    Formats JSON with arrays on a single line while keeping other elements properly indented.
    """
    def format_value(value, current_indent):
        if isinstance(value, dict):
            items = []
            for key, val in value.items():
                items.append(
                    f'{" " * current_indent}"{key}": {format_value(val, current_indent + indent)}'
                )
            return "{\n" + ",\n".join(items) + f"\n{' ' * (current_indent - indent)}}}"
        elif isinstance(value, list):
            return f"[{', '.join(json.dumps(el, ensure_ascii=False) for el in value)}]"
        else:
            return json.dumps(value, ensure_ascii=False)

    return format_value(data, indent)

# Recursive function to check and update nested dictionaries
def update_dict(default, actual):
    updated = False
    for key, value in default.items():
        if key not in actual:
            actual[key] = value
            updated = True
        elif isinstance(value, dict):
            # Recursively check nested dictionaries
            updated = update_dict(value, actual[key]) or updated
    return updated

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
            "background": [" ", "black"],
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
            "settings_default": ["white", "black"],
            "settings_sensitive": ["red", "black"],
            "settings_save": ["green", "black"],
            "settings_breadcrumbs": ["white", "black"]
        },
    }

    if not os.path.exists(json_file_path):
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            formatted_json = format_json_single_line_arrays(default_config_variables)
            json_file.write(formatted_json)

    # Ensure all default variables exist in the JSON file
    with open(json_file_path, "r", encoding="utf-8") as json_file:
        loaded_config = json.load(json_file)

    # Check and add missing variables
    updated = update_dict(default_config_variables, loaded_config)

    # Update the JSON file if any variables were missing
    if updated:
            formatted_json = format_json_single_line_arrays(loaded_config)
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json_file.write(formatted_json)
            logging.info(f"JSON file updated with missing default variables and COLOR_CONFIG items.")

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


if __name__ == "__main__":
    logging.basicConfig( # Run `tail -f client.log` in another terminal to view live
    filename="default_config.log",
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"
    )
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
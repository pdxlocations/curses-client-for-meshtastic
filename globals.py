import os

# App Variables
app_directory = os.path.dirname(os.path.abspath(__file__))
interface = None
display_log = False
all_messages = {}
channel_list = []
notifications = set()
packet_buffer = []
node_list = []
myNodeNum = 0
selected_channel = 0
selected_message = 0
selected_node = 0
current_window = 0

# User Configurable
db_file_path = os.path.join(app_directory, "client.db")
log_file_path = os.path.join(app_directory, "client.log")
message_prefix = ">>"
sent_message_prefix = message_prefix + " Sent"
notification_symbol = "*"
ack_implicit_str = "[◌]"
ack_str = "[✓]"
nak_str = "[x]"
ack_unknown_str = "[…]"

# (forground, background) white, black, red, green, yellow, blue, magenta, cyan
COLOR_CONFIG = {
    "default": ("white", "black"),
    "splash_logo": ("green", "black"),
    "splash_text": ("white", "black"),
    "input": ("white", "black"),
    "node_list": ("white", "black"),
    "channel_list": ("white", "black"),
    "channel_selected": ("green", "black"),
    "rx_messages": ("cyan", "black"),
    "tx_messages": ("green", "black"),
    "timestamps": ("white", "black"),
    "commands": ("white", "black"),
    "window_frame": ("white", "black"),
    "window_frame_selected": ("green", "black"),
    "log_header": ("blue", "black"),
    "log": ("green", "black"),
    "settings_sensitive": ("red", "black"),
    "settings_okay": ("green", "black")
}

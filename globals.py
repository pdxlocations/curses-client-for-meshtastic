import os

app_directory = os.path.dirname(os.path.abspath(__file__))
db_file_path = os.path.join(app_directory, "client.db")

all_messages = {}
channel_list = []
notifications = set()
packet_buffer = []
myNodeNum = 0
selected_channel = 0
selected_message = 0
selected_node = 0
current_window = 0
interface = None
display_log = False
message_prefix = ">>"
sent_message_prefix = message_prefix + " Sent"
notification_symbol = "*"
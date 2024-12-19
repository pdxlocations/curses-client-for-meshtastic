
class AppState:
    _instance = None  # Class-level attribute for the singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.all_messages = {}
            self.channel_list = []
            self.packet_buffer = []
            self.myNodeNum = 0
            self.selected_channel = 0
            self.selected_node = 0
            self.direct_message = False
            self.interface = None
            self.display_log = False
            self._initialized = True  # Prevent reinitialization

    def reset(self):
        """Reset the state to its initial values."""
        self.all_messages = {}
        self.channel_list = []
        self.packet_buffer = []
        self.myNodeNum = 0
        self.selected_channel = 0
        self.selected_node = 0
        self.direct_message = False
        self.interface = None
        self.display_log = False
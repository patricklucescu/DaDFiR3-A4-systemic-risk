class LogMessage:
    def __init__(self, message: str, time: float, data: list):
        self.message: str = message
        self.time = time
        self.data = data

    def set_time(self, time: str):
        self.time = time

    def set_message(self, message: str):
        self.message = message

    def set_data(self, data: str):
        self.data = data

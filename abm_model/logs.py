

class LogMessage:
    """
    | LogMessage class represents a log message with a message, time, and data.
    """
    def __init__(self, message: str, time: float, data: list):
        """
        | Initializes a LogMessage object with the specified message, time, and data.

        :param message: A string representing the log message.
        :param time: A float representing the time when the log message was created.
        :param data: A list representing additional data associated with the log message.
        """
        self.message: str = message
        self.time = time
        self.data = data

    def set_time(self, time: str):
        """
        | Sets the time attribute of the LogMessage.

        :param time: A float representing the time to be set.
        """
        self.time = time

    def set_message(self, message: str):
        """
        | Sets the message attribute of the LogMessage.

        :param message: A string representing the message to be set.
        """
        self.message = message

    def set_data(self, data: str):
        """
        | Sets the data attribute of the LogMessage.

        :param data: A list representing the data to be set.
        """
        self.data = data

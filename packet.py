from enum import IntEnum


class Priority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2


class Packet:
    def __init__(self, enter_time: float, process_time: float, priority: Priority):
        self.enter_time = enter_time
        self.process_time = process_time
        self.priority = priority
        self.processor_index = None
        self.start_time = None
        self.dropped = False

    @property
    def end_time(self):
        return self.start_time + self.process_time

    @property
    def has_ran(self):
        return self.start_time is not None

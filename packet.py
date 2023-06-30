from enum import IntEnum


class Packet:
    class Priority(IntEnum):
        LOW = 0
        MEDIUM = 1
        HIGH = 2

    def __init__(self, simulation_time: float, enter_time: float, process_time: float, priority: Priority):
        self.simulation_time = simulation_time
        self.enter_time = enter_time
        self.process_time = process_time
        self.priority = priority
        self.processor_index = None
        self.start_time = None
        self.dropped = False

    @property
    def end_time(self):
        assert self.has_started, 'packet is not started yet!'
        return self.start_time + self.process_time

    @property
    def waiting_time(self):
        return (self.start_time or self.simulation_time) - self.enter_time

    def __str__(self):
        return f'({self.priority}): {self.enter_time}, {self.process_time}'

    @property
    def has_started(self):
        return self.start_time is not None

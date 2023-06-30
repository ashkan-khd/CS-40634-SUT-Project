import abc
from enum import Enum
from typing import TYPE_CHECKING, List, Dict

if TYPE_CHECKING:
    from packet import Packet


class QueueObserver(abc.ABC):
    class Type(Enum):
        ADD_QUEUE = 'add'
        POP_QUEUE = 'pop'

    @abc.abstractmethod
    def update(self, observation_type: Type, **update):
        pass


class QueueHistoryObserver(QueueObserver):
    def __init__(self):
        self._history_of_packets: List['Packet'] = []

    def update(self, observation_type: QueueObserver.Type, **update):
        if observation_type != self.Type.ADD_QUEUE:
            return
        self._history_of_packets.append(update['packet'])

    def get_all_historical_packets(self) -> List['Packet']:
        return self._history_of_packets

    def get_average_waiting_time(self) -> float:
        return sum(p.waiting_time for p in self.get_all_historical_packets()) / len(
            self.get_all_historical_packets()
        )


class QueueLengthObserver(QueueObserver):
    def __init__(self):
        self._length_to_time: Dict[int, float] = {}
        self._previous_update = 0

    def safe_add(self, length, new_delta_t: float):
        try:
            self._length_to_time[length] += new_delta_t
        except KeyError:
            self._length_to_time[length] = new_delta_t

    def _handle_add(self, current_time, new_length):
        self.safe_add(new_length - 1, current_time - self._previous_update)

    def _handle_pop(self, current_time, new_length):
        self.safe_add(new_length + 1, current_time - self._previous_update)

    def update(self, observation_type: QueueObserver.Type, **update):
        if observation_type not in [self.Type.ADD_QUEUE, self.Type.POP_QUEUE]:
            return
        current_time, new_length = update['current_time'], update['new_length']
        {
            self.Type.ADD_QUEUE: self._handle_add,
            self.Type.POP_QUEUE: self._handle_pop,
        }[observation_type](current_time, new_length)

        self._previous_update = current_time

    def get_time_weighted_length(self) -> float:
        sum_ = 0
        for length, time in self._length_to_time.items():
            sum_ += length * time
        return sum_

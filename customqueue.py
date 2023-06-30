import abc
import typing
from collections import deque

from queue_observer import QueueObserver

if typing.TYPE_CHECKING:
    from packet import Packet


class AbstractQueue(abc.ABC):
    observers: typing.List[QueueObserver]

    @abc.abstractmethod
    def add_packet(self, packet: "Packet", current_time: float) -> bool:
        """
        :param packet:
        :param current_time:
        :return: True if the packet was added, false if it was dropped
        """
        pass

    @abc.abstractmethod
    def pop(self, current_time: float) -> typing.Optional["Packet"]:
        """
        :param current_time:
        :return: "Packet" on top of the queue. None if there was no packet.
        """
        pass

    @abc.abstractmethod
    def empty(self) -> bool:
        """
        :return: Whether the queue is empty or not
        """

    @abc.abstractmethod
    def length(self) -> int:
        pass

    @abc.abstractmethod
    def register_observer(self, observers: typing.List[QueueObserver]):
        pass

    @abc.abstractmethod
    def get_all_subqueues(self) -> typing.List['AbstractQueue']:
        pass
    #
    # @abc.abstractmethod
    # def get_all_historical_packets(self) -> typing.List['Packet']:
    #     pass


class BaseQueue(AbstractQueue, abc.ABC):
    def __init__(self):
        self.observers: typing.List[QueueObserver] = []

    def register_observer(self, observers: typing.List[QueueObserver]):
        self.observers = observers

    def update_observers(self, observation_type: QueueObserver.Type, **update):
        for observer in self.observers:
            observer.update(observation_type, **update)

    def add_packet(self, packet: "Packet", current_time: float) -> bool:
        self.update_observers(
            QueueObserver.Type.ADD_QUEUE,
            packet=packet,
            current_time=current_time,
            new_length=self.length(),
        )
        return True

    def pop(self, current_time: float) -> typing.Optional["Packet"]:
        self.update_observers(
            QueueObserver.Type.POP_QUEUE,
            current_time=current_time,
            new_length=self.length(),
        )
        return None


class FIFOQueue(BaseQueue):
    def length(self) -> int:
        return len(self.q)

    def get_all_subqueues(self) -> typing.List['AbstractQueue']:
        return [self]

    def __init__(self, length_limit: int):
        super().__init__()
        self.length_limit = length_limit
        self.q: typing.Deque["Packet"] = deque()

    def add_packet(self, packet: "Packet", current_time: float) -> bool:
        if len(self.q) >= self.length_limit:
            return False
        self.q.append(packet)
        return super().add_packet(packet, current_time)

    def pop(self, current_time: float) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        super().pop(current_time)
        return self.q.popleft()

    def empty(self) -> bool:
        return len(self.q) == 0

    def __str__(self):
        return f'FIFO Queue: Size = {self.length_limit}'


class WRRQueue(BaseQueue):
    def length(self) -> int:
        return sum(q.length() for q in self.queues)

    def get_all_subqueues(self) -> typing.List['AbstractQueue']:
        return self.queues

    def __init__(self, queues: typing.List[FIFOQueue], weights: typing.List[int]):
        super().__init__()
        self.queues = queues
        self.weights = weights
        self._current_queue_index = len(queues) - 1
        self._current_queue_popped = 0

    def add_packet(self, packet: "Packet", current_time: float) -> bool:
        queue = self._get_packet_queue(packet)
        if queue.add_packet(packet, current_time):
            return super().add_packet(packet, current_time)
        return False

    def _get_packet_queue(self, packet: "Packet") -> FIFOQueue:
        return self.queues[packet.priority]

    def pop(self, current_time: float) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        while True:
            if not self.queues[self._current_queue_index].empty():
                packet = self.queues[self._current_queue_index].pop(current_time)
                self._current_queue_popped += 1
                if self._current_queue_popped == self.weights[self._current_queue_index]:
                    self._next_queue()
                super(WRRQueue, self).pop(current_time)
                return packet
            self._next_queue()

    def _next_queue(self):
        self._current_queue_index = (self._current_queue_index - 1) % len(self.queues)
        self._current_queue_popped = 0

    def empty(self) -> bool:
        return all(queue.empty() for queue in self.queues)

    def __str__(self):
        return 'Weighted Round Robin Queue: Subqueues=[{}]\t'.format(
            ''.join([f'({str(subq)}, w={self.weights[i]})' for i, subq in self.queues])
        )


class NPPSQueue(BaseQueue):
    def length(self) -> int:
        return len(self.q)

    def get_all_subqueues(self) -> typing.List['AbstractQueue']:
        return [self]

    def __init__(self, length_limit: int):
        super().__init__()
        self.length_limit = length_limit
        self.q: typing.List["Packet"] = []

    def add_packet(self, packet: "Packet", current_time: float) -> bool:
        if len(self.q) == self.length_limit:
            return False
        self.q.append(packet)
        index = len(self.q) - 1
        while index and self.q[index - 1].priority < self.q[index].priority:
            self.q[index - 1], self.q[index] = self.q[index], self.q[index - 1]
            index -= 1
        return super().add_packet(packet, current_time)

    def pop(self, current_time: float) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        super(NPPSQueue, self).pop(current_time)
        return self.q.pop(0)

    def empty(self) -> bool:
        return len(self.q) == 0

    def __str__(self):
        return f'Non-preemptive Priority Scheduling Queue: Size={self.length_limit}'

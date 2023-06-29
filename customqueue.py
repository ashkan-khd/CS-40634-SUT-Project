import abc
import typing
from collections import deque

if typing.TYPE_CHECKING:
    from packet import Packet


class AbstractQueue(abc.ABC):
    @abc.abstractmethod
    def add_packet(self, packet: "Packet") -> bool:
        """
        :param packet:
        :return: True if the packet was added, false if it was dropped
        """
        pass

    @abc.abstractmethod
    def pop(self) -> typing.Optional["Packet"]:
        """
        :return: "Packet" on top of the queue. None if there was no packet.
        """
        pass

    @abc.abstractmethod
    def empty(self) -> bool:
        """
        :return: Whether the queue is empty or not
        """


class FIFOQueue(AbstractQueue):
    def __init__(self, length_limit: int):
        super().__init__()
        self.length_limit = length_limit
        self.q: typing.Deque["Packet"] = deque()

    def add_packet(self, packet: "Packet") -> bool:
        if len(self.q) >= self.length_limit:
            return False
        self.q.append(packet)
        return True

    def pop(self) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        return self.q.popleft()

    def empty(self) -> bool:
        return len(self.q) == 0


class WRRQueue(AbstractQueue):
    def __init__(self, queues: typing.List[FIFOQueue], weights: typing.List[int]):
        self.queues = queues
        self.weights = weights
        self._current_queue_index = len(queues) - 1
        self._current_queue_popped = 0

    def add_packet(self, packet: "Packet") -> bool:
        queue = self._get_packet_queue(packet)
        return queue.add_packet(packet)

    def _get_packet_queue(self, packet: "Packet") -> FIFOQueue:
        return self.queues[packet.priority]

    def pop(self) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        while True:
            if not self.queues[self._current_queue_index].empty():
                packet = self.queues[self._current_queue_index].pop()
                self._current_queue_popped += 1
                if self._current_queue_popped == self.weights[self._current_queue_index]:
                    self._next_queue()
                return packet
            self._next_queue()

    def _next_queue(self):
        self._current_queue_index = (self._current_queue_index - 1) % len(self.queues)

    def empty(self) -> bool:
        return all(queue.empty() for queue in self.queues)


class NPPSQueue(AbstractQueue):
    def __init__(self, length_limit: int):
        self.length_limit = length_limit
        self.q: typing.List["Packet"] = []

    def add_packet(self, packet: "Packet") -> bool:
        if len(self.q) == self.length_limit:
            return False
        self.q.append(packet)
        index = len(self.q) - 1
        while index and self.q[index - 1].priority < self.q[index].priority:
            self.q[index - 1], self.q[index] = self.q[index], self.q[index - 1]
            index -= 1

    def pop(self) -> typing.Optional["Packet"]:
        if self.empty():
            return None
        return self.q.pop(0)

    def empty(self) -> bool:
        return len(self.q) == 0

import dataclasses
import heapq
import random
import typing
from enum import Enum
from packet import Packet

if typing.TYPE_CHECKING:
    from customqueue import AbstractQueue


class EventType(Enum):
    DONE = "done"
    SPAWN = "spawn"


@dataclasses.dataclass(order=True)
class Event:
    time: float
    event_type: EventType = dataclasses.field(compare=False)
    packet: Packet = dataclasses.field(compare=False)


class EventSet:
    def __init__(self):
        self.events: typing.List[Event] = []

    def add_event(self, event: Event):
        heapq.heappush(self.events, event)

    def pop(self):
        return heapq.heappop(self.events)

    def top(self):
        return self.events[0]

    def empty(self):
        return len(self.events) == 0


class Processor:
    def __init__(self):
        self.is_busy = False
        self._start_time = None
        self.account = 0

    def set_is_busy(self, current_time):
        self.is_busy = True
        self._start_time = current_time

    def reset_is_busy(self, current_time):
        self.account += current_time - self._start_time
        self.is_busy = False
        self._start_time = None


class Scheduler:
    def __init__(
        self,
        *,
        queue: "AbstractQueue",
        x: float,
        y: float,
        t: float,
        processors: int,
        priority_probs: typing.List[float]
    ):
        self.queue = queue
        self.event_set = EventSet()
        self.processors = [Processor() for _ in range(processors)]
        self.host_rate = x
        self.process_rate = y
        self.simulation_time = t
        self.priority_probs = priority_probs
        self.all_packets: typing.List[Packet] = []

    def _get_random_priority(self) -> Packet.Priority:
        return random.choices(list(Packet.Priority), weights=self.priority_probs, k=1)[0]

    def _get_process_time(self) -> float:
        return random.expovariate(self.process_rate)

    def _create_packets(self):
        current_time = 0
        while current_time < self.simulation_time:
            interval = random.expovariate(self.host_rate)
            current_time += interval
            if current_time < self.simulation_time:
                packet = Packet(
                    simulation_time=self.simulation_time,
                    enter_time=current_time,
                    priority=self._get_random_priority(),
                    process_time=self._get_process_time()
                )
                self.event_set.add_event(Event(time=packet.enter_time, event_type=EventType.SPAWN, packet=packet))
                self.all_packets.append(packet)

    def run(self):
        self._create_packets()
        current_time = 0
        while current_time < self.simulation_time and not self.event_set.empty():
            for event in self._draw_events():
                current_time = event.time
                self._apply_event(event)
            self._fill_processors(current_time)

    def _apply_event(self, event: Event):
        if event.event_type == EventType.SPAWN:
            added = self.queue.add_packet(event.packet, event.time)
            if not added:
                event.packet.dropped = True
        if event.event_type == EventType.DONE:
            self.processors[event.packet.processor_index].reset_is_busy(current_time=event.time)

    def _draw_events(self) -> typing.Iterable[Event]:
        event = self.event_set.pop()
        if event.time >= self.simulation_time:
            return
        yield event
        while not self.event_set.empty() and self.event_set.top().time == event:
            yield self.event_set.pop()

    def _fill_processors(self, current_time):
        if not self.queue.empty():
            for i, processor in enumerate(self.processors):
                if not processor.is_busy:
                    packet = self.queue.pop(current_time)
                    packet.processor_index = i
                    packet.start_time = current_time
                    processor.set_is_busy(current_time)
                    self.event_set.add_event(Event(time=packet.end_time, event_type=EventType.DONE, packet=packet))
                    if self.queue.empty():
                        break

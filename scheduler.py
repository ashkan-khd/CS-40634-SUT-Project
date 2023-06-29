import dataclasses
import heapq
import random
import typing
from enum import Enum
from packet import Packet, Priority

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


@dataclasses.dataclass
class Processor:
    is_busy: bool = dataclasses.field(default=False)


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
        self.x = x
        self.y = y
        self.t = t
        self.priority_probs = priority_probs
        self.all_packets: typing.List[Packet] = []

    def _get_random_priority(self) -> Priority:
        return random.choices(list(Priority), weights=self.priority_probs, k=1)[0]

    def _get_process_time(self) -> float:
        return random.expovariate(1 / self.y)

    def _create_packets(self):
        current_time = 0
        while current_time < self.t:
            interval = random.expovariate(self.x)
            current_time += interval
            if current_time < self.t:
                packet = Packet(
                    enter_time=current_time,
                    priority=self._get_random_priority(),
                    process_time=self._get_process_time()
                )
                self.event_set.add_event(Event(time=packet.enter_time, event_type=EventType.SPAWN, packet=packet))
                self.all_packets.append(packet)

    def run(self):
        self._create_packets()
        current_time = 0
        while current_time < self.t and not self.event_set.empty():
            for event in self._draw_events():
                current_time = event.time
                self._apply_event(event)
            self._fill_processors(current_time)

    def _apply_event(self, event: Event):
        if event.event_type == EventType.SPAWN:
            added = self.queue.add_packet(event.packet)
            if not added:
                event.packet.dropped = True
        if event.event_type == EventType.DONE:
            self.processors[event.packet.processor_index].is_busy = False

    def _draw_events(self) -> typing.Iterable[Event]:
        event = self.event_set.pop()
        if event.time >= self.t:
            return
        yield event
        while not self.event_set.empty() and self.event_set.top().time == event:
            yield self.event_set.pop()

    def _fill_processors(self, current_time):
        if not self.queue.empty():
            for i, processor in enumerate(self.processors):
                if not processor.is_busy:
                    packet = self.queue.pop()
                    packet.processor_index = i
                    packet.start_time = current_time
                    processor.is_busy = True
                    self.event_set.add_event(Event(time=packet.end_time, event_type=EventType.DONE, packet=packet))
                    if self.queue.empty():
                        break

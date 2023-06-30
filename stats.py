from functools import cached_property
from typing import TYPE_CHECKING, List, Tuple, Type

import numpy as np
from matplotlib import pyplot as plt

if TYPE_CHECKING:
    from packet import Packet
    from scheduler import Scheduler
    from customqueue import AbstractQueue
    from queue_observer import QueueObserver


class SchedulerStats:

    def __init__(self, scheduler: "Scheduler"):
        self._scheduler = scheduler

    def get_queue_observer(self, queue: 'AbstractQueue', observer_type: Type['QueueObserver']):
        for observer in queue.observers:
            if isinstance(observer, observer_type):
                return observer

    @cached_property
    def avg_queues_length(self) -> List[Tuple['AbstractQueue', float]]:
        avgs = []
        from queue_observer import QueueLengthObserver
        for subq in self._scheduler.queue.get_all_subqueues():
            observer: QueueLengthObserver = self.get_queue_observer(subq, QueueLengthObserver)
            avgs.append((subq, observer.get_time_weighted_length() / self._scheduler.simulation_time))
        return avgs

    @cached_property
    def avg_waiting_time_in_all_queues(self) -> float:
        return sum(p.waiting_time for p in self._scheduler.all_packets) / len(self._scheduler.all_packets)

    @cached_property
    def avg_witing_time_in_each_queue(self) -> List[Tuple['AbstractQueue', float]]:
        avgs = []
        from queue_observer import QueueHistoryObserver
        for subq in self._scheduler.queue.get_all_subqueues():
            observer: QueueHistoryObserver = self.get_queue_observer(subq, QueueHistoryObserver)
            avgs.append((subq, observer.get_average_waiting_time()))
        return avgs

    @cached_property
    def processors_utilization(self) -> List[float]:
        return [
            processor.account / self._scheduler.simulation_time
            for processor in self._scheduler.processors
        ]

    @cached_property
    def all_dropped_packets_count(self):
        return len([p for p in self._scheduler.all_packets if p.dropped])

    @cached_property
    def all_processed_packets_count(self):
        return len([p for p in self._scheduler.all_packets if p.has_started])

    @cached_property
    def all_ended_in_queue_packets_count(self):
        return len([p for p in self._scheduler.all_packets if not (p.has_started or p.dropped)])

    @cached_property
    def high_priority_packets_waiting_time(self) -> List[float]:
        return [
            p.waiting_time
            for p in self._scheduler.all_packets
            if p.priority == p.Priority.HIGH and not p.dropped
        ]

    def configured_log(self):
        print('Long-time-average of queue lengths')
        print('--------------------------')
        for q, L in self.avg_queues_length:
            print(f'\tL_Q for ({str(q)}): {L}')

        print(f'Average waiting time in all queues = {self.avg_waiting_time_in_all_queues}')
        print('Average waiting time in each queue:')
        print('--------------------------')
        for q, WQ in self.avg_witing_time_in_each_queue:
            print(f'\tW_Q for ({str(q)}): {WQ}')

        print('Processors utilizations')
        print('--------------------------')
        for i, rho in enumerate(self.processors_utilization):
            print(f'processor #{i + 1}: ρ = {rho}')

        print('Packets Status')
        print(f'#Dropped packets = {self.all_dropped_packets_count}')
        print(f'#Processed packets  = {self.all_processed_packets_count}')
        print(f'#Ended up in queue packets  = {self.all_ended_in_queue_packets_count}')

        count, bins_count = np.histogram(self.high_priority_packets_waiting_time, bins=10)
        pdf = count / sum(count)
        cdf = np.cumsum(pdf)
        plt.plot(bins_count[1:], cdf, label="Waiting Time CDF")
        plt.legend()
        plt.title('CDF of high-priority packets waiting time')
        plt.xlabel('waiting time (second)')
        plt.ylabel('cumulative probability')
        plt.ylim([-0.1, 1.2])
        plt.show()

"""
Search stats
"""

import collections


__all__ = [
    "Timing",
    "Profiler",
]


class Timing(object):
    def __init__(self, count=0, total_time=0.0):
        self.count = count
        self.total_time = total_time

    def add_timing(self, total_time):
        self.total_time += total_time
        self.count += 1

    @property
    def average_time(self):
        return self.total_time / self.count

    def __repr__(self):
        return "{}(count={!r}, total_time={!r})".format(
            self.__class__.__name__,
            self.count, self.total_time)


class Profiler(collections.defaultdict):
    def __init__(self):
        super().__init__(Timing)

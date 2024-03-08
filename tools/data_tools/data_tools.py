# -*- coding: utf-8 -*-

import time
from threading import Thread

import numpy as np


class CircularDataBuffer(object):
    def __init__(self, shape):
        self.data = np.zeros(shape)
        self.index = 0

    ##TODO: check length of buffer, maybe return only value if length is 1
    def __getitem__(self, idx):
        data = self.data[:self.index]
        return data[idx]

    def append(self, data):
        if np.shape(data) == ():
            data = np.array([data])
        elif len(np.shape(data)) == 1 and len(np.shape(self.data)) > 1:
            if np.shape(data)[0] == np.shape(self.data)[1]:
                data = np.array([data])
        if len(data) > len(self.data):
            self.data = data[-len(self.data):]
            self.index = len(self.data)
        elif self.index < len(self.data):
            remaining = len(self.data) - self.index - 1
            if remaining > len(data):
                self.data[self.index:self.index + len(data)] = data
                self.index += len(data)
            else:
                self.data[self.index:] = data[:remaining]
                self.index = len(self.data)
                self.append(data[remaining:])
        else:
            if len(data) > 0:
                self.data = np.roll(self.data, -len(data), axis=0)
                self.data[-len(data):] = data

    def extend(self, data):
        self.append(np.array([data]))

    def get(self):
        "Returns the first-in-first-out data in the ring buffer"
        return self.data[:self.index]

    def copy(self):
        return self.data[:self.index].copy()

    def __repr__(self):
        return np.array(self.data[:self.index])

    def __str__(self):
        return str(self.data[:self.index])

    def clear(self):
        self.index = 0


class ThreadedContinuousAcquisition():
    def __init__(self, target_method, buffer_size=(10000, 2), multithreading_lock=None, returns_time=False, delay=0):
        self.target_method = target_method
        self.buffer = CircularDataBuffer(buffer_size)
        self.lock = multithreading_lock
        self.returns_time = returns_time
        self.delay = delay
        self.thread = Thread(target=self._thread_run)
        self.is_running = False

    def _thread_run(self):
        while self.is_running:
            if not self.returns_time:
                time_data = time.perf_counter()
                data = self.target_method()
                data = np.insert(np.array(data), 0, time_data)
            else:
                data = self.target_method()
            self.buffer.append(data)
            time.sleep(self.delay)

    def reset_buffer(self, size):
        self.buffer = CircularDataBuffer(size)

    def start(self):
        self.stop()
        self.is_running = True
        self.thread = Thread(target=self._thread_run)
        self.thread.start()

    def stop(self):
        self.is_running = False
        if self.thread.is_alive():
            self.thread.join()

    def get_buffer(self, clear_buffer=False, align_time_at_zero=False):
        if clear_buffer:
            buffer = self.buffer.copy()
            self.buffer.clear()
        elif align_time_at_zero:
            buffer = self.buffer.copy()
            if len(buffer) > 0:
                buffer[:, 0] -= buffer[0, 0]
        else:
            buffer = self.buffer.get()
        return buffer

    def clear_buffer(self):
        self.buffer.clear()


def test_thread_continuous():
    return np.random.random((100, 2))


if __name__ == "__main__":
    continuous_buffer = ThreadedContinuousAcquisition(test_thread_continuous, buffer_size=(10000, 2), returns_time=True)
    continuous_buffer.start()
    time.sleep(0.1)
    continuous_buffer.stop()
    print(continuous_buffer.buffer)

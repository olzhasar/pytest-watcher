import threading
import time


class Trigger:
    _value: float
    _lock: threading.Lock

    def __init__(self, delay: float = 0.0):
        self._lock = threading.Lock()
        self._value = 0
        self._delay = delay

    def emit(self):
        with self._lock:
            self._value = time.time() + self._delay

    def emit_now(self):
        with self._lock:
            self._value = time.time()

    def is_active(self):
        return self._value != 0

    def release(self):
        with self._lock:
            self._value = 0

    def check(self):
        return self._value > 0 and time.time() > self._value

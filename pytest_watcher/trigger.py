import threading
import time


class Trigger:
    value: float
    lock: threading.Lock

    def __init__(self):
        self.lock = threading.Lock()
        self.value = 0

    def emit(self):
        with self.lock:
            self.value = time.time()

    def is_active(self):
        return self.value != 0

    def release(self):
        with self.lock:
            self.value = 0

    def check(self, delay: float):
        now = time.time()
        return self.value > 0 and now - self.value > delay

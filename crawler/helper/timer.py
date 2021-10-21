import logging
import time


class Timer:
    def __init__(self):
        self._tick = None

    def tick(self):
        self._tick = time.time()

    def tock_s(self):
        if self._tick:
            tock = time.time() - self._tick
            self._tick = None
            return tock

    def tock(self, msg: str):
        tock = self.tock_s()
        logging.info("%s: took %f", msg, tock)
        return tock
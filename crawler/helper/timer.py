import logging
import time


class Timer:
    def __init__(self):
        self._tick = None

    def tick(self):
        self._tick = time.time()

    def tock(self, msg):
        if self._tick:
            tock = time.time() - self._tick
            self._tick = None
            logging.info("%s: took %f", msg, tock)
            return tock

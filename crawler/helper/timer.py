import logging
import time


class Timer:
    def __init__(self):
        self._tick = []

    def tick(self):
        self._tick.append(time.time())

    def tock_s(self):
        tick = self._tick.pop()
        tock = time.time() - tick
        return tock

    def tock(self, msg: str):
        tock = self.tock_s()
        logging.info("%s: took %f", msg, tock)
        return tock
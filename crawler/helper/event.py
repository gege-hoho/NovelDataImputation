import time
import logging


class Event:
    def __init__(self, func, instant=True, hour=0, minutes=0, seconds=0, args=None):
        """
        Event that is called every x hour y minutes and z seconds
        :param instant: if the Event should be raised at first check aswell
        :type instant: bool
        :param func: callback function
        :type func:
        :param hour: hours
        :type hour: int
        :param minutes: minutes
        :type minutes: int
        :param seconds: seconds
        :type seconds: int
        :param args: args given to the callback function as list
        :type args: list
        """
        if args is None:
            args = []
        self.raise_every = seconds + minutes * 60 + hour * 3600
        self.raise_at = time.time()
        if not instant:
            self.raise_at += self.raise_every
        self.func = func
        self.args = args
        pass

    def check(self):
        """
        Calls the callback function with the given arguments if the time is there
        """
        if time.time() >= self.raise_at:
            logging.info("Event %s fired", str(self.func))
            self.func(*self.args)
            self.raise_at = time.time() + self.raise_every


class EventController:
    def __init__(self):
        """
        Initialises an EventController that holds all Events
        """
        self.events = []

    def add_event(self, event: Event):
        """
        Add an Event to the Eventcontroller
        :param event:
        :type event:
        """
        self.events.append(event)

    def check_events(self):
        """
        Check if an Event occurred. Needs to be called repeatedly in the main program loop
        """
        for event in self.events:
            event.check()

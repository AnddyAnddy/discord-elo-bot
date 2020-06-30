import time
from player import Player


class Ban():

    def __init__(self, name: str, time_left: int, reason: str):
        self.name = name
        self.date_now = time.time()
        self.time_end = time_left + self.date_now
        self.reason = reason

    def __str__(self):
        return f"{self.name} is still banned for \
{time_left(self.time_end)} for the reason: {self.reason}"


def time_left(secs: int):
    """Return the time left in the correct format."""
    (days, remainder) = divmod(secs - time.time(), 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, remainder) = divmod(remainder, 60)
    return f"{int(days)}d: {int(hours)}h: {int(minutes)}m: {int(remainder)}s"
    # return time.strftime('%H:%M:%S', time.gmtime(secs - time.time()))

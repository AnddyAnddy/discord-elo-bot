import time


class Ban:

    def __init__(self, user_id: int, my_time_left: int, reason: str):
        self.user_id = user_id
        self.date_now = time.time()
        self.time_end = my_time_left + self.date_now
        self.reason = reason

    def __str__(self):
        return f"<@{self.user_id}> is still banned for \
{time_left(int(self.time_end))} for the reason: {self.reason}"


def time_left(secs: int):
    """Return the time left in the correct format."""
    (days, remainder) = divmod(secs - time.time(), 86400)
    (hours, remainder) = divmod(remainder, 3600)
    (minutes, remainder) = divmod(remainder, 60)
    return f"{int(days)}d: {int(hours)}h: {int(minutes)}m: {int(remainder)}s"

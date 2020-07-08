from random import randint


class Rank():
    def __init__(self, mode, name, url, min_points, max_points):
        self.mode = mode
        self.name = name
        self.url = url
        self.range = range(min_points, max_points)

    def start(self):
        """Return the range start."""
        return self.range.start

    def stop(self):
        """Return the range stop."""
        return self.range.stop

    def __str__(self):
        return f"Name: {self.name}\n"\
               f"Mode: {self.mode}\n"\
               f"Url: {self.url}\n"\
               f"From: {self.range.start}\n"\
               f"To: {self.range.stop}\n"

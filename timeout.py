from signal import alarm, SIGALRM, signal


class TimeoutException(Exception):
    pass


def alarm_handler(signum, frame):
    raise TimeoutException()


class timeout(object):
    def __init__(self, time):
        self.time = time

    def __enter__(self):
        self.previous_handler = signal(SIGALRM, alarm_handler)
        alarm(self.time)
        return self

    def __exit__(self, type_, value, traceback):
        alarm(0)
        signal(SIGALRM, self.previous_handler)
        if type_ is not None or value is not None or traceback is not None:
            return False  # reraise exception

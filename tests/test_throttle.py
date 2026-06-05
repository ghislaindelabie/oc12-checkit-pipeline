from checkit.extract.throttle import Throttle


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.slept: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def test_first_call_does_not_wait():
    clock = FakeClock()
    throttle = Throttle(clock=clock)
    throttle.wait("gdelt", min_interval=5.0)
    assert clock.slept == []


def test_second_call_waits_the_remaining_interval():
    clock = FakeClock()
    throttle = Throttle(clock=clock)
    throttle.wait("gdelt", min_interval=5.0)
    clock.now += 2.0
    throttle.wait("gdelt", min_interval=5.0)
    assert clock.slept == [3.0]


def test_no_wait_when_interval_already_elapsed():
    clock = FakeClock()
    throttle = Throttle(clock=clock)
    throttle.wait("api", min_interval=1.0)
    clock.now += 5.0
    throttle.wait("api", min_interval=1.0)
    assert clock.slept == []


def test_keys_are_independent():
    clock = FakeClock()
    throttle = Throttle(clock=clock)
    throttle.wait("gdelt", min_interval=5.0)
    throttle.wait("rss:lemonde.fr", min_interval=1.0)  # different key: no wait
    assert clock.slept == []


def test_zero_interval_never_sleeps():
    clock = FakeClock()
    throttle = Throttle(clock=clock)
    throttle.wait("x", min_interval=0.0)
    throttle.wait("x", min_interval=0.0)
    assert clock.slept == []

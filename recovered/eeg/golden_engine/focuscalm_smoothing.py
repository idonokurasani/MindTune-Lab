import numpy as np


class AttentionSmoother:
    """
    Replicates attention_moving_average (libfusi.so 0x4375c).

    The native ring buffer is 20 doubles, initialised to 2.5, with the
    accumulator initialised to 50.0 (20 * 2.5). Each incoming candidate is
    divided by 20 before being added, so the steady-state output is the
    arithmetic mean of the last 20 candidates.
    """

    def __init__(self) -> None:
        self.size = 20
        self.scale = 20.0
        self.buffer = np.full(self.size, 2.5, dtype=np.float64)
        self.index = 0
        self.accum = 50.0

    def update(self, candidate: float) -> float:
        scaled = candidate / self.scale
        old = self.buffer[self.index]
        self.accum += scaled - old
        self.buffer[self.index] = scaled
        self.index = (self.index + 1) % self.size
        return float(self.accum)


class MeditationSmoother:
    """
    Replicates meditation_moving_average (libfusi.so 0x439b0).

    Native code allocates an 80-slot ring buffer but subtracts the entry
    written 20 steps ago, so the effective smoothing window is 20.  The
    buffer slots and accumulator are initialised to 2.5 and 50.0 respectively.
    """

    def __init__(self) -> None:
        self.buffer_size = 80
        self.lag = 20
        self.scale = 20.0
        self.buffer = np.full(self.buffer_size, 2.5, dtype=np.float64)
        self.index = 0
        self.accum = 50.0

    def update(self, candidate: float) -> float:
        scaled = candidate / self.scale
        lag_index = (self.index - self.lag) % self.buffer_size
        old = self.buffer[lag_index]
        self.accum += scaled - old
        self.buffer[self.index] = scaled
        self.index = (self.index + 1) % self.buffer_size
        return float(self.accum)


def demo() -> None:
    import numpy as np

    att = AttentionSmoother()
    med = MeditationSmoother()

    print("attention:")
    for i in range(25):
        print(i, att.update(100.0))

    print("\nmeditation:")
    for i in range(25):
        print(i, med.update(80.0))


if __name__ == "__main__":
    demo()

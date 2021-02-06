import matplotlib.pyplot as plot
import numpy as np


# Sampling rate 1000 hz / second

t = np.linspace(0, 100, 100, endpoint=True)


def square(t):
    T = 3
    D = 0.5
    return max((-1) ** int((t % T) / T >= D), 0)


plot.plot(t, list(map(square, t)))
# Give a title for the square wave plot
plot.title("Square wave")

plot.xlabel("Time")
plot.ylabel("Amplitude")


plot.grid(True, which="both")
plot.axhline(y=0, color="k")
plot.ylim(-2, 2)

plot.show()

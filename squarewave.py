from scipy import signal
import matplotlib.pyplot as plot
import numpy as np


# Sampling rate 1000 hz / second

t = np.linspace(0, 100, 100, endpoint=True) 

def square(t):
    T = 30
    D = 0.2
    return max((-1) ** int(((t * 1000) % T)/T >= D), 0)

plot.plot(t, list(map(square, t)))
# Give a title for the square wave plot
plot.title('Square wave')

plot.xlabel('Time')
plot.ylabel('Amplitude')


plot.grid(True, which='both')
plot.axhline(y=0, color='k')
plot.ylim(-2, 2)

plot.show()

import matplotlib.pyplot as plt
import numpy as np
import time
from signal_source.synthetic_ecg import generate_ecg_stream

sampling_rate = 360
window_size = 720  # 2 seconds display

buffer = np.ones(window_size) * 2048  # ADC mid baseline

plt.ion()
fig, ax = plt.subplots()
line, = ax.plot(buffer, lw=1)

ax.set_ylim(1500, 2600)
ax.set_xlim(0, window_size)

start_time = time.perf_counter()
sample_index = 0

# Continuous generator
ecg_stream = generate_ecg_stream(sampling_rate=sampling_rate)

while True:

    current_time = time.perf_counter()
    expected_index = int((current_time - start_time) * sampling_rate)

    # Add samples up to expected time
    while sample_index < expected_index:

        sample = next(ecg_stream)

        # shift buffer (scrolling effect)
        buffer[:-1] = buffer[1:]
        buffer[-1] = sample

        sample_index += 1

    # Update plot (not every sample, just frame)
    line.set_ydata(buffer)
    plt.draw()
    plt.pause(0.001)
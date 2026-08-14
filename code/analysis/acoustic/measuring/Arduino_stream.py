"""
Live plot of the Arduino dual-KY-037 p2p/rms stream.

Expects lines of the form: t_ms,vmax_0,vmin_0,rms_0,vmax_1,vmin_1,rms_1,n
(this matches the sketch that computes p2p and mean-corrected RMS per window
for both sensors)

Run as a standalone script:
    python live_mic_plot.py

If you'd rather run this inside Jupyter, the inline backend does NOT support
live animation. Use `%matplotlib widget` (requires ipympl) or `%matplotlib qt`
at the top of the notebook cell before running this.
"""

import time
from collections import deque

import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

PORT = "/dev/cu.usbserial-1110"   # adjust to your port (ls /dev/cu.*)
BAUD = 115200
WINDOW_SIZE = 200                   # number of points kept on screen
#Y_LIM = (0, 1023)
Y_LIM = (0, 500)


def open_serial(port=PORT, baud=BAUD):
    ser = serial.Serial(port, baud, timeout=1)
    time.sleep(2.0)                 # wait out the DTR reset
    ser.reset_input_buffer()
    return ser


def read_sample(ser):
    """Read one line and return
    (t_seconds, p2p_0, rms_0, vmax_0, vmin_0, p2p_1, rms_1, vmax_1, vmin_1)
    or None if invalid/partial.
    """
    raw = ser.readline().decode("ascii", errors="ignore").strip()
    if not raw:
        return None

    parts = raw.split(",")
    if len(parts) != 8:
        return None

    try:
        t_ms, vmax_0, vmin_0, rms_0, vmax_1, vmin_1, rms_1, n = parts
        vmax_0 = float(vmax_0)
        vmin_0 = float(vmin_0)
        rms_0 = float(rms_0)
        vmax_1 = float(vmax_1)
        vmin_1 = float(vmin_1)
        rms_1 = float(rms_1)
        p2p_0 = vmax_0 - vmin_0
        p2p_1 = vmax_1 - vmin_1
        return (int(t_ms) / 1000.0, p2p_0, rms_0, vmax_0, vmin_0,
                p2p_1, rms_1, vmax_1, vmin_1)
    except ValueError:
        return None


def read_latest_sample(ser, max_reads=1000):
    """Drain everything currently buffered and return only the newest valid
    sample, discarding any backlog. Returns None if nothing new arrived.

    Without this, a per-frame redraw slower than the Arduino's ~20ms report
    rate lets unread lines pile up in the serial buffer; since read_sample()
    always returns the oldest line (FIFO), the plot would keep falling
    further behind real time instead of showing the current level.
    """
    latest = None
    for _ in range(max_reads):
        if ser.in_waiting == 0:
            break
        sample = read_sample(ser)
        if sample is not None:
            latest = sample
    return latest


def main():
    ser = open_serial()

    t_data = deque(maxlen=WINDOW_SIZE)
    channels = {
        0: {k: deque(maxlen=WINDOW_SIZE) for k in ("p2p", "rms", "vmax", "vmin")},
        1: {k: deque(maxlen=WINDOW_SIZE) for k in ("p2p", "rms", "vmax", "vmin")},
    }

    fig, (ax0, ax1) = plt.subplots(2, 1, sharex=True, figsize=(8, 7))
    axes = {0: ax0, 1: ax1}
    lines = {}
    for ch, ax in axes.items():
        lines[ch] = {k: ax.plot([], [], lw=1.5, label=k)[0] for k in ("p2p", "rms", "vmax", "vmin")}
        ax.set_ylabel("ADC counts")
        ax.set_ylim(Y_LIM)
        ax.set_title(f"Sensor {ch}")
        ax.legend(loc="upper left")
    ax1.set_xlabel("time (s)")
    fig.suptitle("Live microphone level")

    all_lines = [line for ch_lines in lines.values() for line in ch_lines.values()]

    def update(frame):
        sample = read_latest_sample(ser)
        if sample is None:
            return all_lines

        t_s, p2p_0, rms_0, vmax_0, vmin_0, p2p_1, rms_1, vmax_1, vmin_1 = sample
        t_data.append(t_s)
        values = {0: (p2p_0, rms_0, vmax_0, vmin_0), 1: (p2p_1, rms_1, vmax_1, vmin_1)}

        for ch, ax in axes.items():
            p2p, rms, vmax, vmin = values[ch]
            channels[ch]["p2p"].append(p2p)
            channels[ch]["rms"].append(rms)
            channels[ch]["vmax"].append(vmax)
            channels[ch]["vmin"].append(vmin)

            ax.set_xlim(t_data[0], t_data[-1] + 0.1)
            for k in ("p2p", "rms", "vmax", "vmin"):
                lines[ch][k].set_data(t_data, channels[ch][k])
                lines[ch][k].set_label(f"{k}: mean = {np.mean(channels[ch][k]):.1f}")
            ax.legend(loc="upper left")

        return all_lines

    ani = animation.FuncAnimation(fig, update, interval=10, blit=False)
    plt.show()

    ser.close()


if __name__ == "__main__":
    main()
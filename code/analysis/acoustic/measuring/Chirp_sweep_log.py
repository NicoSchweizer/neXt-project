"""
Play a logarithmic 20 Hz -> 20,000 Hz sine sweep out the Mac's default audio
output (headphone jack) while concurrently logging the Arduino's two KY-37/38
mic streams to CSV, with each row tagged by the sweep's instantaneous
frequency and an absolute wall-clock timestamp for later InfluxDB
correlation.

Run as a standalone script:
    python Chirp_sweep_log.py

Adjust F0/F1/AMPLITUDE below, or override the sweep duration from the
command line: `python Chirp_sweep_log.py 90` sweeps over 90 seconds.

Set VERBOSE = True below to plot p2p/rms vs time and vs frequency right
after the run (saved as a PNG under fig/, see plot_measurement.py).

Caveats:
- The Arduino sketch busy-samples analogRead(A0) and analogRead(A1) for
  ~20ms per report with no fixed internal sample rate and no anti-aliasing
  filter, so amplitude readings above a few kHz reflect that hardware
  limitation as much as the enclosure's real acoustic response.
- arduino_t_ms is millis() since board reset (no date reference); wall_clock
  is the authoritative timestamp for any time-based correlation.
- The Arduino's ~25ms/row update rate means each row is tagged with one
  instantaneous frequency, but the absolute-Hz span covered per row grows
  toward the top of the sweep (a log sweep spends equal time per octave, not
  equal time per Hz) -- interpret the high end accordingly.
"""

import datetime
import math
import sys

import sounddevice as sd

from Arduino_log_csv import open_serial, read_sample, PORT, BAUD
from sound_measurement_helper import make_log_sweep, log_sweep_freq, run_acquisition
from plot_measurement import plot_results, FIG_DIR

F0 = 20.0
F1 = 20000.0
DURATION_S = 40.0                  # default sweep length in seconds
SAMPLERATE = 48000
AMPLITUDE = 1.0                    # loudness -- tune this
OUT_DIR = "../data"  # output folder, relative to this script
VERBOSE = True                    # plot p2p/rms vs time and vs frequency after the run, saved under fig/

HEADER = ["wall_clock", "t_rel_s", "f_inst_hz", "arduino_t_ms",
          "p2p_0", "rms_0", "vmax_0", "vmin_0",
          "p2p_1", "rms_1", "vmax_1", "vmin_1"]


def main():
    duration_s = float(sys.argv[1]) if len(sys.argv) > 1 else DURATION_S

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_path = f"{OUT_DIR}/chirp_sweep_{current_time}.csv"

    waveform = make_log_sweep(F0, F1, duration_s, SAMPLERATE, AMPLITUDE)

    try:
        output_device = sd.query_devices(kind="output")["name"]
    except Exception:
        output_device = None

    metadata = {
        "script": "Chirp_sweep_log.py",
        "csv_file": csv_path,
        "samplerate": SAMPLERATE,
        "amplitude": AMPLITUDE,
        "output_device": output_device,
        "port": PORT,
        "baud": BAUD,
        "sweep": {"f0": F0, "f1": F1, "duration_s": duration_s, "type": "log"},
    }

    def freq_cols_fn(t_rel):
        f = log_sweep_freq(t_rel, F0, F1, duration_s)
        return [f"{f:.2f}" if not math.isnan(f) else ""]

    ser = open_serial()
    try:
        run_acquisition(ser, read_sample, waveform, SAMPLERATE, duration_s,
                         csv_path, HEADER, freq_cols_fn, metadata)
    finally:
        ser.close()

    if VERBOSE:
        plot_results(csv_path, fig_dir=FIG_DIR)


if __name__ == "__main__":
    main()

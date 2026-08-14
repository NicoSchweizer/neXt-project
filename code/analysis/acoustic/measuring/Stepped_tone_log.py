"""
Play a set of steady sine tones (held for a fixed dwell time each) out the
Mac's default audio output while concurrently logging the Arduino's two
KY-37/38 mic streams to CSV, with each row tagged by the scheduled tone
frequency and an absolute wall-clock timestamp for later InfluxDB
correlation.

Default frequencies are sourced from the thesis notes:
  Notes/Baseplate/Baseplate_design.md -- dominant lab-noise band ~100-115 Hz;
    FEA modal freqs, design iter 1: 107, 143, 292, 306 Hz;
    design iter 2: 123, 241, 333, 495 Hz
  Notes/Coldplate/Coldplate.md -- 238 Hz pump-noise peak

Run as a standalone script:
    python Stepped_tone_log.py

Adjust TONES/DWELL_S/AMPLITUDE below to change what gets measured.

Set VERBOSE = True below to plot p2p/rms vs time and vs frequency right
after the run (saved as a PNG under fig/, see plot_measurement.py).

Caveats:
- The Arduino sketch busy-samples analogRead(A0) and analogRead(A1) for
  ~20ms per report with no fixed internal sample rate and no anti-aliasing
  filter, so amplitude readings above a few kHz reflect that hardware
  limitation as much as the enclosure's real acoustic response.
- arduino_t_ms is millis() since board reset (no date reference); wall_clock
  is the authoritative timestamp for any time-based correlation.
"""

import datetime
import math

import sounddevice as sd

from Arduino_log_csv import open_serial, read_sample, PORT, BAUD
from sound_measurement_helper import make_stepped_tones, scheduled_freq, run_acquisition
from plot_measurement import plot_results, FIG_DIR

TONES = [100, 107, 115, 123, 143, 238, 241, 292, 306, 333, 495]   # Hz, editable
DWELL_S = 4.0                      # seconds held per tone
SAMPLERATE = 48000
AMPLITUDE = 1.0                    # loudness -- tune this
OUT_DIR = "../data"  # output folder, relative to this script
VERBOSE = True                    # plot p2p/rms vs time and vs frequency after the run, saved under fig/

HEADER = ["wall_clock", "t_rel_s", "f_scheduled_hz", "tone_index", "arduino_t_ms",
          "p2p_0", "rms_0", "vmax_0", "vmin_0",
          "p2p_1", "rms_1", "vmax_1", "vmin_1"]


def main():
    duration_total = len(TONES) * DWELL_S

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_path = f"{OUT_DIR}/stepped_tone_{current_time}.csv"

    waveform = make_stepped_tones(TONES, DWELL_S, SAMPLERATE, AMPLITUDE)

    try:
        output_device = sd.query_devices(kind="output")["name"]
    except Exception:
        output_device = None

    metadata = {
        "script": "Stepped_tone_log.py",
        "csv_file": csv_path,
        "samplerate": SAMPLERATE,
        "amplitude": AMPLITUDE,
        "output_device": output_device,
        "port": PORT,
        "baud": BAUD,
        "tones": TONES,
        "dwell_s": DWELL_S,
        "notes_source": "Notes/Baseplate/Baseplate_design.md, Notes/Coldplate/Coldplate.md",
    }

    def freq_cols_fn(t_rel):
        f, idx = scheduled_freq(t_rel, TONES, DWELL_S)
        if math.isnan(f):
            return ["", ""]
        return [f"{f:.1f}", idx]

    ser = open_serial()
    try:
        run_acquisition(ser, read_sample, waveform, SAMPLERATE, duration_total,
                         csv_path, HEADER, freq_cols_fn, metadata)
    finally:
        ser.close()

    if VERBOSE:
        plot_results(csv_path, fig_dir=FIG_DIR)


if __name__ == "__main__":
    main()

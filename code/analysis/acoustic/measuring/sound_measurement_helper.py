"""
Shared audio synthesis + concurrent playback/acquisition scaffold for the
enclosure acoustic-response measurements (log chirp and stepped tones).

Caveats that carry through to every CSV produced with this module:
- The Arduino sketch busy-samples analogRead(A0) and analogRead(A1) for
  ~20ms per report with no fixed internal sample rate and no anti-aliasing
  filter, so amplitude readings above a few kHz reflect that hardware
  limitation as much as the enclosure's real acoustic response.
- arduino_t_ms is millis() since board reset (no date reference); wall_clock
  is the authoritative timestamp for any time-based correlation (e.g. with
  InfluxDB temperature data via Freq_stab_noise/Tone_timestamp_influxDB.py).
"""

import csv
import json
import math
import time
from datetime import datetime

import numpy as np
import sounddevice as sd


def make_log_sweep(f0, f1, duration, samplerate, amplitude):
    """Generate a logarithmic (exponential) sine sweep from f0 to f1 Hz.

    Uses the closed-form phase integral of f(t) = f0*(f1/f0)**(t/duration),
    not sin(2*pi*f(t)*t) directly, which would produce the wrong
    instantaneous frequency.
    """
    n = int(round(samplerate * duration))
    t = np.linspace(0, duration, n, endpoint=False)
    ratio = f1 / f0
    k = duration / math.log(ratio)
    phase = 2 * math.pi * f0 * k * (ratio ** (t / duration) - 1)
    return (amplitude * np.sin(phase)).astype(np.float32)


def log_sweep_freq(t_rel, f0, f1, duration):
    """Instantaneous frequency of make_log_sweep at t_rel seconds.

    NaN outside [0, duration] (row arrived before/after playback).
    """
    if not (0.0 <= t_rel <= duration):
        return float("nan")
    return f0 * (f1 / f0) ** (t_rel / duration)


def _fade_window(n_fade):
    return 0.5 * (1 - np.cos(np.linspace(0, math.pi, n_fade)))


def make_stepped_tones(tones, dwell, samplerate, amplitude, fade_s=0.005):
    """Concatenate one sine tone per entry in `tones`, each held for `dwell`
    seconds, with a short raised-cosine fade at each segment boundary to
    avoid audible clicks between tones.
    """
    n_dwell = int(round(samplerate * dwell))
    n_fade = min(int(round(samplerate * fade_s)), n_dwell // 2)
    fade_in = _fade_window(n_fade) if n_fade > 0 else np.array([])
    fade_out = fade_in[::-1]

    t = np.arange(n_dwell) / samplerate
    segments = []
    for f in tones:
        seg = (amplitude * np.sin(2 * math.pi * f * t)).astype(np.float32)
        if n_fade > 0:
            seg[:n_fade] *= fade_in
            seg[-n_fade:] *= fade_out
        segments.append(seg)

    return np.concatenate(segments)


def scheduled_freq(t_rel, tones, dwell):
    """Which tone is scheduled to be playing at t_rel seconds.

    Returns (freq_hz, tone_index); (nan, nan) outside [0, len(tones)*dwell).
    """
    total = len(tones) * dwell
    if not (0.0 <= t_rel < total):
        return float("nan"), float("nan")
    idx = int(t_rel // dwell)
    return float(tones[idx]), idx


def _write_comment_block(f, metadata):
    """Write metadata as '#'-prefixed lines. Nested dict/list values are
    JSON-encoded inline. Load these CSVs with pd.read_csv(path, comment='#')
    to skip them.
    """
    for key, value in metadata.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        f.write(f"# {key}: {value}\n")


def run_acquisition(ser, read_sample, waveform, samplerate, duration_total,
                     out_csv_path, header, freq_cols_fn, metadata,
                     tail_s=1.0):
    """Play `waveform` (non-blocking) while concurrently reading Arduino
    serial samples via `read_sample(ser)`, writing one CSV row per valid
    sample:

        [wall_clock_iso, t_rel_s, *freq_cols_fn(t_rel), arduino_t_ms,
         p2p_0, rms_0, vmax_0, vmin_0, p2p_1, rms_1, vmax_1, vmin_1]

    `freq_cols_fn(t_rel)` must return a list of already CSV-ready values
    (numbers or strings, "" for not-applicable) -- formatting is left to the
    caller since chirp vs. stepped-tone columns want different precision.

    Runs until t_rel >= duration_total + tail_s (the tail catches any
    samples still in flight right after playback ends) or KeyboardInterrupt.
    `metadata` is written as '#'-prefixed comment lines before the header
    row (run config) and a short summary block after the last data row
    (n_rows, completed_at) -- load with pd.read_csv(path, comment='#').
    Returns n_rows.

    Does not open or close `ser` -- that is the caller's responsibility,
    matching Arduino_log_csv.py's existing open/close pattern.
    """
    n_rows = 0
    sweep_start_wall = datetime.now().astimezone()
    metadata = dict(metadata)  # don't mutate the caller's dict
    metadata["run_timestamp_local"] = sweep_start_wall.isoformat()

    sd.play(waveform, samplerate)
    sweep_start_mono = time.monotonic()
    end_mono = sweep_start_mono + duration_total + tail_s

    print(f"Playing + logging to {out_csv_path} for {duration_total:.1f}s "
          f"(+{tail_s:.1f}s tail)...")

    try:
        with open(out_csv_path, "w", newline="") as f:
            _write_comment_block(f, metadata)
            writer = csv.writer(f)
            writer.writerow(header)

            while time.monotonic() < end_mono:
                sample = read_sample(ser)
                if sample is None:
                    continue

                t_s, p2p_0, rms_0, vmax_0, vmin_0, p2p_1, rms_1, vmax_1, vmin_1 = sample
                wall_clock = datetime.now().astimezone()
                t_rel = time.monotonic() - sweep_start_mono
                arduino_t_ms = int(round(t_s * 1000))
                extra = freq_cols_fn(t_rel)

                writer.writerow([wall_clock.isoformat(), f"{t_rel:.3f}", *extra,
                                  arduino_t_ms, p2p_0, rms_0, vmax_0, vmin_0,
                                  p2p_1, rms_1, vmax_1, vmin_1])
                n_rows += 1

                remaining = max(0.0, end_mono - time.monotonic())
                print(f"\rRemaining: {remaining:5.1f}s  rows: {n_rows}", end="", flush=True)

            f.write(f"# n_rows: {n_rows}\n")
            f.write(f"# completed_at: {datetime.now().astimezone().isoformat()}\n")

        print(f"\rRemaining:   0.0s  rows: {n_rows}")
    except KeyboardInterrupt:
        print("\nAcquisition aborted by user.")
    finally:
        sd.stop()

    print(f"Saved {n_rows} rows to {out_csv_path}")
    return n_rows

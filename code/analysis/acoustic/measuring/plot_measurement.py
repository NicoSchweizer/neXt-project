"""
Plot p2p/rms from a chirp or stepped-tone measurement CSV (written by
sound_measurement_helper.run_acquisition), both as a timeseries and as a
function of frequency, in a single 2x2 figure. Saves the figure as a PNG
under fig/ next to the data/ folder.

Works standalone on any already-saved CSV:
    python plot_measurement.py data/chirp_sweep_2026-07-15_14-32-07.csv

Chirp_sweep_log.py / Stepped_tone_log.py also call plot_results()
automatically right after a run when their VERBOSE flag is set.
"""

import os
import sys

import matplotlib.pyplot as plt
import pandas as pd

FIG_DIR = "fig"


def _freq_column(df):
    for col in ("f_inst_hz", "f_scheduled_hz"):
        if col in df.columns:
            return col
    raise ValueError(f"No known frequency column (f_inst_hz / f_scheduled_hz) in {list(df.columns)}")


def _sensor_channels(df):
    """Return a list of (suffix, label) for the p2p/rms columns present.

    Handles both the single-sensor CSVs (columns "p2p", "rms") produced
    before the Arduino sketch was extended to two mics, and the current
    dual-sensor CSVs (columns "p2p_0"/"rms_0", "p2p_1"/"rms_1").
    """
    if "p2p_0" in df.columns:
        channels = []
        for suffix in ("0", "1"):
            if f"p2p_{suffix}" in df.columns:
                channels.append((f"_{suffix}", f"sensor {suffix}"))
        return channels
    return [("", "sensor")]


def plot_results(csv_path, fig_dir=FIG_DIR, show=True):
    """Read `csv_path` and plot p2p/rms vs time and vs frequency (log-x) in
    a 2x2 grid, one line/scatter series per sensor channel present in the
    CSV. Saves to <fig_dir>/<csv-stem>.png (creating fig_dir if needed) and
    returns the saved path.
    """
    df = pd.read_csv(csv_path, comment="#")
    freq_col = _freq_column(df)
    freq_df = df.dropna(subset=[freq_col])
    channels = _sensor_channels(df)

    fig, ((ax_p2p_t, ax_rms_t), (ax_p2p_f, ax_rms_f)) = plt.subplots(2, 2, figsize=(11, 7))

    for suffix, label in channels:
        ax_p2p_t.plot(df["t_rel_s"], df[f"p2p{suffix}"], lw=1, label=label)
        ax_rms_t.plot(df["t_rel_s"], df[f"rms{suffix}"], lw=1, label=label)
        ax_p2p_f.scatter(freq_df[freq_col], freq_df[f"p2p{suffix}"], s=8, label=label)
        ax_rms_f.scatter(freq_df[freq_col], freq_df[f"rms{suffix}"], s=8, label=label)

    ax_p2p_t.set_xlabel("time (s)")
    ax_p2p_t.set_ylabel("p2p (ADC counts)")
    ax_p2p_t.set_title("p2p vs time")

    ax_rms_t.set_xlabel("time (s)")
    ax_rms_t.set_ylabel("rms (ADC counts)")
    ax_rms_t.set_title("rms vs time")

    ax_p2p_f.set_xscale("log")
    ax_p2p_f.set_xlabel("frequency (Hz)")
    ax_p2p_f.set_ylabel("p2p (ADC counts)")
    ax_p2p_f.set_title("p2p vs frequency")

    ax_rms_f.set_xscale("log")
    ax_rms_f.set_xlabel("frequency (Hz)")
    ax_rms_f.set_ylabel("rms (ADC counts)")
    ax_rms_f.set_title("rms vs frequency")

    if len(channels) > 1:
        for ax in (ax_p2p_t, ax_rms_t, ax_p2p_f, ax_rms_f):
            ax.legend(loc="best", fontsize=8)

    fig.suptitle(os.path.basename(csv_path))
    fig.tight_layout()

    os.makedirs(fig_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(csv_path))[0]
    fig_path = os.path.join(fig_dir, f"{stem}.png")
    fig.savefig(fig_path, dpi=150)
    print(f"Saved figure to {fig_path}")

    if show:
        plt.show()
    else:
        plt.close(fig)

    return fig_path


if __name__ == "__main__":
    plot_results(sys.argv[1])

"""
Log the Arduino dual-KY-037 p2p/rms stream to a CSV file for a fixed duration.

Expects lines of the form: t_ms,vmax_0,vmin_0,rms_0,vmax_1,vmin_1,rms_1,n
(same sketch/format as Arduino_stream.py)

Run as a standalone script:
    python Arduino_log_csv.py

Adjust PORT, BAUD and DURATION_S below, or override DURATION_S from the
command line: `python Arduino_log_csv.py 120` logs for 120 seconds.
"""

import csv
import datetime
import sys
import time

import serial

PORT = "/dev/cu.usbserial-1110"   # adjust to your port (ls /dev/cu.*)
BAUD = 115200
DURATION_S = 60                    # default recording length in seconds
OUT_DIR = "../data"  # output folder, relative to this script


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


def format_time(seconds):
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m:02d}:{s:02d}"


def main():
    duration_s = float(sys.argv[1]) if len(sys.argv) > 1 else DURATION_S

    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{OUT_DIR}/arduino_stream_{current_time}.csv"

    ser = open_serial()

    n_rows = 0
    start = time.time()
    end = start + duration_s

    print(f"Logging to {file_name} for {format_time(duration_s)} (mm:ss)...")

    try:
        with open(file_name, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["t_s", "p2p_0", "rms_0", "vmax_0", "vmin_0",
                              "p2p_1", "rms_1", "vmax_1", "vmin_1"])

            while True:
                now = time.time()
                if now >= end:
                    break

                sample = read_sample(ser)
                if sample is not None:
                    writer.writerow(sample)
                    n_rows += 1

                remaining = int(end - now)
                print(f"\rRemaining: {format_time(remaining)}  rows: {n_rows}", end="", flush=True)

        print(f"\rRemaining: 00:00  rows: {n_rows}")
    except KeyboardInterrupt:
        print("\nLogging aborted by user.")
    finally:
        ser.close()

    print(f"Saved {n_rows} rows to {file_name}")


if __name__ == "__main__":
    main()

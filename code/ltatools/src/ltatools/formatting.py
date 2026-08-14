"""Significant-digits (PDG-style) value +/- error formatting.

This module rounds a measured value together with its error so that the
error is shown with a chosen number of significant digits and the value is
rounded to the same decimal place, e.g. ``78.49 +/- 0.36`` becomes
``78.5(4)``. Formatted output includes digit grouping with apostrophes for
readability, e.g. ``56'000(100)``. The rounding logic lives here so it can be
reused by the plotting layer, a future LaTeX/JSON export, and asymmetric
confidence intervals alike, instead of being duplicated at each call site.
"""

from __future__ import annotations

import math


def _group_digits(digits: str, group: int = 3, sep: str = "'") -> str:
    """Insert `sep` every `group` characters, grouping from the right (integers).

    Example: _group_digits("55992") -> "55'992"
    """
    if len(digits) <= group:
        return digits
    reversed_digits = digits[::-1]
    chunks = [chunk[::-1] for chunk in (reversed_digits[i : i + group] for i in range(0, len(reversed_digits), group))]
    chunks.reverse()
    return sep.join(chunks)


def _group_integer_part(text: str) -> str:
    """Group the integer part of a formatted number string with apostrophes.

    Handles negative signs and decimal points. Fractional parts are left
    unchanged. E.g.:
      "1277" -> "1'277"
      "-56000" -> "-56'000"
      "78.5" -> "78.5" (only integer part grouped, if it were large)
      "78500.5" -> "78'500.5"
    """
    if "e" in text or "E" in text:
        return text
    sign, text = ("-", text[1:]) if text.startswith("-") else ("", text)
    integer_part, _, frac_part = text.partition(".")
    grouped_int = _group_digits(integer_part)
    if not frac_part:
        return f"{sign}{grouped_int}"
    return f"{sign}{grouped_int}.{frac_part}"


def round_value_error(value: float, error: float, sig: int = 1) -> tuple[float, float, int]:
    """Round `error` to `sig` significant digits and `value` to the same
    decimal place.

    Returns
    -------
    (rounded_value, rounded_error, decimals)
        `decimals` is the number of digits after the decimal point that both
        numbers were rounded to. It may be negative (e.g. -2 means rounded to
        hundreds). Raises ValueError if `error` is not usable (0, NaN, inf) or
        if `sig < 1`.
    """
    if sig < 1:
        raise ValueError(f"sig must be >= 1, got {sig}")
    if error == 0 or math.isnan(error) or math.isinf(error):
        raise ValueError(f"error must be a finite, non-zero number, got {error}")

    exp = math.floor(math.log10(abs(error)))
    decimals = -(exp - (sig - 1))
    err_r = round(error, decimals)

    # Rounding can push the error into the next decade: 0.96 -> 1.0 with sig=1.
    # Recompute in that case so the number of significant digits stays correct.
    if err_r != 0 and math.floor(math.log10(abs(err_r))) != exp:
        exp = math.floor(math.log10(abs(err_r)))
        decimals = -(exp - (sig - 1))
        err_r = round(error, decimals)

    val_r = round(value, decimals)
    return val_r, err_r, decimals


def format_compact(value: float, error: float, sig: int = 1, unit: str | None = None) -> str:
    """Compact notation with grouped digits, e.g. '1'277(2) kHz' or '56'000(100) kHz'."""
    try:
        val_r, err_r, decimals = round_value_error(value, error, sig)
    except ValueError:
        text = _group_integer_part(f"{value:.4g}")
        return f"{text} {unit}" if unit else text

    if value != 0 and error >= abs(value):
        return format_plusminus(value, error, sig, unit)

    if decimals > 0:
        val_str = f"{val_r:.{decimals}f}"
        err_int = int(round(err_r * 10**decimals))
        # Group the value's integer part, leave fractional part ungrouped
        val_grouped = _group_integer_part(val_str)
        err_grouped = _group_integer_part(str(err_int))
        text = f"{val_grouped}({err_grouped})"
    elif decimals == 0:
        val_str = f"{val_r:.0f}"
        err_int = int(round(err_r))
        val_grouped = _group_integer_part(val_str)
        err_grouped = _group_integer_part(str(err_int))
        text = f"{val_grouped}({err_grouped})"
    else:
        # NOTE: for decimals < 0 the number in parentheses is the rounded
        # error itself (e.g. the "100" in "56000(100)"), not the error
        # expressed in units of the last displayed digit as strict compact
        # notation would require. This is a deliberate deviation and must be
        # called out in any figure caption/legend that uses this format.
        val_str = f"{val_r:.0f}"
        err_str = f"{err_r:.0f}"
        val_grouped = _group_integer_part(val_str)
        err_grouped = _group_integer_part(err_str)
        text = f"{val_grouped}({err_grouped})"

    return f"{text} {unit}" if unit else text


def format_plusminus(value: float, error: float, sig: int = 1, unit: str | None = None) -> str:
    """Fallback notation with grouped digits, e.g. '1'277 +/- 2 kHz'. Used when
    the compact form would be misleading (see edge cases below)."""
    try:
        val_r, err_r, decimals = round_value_error(value, error, sig)
    except ValueError:
        text = _group_integer_part(f"{value:.4g}")
        return f"{text} {unit}" if unit else text

    if decimals >= 0:
        val_str = f"{val_r:.{decimals}f}"
        err_str = f"{err_r:.{decimals}f}"
        val_grouped = _group_integer_part(val_str)
        err_grouped = _group_integer_part(err_str)
        text = f"{val_grouped} +/- {err_grouped}"
    else:
        val_str = f"{val_r:.0f}"
        err_str = f"{err_r:.0f}"
        val_grouped = _group_integer_part(val_str)
        err_grouped = _group_integer_part(err_str)
        text = f"{val_grouped} +/- {err_grouped}"

    return f"{text} {unit}" if unit else text

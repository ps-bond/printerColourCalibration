
"""High-level workflow orchestration for printer calibration.

This module provides a small, stable entrypoint used by the CLI to
perform a single calibration analysis pass. It wires together the
lower-level helpers in :mod:`printer_calibration.io` and
:mod:`printer_calibration.analysis` and returns the important,
human-readable results that the CLI prints or stores.

The workflow is intentionally simple: it loads a measurement CSV, uses
the neutral patch analysis to compute offsets in the `a`/`b` channels,
and asks the analysis module for a suggested ink/toner adjustment
expressed as a small mapping (per-channel steps).

Example
-------
>>> from printer_calibration.workflow import run
>>> a, b, adjustments = run('printer_calibration/example_measurements.csv')
>>> print(a, b)

Notes
-----
- Input CSV format: see :mod:`printer_calibration.io` and the project
    README. Required columns are ``patch``, ``rgb``, ``L``, ``a``, ``b``.
- The returned `adjustments` value is produced by
    :func:`printer_calibration.analysis.suggest_adjustment` and typically
    contains keys for colour channels (e.g. 'C','M','Y') mapping to
    coarse/fine step adjustments from :class:`printer_calibration.config.InkSteps`.
"""

from .io import load_csv
# from .analysis import neutral_error, suggest_adjustment
from .config import InkSteps
from printer_calibration.charts import (
    generate_neutral_chart,
    generate_colour_chart,
)


def generate_chart(
    chart_type: str = "neutral",
    filename: str | None = None,
    format: str | None = None,
    dpi: int = 300,
    title: str | None = None,
    all_charts: bool = False,
) -> None:
    """Generate a test chart and save it to disk.

    Parameters
    ----------
    chart_type : str
        ``"neutral"`` to generate a grayscale chart, ``"colour"`` to
        generate a multicolour patch chart.
    filename : str | None
        Optional output filename. If omitted a sensible default is used
        (``neutral_chart.png`` or the default filename used by
        :func:`generate_colour_chart`).
    format : str | None
        Optional explicit image format to pass to Pillow's ``save``
        (for example ``'PDF'``). If omitted the filename extension is
        used to determine the format.
    dpi : int
        DPI to use for neutral chart generation (where applicable).
    """
    # Choose sensible default filenames that match requested format
    # If requested, generate all available charts.
    if all_charts:
        # Compute a single extension to use for all chart filenames
        ext = format.lower().lstrip('.') if format else 'png'
        neutral_out = f"neutral_chart.{ext}"
        colour_out = f"colour_test_A4.{ext}"

        generate_neutral_chart(neutral_out, dpi=dpi, format=format, title=title)
        generate_colour_chart(colour_out, format=format, title=title)
        return

    if chart_type == "neutral":
        if filename:
            out = filename
        else:
            if format:
                ext = format.lower()
                out = f"neutral_chart.{ext if not ext.startswith('.') else ext.lstrip('.')}"
            else:
                out = "neutral_chart.png"
        generate_neutral_chart(out, dpi=dpi, format=format, title=title)
    elif chart_type == "colour":
        if filename:
            out = filename
        else:
            if format:
                ext = format.lower()
                out = f"colour_test_A4.{ext if not ext.startswith('.') else ext.lstrip('.')}"
            else:
                out = None
        # generate_colour_chart provides its own default when passed None
        generate_colour_chart(out, format=format, title=title)
    else:
        raise ValueError(f"Unknown chart type: {chart_type}")


# def run(csv_path: str):
#     """Run one analysis pass for the given measurement CSV.

#     Parameters
#     ----------
#     csv_path : str
#         Path to the measurement CSV file. The loader will normalize
#         columns and coerce numeric Lab values; see
#         :func:`printer_calibration.io.load_csv` for details.

#     Returns
#     -------
#     tuple
#         A 3-tuple ``(a_mean, b_mean, adjustments)`` where ``a_mean`` and
#         ``b_mean`` are the computed mean offsets for the neutral mid-tones,
#         and ``adjustments`` is the dictionary returned by
#         :func:`printer_calibration.analysis.suggest_adjustment`.
#     """

#     # Load and clean measurement data. The loader is tolerant of common
#     # CSV issues (comments, whitespace, case differences) and will raise
#     # a ValueError if required columns are missing.
#     df = load_csv(csv_path)

#     # Compute neutral-channel error (mean a and b for mid-tone patches).
#     a, b = neutral_error(df)

#     # Suggest per-channel ink adjustments using configured step sizes.
#     adj = suggest_adjustment(a, b, InkSteps())

#     return a, b, adj

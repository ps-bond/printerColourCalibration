"""printer_calibration.cli
=========================

Command-line interface for the printer calibration workflow.

This module is intended to be executed with Python's `-m` switch from the
repository root, for example::

    python -m printer_calibration.cli generate-chart --type neutral

It provides a thin wrapper around :mod:`printer_calibration.workflow` with
four user-facing commands: ``generate-chart``, ``analyse``, ``plot`` and
``export-icc``.
"""

import argparse
import os
import sys
from . import workflow


def build_parser() -> argparse.ArgumentParser:
    """Create and return the top-level argument parser.

    The parser defines subcommands that map directly to functions in
    :mod:`printer_calibration.workflow`.
    """

    parser = argparse.ArgumentParser(
        prog="python -m printer_calibration.cli",
        description=(
            "Printer calibration helper: generate test charts, analyse "
            "measurements, plot convergence and export ICC profiles"
        ),
        epilog=(
            "Examples:\n  python -m printer_calibration.cli generate-chart --type neutral\n"
            "  python -m printer_calibration.cli analyse measurements.csv"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate-chart
    gen = subparsers.add_parser(
        "generate-chart",
        help="Generate a printable test chart used to measure printer output",
        description=(
            "Create a neutral (grayscale) or colour test chart. Print the generated "
            "chart on the target printer and measure the printed patches with your "
            "spectrophotometer to produce a CSV for analysis."
        ),
    )
    gen.add_argument(
        "--type",
        choices=["neutral", "colour"],
        default="neutral",
        help="Type of chart to generate: 'neutral' for grayscale, 'colour' for colour patches",
    )
    gen.add_argument(
        "-o",
        "--output",
        dest="output",
        help="Output filename for the generated chart (defaults used if omitted)",
    )
    gen.add_argument(
        "--format",
        dest="format",
        help="Explicit image format to pass to Pillow (e.g. 'PDF')",
    )
    gen.add_argument(
        "--title",
        dest="title",
        help="Optional title to render on the generated chart",
    )
    gen.add_argument(
        "--all",
        dest="all",
        action="store_true",
        help="Generate all available charts (ignores --type and --output)",
    )
    gen.add_argument(
        "--dpi",
        dest="dpi",
        type=int,
        default=300,
        help="DPI for neutral chart generation (default: 300)",
    )

    # analyse
    analyse = subparsers.add_parser(
        "analyse",
        help="Analyse measured patches and suggest adjustments to toner/ink curves",
        description=(
            "Read a measurement CSV exported from your measurement tool and run "
            "the analysis that suggests per-channel adjustments or convergence data."
        ),
    )
    analyse.add_argument(
        "csv",
        help=(
            "Path to the measurement CSV file produced by your spectrophotometer "
            "or measurement software. The file should contain patch readings."
        ),
    )

    # plot
    subparsers.add_parser(
        "plot",
        help="Plot calibration convergence metrics over time",
        description=(
            "Show a graph of the deltaE / error metrics across successive runs, "
            "helpful for assessing whether calibration is improving."
        ),
    )

    # make plot accept optional output/save flags
    plot = subparsers.choices.get("plot")
    if plot is not None:
        plot.add_argument(
            "-o",
            "--output",
            dest="output",
            help="Save the plotted convergence graph to this filename",
        )
        plot.add_argument(
            "--show",
            dest="show",
            action="store_true",
            help="Display the plot interactively (default is non-blocking)",
        )

    # export-icc
    subparsers.add_parser(
        "export-icc",
        help="Export an ICC profile derived from the converged calibration state",
        description=(
            "When the calibration workflow indicates convergence, export an ICC "
            "profile for use in colour-managed applications."
        ),
    )

    return parser


def main() -> None:
    """Parse CLI args and dispatch to the workflow functions."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command == "generate-chart":
        # Warn if the user provided both a format and an output filename
        if args.format and args.output:
            out_ext = os.path.splitext(args.output)[1].lower().lstrip('.')
            fmt = args.format.lower().lstrip('.')
            if out_ext != fmt:
                print(
                    f"Warning: output filename extension '.{out_ext}' does not match requested format '{args.format}'.",
                    file=sys.stderr,
                )
        # If user asked to generate all charts, ignore provided output filename
        if args.all and args.output:
            print(
                "Warning: --output is ignored when --all is specified; generating all charts using defaults.",
                file=sys.stderr,
            )
        workflow.generate_chart(
            chart_type=args.type,
            filename=args.output,
            format=args.format,
            dpi=args.dpi,
            title=args.title,
            all_charts=args.all,
        )

    elif args.command == "analyse":
        # run analysis and print succinct results
        a, b, adj = workflow.run(args.csv)
        print(f"a_mean={a:.3f}, b_mean={b:.3f}")
        print("adjustments:", adj)

    elif args.command == "plot":
        # Use workflow helper to plot (can save or show)
        workflow.plot_convergence(show=bool(getattr(args, "show", False)), savepath=getattr(args, "output", None))

    elif args.command == "export-icc":
        workflow.export_icc()


if __name__ == "__main__":
    main()

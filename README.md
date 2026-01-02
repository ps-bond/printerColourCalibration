# Printer Calibration

This repository provides a selection of utility modules for use in calibrating an inkjet printer.

The rationale was that my Epson 7100 is printing with a significant blue shift (not Doppler related) and I wanted the colours to be more accurate, but without going to the trouble of using professional colour match equipment.

I've been using a Color Muse 3 to read CIELAB values off printed swatches; I can then pass these into the scripts to calculate firstly gross colour balance (using the sliders for CMY in the Epson driver), then build an ICC profile.  It's crude, it's not as accurate as a pro setup but it's close enough for my needs.

The CLI exposes a few convenient commands used during calibration and
profile generation:

- `generate-chart`: produce a printable neutral or colour test chart
- `analyse`: analyse measured patch CSV files and suggest adjustments
- `plot`: visualise convergence metrics across runs
- `export-icc`: export an ICC profile when the workflow has converged

Prerequisites
-------------

- Python 3.8+ (developed and tested on modern Python 3.x)
- Install dependencies:

```bash
pip install -r requirements.txt
```

Usage
-----

Run the CLI with Python from the repository root. The CLI is packaged as
`printer_calibration.cli` and should be run using the module invocation so
imports resolve correctly. Examples:

Generate a neutral chart:

```bash
python -m printer_calibration.cli generate-chart --type neutral
```

Save charts as PDF
------------------

You can save charts as PDF either by using a `.pdf` filename or by
passing an explicit format to the chart functions. Examples:

```bash
python -m printer_calibration.cli generate-chart --type neutral --output neutral.pdf
```

Or in Python:

```py
from printer_calibration import charts
charts.generate_neutral_chart('neutral.pdf', format='PDF')
```

Analyse a CSV of measured patches:

```bash
python -m printer_calibration.cli analyse path/to/measurements.csv
```

Plot convergence metrics:

```bash
python -m printer_calibration.cli plot
```

Export an ICC profile after convergence:

```bash
python -m printer_calibration.cli export-icc
```

Running tests
-------------

Run the unit test suite from the repository root:

```bash
python -m unittest discover -v
# or if you prefer pytest:
pytest -q
```

Run the style checks (requires `flake8`):

```bash
flake8
```

Notes
-----

- The CLI is a thin wrapper around the functions in
  `printer_calibration.workflow`. For more advanced usage or parameter
  tuning, consult that module's source.
- The `generate-chart` command produces chart data that should be printed
  and measured with a spectrophotometer. The resulting CSV can then be
  analysed with `analyse`.

Measurement CSV format
----------------------

When you run the measurement-analysis commands the CLI expects a CSV
file containing measured colour patches. The loader requires the
following columns be present:

- `patch`: an identifier or label for the patch (string or integer)
- `rgb`: the printed patch nominal RGB value or code (used by the
  analysis; in the provided code examples a single-channel level such as
  100 or 150 is used for neutral patches)
- `L`, `a`, `b`: the measured CIELAB coordinates for the patch (numeric)

Example (CSV):

```csv
patch,rgb,L,a,b
0,100,53.2,-0.5,1.2
1,150,67.1,0.1,-0.9
2,50,32.4,0.3,0.7
```

If any of these columns are missing the loader will raise a
`ValueError`. The CSV format should match the output from your
measurement tool (or be converted to the column names above before
running the CLI).

Workflow
--------

```text
 ┌────────────────────────────┐
 │ 1. Generate Test Charts    │
 │                            │
 │ - Neutral grey chart       │
 │ - Colour chart             │
 │ - Patches labelled above   │
 │   each patch               │
 │ - CSV measurement template │
 └─────────────┬──────────────┘
               │
               ▼
 ┌──────────────────────────────┐
 │ 2. Print Charts              │
 │                              │
 │ - Use same driver settings   │
 │ - Disable colour management  │
 │ - Standard/High quality      │
 │ - Fully dry before measuring │
 └─────────────┬────────────────┘
               │
               ▼
 ┌────────────────────────────┐
 │ 3. Measure Patches         │
 │                            │
 │ - Use Color Muse 3         │
 │ - Centre of patch only     │
 │ - Fill CSV template with   │
 │   L*, a*, b* values        │
 └─────────────┬──────────────┘
               │
               ▼
 ┌───────────────────────────────────────────────────────────────────┐
 │ 4. Analyse & Adjust Sliders                                       │
 │                                                                   │
 │ - Run: python -m printer_calibration.cli analyse measurements.csv │
 │ - Output:                                                         │
 │   * Neutral bias                                                  │
 │   * ΔE per patch                                                  │
 │   * Suggested CMY adjustment                                      │
 │ - Apply CMY adjustments in driver                                 │
 └───────────────────────────────────────────────────────────────────┘
               │
               ▼
 ┌────────────────────────────┐
 │ 5. Iterate for Convergence │
 │                            │
 │ - Reprint same chart       │
 │ - Dry completely           │
 │ - Re-measure               │
 │ - Analyse again            │
 │ - Track ΔE and bias trend  │
 │ - Repeat until stable      │
 └─────────────┬──────────────┘
               │
               ▼
 ┌──────────────────────────────┐
 │ 6. Optional Colour Patch ΔE  │
 │                              │
 │ - Analyse colour chart       │
 │ - Verify ΔE < ~4 per patch   │
 │ - Detect hue/saturation drift│
 └─────────────┬────────────────┘
               │
               ▼
 ┌─────────────────────────────────────────────────────┐
 │ 7. Export ICC Profile                               │
 │                                                     │
 │ - Run: python -m printer_calibration.cli export-icc │
 │ - Output: custom_neutral_printer.icc                │
 │ - Apply ICC in all future prints                    │
 └─────────────┬───────────────────────────────────────┘
               │
               ▼
 ┌─────────────────────────────────┐
 │ 8. Verify & Use                 │
 │                                 │
 │ - Test print with ICC           │
 │ - Ensure neutrals and highlights│
 │   are stable                    │
 │ - Adjust if any new drift       │
 └─────────────────────────────────┘
```

# Printer Colour Balance

A collection of Python scripts for analyzing and adjusting printer color balance using ICC profiles and colorimetric data.

## Modules

*   `analysis.py`: Contains functions for analyzing color data and suggesting adjustments.
*   `charts.py`: Used for generating visual charts or color patches.
*   `config.py`: Configuration settings for the project, such as ink steps.
*   `convergence.py`: Used for iterative processes to converge on an ideal color balance.
*   `deltae.py`: Functions related to calculating Delta E values, a measure of color difference.
*   `icc.py`: Utilities for working with ICC color profiles.
*   `io.py`: Handles input/output operations, like loading CSV data.
*   `workflow.py`: Appears to orchestrate the overall color balancing process.

## Dependencies

The required Python packages are listed in the `requirements.txt` file. You can install them using pip:

```bash
pip install -r requirements.txt
```

## Usage

The command-line interface has been moved into the package as
``printer_calibration.cli``. Run it from the repository root using Python's
module invocation so imports resolve correctly:

```bash
python -m printer_calibration.cli <command> [options]
```

Common commands:

- `generate-chart`: produce a neutral or colour test chart
- `analyse`: analyse measured patch CSV files and suggest adjustments
- `plot`: visualise convergence metrics across runs
- `export-icc`: export a final ICC profile after convergence

The `generate-chart` command accepts additional options to control output
format and resolution:

- `--output` / `-o`: write the generated chart to the given filename
- `--format`: explicitly set the image format passed to the saver (e.g. `PDF`)
- `--dpi`: specify the DPI used for layout when generating neutral charts

For example, to analyse a CSV of measured patches::

	python -m printer_calibration.cli analyse path/to/measurements.csv

Measurement CSV format
----------------------

The code expects measurement CSV files to include these columns:

- `patch`: patch identifier (string or integer)
- `rgb`: printed patch nominal RGB value or code (e.g. single-channel levels like 100, 150)
- `L`, `a`, `b`: measured CIELAB values for the patch

Small example CSV contents::

	patch,rgb,L,a,b
	0,100,53.2,-0.5,1.2
	1,150,67.1,0.1,-0.9

If required columns are missing `printer_calibration.io.load_csv` will
raise a ``ValueError``.

Utilities
---------

- `printer_calibration.validate_csv`: small CLI to validate measurement CSVs. Run:

```bash
python -m printer_calibration.validate_csv printer_calibration/example_measurements.csv
```

- `printer_calibration/example_measurements.csv`: example measurement file you can use to test the CLI and validation.

Saving charts as PDF
--------------------

Both chart generators can save PDF output. Either pass a filename
ending with `.pdf` or call the functions with `format='PDF'`:

```py
from printer_calibration import charts
charts.generate_colour_chart('colour.pdf', format='PDF')
```

Running tests
-------------

Run the project's unit tests from the repository root:

```bash
python -m unittest discover -v
```

You can also run the style checks with `flake8` if installed:

```bash
flake8 printer_calibration
```

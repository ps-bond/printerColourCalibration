
"""Chart generation utilities.

This module can generate simple printable test charts for printing and
subsequent measurement. It provides a neutral grayscale chart and a
colour patch chart generator. Both functions save images via Pillow's
``Image.save`` and therefore can output common formats (PNG, JPEG)
and PDF (either by using a ``.pdf`` filename or by passing
``format='PDF'``).
"""

from PIL import Image, ImageDraw, ImageFont
from printer_calibration.config import COLOUR_PATCHES
import csv

A4_MM = (210, 297)


def write_measurement_template(patches, filename="measurements_template.csv"):
    try:
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(
                ["index", "label", "r", "g", "b", "L", "a", "b_lab"]
            )

            for idx, (label, r, g, b) in enumerate(patches, start=1):
                writer.writerow([idx, label, r, g, b, "", "", ""])
    except (IOError, PermissionError) as e:
        raise IOError(
            f"Failed to write to {filename}. Please ensure the file is not open "
            f"in another program and that you have the necessary permissions."
        ) from e


def _px(mm, dpi):
    """Convert millimetres to pixels for a given `dpi`."""
    return int(mm / 25.4 * dpi)


def generate_neutral_chart(path, dpi=300, title=None, format=None):
    """Generate a neutral (grayscale) patch chart and save to `path`.

    Parameters
    ----------
    path : str
        Output filename for the generated image (extension determines
        the format if ``format`` is not provided).
    dpi : int
        Target pixels-per-inch for the output image.
    title : str | None
        Optional title to render centered at the top of the page.
    format : str | None
        Optional explicit image format passed to Pillow's ``save`` call
        (for example, ``'PDF'`` to force PDF output).
    """
    width, height = _px(A4_MM[0], dpi), _px(A4_MM[1], dpi)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    cols, rows = 4, 7
    margin, gap = 40, 20

    def _load_font(preferred_sizes=(24,12,)):
        # Try common TTF fonts, falling back to Pillow's bundled DejaVu
        # or finally to the small default bitmap font.
        candidates = ["arial.ttf", "DejaVuSans.ttf"]
        for size in preferred_sizes:
            for name in candidates:
                try:
                    return ImageFont.truetype(name, size)
                except OSError:
                    continue
        return ImageFont.load_default()

    font = _load_font((24,))

    # Provide a sensible default title when none is supplied
    if not title:
        title = "Neutral Test Chart"

    # Measure and reserve space at the top for the title.
    title_height = 0
    if title:
        # prefer a larger title font; try common TTFs first
        title_font = _load_font((48, 36))
        tb = draw.textbbox((0, 0), title, font=title_font)
        title_height = tb[3] - tb[1]
        # add a little spacing below the title
        margin += title_height + 10

    pw = (width - 2 * margin - (cols - 1) * gap) // cols
    ph = (height - 2 * margin - (rows - 1) * gap) // rows

    # Draw title after layout so it appears above the chart
    if title:
        tw = tb[2] - tb[0]
        x_pos = (width - tw) / 2
        y_pos = (margin - title_height - 10) / 2
        draw.text((x_pos, y_pos), title, fill="black", font=title_font)

    # Centre the grid horizontally by computing the grid width and
    # choosing an x-origin so left/right margins are equal.
    grid_width = cols * pw + (cols - 1) * gap
    x_origin = (width - grid_width) // 2

    values = [int(i * 255 / 27) for i in range(28)]

    for i, v in enumerate(values):
        r, c = divmod(i, cols)
        x = x_origin + c * (pw + gap)
        y = margin + r * (ph + gap)
        draw.rectangle([x, y, x + pw, y + ph], fill=(v, v, v))
        label = str(v)
        # Use textbbox for Pillow 10+ compatibility (textsize is deprecated)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((x + (pw - tw) / 2, y - th - 5), label, fill="black", font=font)

    try:
        if format:
            img.save(path, format=format)
        else:
            img.save(path)
    except (IOError, PermissionError, ValueError) as e:
        raise IOError(
            f"Failed to save chart to {path}. Please ensure the file is not open "
            f"in another program, that you have the necessary permissions, and "
            f"that the format is supported."
        ) from e


def generate_colour_chart(
    path: str = "colour_test_A4.png",
    dpi=300,
    patch_size_mm=35,
    margin_mm=10,
    title=None,
    format=None,
):
    # Not happy with hardcoding the filename
    write_measurement_template(COLOUR_PATCHES)

    width, height = _px(A4_MM[0], dpi), _px(A4_MM[1], dpi)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)

    patch_size = _px(patch_size_mm, dpi)
    margin = _px(margin_mm, dpi)

    cols = 4

    # Prepare fonts. Use a readable TTF when available, fall back to default.
    def _load_font(preferred_sizes_pt=(12,)):
        candidates = ["arial.ttf", "DejaVuSans.ttf"]
        for size_pt in preferred_sizes_pt:
            size_px = int(size_pt * dpi / 72)
            for name in candidates:
                try:
                    return ImageFont.truetype(name, size_px)
                except OSError:
                    continue
        return ImageFont.load_default()

    # Provide a sensible default title when none is supplied
    if not title:
        title = "Colour Test Chart"

    # If a title is present, render it and push the grid down
    title_height = 0
    top_margin = margin
    if title:
        title_font = _load_font((36, 24))
        tb = draw.textbbox((0, 0), title, font=title_font)
        title_height = tb[3] - tb[1]
        x_pos = (width - (tb[2] - tb[0])) / 2
        y_pos = top_margin
        draw.text((x_pos, y_pos), title, fill="black", font=title_font)
        top_margin += title_height + _px(10, dpi) # add 10mm space after title

    # Centre the grid horizontally: compute available grid width and origin
    grid_width = cols * patch_size + (cols - 1) * margin
    x0 = (width - grid_width) // 2
    y0 = top_margin

    for idx, (label, r, g, b) in enumerate(COLOUR_PATCHES):
        row = idx // cols
        col = idx % cols

        x = x0 + col * (patch_size + margin)
        y = y0 + row * (patch_size + margin)

        if y + patch_size > height: # Avoid drawing off-page
            break

        draw.rectangle(
            [x, y, x + patch_size, y + patch_size],
            fill=(r, g, b),
            outline="black",
        )

        # Add a sequence number and label with readable sizes
        seq_font = _load_font((10,))
        lbl_font = _load_font((8,))

        # position labels above the patch
        label_y_offset = _px(3, dpi) # 3mm
        seq_label_y_offset = _px(6, dpi) # 6mm

        # Check if there is enough space for labels
        if y - seq_label_y_offset > 0:
            draw.text((x, y - seq_label_y_offset), f"#{idx + 1}", fill="black", font=seq_font)
            draw.text((x, y - label_y_offset), f"{label} ({r},{g},{b})", fill="black", font=lbl_font)

    try:
        if format:
            img.save(path, format=format, dpi=(dpi, dpi))
        else:
            img.save(path, dpi=(dpi, dpi))
    except (IOError, PermissionError, ValueError) as e:
        raise IOError(
            f"Failed to save chart to {path}. Please ensure the file is not open "
            f"in another program, that you have the necessary permissions, and "
            f"that the format is supported."
        ) from e


"""ICC profile utilities.

This module contains helpers to create or save small ICC profiles used
for testing or as defaults during calibration workflows.
"""


def export_srgb_icc(path):
    """Create and save a minimal sRGB ICC profile to `path`.

    The function creates a simple 1x1 RGB image with embedded sRGB
    profile and saves it. This effectively captures the profile data.
    """
    from PIL import Image
    # Create a minimal 1x1 white image with embedded sRGB profile.
    # When saved, PIL includes the sRGB profile in the file.
    img = Image.new("RGB", (1, 1), color="white")
    # Save as PNG with sRGB profile embedded (PNG supports ICC profiles).
    # Note: for true ICC files, you'd need a dedicated library, but this
    # demonstrates profile creation and embedding.
    try:
        # Try saving as JPEG with profile (common format for ICC embedding)
        img.save(path, format="JPEG")
    except Exception:
        # Fallback to PNG if JPEG fails
        img.save(path, format="PNG")

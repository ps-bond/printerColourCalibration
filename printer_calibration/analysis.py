"""Color analysis helpers.

This module implements utilities used by the calibration controller
for analyzing measurement data and suggesting adjustments.
"""

import numpy as np
import pandas as pd
import colour

from . import config
from .deltae import delta_e


def get_patch_lab(df, patch_name):
    """Extract (L, a, b) values for a specific patch by name."""
    patch = df[df["patch"] == patch_name]
    if patch.empty:
        return None
    return tuple(patch[["L", "a", "b"]].iloc[0])


def get_lab_distance(lab1: tuple, lab2: tuple) -> float:
    """Calculates the Euclidean distance (Delta E 1976) between two Lab values."""
    return np.sqrt((lab1[0] - lab2[0])**2 + (lab1[1] - lab2[1])**2 + (lab1[2] - lab2[2])**2)


def is_patch_within_target(patch_lab, targets):
    """Check if a patch's Lab values are within Phase 1 target ranges."""
    L, a, b = patch_lab
    return (
        targets.L_range[0] <= L <= targets.L_range[1] and
        targets.a_range[0] <= a <= targets.a_range[1] and
        targets.b_range[0] <= b <= targets.b_range[1]
    )


def suggest_adjustment(patch_lab, targets, steps):
    """Suggest per-channel ink adjustments from neutral errors for Phase 1."""
    _, a, b = patch_lab
    a_target = np.mean(targets.a_range)
    b_target = np.mean(targets.b_range)
    a_tol = (targets.a_range[1] - targets.a_range[0]) / 2
    b_tol = (targets.b_range[1] - targets.b_range[0]) / 2

    a_err = a - a_target
    b_err = b - b_target

    adj = {"C": 0, "M": 0, "Y": 0}

    if a_err > a_tol:
        adj["C"] += steps.fine
    elif a_err < -a_tol:
        adj["M"] += steps.fine

    if b_err > b_tol:
        adj["C"] += steps.fine
        adj["M"] += steps.fine
    elif b_err < -b_tol:
        adj["Y"] += steps.fine

    if abs(a_err) > a_tol * 2 or abs(b_err) > b_tol * 2:
        for channel, value in adj.items():
            if value != 0:
                adj[channel] = steps.coarse

    return adj


def get_reference_lab_values() -> dict:
    """
    Generates a dictionary of reference CIE-Lab values from the sRGB values
    in the config.COLOUR_PATCHES list.
    """
    # Normalize 8-bit RGB values to floating point 0.0-1.0
    rgb_patches = {name: (r/255, g/255, b/255) for name, r, g, b in config.COLOUR_PATCHES}

    # Convert sRGB to CIE-Lab
    # The conversion assumes standard sRGB primaries, D65 illuminant, and 2-degree observer,
    # which is the standard for sRGB.
    lab_patches = {
        name: colour.sRGB_to_Lab(rgb) for name, rgb in rgb_patches.items()
    }
    return lab_patches


def analyze_color_patches(df: pd.DataFrame, targets: config.Phase4Targets) -> tuple[bool, str]:
    """
    Analyzes the full color chart measurements against reference values.
    Computes Delta E (CIEDE2000) statistics and checks against Phase 4 targets.
    """
    reference_labs = get_reference_lab_values()
    measured_patches = {row['patch']: (row['L'], row['a'], row['b']) for _, row in df.iterrows()}

    delta_es = {}
    for name, measured_lab in measured_patches.items():
        if name in reference_labs:
            ref_lab = reference_labs[name]
            delta_es[name] = delta_e(measured_lab, ref_lab)

    if not delta_es:
        return False, "No matching patches found between measurements and references."

    de_values = np.array(list(delta_es.values()))
    mean_de = np.mean(de_values)
    p95_de = np.percentile(de_values, 95)
    max_de = np.max(de_values)
    
    skin_patches = [name for name in delta_es if name in targets.skin_tone_names]
    skin_de_values = [delta_es[name] for name in skin_patches]
    max_skin_de = max(skin_de_values) if skin_de_values else 0.0

    # Check against targets
    mean_ok = mean_de <= targets.mean_delta_e
    p95_ok = p95_de <= targets.percentile_95_delta_e
    max_ok = max_de <= targets.max_delta_e
    skin_ok = max_skin_de <= targets.skin_tone_delta_e

    passed = all([mean_ok, p95_ok, max_ok, skin_ok])

    def _check(v): return "✅" if v else "❌"

    report = (
        f"--- Phase 4 Colour Analysis ---\n"
        f"{_check(passed)} Overall Result: {'PASSED' if passed else 'FAILED'}\n\n"
        f"CIEDE2000 Statistics:\n"
        f"  {_check(mean_ok)} Mean ΔE:   {mean_de:.2f} (Target: ≤ {targets.mean_delta_e})\n"
        f"  {_check(p95_ok)} 95th % ΔE: {p95_de:.2f} (Target: ≤ {targets.percentile_95_delta_e})\n"
        f"  {_check(max_ok)} Max ΔE:    {max_de:.2f} (Target: ≤ {targets.max_delta_e})\n"
        f"  {_check(skin_ok)} Skin Tones ΔE: {max_skin_de:.2f} (Target: ≤ {targets.skin_tone_delta_e})\n"
    )

    return passed, report


"""Configuration dataclasses for calibration behaviour.

This module provides small immutable configuration containers used by
the analysis and workflow modules. They encapsulate tolerance targets
and step sizes for suggested adjustments.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Targets:
    """Target values and tolerances for neutral axis and deltaE.

    Attributes
    ----------
    a_neutral, b_neutral : float
        Desired neutral a/b values (typically ~0.0).
    a_tol, b_tol : float
        Acceptable tolerances for a and b.
    delta_e_tol : float
        Acceptable Delta E threshold for convergence.
    """
    a_neutral: float = 0.0
    b_neutral: float = 0.0
    a_tol: float = 1.5
    b_tol: float = 2.0
    delta_e_tol: float = 4.0


@dataclass(frozen=True)
class InkSteps:
    """Step sizes for coarse and fine ink adjustments."""
    coarse: int = 4
    fine: int = 1


COLOUR_PATCHES = [
    # Neutrals
    ("N0", 0, 0, 0),
    ("N64", 64, 64, 64),
    ("N128", 128, 128, 128),
    ("N192", 192, 192, 192),
    ("N224", 224, 224, 224),
    ("N240", 240, 240, 240),
    ("N248", 248, 248, 248),
    ("N255", 255, 255, 255),

    # Primaries
    ("R", 255, 0, 0),
    ("G", 0, 255, 0),
    ("B", 0, 0, 255),

    # Secondaries
    ("C", 0, 255, 255),
    ("M", 255, 0, 255),
    ("Y", 255, 255, 0),

    # Light tints
    ("R+64", 255, 64, 64),
    ("G+64", 64, 255, 64),
    ("B+64", 64, 64, 255),

    # Dark tones
    ("R-64", 192, 0, 0),
    ("G-64", 0, 192, 0),
    ("B-64", 0, 0, 192),

    # Memory colours
    ("Skin1", 224, 172, 105),
    ("Skin2", 198, 134, 66),
    ("Sky", 135, 206, 235),
    ("Leaf", 34, 139, 34),
]

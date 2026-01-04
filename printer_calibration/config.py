
"""Configuration dataclasses for calibration behaviour.

This module provides small immutable configuration containers used by
the analysis and workflow modules. They encapsulate tolerance targets
and step sizes for suggested adjustments.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Phase1Targets:
    """Target values and tolerances for Phase 1 (mid-grey anchor).

    Corresponds to patch RGB(100, 100, 100).
    """
    patch_name: str = "RGB100"
    L_range: Tuple[float, float] = (36.5, 39.5)
    a_range: Tuple[float, float] = (-2.0, 2.0)
    b_range: Tuple[float, float] = (-4.0, 4.0)


@dataclass(frozen=True)
class Phase2Targets:
    """Target values and tolerances for Phase 2 (neutral slope validation)."""
    rgb150_patch_name: str = "RGB150"
    rgb150_a_tol: float = 2.0
    rgb150_b_tol: float = 4.0

    rgb200_patch_name: str = "RGB200"
    rgb200_a_tol: float = 2.0
    rgb200_b_tol: float = 3.5


@dataclass(frozen=True)
class Phase4Targets:
    """Target values and tolerances for Phase 4 (colour patch analysis)."""
    mean_delta_e: float = 13.0
    percentile_95_delta_e: float = 24.0
    max_delta_e: float = 27.0
    skin_tone_delta_e: float = 12.0
    skin_tone_names: Tuple[str, ...] = ("Skin1", "Skin2")


@dataclass(frozen=True)
class Convergence:
    """Stopping criteria for iterative adjustments."""
    min_abs_change: float = 0.5


@dataclass(frozen=True)
class InkSteps:
    """Step sizes for coarse and fine ink adjustments."""
    coarse: int = 4
    fine: int = 1


# Patches used for neutral calibration phases 1 and 2.
NEUTRAL_PATCHES = [
    ("RGB100", 100, 100, 100),
    ("RGB150", 150, 150, 150),
    ("RGB200", 200, 200, 200),
]

# Patches used for full colour analysis in phase 4.
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

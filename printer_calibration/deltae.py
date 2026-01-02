
"""Delta E computations wrapper.

This module wraps third-party colour-science functionality to compute
perceptual colour differences between measured and reference Lab
triples.
"""

import colour


def delta_e(lab_meas, lab_ref):
    """Return the Delta E (CIEDE2000) between two Lab values.

    Parameters
    ----------
    lab_meas, lab_ref : sequence
        Lab triples (L, a, b) for measured and reference patches.

    Returns
    -------
    float
        The computed Delta E value.
    """
    return float(colour.delta_E(lab_meas, lab_ref, method="CIE 2000"))

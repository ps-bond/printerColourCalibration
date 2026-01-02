"""Color analysis helpers.

This module implements a couple of small utilities used by the
workflow: computing neutral-channel errors from measured patches and
suggesting simple per-channel adjustments based on configured step
sizes.
"""


def neutral_error(df):
    """Compute mean `a` and `b` for neutral mid-tone patches.

    The function selects rows where the `rgb` column is one of the
    neutral levels (100 or 150 in the reference data) and returns the
    mean `a` and `b` values. Returns a tuple `(a_mean, b_mean)`.
    """
    mid = df[df["rgb"].isin([100, 150])]
    return mid["a"].mean(), mid["b"].mean()


def suggest_adjustment(a, b, steps):
    """Suggest per-channel ink adjustments from neutral errors.

    Parameters
    ----------
    a, b : float
        Mean `a` and `b` offsets computed from `neutral_error`.
    steps : printer_calibration.config.InkSteps
        Step sizes for coarse and fine adjustments.

    Returns
    -------
    dict
        Mapping of channel keys (e.g. 'C','M','Y') to integer steps.
    """
    adj = {"C": 0, "M": 0, "Y": 0}
    if b < -3:
        adj["Y"] += steps.coarse
    elif b < -1:
        adj["Y"] += steps.fine
    if a < -2:
        adj["M"] += steps.fine
    return adj

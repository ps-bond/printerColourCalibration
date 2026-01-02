"""Helpers for plotting convergence history.

The module provides a simple convenience function to visualise metrics
collected across iterative calibration runs.

The primary function :func:`plot` returns a :class:`matplotlib.figure.Figure`
object so callers can save or display it. Tests and non-interactive callers
should use ``show=False`` (the default) to avoid blocking.

Example
-------
Run non-interactively and save to a file::

    from printer_calibration.convergence import plot

    history = {"a_mean": [0, 1, 0], "b_mean": [0, -1, 0]}
    plot(history, savepath="convergence.png")

Show interactively (blocking) in a GUI session::

    plot(history, show=True)

Obtain the figure object and manage closing yourself::

    fig = plot(history, auto_close=False)
    # do additional matplotlib operations
    from printer_calibration.convergence import close
    close(fig)

"""

import matplotlib.pyplot as plt


def plot(history, show=False, savepath=None, auto_close=True):
    """Plot convergence series stored in ``history``.

    Parameters
    ----------
    history : dict
        Mapping of metric names to sequences of numeric values.
    show : bool
        If True, call :func:`matplotlib.pyplot.show()` to display the plot.
    savepath : str | None
        If provided, save the figure to this path using
        :meth:`matplotlib.figure.Figure.savefig`.
    auto_close : bool
        If True (default) close the figure after save/show to avoid
        leaking GUI resources in long-running processes or tests.

    Returns
    -------
    matplotlib.figure.Figure
        The created figure object.
    """
    fig, ax = plt.subplots()
    for k, v in history.items():
        ax.plot(v, label=k)
    ax.axhline(0, linestyle="--", color="grey")
    ax.legend()
    ax.grid(True)

    if savepath:
        fig.savefig(savepath)

    if show:
        plt.show()

    if auto_close:
        plt.close(fig)

    return fig


def close(fig):
    """Close a figure created by :func:`plot`.

    This is a convenience wrapper around :func:`matplotlib.pyplot.close`.
    """
    plt.close(fig)

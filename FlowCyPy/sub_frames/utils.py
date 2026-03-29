import numpy as np
import pint_pandas
from TypedUnit import Quantity


def clip_data(
    signal: pint_pandas.PintArray, clip_value: str | Quantity = None
) -> pint_pandas.PintArray:
    """
    Clips the data in a PintArray based on a specified threshold.
    If `clip_value` is a string ending with '%', it is treated as a percentage of the maximum value.
    If `clip_value` is a Quantity, it is used as the threshold value.
    If `clip_value` is None, no clipping is performed.
    Parameters
    ----------
    signal : pint_pandas.PintArray
        The data to be clipped.
    clip_value : str or Quantity, optional
        The clipping threshold. If a string, it should end with '%'. If a Quantity, it should have compatible units.
        If None, no clipping is performed.
    Returns
    -------
    pint_pandas.PintArray
        The clipped data.
    """
    if clip_value is None:
        # If no clip value is provided, return the original signal.
        return signal

    # Remove data above the clip threshold if clip_value is provided.
    if clip_value is not None:
        if isinstance(clip_value, str) and clip_value.endswith("%"):
            # For a percentage clip, compute the threshold quantile.
            percent = float(clip_value.rstrip("%"))
            clip_value = np.percentile(signal, 100 - percent)
        else:
            clip_value = clip_value.to(signal.pint.signal_units).magnitude
        # Remove values above clip_value instead of clipping them.
        signal = signal[signal <= clip_value]

    return signal

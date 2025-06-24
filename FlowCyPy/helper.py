# -*- coding: utf-8 -*-
from functools import wraps
import inspect
from FlowCyPy.units import Quantity
from functools import wraps



def validate_input_units(**expected_units):
    """
    Decorator to enforce that function arguments of type Quantity have the correct units.

    Parameters
    ----------
    expected_units : dict
        A dictionary where keys are argument names and values are the expected Pint units.

    Raises
    ------
    ValueError
        If any argument does not have the expected unit.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature and argument values
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            for arg_name, expected_unit in expected_units.items():
                if arg_name in bound_args.arguments:
                    value = bound_args.arguments[arg_name]

                    if value is None:
                        continue

                    # Check if the value is a Pint Quantity
                    if not isinstance(value, Quantity):
                        raise TypeError(f"Argument '{arg_name}' must be a Pint Quantity, but got {type(value)}")

                    # Check if the argument has the expected units
                    if not value.check(value.units):
                        raise ValueError(f"Argument '{arg_name}' must have units of {expected_unit}, but got {value.units}")

            return func(*bound_args.args, **bound_args.kwargs)

        return wrapper
    return decorator






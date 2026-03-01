#!/usr/bin/env python
# -*- coding: utf-8 -*-
# =============================================================================
#                    Author: Florent TOURNOIS | License: MIT
# =============================================================================
"""
pymdtools.common.core
=====================

Core (non-I/O) utilities for the ``pymdtools.common`` package.

This module contains:
- **Typing primitives** used across the project (TypeVars, ParamSpec, PathInput)
- A **runtime error enrichment decorator** (``handle_exception``)
- A **constant descriptor** (``Constant``)
- A small decorator to emulate **function static attributes** (``static``)

It intentionally avoids any filesystem or text/markdown specific logic. Those
concerns live in sibling modules (e.g. ``pymdtools.common.fs`` and
``pymdtools.common.text``).

Stability
---------
Symbols re-exported from ``pymdtools.common`` are considered part of the public
API. This module is an implementation unit; however, the functions/classes
below are designed to remain stable because they are re-exported by the package
façade.

No heavy dependencies
---------------------
This file has no third-party dependency. It only uses Python's standard library.

Validation helper
~~~~~~~~~~~~~~~~~

check_len(obj, expected=1, *, name="object") -> obj
    Ensure that an object has an expected length, raising informative errors.

    
Examples
--------
Enrich exceptions with contextual metadata:

    >>> from pymdtools.common import handle_exception
    >>>
    >>> @handle_exception("Error while converting file", filename="File")
    ... def convert(filename: str) -> None:
    ...     raise ValueError("Invalid format")
    ...
    >>> convert(filename="doc.md")
    Traceback (most recent call last):
        ...
    RuntimeError: Invalid format
    Error while converting file (convert)
    File : doc.md

Define immutable constants on a class:

    >>> from pymdtools.common import Constant
    >>>
    >>> class Config:
    ...     VERSION = Constant("1.0")
    ...
    >>> Config.VERSION
    '1.0'
    >>> Config().VERSION
    '1.0'

Emulate static variables in a function:

    >>> from pymdtools.common import static
    >>>
    >>> @static(counter=0)
    ... def f():
    ...     f.counter += 1
    ...     return f.counter
    ...
    >>> f()
    1
    >>> f()
    2
"""

from __future__ import annotations

import functools
from os import PathLike
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    Mapping,
    Optional,
    ParamSpec,
    Sized,
    TypeVar,
)

# =============================================================================
# Typing variables (copied from common.py, unchanged)
# =============================================================================

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
P = ParamSpec("P")
R = TypeVar("R")
T_sized = TypeVar("T_sized", bound=Sized)
PathInput = str | PathLike[str] | Path


# =============================================================================
# Core helpers (exceptions, decorators, lightweight utilities)
# =============================================================================


# -----------------------------------------------------------------------------
def handle_exception(
    action_desc: str, 
    **kwargs_print_name: str
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator used to enrich exceptions with contextual information.

    This decorator catches any exception raised by the decorated function,
    enriches the error message with:
      - a functional description (`action_desc`),
      - the decorated function name,
      - selected keyword argument values (as provided via `kwargs_print_name`),
    and then re-raises a `RuntimeError` while preserving the original exception
    using exception chaining (`raise ... from ex`).

    The original exception is accessible through the `__cause__` attribute.

    Typing / Pylance compatibility
    ------------------------------
    This implementation uses `ParamSpec` and `TypeVar` so that the decorated
    function signature is preserved for static type checkers (Pylance/Pyright,
    mypy). That means:
      - argument types are preserved,
      - return type is preserved,
      - call sites benefit from autocompletion and type checking.

    Parameters
    ----------
    action_desc : str
        Human-readable description of the action being performed.
        Example: "Error while processing markdown file".
    **kwargs_print_name : str
        Mapping between keyword argument names of the decorated function and
        their display labels to include in the error message.

        Each key must match a keyword argument name used when calling the
        decorated function. Only keyword arguments present in the actual call
        are printed.

        Example:
            filename="File", output_dir="Output directory"

    Returns
    -------
    Callable[[Callable[P, R]], Callable[P, R]]
        A decorator which wraps the target function while preserving its
        signature (Pylance-friendly).

    Raises
    ------
    RuntimeError
        Raised when the decorated function fails. The original exception is
        attached as the cause and can be accessed through `__cause__`.

    Notes
    -----
    - Only keyword arguments (`**kwargs`) are included in the enriched message.
      If you also want positional arguments (`*args`) to be displayed, use
      `inspect.signature(...).bind_partial(...)` to map them to parameter names.
    - The formatting is intentionally simple and stable for logs/CLI.

    Examples
    --------
    >>> @handle_exception(
    ...     "Error while converting file",
    ...     filename="File",
    ...     output="Output directory",
    ... )
    ... def convert(filename: str, output: str) -> None:
    ...     raise ValueError("Invalid format")
    ...
    >>> convert("doc.md", "/tmp")
    Traceback (most recent call last):
        ...
    RuntimeError: Invalid format
    Error while converting file (convert)
    File : doc.md
    Output directory : /tmp
    """

    labels: Mapping[str, str] = kwargs_print_name

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return func(*args, **kwargs)
            except Exception as ex:
                lines = [f"{action_desc} ({func.__name__})"]
                for key, label in labels.items():
                    if key in kwargs:
                        lines.append(f"{label} : {kwargs[key]}")
                message = "\n".join(lines)
                raise RuntimeError(f"{ex}\n{message}") from ex

        return wrapper

    return decorator
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
class Constant(Generic[T]):
    """
    Descriptor representing an immutable constant value.

    This class is intended to be used as a *class attribute* and provides
    read-only access to a fixed value through both the class and its instances.

    The constant value cannot be modified or deleted **via an instance**.
    Any attempt to assign or delete the attribute on an instance will raise
    a `ValueError`.

    Note:
        Assignment at the *class level* (e.g. ``MyClass.CONST = ...``) is not
        prevented. This is a limitation of Python descriptors and is considered
        acceptable by design. Preventing class-level reassignment would require
        a metaclass or custom `__setattr__` logic on the owning class.

    Example:
        class Config:
            VERSION = Constant("1.0")
            DEBUG = Constant(False)

        Config.VERSION        # "1.0"
        Config().VERSION      # "1.0"

        Config().VERSION = "2.0"
        # ValueError: You can't change a constant value

        Config.VERSION = "2.0"
        # Allowed: the descriptor is replaced at the class level
    """

    def __init__(self, value: Optional[T] = None):
        self._value = value

    def __get__(self, instance: Any, owner: Any) -> Optional[T]:
        return self._value

    def __set__(self, instance: Any, value: Any) -> None:
        raise ValueError("You can't change a constant value")
    
    def __delete__(self, instance: Any) -> None:
        raise ValueError("Cannot delete a constant value")

    @property
    def value(self) -> Optional[T]:
        """Return the constant value."""
        return self._value
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
def static(**attributes: Any) -> Callable[[F], F]:
    """
    Attach static attributes to a function.

    This decorator sets attributes on the decorated function object. It is
    typically used to emulate "static variables" inside a function, i.e. to
    keep state across calls without using globals.

    Args:
        **attributes: Attribute names and their initial values to attach to the
            function.

    Returns:
        A decorator that returns the same function with attributes set.

    Example:
        >>> @static(counter=0)
        ... def f():
        ...     f.counter += 1
        ...     return f.counter
        ...
        >>> f()
        1
        >>> f()
        2
    """
    def decorator(func: F) -> F:
        for key, value in attributes.items():
            setattr(func, key, value)
        return func

    return decorator
# -----------------------------------------------------------------------------


# =============================================================================
# Validation helpers
# =============================================================================


# -----------------------------------------------------------------------------
def check_len(
    obj: T_sized, 
    expected: int = 1, 
    *, 
    name: str = "object"
) -> T_sized:
    """
    Ensure that an object has the expected length.

    Args:
        obj: Any object supporting len().
        expected: Expected length (must be >= 0).
        name: Logical name used in error messages.

    Returns:
        The input object (for fluent-style usage).

    Raises:
        ValueError: If the object's length does not match `expected`,
            or if `expected` is negative.
        TypeError: If `obj` does not support len().
    """
    if expected < 0:
        raise ValueError(f"expected length must be >= 0, got: {expected}")

    try:
        actual = len(obj)
    except TypeError as ex:
        raise TypeError(f"{name} does not support len()") from ex

    if actual != expected:
        raise ValueError(f"{name} must have length {expected}, got {actual}")

    return obj
# -----------------------------------------------------------------------------


# =============================================================================
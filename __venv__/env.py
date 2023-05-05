# The MIT License (MIT)
#
# Copyright 2020-2022 Python Packaging Authority
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import glob
import os
import pathlib
import re

FALSE_VALUES = ("0", "false", "no", "off")
TRUE_VALUES = ("1", "true", "yes", "on")


def env_to_bool(val):
    """
    Convert **val** to boolean, returning True if truthy or False if falsey

    :param Any val: The value to convert
    :return: False if falsey, True if truthy
    :rtype: bool
    :raises:
        ValueError: if val is not a valid boolean-like
    """
    if isinstance(val, bool):
        return val

    try:
        if val.lower() in FALSE_VALUES:
            return False
        if val.lower() in TRUE_VALUES:
            return True
    except AttributeError:
        pass

    raise ValueError(f"Value is not a valid boolean-like: {val}")


def get_from_env(arg, prefix="PIPENV", check_for_negation=True, default=None):
    """
    Check the environment for a variable, returning its truthy or stringified value

    For example, setting ``PIPENV_NO_RESOLVE_VCS=1`` would mean that
    ``get_from_env("RESOLVE_VCS", prefix="PIPENV")`` would return ``False``.

    :param str arg: The name of the variable to look for
    :param str prefix: The prefix to attach to the variable, defaults to "PIPENV"
    :param bool check_for_negation: Whether to check for ``<PREFIX>_NO_<arg>``, defaults
        to True
    :param Optional[Union[str, bool]] default: The value to return if the environment variable does
        not exist, defaults to None
    :return: The value from the environment if available
    :rtype: Optional[Union[str, bool]]
    """
    negative_lookup = f"NO_{arg}"
    positive_lookup = arg
    if prefix:
        positive_lookup = f"{prefix}_{arg}"
        negative_lookup = f"{prefix}_{negative_lookup}"
    if positive_lookup in os.environ:
        value = os.environ[positive_lookup]
        try:
            return env_to_bool(value)
        except ValueError:
            return value
    if check_for_negation and negative_lookup in os.environ:
        value = os.environ[negative_lookup]
        try:
            return not env_to_bool(value)
        except ValueError:
            return value
    return default


def normalize_drive(path):
    """Normalize drive in path so they stay consistent.

    This currently only affects local drives on Windows, which can be
    identified with either upper or lower cased drive names. The case is
    always converted to uppercase because it seems to be preferred.

    See: <https://github.com/pypa/pipenv/issues/1218>
    """
    if os.name != "nt" or not isinstance(path, str):
        return path

    drive, tail = os.path.splitdrive(path)
    # Only match (lower cased) local drives (e.g. 'c:'), not UNC mounts.
    if drive.islower() and len(drive) == 2 and drive[1] == ":":
        return f"{drive.upper()}{tail}"

    return path


def normalize_pipfile_path(p):
    if p is None:
        return None
    loc = pathlib.Path(p)
    try:
        loc = loc.resolve()
    except OSError:
        loc = loc.absolute()
    # Recase the path properly on Windows. From https://stackoverflow.com/a/35229734/5043728
    if os.name == "nt":
        matches = glob.glob(re.sub(r"([^:/\\])(?=[/\\]|$)", r"[\1]", str(loc)))
        path_str = matches and matches[0] or str(loc)
    else:
        path_str = str(loc)
    return normalize_drive(os.path.abspath(path_str))


PIPENV_CUSTOM_VENV_NAME = get_from_env(
    "CUSTOM_VENV_NAME", check_for_negation=False
)
"""Tells Pipenv whether to name the venv something other than the default dir name."""

PIPENV_IGNORE_VIRTUALENVS = bool(get_from_env("IGNORE_VIRTUALENVS"))
"""If set, Pipenv will always assign a virtual environment for this project.

By default, Pipenv tries to detect whether it is run inside a virtual
environment, and reuses it if possible. This is usually the desired behavior,
and enables the user to use any user-built environments with Pipenv.
"""

PIPENV_USE_SYSTEM = False
PIPENV_VIRTUALENV = None
if "PIPENV_ACTIVE" not in os.environ and not PIPENV_IGNORE_VIRTUALENVS:
    PIPENV_VIRTUALENV = os.environ.get("VIRTUAL_ENV")
# Internal, support running in a different Python from sys.executable.
PIPENV_PYTHON = get_from_env("PYTHON", check_for_negation=False)

PIPENV_VENV_IN_PROJECT = get_from_env("VENV_IN_PROJECT")
""" When set True, will create or use the ``.venv`` in your project directory.
When Set False, will ignore the .venv in your project directory even if it exists.
If unset (default), will use the .venv of project directory should it exist, otherwise
  will create new virtual environments in a global location.
"""
pipenv_pipfile = get_from_env("PIPFILE", check_for_negation=False)
if pipenv_pipfile:
    if not os.path.isfile(pipenv_pipfile):
        raise RuntimeError("Given PIPENV_PIPFILE is not found!")

    else:
        pipenv_pipfile = normalize_pipfile_path(pipenv_pipfile)
        # Overwrite environment variable so that subprocesses can get the correct path.
        # See https://github.com/pypa/pipenv/issues/3584
        os.environ["PIPENV_PIPFILE"] = pipenv_pipfile
PIPENV_PIPFILE = pipenv_pipfile
"""If set, this specifies a custom Pipfile location.

When running pipenv from a location other than the same directory where the
Pipfile is located, instruct pipenv to find the Pipfile in the location
specified by this environment variable.

Default is to find Pipfile automatically in the current and parent directories.
See also ``PIPENV_MAX_DEPTH``.
"""
# NOTE: +1 because of a temporary bug in Pipenv.
PIPENV_MAX_DEPTH = int(get_from_env("MAX_DEPTH", default=3)) + 1
"""Maximum number of directories to recursively search for a Pipfile.

Default is 3. See also ``PIPENV_NO_INHERIT``.
"""

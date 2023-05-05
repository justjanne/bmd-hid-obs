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

import base64
import hashlib
import io
import os
import pathlib
import re

from __venv__ import env


def is_virtual_environment(path):
    """Check if a given path is a virtual environment's root.

    This is done by checking if the directory contains a Python executable in
    its bin/Scripts directory. Not technically correct, but good enough for
    general usage.
    """
    if not path.is_dir():
        return False
    for bindir_name in ("bin", "Scripts"):
        for python in path.joinpath(bindir_name).glob("python*"):
            try:
                exeness = python.is_file() and os.access(str(python), os.X_OK)
            except OSError:
                exeness = False
            if exeness:
                return True
    return False


def sanitize(name: str) -> str:
    # Replace dangerous characters into '_'. The length of the sanitized
    # project name is limited as 42 because of the limit of linux kernel
    #
    # 42 = 127 - len('/home//.local/share/virtualenvs//bin/python2') - 32 - len('-HASHHASH')
    #
    #      127 : BINPRM_BUF_SIZE - 1
    #       32 : Maximum length of username
    #
    # References:
    #   https://www.gnu.org/software/bash/manual/html_node/Double-Quotes.html
    #   http://www.tldp.org/LDP/abs/html/special-chars.html#FIELDREF
    #   https://github.com/torvalds/linux/blob/2bfe01ef/include/uapi/linux/binfmts.h#L18
    return re.sub(r'[ &$`!*@"()\[\]\\\r\n\t]', "_", name)[0:42]


def walk_up(bottom):
    """mimic os.walk, but walk 'up' instead of down the directory tree.
    From: https://gist.github.com/zdavkeos/1098474
    """

    bottom = os.path.realpath(bottom)

    # get files in current dir
    try:
        names = os.listdir(bottom)
    except Exception:
        return

    dirs, nondirs = [], []
    for name in names:
        if os.path.isdir(os.path.join(bottom, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    yield bottom, dirs, nondirs

    new_path = os.path.realpath(os.path.join(bottom, ".."))

    # see if we are at the top
    if new_path == bottom:
        return

    for x in walk_up(new_path):
        yield x


def find_pipfile(project_directory: str, max_depth=3):
    """Returns the path of a Pipfile in parent directories."""
    i = 0
    for c, _, _ in walk_up(project_directory):
        i += 1

        if i < max_depth:
            if "Pipfile":
                p = os.path.join(c, "Pipfile")
                if os.path.isfile(p):
                    return p
    raise RuntimeError("No Pipfile found!")


def pipfile_location(project_directory: str) -> str:
    if env.PIPENV_PIPFILE:
        return env.PIPENV_PIPFILE

    try:
        loc = find_pipfile(project_directory, max_depth=env.PIPENV_MAX_DEPTH)
    except RuntimeError:
        loc = "Pipfile"
    return env.normalize_pipfile_path(loc)


def get_virtualenv_hash(project_directory: str, name: str) -> (str, str):
    """Get the name of the virtualenv adjusted for windows if needed

    Returns (name, encoded_hash)
    """

    def get_name(name, location):
        name = sanitize(name)
        hash = hashlib.sha256(location.encode()).digest()[:6]
        encoded_hash = base64.urlsafe_b64encode(hash).decode()
        return name, encoded_hash[:8]

    clean_name, encoded_hash = get_name(name, pipfile_location(project_directory))
    venv_name = "{0}-{1}".format(clean_name, encoded_hash)

    # This should work most of the time for
    #   Case-sensitive filesystems,
    #   In-project venv
    #   "Proper" path casing (on non-case-sensitive filesystems).
    if (
            os.path.normcase("A") != os.path.normcase("a")
            or is_venv_in_project(project_directory)
            or get_workon_home().joinpath(venv_name).exists()
    ):
        return clean_name, encoded_hash

    # Check for different capitalization of the same project.
    for path in get_workon_home().iterdir():
        if not is_virtual_environment(path):
            continue
        try:
            env_name, hash_ = path.name.rsplit("-", 1)
        except ValueError:
            continue
        if len(hash_) != 8 or env_name.lower() != name.lower():
            continue
        return get_name(env_name, pipfile_location(project_directory).replace(name, env_name))

    # Use the default if no matching env exists.
    return clean_name, encoded_hash


def name(project_directory: str) -> str:
    return pipfile_location(project_directory).split(os.sep)[-2]


def virtualenv_name(project_directory: str) -> str:
    custom_name = env.PIPENV_CUSTOM_VENV_NAME
    if custom_name:
        return custom_name
    sanitized, encoded_hash = get_virtualenv_hash(project_directory, name(project_directory))
    suffix = ""
    if env.PIPENV_PYTHON:
        if os.path.isabs(env.PIPENV_PYTHON):
            suffix = "-{0}".format(os.path.basename(env.PIPENV_PYTHON))
        else:
            suffix = "-{0}".format(env.PIPENV_PYTHON)

    # If the pipfile was located at '/home/user/MY_PROJECT/Pipfile',
    # the name of its virtualenv will be 'my-project-wyUfYPqE'
    return sanitized + "-" + encoded_hash + suffix


def get_workon_home():
    workon_home = os.environ.get("WORKON_HOME")
    if not workon_home:
        if os.name == "nt":
            workon_home = "~/.virtualenvs"
        else:
            workon_home = os.path.join(
                os.environ.get("XDG_DATA_HOME", "~/.local/share"), "virtualenvs"
            )
    # Create directory if it does not already exist
    expanded_path = pathlib.Path(os.path.expandvars(workon_home)).expanduser()
    os.makedirs(expanded_path, exist_ok=True)
    return expanded_path


def virtualenv_exists(project_directory: str) -> bool:
    if os.path.exists(virtualenv_location(project_directory)):
        if os.name == "nt":
            extra = ["Scripts", "activate.bat"]
        else:
            extra = ["bin", "activate"]
        return os.path.isfile(os.sep.join([virtualenv_location(project_directory)] + extra))

    return False


def virtualenv_location(project_directory: str) -> str:
    # if VIRTUAL_ENV is set, use that.
    virtualenv_env = os.getenv("VIRTUAL_ENV")
    if (
            "PIPENV_ACTIVE" not in os.environ
            and not env.PIPENV_IGNORE_VIRTUALENVS
            and virtualenv_env
    ):
        return virtualenv_env

    return get_location_for_virtualenv(project_directory)


def is_venv_in_project(project_directory: str) -> bool:
    if env.PIPENV_VENV_IN_PROJECT is False:
        return False
    return env.PIPENV_VENV_IN_PROJECT or (
            project_directory
            and os.path.isdir(os.path.join(project_directory, ".venv"))
    )


def looks_like_dir(path):
    seps = (sep for sep in (os.path.sep, os.path.altsep) if sep is not None)
    return any(sep in path for sep in seps)


def get_location_for_virtualenv(project_directory: str) -> str:
    dot_venv = os.path.join(project_directory, ".venv")

    # If there's no .venv in project root, set location based on config.
    if not os.path.exists(dot_venv):
        if is_venv_in_project(project_directory):
            return dot_venv
        return str(get_workon_home().joinpath(virtualenv_name(project_directory)))

    # If .venv in project root is a directory, use it.
    if os.path.isdir(dot_venv):
        return dot_venv

    # Now we assume .venv in project root is a file. Use its content.
    with io.open(dot_venv) as f:
        name = f.read().strip()

    # If .venv file is empty, set location based on config.
    if not name:
        return str(get_workon_home().joinpath(virtualenv_name(project_directory)))

    # If content looks like a path, use it as a relative path.
    # Otherwise, use directory named after content in WORKON_HOME.
    if looks_like_dir(name):
        path = pathlib.Path(project_directory, name)
        return path.absolute().as_posix()
    return str(get_workon_home().joinpath(name))

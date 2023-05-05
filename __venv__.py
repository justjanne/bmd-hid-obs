import os
import site
import sys

base = os.path.join(os.path.dirname(__file__), ".venv")
bin_dir = os.path.join(base, "bin")

if sys.prefix != base:
    # prepend bin to PATH (this file is inside the bin directory)
    os.environ["PATH"] = os.pathsep.join([bin_dir] + os.environ.get("PATH", "").split(os.pathsep))
    os.environ["VIRTUAL_ENV"] = base  # virtual env is right above bin directory

    # add the virtual environments libraries to the host python import mechanism
    prev_length = len(sys.path)
    site.addsitedir(os.path.join(base, "lib", "python3.11", "site-packages"))
    sys.path[:] = sys.path[prev_length:] + sys.path[0:prev_length]

    sys.real_prefix = sys.prefix
    sys.prefix = base

activated = True

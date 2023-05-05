import os

from __venv__ import find, pivot

project_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
venv_directory = find.virtualenv_location(project_directory)

print("pivoting pwd to " + project_directory)
os.chdir(project_directory)

print("pivoting virtualenv to " + venv_directory)
pivot.activate_virtualenv(venv_directory)

activated = True

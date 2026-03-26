import tomllib
from pathlib import Path

with Path("pyproject.toml").open("rb") as pyproject_file:
    pyproject_data = tomllib.load(pyproject_file)

code = pyproject_data["project"]["version"]

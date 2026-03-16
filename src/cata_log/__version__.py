import tomllib

with open("pyproject.toml", "rb") as pyproject_file:
    pyproject_data = tomllib.load(pyproject_file)

code = pyproject_data["project"]["version"]

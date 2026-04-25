# Development Guide

## Setup

Install uv

```bash
pipx install uv
```

and install all dependencies in a venv

```bash
uv pip install --all-groups
```

Also install the pre-commit hooks

```bash
pre-commit install
```

Don't forget to activate the venv

```bash
source .venv/bin/activate
```

## Debug

To browse the sqlite3 db for debugging, install [sqlitebrowser](https://github.com/sqlitebrowser/sqlitebrowser).

There is a debug docker-compose file that can be used to run the application in debug mode.

## Testing

### Unittests

The projects tests are in the test/ directory.
You can run them from the project root with

```bash
pytest
```

## Validation and Linting

You can use the tools in tools/ to lint and check your changes.

The code is formatted using ruff.

Before every commit the code is formatted, checked and linted by pre-commit.

## IDE setups

## Zed

```json
"lsp": {
    "ruff": {
      "initialization_options": {
        "settings": {
          "configuration": "tools/ruff.toml",
        },
      },
    },
  },
  "languages": {
    "Markdown": {
      "remove_trailing_whitespace_on_save": true,
    },
    "Python": {
      "format_on_save": "on",
    },
    "HTML": {
      "format_on_save": "on",
      "formatter": {
        "external": {
          "command": "djlint",
          "arguments": [
            "-",
            "--reformat",
            "--configuration",
            "tools/djlintrc",
            "{buffer_path}",
          ],
        },
      },
    },
  }
```

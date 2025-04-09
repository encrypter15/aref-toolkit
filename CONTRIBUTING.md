# Contributing to AREF-Toolkit (Prometheus)

## Plugins
1. Add your script to `plugins/` with a `run(target, profile)` function.
2. Test it: `python src/main.py recon --target example.com --plugin your_plugin`.

## Code
- Lint with `flake8`.
- Test with `pytest`.
- Docstrings in Google style.

## Pull Requests
- Target `main`.
- Include tests and docs updates.

#!/usr/bin/env bash

export PYTHONWARNINGS="ignore:the imp module is deprecated in favour of importlib; see the module's documentation for alternative uses:DeprecationWarning:distutils"

exec python -m unittest discover -s tests -p test*.py
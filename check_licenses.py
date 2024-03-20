#!/usr/bin/env python3

"""License check script.

This script checks the licenses of Python modules listed in requirement files
against specified settings in a YAML configuration file.

Usage:
  license_check.py [-s SETTINGS] REQUIREMENTS... [OPTIONS]

Options:
  -h, --help            show this help message and exit
  -s SETTINGS, --settings SETTINGS
                        File containing license settings (default: .licenses.yaml)
  REQUIREMENTS         List of requirements files
  -v, --verbose         Output detailed results
  -d, --debug           Enable debug logging
"""

import argparse
import contextlib
import json
import logging
import re
import sys

import yaml

from license_check import check_licenses

logger = logging.getLogger(__name__)


DEFAULT_SETTINGS = ".licenses.yaml"


def file_to_list(filename):
    """Reads a file and returns a list of non-comment lines.

    Args:
        filename: The name of the file to read.

    Returns:
        A list of non-comment lines from the file.
    """
    with open(filename) as f:
        return [line for line in f.readlines() if not line.strip().startswith("#")]


def extract_requirement_module(line):
    """Extracts the module name from a requirement file line.

    Args:
        line: A line from a requirement file.

    Returns:
        The extracted module name, or None if not found.
    """
    try:
        return re.match("^[a-zA-Z0-9][a-z0-9A-Z-_]+", line)[0]
    except TypeError:
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--settings",
        "-s",
        type=str,
        default=DEFAULT_SETTINGS,
        help="File containing license settings",
    )
    parser.add_argument("requirements", type=str, nargs="+", help="List of requirements files")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--debug", "-d", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    with open(args.settings) as stream:
        try:
            settings = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logger.error("Error while loading settings file: %s", e)
            sys.exit(1)

    # get required modules
    requirements = []

    # remove settings file from args (for pre-commit)
    with contextlib.suppress(ValueError):
        args.requirements.remove(DEFAULT_SETTINGS)
    for file in args.requirements:
        requirements += [extract_requirement_module(line) for line in file_to_list(file)]

    results = check_licenses(settings, requirements)

    if args.verbose:
        print(json.dumps(results, indent=2))  # noqa: T201

    if results["fail"]:
        if not args.verbose:
            print(json.dumps(results["fail"], indent=2))  # noqa: T201
        sys.exit(1)

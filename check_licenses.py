#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import re

import yaml

from license_check import check_licenses

logger = logging.getLogger()


DEFAULT_SETTINGS = ".licenses.yaml"


def file_to_list(filename):
    with open(filename) as f:
        results = [line for line in f.readlines() if not line.strip().startswith("#")]
    return results


def extract_requirement_module(line):
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
    parser.add_argument(
        "requirements", type=str, nargs="+", help="List of requirements files"
    )
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--debug", "-d", action="store_true")

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    with open(args.settings, "r") as stream:
        try:
            settings = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logger.error("Error while loading settings file: {}".format(e))
            exit(1)

    # get required modules
    requirements = []

    # remove settings file from args (for pre-commit)
    try:
        args.requirements.remove(DEFAULT_SETTINGS)
    except ValueError:
        pass
    for file in args.requirements:
        requirements += [
            extract_requirement_module(line) for line in file_to_list(file)
        ]

    results = check_licenses(settings, requirements)

    if args.verbose:
        print(json.dumps(results, indent=2))

    if results["fail"]:
        if not args.verbose:
            print(json.dumps(results["fail"], indent=2))
        exit(1)

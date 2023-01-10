#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
from collections import defaultdict

import yaml

from license_check import (
    check_re_list,
    extract_requirement_module,
    file_to_list,
    get_license_string,
    re_compile_list,
)

logger = logging.getLogger()


DEFAULT_SETTINGS = ".licenses.yaml"

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

    ignored = set(settings.get("ignored", []))

    allowed = re_compile_list(filter(None, settings.get("allowed", [])))
    disallowed = re_compile_list(filter(None, settings.get("disallowed", [])))

    missing = settings.get("missing", {})

    results = {
        "ignored": [],
        "success": {},
        "fail": {},
    }

    to_check = defaultdict(list)
    # get licenses
    for module in filter(None, set(requirements)):
        if module in ignored:
            results["ignored"].append(module)
            continue

        try:
            license_str = get_license_string(module)
        except ValueError as e:
            try:
                # try correct with errata
                license_str = missing[module]
            except KeyError:
                # give up
                results["fail"][module] = str(e)
                continue

        to_check[license_str].append(module)

    for lic, modules in to_check.items():
        # first check forbidden licenses
        if check_re_list(lic, disallowed):
            results["fail"].update(dict.fromkeys(modules, lic))
        elif check_re_list(lic, allowed):
            results["success"].update(dict.fromkeys(modules, lic))
        else:
            results["fail"].update(dict.fromkeys(modules, lic))

    if args.verbose:
        print(json.dumps(results, indent=2))

    if results["fail"]:
        if not args.verbose:
            print(json.dumps(results["fail"], indent=2))
        exit(1)

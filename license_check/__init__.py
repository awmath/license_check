# -*- coding: utf-8 -*-
import json
import logging
import re
from collections import defaultdict
from urllib import request
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


def re_compile_list(patterns: list):
    return [re.compile(pattern) for pattern in patterns]


def check_re_list(text: str, regexes: list):
    return any(regex.match(text) for regex in regexes)


def normalize_license(license_text):
    # we don't want the full text
    try:
        license_text = license_text.split("\n")[0]
    except AttributeError:
        return None

    for char in [","]:
        license_text = license_text.replace(char, " ")
    license_text = re.sub(r"\(.+\)", "", license_text).strip()
    # remove multiple spaces

    return re.sub("  *", " ", license_text) or None


def get_license_string(module):
    url = f"https://pypi.org/pypi/{module}/json"
    try:
        response = request.urlopen(url)
    except HTTPError:
        raise ValueError("NOT FOUND")

    data = json.load(response)
    try:
        license_str = normalize_license(data["info"]["license"])
        if not license_str or license_str == "UNKNOWN":
            raise ValueError("NO LICENSE")

    except KeyError:
        raise ValueError("NO LICENSE")

    return license_str


def check_licenses(settings, requirements: list) -> dict:
    ignored = set(settings.get("ignored", []))

    allowed = re_compile_list(filter(None, settings.get("allowed", [])))
    disallowed = re_compile_list(filter(None, settings.get("disallowed", [])))

    missing = settings.get("missing", {}) or {}

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

    return results

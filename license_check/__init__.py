"""License check library.

This library provides functions for checking the licenses of Python modules
against specified allowed and disallowed licenses. It retrieves license
information from the Python Package Index (PyPI) and compares it to the
provided settings.
"""

import json
import logging
import re
from collections import defaultdict
from urllib import request
from urllib.error import HTTPError

logger = logging.getLogger(__name__)


def re_compile_list(patterns: list):
    """Compiles a list of regular expression patterns into a list of compiled regex objects.

    Args:
        patterns: A list of regular expression patterns as strings.

    Returns:
        A list of compiled regex objects.
    """
    return [re.compile(pattern) for pattern in patterns]


def check_re_list(text: str, regexes: list):
    """Checks if any of the given regular expressions match the text.

    Args:
        text: The text to check against the regexes.
        regexes: A list of compiled regex objects.

    Returns:
        True if any of the regexes match the text, False otherwise.
    """
    return any(regex.match(text) for regex in regexes)


def normalize_license(license_text):
    """Normalizes a license string for comparison.

    Args:
        license_text: The license text to normalize.

    Returns:
        The normalized license string, or None if normalization is not possible.
    """
    try:
        license_text = license_text.split("\n")[0]
    except AttributeError:
        return None

    for char in [","]:
        license_text = license_text.replace(char, " ")
    license_text = re.sub(r"\(.+\)", "", license_text).strip()
    # remove multiple spaces

    return re.sub("  *", " ", license_text) or None


def get_license_from_info(data):
    """Gets the license string from the "info" section of a PyPI package data dictionary.

    Args:
        data: The PyPI package data dictionary.

    Returns:
        The extracted license string, or None if not found or "UNKNOWN".
    """
    try:
        license_str = normalize_license(data["info"]["license"])

        if license_str == "UNKNOWN":
            return None
        return license_str or None
    except KeyError:
        return None


def get_licenses_from_classifiers(classifiers: list[str]) -> list[str]:
    """Yields license strings from the "classifiers" section of a PyPI package  data dictionary.

    Args:
        classifiers: A list of classifiers from the PyPI package data.

    Yields:
        License strings extracted from the classifiers that start with "License :: OSI Approved".
    """
    for classifier in classifiers:
        if classifier.startswith("License :: OSI Approved"):
            yield classifier.split("::")[-1].strip()


def get_license_strings(module):
    """Retrieves license strings for a given module from PyPI.

    Args:
        module: The name of the module to check.

    Returns:
        A list of license strings extracted from PyPI.

    Raises:
        ValueError: If the module is not found on PyPI or has no license information.
    """
    url = f"https://pypi.org/pypi/{module}/json"
    try:
        response = request.urlopen(url)  # noqa: S310
    except HTTPError as err:
        msg = "NOT FOUND"
        raise ValueError(msg) from err

    data = json.load(response)
    license_from_info = get_license_from_info(data)
    try:
        licenses_from_classifiers = list(get_licenses_from_classifiers(data["info"]["classifiers"]))
    except KeyError:
        licenses_from_classifiers = []
    licenses = set(licenses_from_classifiers)
    if license_from_info:
        licenses.add(license_from_info)

    if len(licenses) == 0:
        msg = "NO LICENSE"
        raise ValueError(msg)

    licenses = list(licenses)
    licenses.sort()
    return licenses


def check_licenses(settings, requirements: list) -> dict:
    """Checks the licenses of modules against specified requirements.

    Args:
        settings: A dictionary containing license checking configuration.
        requirements: A list of module names to check.

    Returns:
        A dictionary containing the results of the license checks.
    """
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
            license_strings = get_license_strings(module)
        except ValueError as e:
            try:
                # try correct with errata
                license_strings = [missing[module]]
            except KeyError:
                # give up
                results["fail"][module] = str(e)
                continue

        for license_str in license_strings:
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

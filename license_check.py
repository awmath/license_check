#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from collections import defaultdict
import json
import logging
import re

import yaml
import urllib

logger = logging.getLogger(__name__)


def file_to_list(filename):
    with open(filename) as f:
        results = [line for line in f.readlines() if not line.strip().startswith('#')]
    return results


def extract_requirement_module(line):
    try:
        return re.match('^[a-zA-Z0-9][a-z0-9A-Z-_]+', line)[0]
    except TypeError:
        return None


def re_compile_list(patterns: list):
    return [re.compile(pattern) for pattern in patterns]


def check_re_list(text: str, regexes: list):
    return any(regex.match(text) for regex in regexes)


def normalize_license(license_text):
    # we don't want the full text
    license_text = license_text.split('\n')[0]
    for char in [',']:
        license_text = license_text.replace(char, ' ')
    license_text = re.sub(r'\(.+\)', '', license_text).strip()
    # remove multiple spaces
    return re.sub('  *', ' ', license_text)
from urllib.error import HTTPError
from urllib import request
def get_license_string(module):
    url = f'https://pypi.org/pypi/{module}/json'
    try:
        response = request.urlopen(url)
    except HTTPError:
        raise ValueError('NOT FOUND')

    data = json.load(response)
    try:
        license_str = normalize_license(data['info']['license'])
        if not license_str or license_str == 'UNKNOWN':
            raise ValueError('NO LICENSE')

    except KeyError:
        raise ValueError('NO LICENSE')

    return license_str

DEFAULT_SETTINGS='.licenses.yaml'

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--settings', '-s', type=str, default=DEFAULT_SETTINGS, help='File containing license settings')
    parser.add_argument('requirements', type=str, nargs='+', help='List of requirements files')
    parser.add_argument('--verbose', '-v', action='store_true')
    parser.add_argument('--debug', '-d', action='store_true')

    args = parser.parse_args()

    if args.debug:
        logger.setLevel(logging.DEBUG)

    with open(args.settings, "r") as stream:
        try:
            settings = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            logger.error('Error while loading settings file: {}'.format(e))
            exit(1)

    # get required modules
    requirements = []

    # remove settings file from args (for pre-commit)
    args.requirements.remove(DEFAULT_SETTINGS)
    for file in args.requirements:
        requirements += [extract_requirement_module(line) for line in file_to_list(file)]

    ignored = set(settings.get('ignored', []))

    allowed = re_compile_list(filter(None, settings.get('allowed', [])))
    disallowed = re_compile_list(filter(None, settings.get('disallowed', [])))

    missing = settings.get('missing', {})

    results = {
        'ignored': [],
        'success': {},
        'fail': {},
    }

    to_check = defaultdict(list)
    # get licenses
    for module in filter(None, set(requirements)):
        if module in ignored:
            results['ignored'].append(module)
            continue

        try:
            license_str = get_license_string(module)
        except ValueError as e:
            try:
                # try correct with errata
                license_str = missing[module]
            except KeyError:
                # give up
                results['fail'][module] = str(e)
                continue

        to_check[license_str].append(module)

    for lic, modules in to_check.items():
        # first check forbidden licenses
        if check_re_list(lic, disallowed):
            results['fail'].update(dict.fromkeys(modules, lic))
        elif check_re_list(lic, allowed):
            results['success'].update(dict.fromkeys(modules, lic))
        else:
            results['fail'].update(dict.fromkeys(modules, lic))

    if args.verbose:

        print(json.dumps(results, indent=2))

    if results['fail']:
        exit(1)

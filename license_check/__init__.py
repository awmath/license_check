
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
    try:
        license_text = license_text.split('\n')[0]
    except AttributeError:
        return None
    
    for char in [',']:
        license_text = license_text.replace(char, ' ')
    license_text = re.sub(r'\(.+\)', '', license_text).strip()
    # remove multiple spaces
    
    return re.sub('  *', ' ', license_text) or None
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

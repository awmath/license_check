"""Module setup."""

from setuptools import setup

setup(
    name="LicenseCheck",
    version="0.0.1",
    author="Axel Wegener",
    scripts=["check_licenses.py"],
    install_requires=["pyyaml"],
)

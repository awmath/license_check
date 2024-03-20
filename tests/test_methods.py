import pytest

from license_check import (
    check_licenses,
    get_license_from_info,
    get_license_strings,
    get_licenses_from_classifiers,
    normalize_license,
)


def test_missing_version_info(mocker):
    mocker.patch("license_check.normalize_license", return_value=None)
    mocker.patch("license_check.get_licenses_from_classifiers", return_value=[])
    with pytest.raises(ValueError, match="NO LICENSE"):
        get_license_strings("django")


def test_license_string_empty():
    assert normalize_license(None) is None
    assert normalize_license("") is None
    assert normalize_license(" ") is None


def test_get_license_from_info():
    assert get_license_from_info({"info": {"license": ""}}) is None
    assert get_license_from_info({"info": {"license": "UNKNOWN"}}) is None
    assert get_license_from_info({"info": {"license": None}}) is None
    assert get_license_from_info({"info": {}}) is None
    assert get_license_from_info({}) is None


def test_empty_settings():
    settings = {
        "allowed": [],
        "disallowed": [],
        "ignored": [],
        "missing": [],
    }
    check_licenses(settings, ["missing"])


def test_get_license_from_classifiers():
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "License :: OSI Approved :: Something License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: File Formats :: JSON",
        "Topic :: File Formats :: JSON :: JSON Schema",
    ]

    licenses = list(get_licenses_from_classifiers(classifiers))
    assert "MIT License" in licenses
    assert "Something License" in licenses
    assert len(licenses) == 2

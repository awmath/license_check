# -*- coding: utf-8 -*-
import pytest

from license_check import get_license_string, normalize_license


def test_missing_version_info(mocker):
    mocker.patch("license_check.normalize_license", return_value=None)
    with pytest.raises(ValueError, match="NO LICENSE"):
        get_license_string("django")


def test_license_string_empty():
    assert normalize_license(None) is None
    assert normalize_license("") is None
    assert normalize_license(" ") is None

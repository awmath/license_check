import pytest
from license_check import get_license_string, normalize_license

def test_missing_version_info():
    with pytest.raises(ValueError, match='NO LICENSE'):
        get_license_string('idna')

def test_license_string_empty():
    assert normalize_license(None) is None
    assert normalize_license('') is None
    assert normalize_license(' ') is None
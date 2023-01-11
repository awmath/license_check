# -*- coding: utf-8 -*-
import json
import subprocess


def test_success():
    result = subprocess.run(
        [
            "./check_licenses.py",
            "--settings=tests/license-settings.yaml",
            "tests/requirements/success.txt",
        ],
        capture_output=True,
    )
    assert result.returncode == 0
    assert result.stdout == b""
    assert result.stderr == b""


def test_success_verbose():
    result = subprocess.run(
        [
            "./check_licenses.py",
            "--settings=tests/license-settings.yaml",
            "--verbose",
            "tests/requirements/success.txt",
        ],
        capture_output=True,
    )
    data = json.loads(result.stdout.decode("utf-8"))
    assert result.returncode == 0
    assert data["ignored"] == ["ignoreme"]
    assert data["fail"] == {}
    assert data["success"] == {"django": "BSD-3-Clause", "iammissing": "BSD 2-Clause"}
    assert result.stderr == b""


def test_fail():
    result = subprocess.run(
        [
            "./check_licenses.py",
            "--settings=tests/license-settings.yaml",
            "tests/requirements/fail.txt",
        ],
        capture_output=True,
    )
    assert result.returncode == 1
    assert json.loads(result.stdout.decode("utf-8")) == {"pytest": "MIT"}
    assert result.stderr.decode("utf-8") == ""


def test_fail_verbose():
    result = subprocess.run(
        [
            "./check_licenses.py",
            "--settings=tests/license-settings.yaml",
            "--verbose",
            "tests/requirements/fail.txt",
        ],
        capture_output=True,
    )
    data = json.loads(result.stdout.decode("utf-8"))
    assert result.returncode == 1
    assert data["fail"] == {"pytest": "MIT"}
    assert data["ignored"] == ["ignoreme"]
    assert data["success"] == {"django": "BSD-3-Clause", "iammissing": "BSD 2-Clause"}
    assert result.stderr == b""

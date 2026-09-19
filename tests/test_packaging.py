"""Regression checks for installable ContextFlow package metadata."""

from __future__ import annotations

import importlib
from importlib import resources
import tomllib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_package_and_mcp_server_import() -> None:
    assert importlib.import_module("contextflow")
    assert importlib.import_module("contextflow.mcp")
    assert importlib.import_module("contextflow.mcp.server")


def test_mcp_console_script_targets_server_main() -> None:
    package_config = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert package_config["project"]["scripts"] == {
        "contextflow-mcp": "contextflow.mcp.server:main"
    }


def test_experiment_benchmark_is_a_packaged_resource() -> None:
    benchmark = resources.files("contextflow").joinpath(
        "data", "experiment_001.json"
    )

    assert benchmark.is_file()


def test_mcp_server_entry_point_accepts_help() -> None:
    from contextflow.mcp.server import main

    with pytest.raises(SystemExit, match="0"):
        main(["--help"])

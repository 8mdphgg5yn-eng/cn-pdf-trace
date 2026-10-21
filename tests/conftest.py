import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def gold(root):
    return json.loads((root/"fixtures/gold.json").read_text())


@pytest.fixture(scope="session")
def outputs(root, gold):
    stems = [Path(d["pdf"]).stem for d in gold["documents"]]
    for stem in stems:
        for name in ("document.md", "provenance.json", "check-report.md"):
            assert (root/f"output/{stem}"/name).is_file(), "先执行 python scripts/run_demo.py"
    return {stem: root/f"output/{stem}" for stem in stems}


@pytest.fixture(scope="session")
def converter(root):
    from cntrace.core import build_converter, offline_guard
    with offline_guard():
        return build_converter(root/".cache/models")


@pytest.fixture(scope="session")
def converters(root, converter):
    from cntrace.core import build_converter, offline_guard
    with offline_guard():
        return {"off": converter, "mac": build_converter(root/".cache/models", ocr="mac")}

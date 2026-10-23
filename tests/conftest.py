import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def root():
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def gold(root):
    return json.loads((root/"fixtures/gold.json").read_text())


MAC_OCR_SKIP = "需要macOS Vision OCR的样本在当前系统未生成；此项跳过，完整回归与验收不算通过"


class Outputs(dict):
    """Mapping whose macOS-OCR-only entries (or whole-mapping use) skip the test."""

    def __init__(self, bundles, unavailable):
        super().__init__(bundles)
        self.unavailable = unavailable

    def _whole(self):
        if self.unavailable:
            pytest.skip(MAC_OCR_SKIP)

    def __getitem__(self, stem):
        if stem in self.unavailable:
            pytest.skip(MAC_OCR_SKIP)
        return super().__getitem__(stem)

    def __iter__(self):
        self._whole()
        return super().__iter__()

    def __bool__(self):
        return bool(dict.__len__(self))

    def __len__(self):
        self._whole()
        return super().__len__()

    def items(self):
        self._whole()
        return super().items()

    def values(self):
        self._whole()
        return super().values()

    def keys(self):
        self._whole()
        return super().keys()


@pytest.fixture(scope="session")
def outputs(root, gold):
    from cntrace.core import MAC_OCR_AVAILABLE
    stems = [Path(d["pdf"]).stem for d in gold["documents"]]
    unavailable = set() if MAC_OCR_AVAILABLE else {
        Path(d["pdf"]).stem for d in gold["documents"] if d["ocr"] == "mac"}
    for stem in stems:
        if stem in unavailable:
            continue
        for name in ("document.md", "provenance.json", "check-report.md"):
            assert (root/f"output/{stem}"/name).is_file(), "先执行 python scripts/run_demo.py"
    return Outputs({stem: root/f"output/{stem}" for stem in stems}, unavailable)


@pytest.fixture(scope="session")
def converter(root):
    from cntrace.core import build_converter, offline_guard
    with offline_guard():
        return build_converter(root/".cache/models")


@pytest.fixture(scope="session")
def converters(root, converter):
    from cntrace.core import MAC_OCR_AVAILABLE, build_converter, offline_guard
    if not MAC_OCR_AVAILABLE:
        return Outputs({"off": converter}, {"mac"})
    with offline_guard():
        return {"off": converter, "mac": build_converter(root/".cache/models", ocr="mac")}
